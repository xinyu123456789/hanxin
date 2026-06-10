import calendar as _cal
import math
import random as _random
from datetime import timedelta

from django.contrib.auth.decorators import login_required

# 心情樹視覺化常數
TREE_GOLDEN_ANGLE = 2.399963  # 黃金角弧度（讓果實均勻分散）
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from .models import KudosNote, DailyTask, DailyTaskLog, DailyMood
from board.models import PresetMessage

def _build_viz_ctx(user, tree_style: str, tree_points: int, prev_tree_points: int = -1) -> dict:
    """樹/花園/罐視覺化座標預算，回傳 template context dict。"""
    COLORS = ['#F0A985', '#E47B72', '#F3D08A', '#CDB8DE']
    FLOWER_COLORS = ['#F2A89F', '#F3D08A', '#CDB8DE', '#AAC8E0', '#A9C7A0', '#F0A985']
    ctx: dict = {}

    if tree_style == "tree":
        MAX = 28
        n = min(tree_points, MAX)
        spots = []
        for i in range(n):
            ang = i * TREE_GOLDEN_ANGLE
            rr = 92 * 0.86 * math.sqrt((i + 0.5) / MAX)
            x = round(150 + math.cos(ang) * rr, 1)
            y = round(120 + math.sin(ang) * rr * 0.9, 1)
            spots.append({'x': x, 'y': y,
                          'rx': round(x - 0.9, 1), 'ry': round(y - 9, 1),
                          'hx': round(x - 3, 1),   'hy': round(y - 3.4, 1),
                          'c': COLORS[i % 4]})
        ctx['viz_spots'] = spots

    elif tree_style == "garden":
        flowers = min(tree_points, 12)
        items = []
        for i in range(flowers):
            x = 40 + (i % 6) * 44 + (math.floor(i / 6) % 2) * 22
            y = 150 + math.floor(i / 6) * 54
            c = FLOWER_COLORS[i % len(FLOWER_COLORS)]
            petals = []
            for k in range(5):
                a = (k / 5) * math.pi * 2
                px = round(x + math.cos(a) * 9, 1)
                py = round(y + math.sin(a) * 9, 1)
                petals.append({'px': px, 'py': py, 'rot': round(a * 57 + 90, 1), 'c': c})
            items.append({'x': x, 'y': y,
                          'rx': round(x - 1.5, 1), 'base_y': round(y + 24, 1),
                          'lx': round(x - 7, 1), 'ly': round(y + 18, 1),
                          'petals': petals})
        ctx['viz_flowers'] = items

    else:  # jar
        fill = min(tree_points / 14, 1)
        jar_stars = []
        STAR_COLORS = ['#F3D08A', '#F2A89F', '#CDB8DE', '#AAC8E0', '#A9C7A0']
        STAR_CHARS = ['✦', '♥', '✿']
        _random.seed(42)
        for i in range(min(tree_points, 16)):
            sx = round(110 + _random.random() * 80, 1)
            sy = round(232 - _random.random() * (fill * 120 + 10), 1)
            jar_stars.append({'x': sx, 'y': sy,
                              'c': STAR_COLORS[i % len(STAR_COLORS)],
                              'char': STAR_CHARS[i % 3]})
        _random.seed()
        ctx['viz_jar'] = {'fill_y': round(232 - fill * 150, 1),
                          'fill_h': round(fill * 160, 1),
                          'stars': jar_stars}

    ctx['prev_tree_points'] = prev_tree_points
    return ctx


KUDOS_PROMPTS = [
    "今天我有好好把自己照顧好。",
    "我願意休息，這也是一種勇敢。",
    "我完成了一件小事，值得被看見。",
    "即使慢，我也還在往前走。",
    "我對別人溫柔，也記得對自己溫柔。",
]

FUTURE_CARDS = [
    "嘿，未來的你：謝謝你撐到了現在。",
    "不管現在發生什麼，你都值得被好好對待。",
    "你不需要很厲害才值得休息。",
    "你已經做得比你以為的更好了。",
    "今天的烏雲，會成為明天彩虹的背景。",
]


class GrowView(LoginRequiredMixin, TemplateView):
    template_name = "grow.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()

        # 過去 7 天（含今天），避免整週沒上站就錯過回顧
        week_start = today - timedelta(days=6)

        # 誇誇列表（過去 7 天）— 評估為 list 一次，後面用 len() 不再查 DB
        kudos_list = list(
            user.kudos.filter(
                created_at__date__gte=week_start, is_deleted=False
            ).order_by("-created_at")
        )
        ctx["kudos"] = kudos_list
        ctx["kudos_prompts"] = KUDOS_PROMPTS

        # 暖心小卡：從 PresetMessage 拿（管理員可在後台新增），回退到硬編碼列表
        warm_msgs = list(PresetMessage.objects.filter(is_active=True).values_list("content", flat=True))
        ctx["future_cards"] = warm_msgs if warm_msgs else FUTURE_CARDS

        # ── 今天的任務（可勾選 / 取消） ──
        tasks = DailyTask.objects.filter(is_active=True)
        today_done_ids = set(
            DailyTaskLog.objects.filter(user=user, date=today)
            .values_list("task_id", flat=True)
        )
        ctx["tasks"] = [(t, t.id in today_done_ids) for t in tasks]
        ctx["done_count"] = len(today_done_ids)

        # ── 過去 7 天歷史任務（唯讀，每天獨立，供週回顧使用） ──
        week_logs = (
            DailyTaskLog.objects
            .filter(user=user, date__range=(week_start, today))
            .select_related("task")
            .order_by("date", "task__sort_order")
        )
        # 整理成 {date: [task_label, ...]} 格式
        week_history = {}
        for log in week_logs:
            if log.date not in week_history:
                week_history[log.date] = []
            week_history[log.date].append(log.task)

        # 轉成有序列表（過去 7 天，含今天）
        week_days = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            week_days.append({
                "date": day,
                "is_today": day == today,
                "tasks_done": week_history.get(day, []),
            })
        ctx["week_days"] = week_days
        ctx["week_start"] = week_start

        # 心情樹點數 = 過去 7 天誇誇 + 過去 7 天所有任務完成數
        week_kudos_count = len(kudos_list)   # 已是 list，len() 不查 DB
        week_task_count = sum(len(d["tasks_done"]) for d in week_days)
        ctx["tree_points"] = week_kudos_count + week_task_count

        # 成長視覺偏好
        pref = getattr(user, "preference", None)
        tree_style = pref.tree_style if pref else "tree"
        ctx["tree_style"] = tree_style

        # 視覺化座標（初始載入，全部果實都播入場動畫）
        ctx.update(_build_viz_ctx(user, tree_style, ctx["tree_points"]))

        # 近 7 天回顧（已生成就顯示，否則顯示生成按鈕）
        from growth.models import WeeklyReview
        existing = WeeklyReview.objects.filter(user=user, start_date=week_start).first()
        ctx["weekly_review"] = existing
        ctx["weekly_review_data"] = existing.summary_data if existing and existing.summary_data else {}

        # ── 每日心情打卡 ──
        ctx["today_mood"] = ""  # 預設空，下方迴圈中填入
        ctx["mood_choices"] = [
            ("awful",   "😭"), ("sad",   "😢"), ("neutral", "😐"),
            ("good",    "🙂"), ("great", "😄"),
        ]

        # 月曆：一次查詢同時取得 emoji map 和今日心情
        mood_map = {}
        for m in DailyMood.objects.filter(
            user=user, date__year=today.year, date__month=today.month
        ):
            mood_map[m.date.day] = DailyMood.MOOD_EMOJI[m.mood]
            if m.date == today:
                ctx["today_mood"] = m.mood

        weeks = _cal.monthcalendar(today.year, today.month)
        calendar_weeks = []
        for week in weeks:
            cells = []
            for day in week:
                cells.append({
                    "day":      day if day != 0 else None,
                    "emoji":    mood_map.get(day) if day != 0 else None,
                    "is_today": day == today.day,
                })
            calendar_weeks.append(cells)

        month_names = ["一月","二月","三月","四月","五月","六月",
                       "七月","八月","九月","十月","十一月","十二月"]
        ctx["mood_calendar_weeks"] = calendar_weeks
        ctx["mood_month_label"] = f"{today.year} 年 {month_names[today.month - 1]}"

        return ctx


@login_required
@require_POST
def kudos_add(request):
    """HTMX：新增一則誇誇筆記，同時 OOB 更新樹視覺化。"""
    text = request.POST.get("text", "").strip()
    if not text:
        return render(request, "_partials/_empty.html")

    note = KudosNote.objects.create(user=request.user, praise_content=text)

    today = timezone.localdate()
    week_start = today - timedelta(days=6)  # 過去 7 天（含今天）
    week_kudos = request.user.kudos.filter(
        created_at__date__gte=week_start, is_deleted=False
    ).count()
    week_tasks = DailyTaskLog.objects.filter(
        user=request.user, date__range=(week_start, today)
    ).count()
    tree_points = week_kudos + week_tasks
    prev_tree_points = tree_points - 1

    pref = getattr(request.user, "preference", None)
    tree_style = pref.tree_style if pref else "tree"

    ctx = _build_viz_ctx(request.user, tree_style, tree_points, prev_tree_points)
    ctx.update({
        "note": note,
        "tree_points": tree_points,
        "prev_tree_points": prev_tree_points,
        "tree_style": tree_style,
    })
    return render(request, "_partials/_kudos_item.html", ctx)


@login_required
@require_POST
def kudos_delete(request, note_id):
    """誇誇筆記軟刪除，同時 OOB 更新樹視覺化和累積份數。"""
    note = get_object_or_404(KudosNote, pk=note_id, user=request.user)
    note.is_deleted = True
    note.deleted_at = timezone.now()
    note.save(update_fields=["is_deleted", "deleted_at"])

    # 重新計算 tree_points（過去 7 天，排除已刪除）
    today = timezone.localdate()
    week_start = today - timedelta(days=6)  # 過去 7 天（含今天）
    week_kudos = request.user.kudos.filter(
        created_at__date__gte=week_start, is_deleted=False
    ).count()
    week_tasks = DailyTaskLog.objects.filter(
        user=request.user, date__range=(week_start, today)
    ).count()
    tree_points = week_kudos + week_tasks
    prev_tree_points = tree_points + 1  # 刪除後比之前少 1

    pref = getattr(request.user, "preference", None)
    tree_style = pref.tree_style if pref else "tree"
    viz_ctx = _build_viz_ctx(request.user, tree_style, tree_points, prev_tree_points)

    ctx = {"tree_points": tree_points, "tree_style": tree_style}
    ctx.update(viz_ctx)
    # 回傳空的筆記列（讓 HTMX outerHTML 移除）+ OOB 更新視覺化
    return render(request, "_partials/_kudos_delete_response.html", ctx)


@require_POST
def task_toggle(request, task_id):
    """HTMX：勾選 / 取消每日任務，同時回傳更新後的心情樹（OOB swap）。
    登入用戶存 DB；訪客存 session（重開瀏覽器後重置）。
    """
    task = get_object_or_404(DailyTask, pk=task_id, is_active=True)
    today = timezone.localdate()

    if request.user.is_authenticated:
        log, created = DailyTaskLog.objects.get_or_create(
            user=request.user, task=task, date=today,
        )
        if not created:
            log.delete()
            done = False
        else:
            done = True

        done_count = DailyTaskLog.objects.filter(
            user=request.user, date=today
        ).count()

        week_start = today - timedelta(days=6)  # 過去 7 天（含今天）
        week_kudos = request.user.kudos.filter(
            created_at__date__gte=week_start, is_deleted=False
        ).count()
        week_tasks = DailyTaskLog.objects.filter(
            user=request.user, date__range=(week_start, today)
        ).count()
        tree_points = week_kudos + week_tasks
        pref = getattr(request.user, "preference", None)
        tree_style = pref.tree_style if pref else "tree"
    else:
        today_str = str(today)
        guest_map = dict(request.session.get("guest_done_tasks", {}))
        guest_done = list(guest_map.get(today_str, []))
        if task_id in guest_done:
            guest_done.remove(task_id)
            done = False
        else:
            guest_done.append(task_id)
            done = True
        guest_map[today_str] = guest_done
        request.session["guest_done_tasks"] = guest_map
        request.session.modified = True

        done_count = len(guest_done)
        tree_points = done_count
        tree_style = "tree"

    prev_tree_points = tree_points - 1 if done else tree_points + 1

    viz_ctx = _build_viz_ctx(request.user, tree_style, tree_points, prev_tree_points)

    ctx = {
        "task": task,
        "done": done,
        "done_count": done_count,
        "task_total": DailyTask.objects.filter(is_active=True).count(),
        "tree_points": tree_points,
        "tree_style": tree_style,
        "prev_tree_points": prev_tree_points,
    }
    ctx.update(viz_ctx)
    return render(request, "_partials/_task_row.html", ctx)


@login_required
@require_POST
def mood_checkin(request):
    """記錄今日心情打卡（當天可重複呼叫以更新心情）。"""
    mood = request.POST.get("mood", "")
    valid = {c[0] for c in DailyMood.MOOD_CHOICES}
    if mood not in valid:
        from django.http import HttpResponseBadRequest
        return HttpResponseBadRequest()

    today = timezone.localdate()
    DailyMood.objects.update_or_create(
        user=request.user,
        date=today,
        defaults={"mood": mood},
    )
    return render(request, "_partials/_empty.html")


@require_POST
def review_generate(request):
    """HTMX：手動觸發生成（或重新生成）本週回顧。"""
    from .review import regenerate_review
    _, data = regenerate_review(request.user)
    return render(request, "_partials/_weekly_review.html", {"weekly_review_data": data})
