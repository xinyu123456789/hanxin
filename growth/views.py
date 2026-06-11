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
    FLOWER_COLORS = ['#F2A89F', '#F3D08A', '#CDB8DE', '#AAC8E0', '#A9C7A0', '#F0A985', '#E8C5D8', '#A7D8D0']
    ctx: dict = {}

    if tree_style == "tree":
        MAX = 36
        n = min(tree_points, MAX)
        FRUIT_COLORS = ['#F0A985', '#E47B72', '#F3D08A', '#CDB8DE', '#9FCBE0', '#F2A89F']
        # round 機率較高，當作主要果實，berry/heart/blossom 是點綴的「特色」造型
        FRUIT_SHAPES = ['round', 'round', 'berry', 'heart', 'blossom']
        FRUIT_SIZE = {'round': 17, 'berry': 19, 'heart': 18, 'blossom': 19}
        spots = []
        for i in range(n):
            ang = i * TREE_GOLDEN_ANGLE
            rr = 92 * 0.86 * math.sqrt((i + 0.5) / MAX)
            x = round(150 + math.cos(ang) * rr, 1)
            y = round(120 + math.sin(ang) * rr * 0.9, 1)
            shape = FRUIT_SHAPES[i % len(FRUIT_SHAPES)]
            size = FRUIT_SIZE[shape]
            spots.append({'x': x, 'y': y,
                          'ux': round(x - size / 2, 1), 'uy': round(y - size / 2, 1),
                          'size': size, 'shape': shape,
                          'c': FRUIT_COLORS[i % len(FRUIT_COLORS)]})
        ctx['viz_spots'] = spots

    elif tree_style == "garden":
        MAX = 20
        n = min(tree_points, MAX)
        COLS = 10
        # round 機率較高，當作主要花朵，daisy/tulip/pompom 是點綴的「特色」花型
        FLOWER_SHAPES = ['round', 'round', 'daisy', 'tulip', 'pompom']
        # 後排較小較遠、前排較大較近，營造花圃的景深
        ROW_CFG = [
            {'head_y': 150, 'stem_h': 26, 'size': 24, 'x_off': 0},
            {'head_y': 192, 'stem_h': 36, 'size': 30, 'x_off': 13},
        ]
        items = []
        for i in range(n):
            row, col = divmod(i, COLS)
            cfg = ROW_CFG[row]
            x = round(16 + col * 27 + cfg['x_off'], 1)
            head_y, stem_h, size = cfg['head_y'], cfg['stem_h'], cfg['size']
            items.append({
                'x': x, 'rx': round(x - 1.5, 1),
                'stem_y': head_y, 'stem_h': stem_h,
                'base_y': round(head_y + stem_h * 0.7, 1),
                'lx': round(x - 7, 1), 'ly': round(head_y + stem_h * 0.5, 1),
                'ux': round(x - size / 2, 1), 'uy': round(head_y - size / 2, 1),
                'size': size,
                'shape': FLOWER_SHAPES[i % len(FLOWER_SHAPES)],
                'c': FLOWER_COLORS[i % len(FLOWER_COLORS)],
            })
        ctx['viz_flowers'] = items

    elif tree_style == "sky":
        MAX = 60
        n = min(tree_points, MAX)
        COLS, ROWS = 10, 6
        CELL_W, CELL_H = 28, 34
        PAD_X, PAD_Y = 10, 13
        # dot 出現機率較高，當作背景小星星，spark/star5/star6 是較顯眼的「特色」星星
        SHAPES = ["dot", "dot", "spark", "star5", "star6"]
        SIZE_RANGE = {"dot": (5, 7), "spark": (8, 12), "star5": (10, 14), "star6": (13, 18)}
        SKY_COLORS = ['#FDF6E3', '#FCE7B2', '#F7C6CE', '#E3D1FF', '#BFE3F5', '#C9F0D6']

        cell_order = list(range(COLS * ROWS))
        _random.seed(7)
        _random.shuffle(cell_order)

        stars = []
        for i in range(n):
            cell = cell_order[i % len(cell_order)]
            col, row = cell % COLS, cell // COLS
            cx = round(PAD_X + col * CELL_W + CELL_W / 2 + _random.uniform(-9, 9), 1)
            cy = round(PAD_Y + row * CELL_H + CELL_H / 2 + _random.uniform(-10, 10), 1)
            shape = SHAPES[_random.randint(0, len(SHAPES) - 1)]
            lo, hi = SIZE_RANGE[shape]
            size = round(_random.uniform(lo, hi), 1)
            stars.append({
                'cx': cx, 'cy': cy, 'size': size,
                'ux': round(cx - size / 2, 1), 'uy': round(cy - size / 2, 1),
                'shape': shape,
                'c': SKY_COLORS[_random.randint(0, len(SKY_COLORS) - 1)],
                'dur': round(_random.uniform(1.8, 3.4), 2),
                'delay': round(_random.uniform(0, 2.4), 2),
            })
        _random.seed()
        ctx['viz_stars'] = stars

    else:  # jar
        MAX = 24
        n = min(tree_points, MAX)
        fill = min(tree_points / 20, 1)
        JAR_COLORS = ['#F3D08A', '#F2A89F', '#CDB8DE', '#AAC8E0', '#A9C7A0', '#E8C5D8', '#A7D8D0']
        JAR_CHARS = ['✦', '♥', '✿', '❀', '✶', '♦']
        jar_stars = []
        _random.seed(42)
        for i in range(n):
            sx = round(110 + _random.random() * 80, 1)
            sy = round(232 - _random.random() * (fill * 130 + 10), 1)
            jar_stars.append({
                'x': sx, 'y': sy,
                'size': round(_random.uniform(12, 20), 1),
                'c': JAR_COLORS[i % len(JAR_COLORS)],
                'char': JAR_CHARS[i % len(JAR_CHARS)],
                'dur': round(_random.uniform(1.8, 3.4), 2),
                'delay': round(_random.uniform(0, 2.4), 2),
            })
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
        # 「已生成」狀態以週日為界（每週日才換新一期），與上方過去 7 天的顯示資料分開判斷
        from growth.models import WeeklyReview
        from .review import get_review_week_start
        review_period_start = get_review_week_start(today)
        existing = WeeklyReview.objects.filter(user=user, start_date=review_period_start).first()
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
