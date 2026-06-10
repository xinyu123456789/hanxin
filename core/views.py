import random
from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from growth.models import DailyTask, DailyTaskLog
from growth.views import _build_viz_ctx
from board.models import PresetMessage
from .models import SituationQuestion, SituationResponse


SESSION_KEY = "current_situation_qid"


def get_current_question(request):
    """
    為此 request 選出目前應顯示的情境題。

    優先順序：
      1. session 已記錄的題目（用戶上次在做的）
      2. 今天指定的每日題目（active_date == today）
      3. 備用題庫隨機一題（active_date is null）

    登入用戶：選出的 id 存進 session，F5 不換題。
    匿名用戶：不存 session，每次給今日/隨機題，F5 可能換。
    """
    today = timezone.localdate()

    # 1. session 有記錄 → 驗證題目還存在
    if request.user.is_authenticated:
        qid = request.session.get(SESSION_KEY)
        if qid:
            q = SituationQuestion.objects.filter(pk=qid, is_active=True).first()
            if q:
                return q

    # 2. 今天有指定題目
    q = SituationQuestion.objects.filter(active_date=today, is_active=True).first()

    # 3. 備用題庫隨機取一題
    if not q:
        pool = list(SituationQuestion.objects.filter(active_date__isnull=True, is_active=True))
        q = random.choice(pool) if pool else None

    # 存進 session（只存登入用戶）
    if q and request.user.is_authenticated:
        request.session[SESSION_KEY] = q.pk
        request.session.modified = True

    return q


def get_question_result(question):
    """
    計算這題的選擇百分比，並取 3 則公開的簡答（各取前 20 字）。
    回傳 dict 供模板渲染結果畫面。
    """
    # 選擇題統計
    choice_responses = SituationResponse.objects.filter(
        question=question, mode="choice"
    )
    total_choices = choice_responses.count()
    counts = {"a": 0, "b": 0, "c": 0}
    for r in choice_responses:
        if r.choice in counts:
            counts[r.choice] += 1

    def pct(n):
        return round(n / total_choices * 100) if total_choices else 0

    # 選項資料（含百分比），搭配 question.options 一起用
    option_results = [
        {"opt": "a", "label": question.option_a, "pct": pct(counts["a"])},
        {"opt": "b", "label": question.option_b, "pct": pct(counts["b"])},
        {"opt": "c", "label": question.option_c, "pct": pct(counts["c"])},
    ]

    # 公開簡答隨機取 3 則
    public_texts = list(
        SituationResponse.objects.filter(
            question=question, mode="text", is_public=True
        ).exclude(text_answer="")
    )
    samples = random.sample(public_texts, min(3, len(public_texts)))

    return {
        "option_results": option_results,
        "total_choices": total_choices,
        "sample_texts": [r.text_answer[:20] for r in samples],
    }

def situation_daily(request):
    """首頁情境題初始載入：依狀態回傳輸入或結果畫面。"""
    question = get_current_question(request)
    if not question:
        return render(request, "_partials/_situation_empty.html")

    if request.user.is_authenticated:
        answered = set(request.session.get("situation_answered", []))
        if question.pk in answered:
            return render(request, "_partials/_situation_result.html", {
                "question": question,
                **get_question_result(question),
            })

    return render(request, "_partials/_situation_input.html", {"question": question})


@require_POST
def situation_submit(request):
    """接收用戶回答，存入 DB，回傳結果畫面。
    每次送出都建新紀錄（允許重複回答同一題，第二輪才有意義）。
    防連點由前端 hx-disabled-elt 處理，不用 DB 查重。
    """
    qid  = request.POST.get("question_id", "")
    mode = request.POST.get("mode", "text")

    # qid 必須是合法整數，否則 Django 轉型會拋 ValueError
    if not qid or not str(qid).isdigit():
        return render(request, "_partials/_situation_empty.html")

    # mode 只接受合法值，非法輸入一律當 text 處理
    if mode not in ("text", "choice"):
        mode = "text"

    question = SituationQuestion.objects.filter(pk=qid, is_active=True).first()
    if not question:
        return render(request, "_partials/_situation_empty.html")

    # choice 模式下必須是合法選項
    choice = request.POST.get("choice", "")
    if mode == "choice" and choice not in ("a", "b", "c"):
        return render(request, "_partials/_situation_empty.html")

    text_answer = request.POST.get("text_answer", "").strip()[:200]
    is_public   = "is_public" in request.POST  # checkbox 未勾選時不提交欄位

    SituationResponse.objects.create(
        user        = request.user if request.user.is_authenticated else None,
        question    = question,
        mode        = mode,
        text_answer = text_answer if mode == "text" else "",
        choice      = choice if mode == "choice" else None,
        is_public   = is_public if mode == "text" else True,
    )

    # Session 記錄「這題已答」，讓 situation_daily F5 時顯示結果畫面
    answered = set(request.session.get("situation_answered", []))
    answered.add(question.pk)
    request.session["situation_answered"] = list(answered)
    request.session.modified = True

    return render(request, "_partials/_situation_result.html", {
        "question": question,
        **get_question_result(question),
    })


@require_POST
def situation_next(request):
    """換下一題：取尚未回答的題目，更新 session，回傳輸入畫面。"""
    # 當前題目 ID，無論如何都排除（不連續抽到同一題）
    current_qid_str = request.POST.get("current_qid", "")
    current_qid = int(current_qid_str) if current_qid_str.isdigit() else None

    answered_ids = set()
    if request.user.is_authenticated:
        answered_ids = set(
            SituationResponse.objects
            .filter(user=request.user)
            .values_list("question_id", flat=True)
        )

    # 第一輪：排除已答 + 當前題
    exclude_ids = answered_ids | ({current_qid} if current_qid else set())
    pool = list(
        SituationQuestion.objects.filter(is_active=True)
        .exclude(pk__in=exclude_ids)
    )

    if not pool:
        # 第二輪：全部答過，只排除當前題（避免連抽同一題）
        pool = list(
            SituationQuestion.objects.filter(is_active=True)
            .exclude(pk=current_qid) if current_qid else
            SituationQuestion.objects.filter(is_active=True)
        )

    question = random.choice(pool) if pool else None

    if question and request.user.is_authenticated:
        request.session[SESSION_KEY] = question.pk
        # 從「已答」清單移除這題，讓 F5 時顯示輸入畫面而非舊結果
        answered = set(request.session.get("situation_answered", []))
        answered.discard(question.pk)
        request.session["situation_answered"] = list(answered)
        request.session.modified = True

    if not question:
        return render(request, "_partials/_situation_empty.html")

    return render(request, "_partials/_situation_input.html", {"question": question})


WARM_WORDS = [
    "我懂你，這真的不容易",
    "辛苦了，你已經很努力了",
    "慢慢來，沒關係的",
    "你願意撐著，真的很勇敢",
    "今天有好好吃飯了嗎",
    "明天會比今天更亮一點",
    "謝謝你願意說出來",
    "抱一個，你不孤單",
    "你的存在本身就很好",
]


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()
        week_start = today - timedelta(days=6)  # 過去 7 天（含今天），與誇誇成長頁一致

        tasks = DailyTask.objects.filter(is_active=True)

        if user.is_authenticated:
            done_ids = set(
                DailyTaskLog.objects.filter(user=user, date=today)
                .values_list("task_id", flat=True)
            )
            week_kudos = user.kudos.filter(
                created_at__date__gte=week_start, is_deleted=False
            ).count()
            week_tasks = DailyTaskLog.objects.filter(
                user=user, date__range=(week_start, today)
            ).count()
            tree_points = week_kudos + week_tasks
            pref = getattr(user, "preference", None)
            tree_style = pref.tree_style if pref else "tree"
        else:
            today_str = str(today)
            guest_map = self.request.session.get("guest_done_tasks", {})
            done_ids = set(guest_map.get(today_str, []))
            tree_points = len(done_ids)
            tree_style = "tree"

        ctx["tasks"] = [(t, t.id in done_ids) for t in tasks]
        ctx["done_count"] = len(done_ids)
        ctx["task_total"] = len(ctx["tasks"])
        ctx["tree_points"] = tree_points
        ctx["tree_style"] = tree_style
        ctx.update(_build_viz_ctx(user, tree_style, tree_points))

        from django.core.cache import cache
        cached_words = cache.get("home_warm_words")
        if cached_words is None:
            cached_words = list(
                PresetMessage.objects.filter(is_active=True).values_list("content", flat=True)
            )
            cache.set("home_warm_words", cached_words, 300)  # 5 分鐘
        ctx["warm_word"] = random.choice(cached_words) if cached_words else random.choice(WARM_WORDS)

        # 周日晚上 8 點後提醒用戶建立本週回顧
        if user.is_authenticated:
            now = timezone.localtime()
            if now.weekday() == 6 and now.hour >= 20:
                from growth.models import WeeklyReview
                existing = WeeklyReview.objects.filter(
                    user=user, start_date=week_start
                ).first()
                has_narrative = existing and existing.summary_data.get("narrative")
                ctx["show_review_reminder"] = not has_narrative

        return ctx
