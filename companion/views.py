import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from .models import ChatSession, AIChatLog, SOSLog
from .crisis import detect_crisis
from .emotion import score_emotion, is_crisis_by_score

logger = logging.getLogger(__name__)

FALLBACK_MESSAGE = "我在這裡。剛剛連線好像不太順，能再說一次嗎？"


def _session_list(user):
    """取得使用者所有 session，並附上標題（第一則使用者訊息前 20 字）。"""
    from django.db.models import Count, OuterRef, Subquery

    first_user_msg = (
        AIChatLog.objects
        .filter(session=OuterRef("pk"), sender="user")
        .order_by("created_at")
        .values("message_content")[:1]
    )

    sessions = list(
        ChatSession.objects
        .filter(user=user, is_deleted=False)
        .order_by("-created_at")
        .annotate(
            first_msg=Subquery(first_user_msg),
            msg_count=Count("logs"),
        )[:30]
    )

    for s in sessions:
        if s.first_msg:
            raw = s.first_msg
            s.title = raw[:20] + ("…" if len(raw) > 20 else "")
        else:
            s.title = s.created_at.strftime("%-m/%-d 的對話")

    return sessions


class ChatView(TemplateView):
    template_name = "chat.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        session_id = self.kwargs.get("session_id")

        # 所有 session 列表（含標題）
        all_sessions = _session_list(user)
        ctx["all_sessions"] = all_sessions

        # 目前 session（不存在或已刪除 → 導回 /chat/ 避免 404）
        if session_id:
            session = ChatSession.objects.filter(
                pk=session_id, user=user, is_deleted=False
            ).first()
        else:
            session = next(
                (s for s in all_sessions if s.end_time is None), None
            )
        ctx["session"] = session
        # 危機狀態從使用者層級讀取（跨 session，30 分鐘有效）
        profile = getattr(user, "profile", None)
        ctx["crisis_mode"] = profile.is_in_crisis if profile else False
        # 傳入到期時間（ISO 格式），讓前端 JS 計時自動隱藏漂浮條
        ctx["crisis_until_iso"] = (
            profile.crisis_until.isoformat() if profile and profile.crisis_until else ""
        )
        if session:
            ctx["logs"] = session.logs.order_by("created_at")
        return ctx


@login_required
@require_POST
def chat_new(request):
    """開啟新對話：結束所有活躍 session，導向空白聊天頁。"""
    ChatSession.objects.filter(
        user=request.user, end_time=None
    ).update(end_time=timezone.now())
    return redirect("chat")




@login_required
def session_list_partial(request):
    """HTMX：回傳 session 列表 HTML，供前端即時刷新側邊欄。"""
    sessions = _session_list(request.user)
    return render(request, "_partials/_session_list_partial.html", {"all_sessions": sessions})


@login_required
def chat_stream_send(request):
    """串流聊天端點：SSE 格式逐字推送 AI 回應。"""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    text = request.POST.get("message", "").strip()
    if not text:
        return JsonResponse({"error": "empty"}, status=400)

    provided_session_id = request.POST.get("session_id")
    session = None

    # 只接受未被軟刪除的 session；被刪掉的視同沒帶 session_id
    if provided_session_id:
        session = ChatSession.objects.filter(
            pk=provided_session_id, user=request.user, is_deleted=False
        ).first()

    if not session:
        with transaction.atomic():
            session = (
                ChatSession.objects
                .select_for_update()
                .filter(user=request.user, end_time=None, is_deleted=False)
                .first()
            )
            if not session:
                session = ChatSession.objects.create(user=request.user)

    # 前端需要更新 session-id：沒帶 id，或帶了但那個已被刪除（換到新 session）
    is_new_session = (
        not provided_session_id or str(session.pk) != str(provided_session_id)
    )

    # 防禦性存取（signal 未觸發或手動建立用戶時 profile 可能不存在）
    profile = getattr(request.user, "profile", None)
    if profile is None:
        from accounts.models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # 主偵測：Gemini 語意評分
    mood_score, mood_reason = score_emotion(session, text)

    if mood_score is not None:
        triggered = is_crisis_by_score(mood_score)
        detector = "llm_score"
        kw_trigger = f"score:{mood_score}"
    else:
        # Gemini 失敗 → 降級到關鍵字備援
        kw = detect_crisis(text)
        triggered = bool(kw)
        detector = "keyword_fallback"
        kw_trigger = kw or ""
        mood_score = None

    user_log = AIChatLog.objects.create(
        session=session, sender="user",
        message_content=text,
        crisis_flagged=triggered,
        mood_score=mood_score,
        mood_reasoning=mood_reason,
    )

    just_entered_crisis = False
    if triggered and not profile.is_in_crisis:
        profile.enter_crisis()
        session.enter_crisis()
        SOSLog.objects.create(
            user=request.user, chat_log=user_log,
            triggering_keyword=kw_trigger,
            detector=detector,
        )
        just_entered_crisis = True

    is_crisis = profile.is_in_crisis

    def _generate():
        from google import genai
        from google.genai import types
        from .prompts import NORMAL_SYSTEM_PROMPT, CRISIS_SYSTEM_PROMPT
        # 第一包：metadata（含 session_id 讓前端即時更新 URL 和 sidebar）
        yield f"data: {json.dumps({'type':'meta','crisis':is_crisis,'just_entered_crisis':just_entered_crisis,'session_id':session.id,'is_new_session':is_new_session})}\n\n"

        # 組歷史 contents
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        model  = settings.GEMINI_MODEL_CHAT
        system = CRISIS_SYSTEM_PROMPT if is_crisis else NORMAL_SYSTEM_PROMPT

        contents = []
        for log in session.logs.exclude(pk=user_log.pk).order_by("created_at"):
            role = "user" if log.sender == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=log.message_content)],
            ))
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=text)],
        ))

        full_text = ""
        try:
            stream = client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=0.8, max_output_tokens=2048,
                ),
            )
            for chunk in stream:
                if chunk.text:
                    full_text += chunk.text
                    yield f"data: {json.dumps({'type':'chunk','text':chunk.text})}\n\n"
        except Exception:
            logger.exception("Gemini 串流失敗（user=%s）", request.user.pk)
            full_text = FALLBACK_MESSAGE
            yield f"data: {json.dumps({'type':'chunk','text':full_text})}\n\n"

        # 串流結束後儲存完整回應
        AIChatLog.objects.create(
            session=session, sender="ai", message_content=full_text,
        )
        yield f"data: {json.dumps({'type':'done'})}\n\n"

    resp = StreamingHttpResponse(_generate(), content_type="text/event-stream; charset=utf-8")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"   # 關閉 Nginx 緩衝
    return resp


@login_required
@require_POST
def session_delete(request, session_id):
    """軟刪除：對用戶隱藏，後端保留資料。"""
    session = get_object_or_404(ChatSession, pk=session_id, user=request.user)
    session.is_deleted = True
    session.save(update_fields=["is_deleted"])

    # 非 HTMX（聊天區的刪除按鈕）→ 直接整頁導回 /chat/
    if not request.headers.get("HX-Request"):
        return redirect("chat")

    # HTMX：如果刪的是當前正在看的 session → 整頁導回 /chat/
    current_url = request.headers.get("HX-Current-URL", "")
    if f"/chat/{session_id}/" in current_url:
        resp = HttpResponse()
        resp["HX-Redirect"] = "/chat/"
        return resp

    # HTMX：刪的是列表裡其他 session → 把該列從 DOM 移除
    return render(request, "_partials/_empty.html")


