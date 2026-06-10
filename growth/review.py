"""
週回顧：收集過去 7 天（含今天）的所有活動，用 Gemini 生成溫柔的個人化敘事。
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

REVIEW_PROMPT = """你是「涵涵」，涵心平台上溫柔的 AI 陪伴。
請根據以下用戶最近 7 天的完整活動記錄，撰寫一份**個人化的回顧報告**。

---

**輸出格式：使用 Markdown**，包含以下章節：

## 🌸 這七天的你

用 2-4 句溫柔的話開場，點出這七天最有感的主題或情緒走向。

## ✨ 這七天你做到的事

用條列式列出這七天值得被看見的事情（誇誇筆記的內容、完成的任務模式、與涵涵聊天的頻率等），每條加一句鼓勵或同理。

## 💬 心情的流動

根據情緒分數趨勢、看板發布的天氣類型，描述這七天情緒的高低起伏。
若有危機事件，溫柔地表達你在乎，並肯定用戶願意說出來的勇氣。
若情緒平均偏低，語氣要更多陪伴，讓用戶感覺被接住。

## 📚 補充能量

列出這七天閱讀的文章或資源，簡單說明這些內容和用戶這段時間狀態的連結。
若沒有閱讀記錄，鼓勵他之後找時間去看看心理資源頁面。

## 🌱 給接下來的自己

一段話，溫柔地祝福或邀請用戶繼續某件小事。
語氣輕鬆，不施壓，像是朋友的叮嚀。

---

**語氣要求：**
- 溫暖、鼓勵、不批判、不說教
- 聚焦用戶「做到的事」，不強調「沒做到的事」
- 語言自然、口語化，像真人朋友在說話
- 使用繁體中文
- 每個章節 50-100 字，總字數 350-500 字
"""


def collect_week_data(user, week_start, week_end) -> dict:
    """收集用戶過去 7 天所有活動資料。"""
    from growth.models import KudosNote, DailyTask, DailyTaskLog, DailyMood
    from companion.models import AIChatLog, ChatSession, SOSLog
    from board.models import BoardPost, BoardReaction
    from resources.models import ArticleView
    from core.models import SituationResponse

    # ── 誇誇筆記 ──
    kudos = list(
        KudosNote.objects.filter(
            user=user, created_at__date__range=(week_start, week_end),
            is_deleted=False
        ).values_list("praise_content", flat=True)
    )

    # ── 每日任務 ──
    task_logs = list(
        DailyTaskLog.objects.filter(user=user, date__range=(week_start, week_end))
        .select_related("task")
    )
    all_tasks = DailyTask.objects.filter(is_active=True)
    days_elapsed = (week_end - week_start).days + 1
    task_total_possible = all_tasks.count() * days_elapsed
    task_completions = len(task_logs)
    task_rate = round(task_completions / max(task_total_possible, 1) * 100)

    task_by_day = {}
    for log in task_logs:
        task_by_day[log.date] = task_by_day.get(log.date, 0) + 1

    # ── 聊天 ──
    sessions = ChatSession.objects.filter(
        user=user, created_at__date__range=(week_start, week_end), is_deleted=False
    )
    chat_logs = list(
        AIChatLog.objects.filter(
            session__user=user,
            session__is_deleted=False,
            created_at__date__range=(week_start, week_end),
            sender="user",
        ).values("mood_score", "message_content")
    )
    mood_scores = [l["mood_score"] for l in chat_logs if l["mood_score"] is not None]
    # avg_mood 只在有評分記錄時計算；None 表示本週 Gemini 未成功評分
    avg_mood = round(sum(mood_scores) / len(mood_scores), 1) if mood_scores else None
    # 情緒偏低的訊息則數（≤4分），與 avg_mood 使用同一來源，資料一致
    low_mood_messages = sum(1 for s in mood_scores if s <= 4)

    # ── 危機事件 ──
    crisis_count = SOSLog.objects.filter(
        user=user, created_at__date__range=(week_start, week_end)
    ).count()

    # ── 看板 ──
    board_posts = list(
        BoardPost.objects.filter(
            user=user, created_at__date__range=(week_start, week_end),
            is_deleted=False  # 不納入已撤回的貼文
        )
        .select_related("preset_icon")
        .values_list("preset_icon__label", flat=True)
    )
    reactions_sent = BoardReaction.objects.filter(
        user=user, created_at__date__range=(week_start, week_end)
    ).count()
    reactions_received = BoardReaction.objects.filter(
        post__user=user,
        post__is_deleted=False,
        created_at__date__range=(week_start, week_end),
    ).count()

    # ── 文章閱讀 ──
    articles_read = list(
        ArticleView.objects.filter(
            user=user, first_viewed_at__date__range=(week_start, week_end)
        ).select_related("article").values_list("article__title", flat=True)
    )

    # ── 每日心情打卡 ──
    daily_moods = list(
        DailyMood.objects.filter(
            user=user, date__range=(week_start, week_end)
        ).order_by("date")
    )
    mood_records = [
        {"date": str(m.date), "mood": m.get_mood_display(), "emoji": m.emoji}
        for m in daily_moods
    ]

    # ── 情境題互動 ──
    situation_responses = list(
        SituationResponse.objects.filter(
            user=user,
            created_at__date__range=(week_start, week_end),
        ).select_related("question").order_by("created_at")
    )
    situation_records = []
    for r in situation_responses:
        if r.mode == "choice":
            # 找選項文字
            option_map = {"a": r.question.option_a, "b": r.question.option_b, "c": r.question.option_c}
            answer = f"選了「{r.choice.upper()}. {option_map.get(r.choice, '')}」"
        else:
            answer = f"說：「{r.text_answer[:40]}{'⋯' if len(r.text_answer) > 40 else ''}」"
        situation_records.append({
            "question": r.question.content[:50],
            "answer": answer,
        })

    return {
        "week_start": str(week_start),
        "week_end": str(week_end),
        "kudos": list(kudos),
        "kudos_count": len(kudos),
        "task_completions": task_completions,
        "task_total_possible": task_total_possible,
        "task_rate": task_rate,
        "task_by_day": {str(k): v for k, v in task_by_day.items()},
        "chat_sessions": sessions.count(),
        "chat_user_messages": len(chat_logs),
        "avg_mood": avg_mood,
        "low_mood_messages": low_mood_messages,
        "crisis_count": crisis_count,
        "board_posts": board_posts,
        "board_posts_count": len(board_posts),
        "reactions_sent": reactions_sent,
        "reactions_received": reactions_received,
        "articles_read": list(articles_read),
        "articles_count": len(articles_read),
        "mood_records": mood_records,
        "mood_count": len(mood_records),
        "situation_records": situation_records,
        "situation_count": len(situation_records),
        "tree_points": len(kudos) + task_completions,
    }


def build_review_context(data: dict) -> str:
    """把活動資料轉成給 Gemini 的結構化說明文字。"""
    from collections import Counter

    lines = [
        f"【週期】{data['week_start']} ~ {data['week_end']}",
        "",
        f"【誇誇筆記】這 7 天共 {data['kudos_count']} 則",
    ]
    for k in data["kudos"]:
        lines.append(f"  · {k[:60]}")

    lines += [
        "",
        f"【每日任務】",
        f"  完成次數：{data['task_completions']} / {data['task_total_possible']}（完成率 {data['task_rate']}%）",
    ]
    for day, count in sorted(data["task_by_day"].items()):
        lines.append(f"  {day}：完成 {count} 項")

    lines += [
        "",
        f"【與涵涵的對話】",
        f"  對話段數：{data['chat_sessions']}",
        f"  傳送訊息：{data['chat_user_messages']} 則",
    ]
    if data["avg_mood"] is not None:
        lines.append(f"  平均情緒分數：{data['avg_mood']}/10")
        lines.append(f"  情緒偏低的訊息（≤4分）：{data['low_mood_messages']} 則")
    if data["crisis_count"] > 0:
        lines.append(f"  ⚠️ 危機事件次數：{data['crisis_count']}")

    lines += [
        "",
        f"【心情看板】",
        f"  發布貼文：{data['board_posts_count']} 篇",
    ]
    if data["board_posts"]:
        most = Counter(data["board_posts"]).most_common(3)
        lines.append(f"  最常出現的心情：" + "、".join(f"{m[0]}({m[1]}次)" for m in most))
    lines += [
        f"  送出回應：{data['reactions_sent']} 個",
        f"  收到回應：{data['reactions_received']} 個",
    ]

    lines += [
        "",
        f"【閱讀文章】共 {data['articles_count']} 篇",
    ]
    for a in data["articles_read"]:
        lines.append(f"  · {a}")

    if data.get("mood_count", 0) > 0:
        lines += ["", f"【每日心情打卡】共 {data['mood_count']} 天"]
        for m in data.get("mood_records", []):
            lines.append(f"  · {m['date']}：{m['emoji']} {m['mood']}")

    if data.get("situation_count", 0) > 0:
        lines += [
            "",
            f"【情境題互動】共 {data['situation_count']} 題",
        ]
        for s in data.get("situation_records", []):
            lines.append(f"  · 情境：{s['question']}⋯")
            lines.append(f"    {s['answer']}")

    return "\n".join(lines)


def generate_narrative(user, data: dict) -> str:
    """用 Gemini 生成 Markdown 格式的週回顧敘事。失敗時回傳空字串。"""
    try:
        from google import genai
        from google.genai import types

        context_text = build_review_context(data)
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        resp = client.models.generate_content(
            model=settings.GEMINI_MODEL_REVIEW,
            contents=f"以下是用戶最近 7 天的完整活動記錄：\n\n{context_text}\n\n請為他寫一份這七天的回顧報告。",
            config=types.GenerateContentConfig(
                system_instruction=REVIEW_PROMPT,
                temperature=0.8,
                max_output_tokens=4096,
            ),
        )
        return resp.text or ""
    except Exception:
        logger.exception("Gemini 週回顧生成失敗（user=%s）", user.pk)
        return ""


def get_or_generate_review(user):
    """
    取得本週回顧。
    - 若已有 narrative → 直接回傳（不重新生成）
    - 若沒有 → 即時生成並儲存
    回傳 (WeeklyReview instance, data_dict)
    """
    from growth.models import WeeklyReview

    today = timezone.localdate()
    week_start = today - timedelta(days=6)  # 過去 7 天（含今天）

    review, _ = WeeklyReview.objects.get_or_create(
        user=user,
        start_date=week_start,
        defaults={"end_date": today},
    )

    if not review.summary_data.get("narrative"):
        data = collect_week_data(user, week_start, today)
        narrative = generate_narrative(user, data)
        data["narrative"] = narrative
        review.end_date = today
        review.summary_data = data
        review.save(update_fields=["end_date", "summary_data"])

    return review, review.summary_data


def regenerate_review(user):
    """強制重新生成本週回顧，並儲存版本歷史（每次都留一份）。"""
    from growth.models import WeeklyReview, WeeklyReviewVersion

    today = timezone.localdate()
    week_start = today - timedelta(days=6)  # 過去 7 天（含今天）

    data = collect_week_data(user, week_start, today)
    narrative = generate_narrative(user, data)
    data["narrative"] = narrative

    # 更新「最新版」
    review, _ = WeeklyReview.objects.update_or_create(
        user=user,
        start_date=week_start,
        defaults={"end_date": today, "summary_data": data},
    )

    # 存版本歷史（永遠新增，不覆蓋）
    WeeklyReviewVersion.objects.create(
        user=user,
        week_start=week_start,
        summary_data=data,
    )

    return review, data
