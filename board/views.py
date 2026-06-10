from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from .models import BoardPost, BoardReaction, PresetIcon, PresetMessage

STICKER_KEYS = ["hug", "pat", "highfive", "warm"]
DAILY_POST_LIMIT = 50  # 每位用戶每天最多發幾則心情


def _build_posts_data(posts, user):
    """將 BoardPost queryset 轉為模板需要的 posts_data（counts/mine/total）。
    posts 應已 select_related/prefetch_related。"""
    posts_data = []
    for post in posts:
        counts = {s: 0 for s in STICKER_KEYS}
        mine = set()
        for r in post.reactions.all():
            counts[r.sticker] = counts.get(r.sticker, 0) + 1
            if r.user_id == user.id:
                mine.add(r.sticker)
        posts_data.append({
            "post": post, "counts": counts, "total": sum(counts.values()), "mine": mine,
        })
    return posts_data


class BoardView(TemplateView):
    template_name = "board.html"

    def get_template_names(self):
        """HTMX 請求只回 feed partial，避免整頁塞進 #board-feed。"""
        if self.request.headers.get("HX-Request"):
            return ["_partials/_board_feed.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        today = timezone.localdate()
        posts = (
            BoardPost.objects
            .filter(is_deleted=False, created_at__date=today)
            .select_related("preset_icon", "preset_message", "user", "user__profile")
            .prefetch_related("reactions")
            .order_by("-created_at")[:100]
        )

        ctx["posts_data"] = _build_posts_data(posts, user)
        pref = getattr(user, "preference", None)
        ctx["board_react"] = pref.board_react if pref else "tray"
        return ctx


@login_required
def board_post_create_view(request):
    """發文頁面：選天氣與/或暖心語、選擇是否不匿名。"""
    profile = getattr(request.user, "profile", None)
    return render(request, "board_post_create.html", {
        "preset_icons": PresetIcon.objects.filter(is_active=True),
        "preset_messages": PresetMessage.objects.filter(is_active=True),
        "message_categories": PresetMessage.CATEGORY_CHOICES,
        "nickname": profile.nickname if profile else "",
    })


@login_required
@require_POST
def board_post(request):
    today = timezone.localdate()
    today_count = BoardPost.objects.filter(
        user=request.user,
        created_at__date=today,
    ).count()
    if today_count >= DAILY_POST_LIMIT:
        messages.error(request, f"今天的心情已分享很多了，每天最多 {DAILY_POST_LIMIT} 則，明天再來吧 🌱")
        return redirect("board_post_create")

    icon_id = request.POST.get("preset_icon_id") or None
    message_id = request.POST.get("preset_message_id") or None

    icon = get_object_or_404(PresetIcon, pk=icon_id, is_active=True) if icon_id else None
    preset_message = get_object_or_404(PresetMessage, pk=message_id, is_active=True) if message_id else None

    if icon is None and preset_message is None:
        messages.error(request, "請至少選擇一個天氣圖示或一句暖心語。")
        return redirect("board_post_create")

    show_nickname = request.POST.get("show_nickname") == "1"
    is_anonymous = not show_nickname
    if not is_anonymous:
        profile = getattr(request.user, "profile", None)
        if not profile or not profile.nickname.strip():
            is_anonymous = True  # 安全網：沒暱稱就只能匿名

    BoardPost.objects.create(
        user=request.user, preset_icon=icon, preset_message=preset_message,
        is_anonymous=is_anonymous,
    )
    messages.success(request, "已分享到心情看板 🌤️")
    return redirect("board")


@login_required
@require_POST
def board_delete(request, post_id):
    """軟刪除：只有自己的貼文可以撤回，後台保留稽核記錄。"""
    post = get_object_or_404(BoardPost, pk=post_id, user=request.user)
    post.is_deleted = True
    post.deleted_at = timezone.now()
    post.save(update_fields=["is_deleted", "deleted_at"])
    # HTMX：回傳空，讓該卡片從 DOM 消失
    resp = HttpResponse()
    resp["HX-Reswap"] = "outerHTML"
    resp.content = b""
    return resp


@login_required
def board_mine(request):
    """個人心情頁：只看自己的貼文（非刪除），HTMX 局部載入。"""
    user = request.user
    my_posts = (
        BoardPost.objects
        .filter(user=user, is_deleted=False)
        .select_related("preset_icon", "preset_message", "user__profile")
        .prefetch_related("reactions")
        .order_by("-created_at")[:50]
    )
    posts_data = _build_posts_data(my_posts, user)
    pref = getattr(user, "preference", None)
    return render(request, "_partials/_board_mine.html", {
        "posts_data": posts_data,
        "board_react": pref.board_react if pref else "tray",
    })


def board_search(request):
    """依暱稱搜尋「不匿名」貼文，跨全部歷史。訪客也可搜尋瀏覽（與 BoardView 一致）。"""
    query = request.GET.get("nickname", "").strip()
    posts_data = []
    if query:
        posts = (
            BoardPost.objects
            .filter(is_deleted=False, is_anonymous=False,
                    user__profile__nickname__icontains=query)
            .select_related("preset_icon", "preset_message", "user", "user__profile")
            .prefetch_related("reactions")
            .order_by("-created_at")[:50]
        )
        posts_data = _build_posts_data(posts, request.user)

    pref = getattr(request.user, "preference", None) if request.user.is_authenticated else None
    return render(request, "_partials/_board_search_results.html", {
        "posts_data": posts_data,
        "query": query,
        "board_react": pref.board_react if pref else "tray",
    })


@login_required
@require_POST
def board_react(request, post_id):
    post = get_object_or_404(BoardPost, pk=post_id)
    sticker = request.POST.get("sticker")

    if sticker not in dict(BoardReaction.STICKER_CHOICES):
        return render(request, "_partials/_empty.html")

    # 單選：先刪除此用戶對這則貼文的所有既有回應
    had_this = BoardReaction.objects.filter(
        post=post, user=request.user, sticker=sticker
    ).exists()
    BoardReaction.objects.filter(post=post, user=request.user).delete()

    # 若不是點同一個（取消），就建立新的
    if not had_this:
        BoardReaction.objects.create(post=post, user=request.user, sticker=sticker)

    # 重算計數
    counts_qs = (
        BoardReaction.objects.filter(post=post)
        .values("sticker").annotate(n=Count("id"))
    )
    counts = {s: 0 for s in STICKER_KEYS}
    for row in counts_qs:
        counts[row["sticker"]] = row["n"]

    mine = set(
        BoardReaction.objects.filter(post=post, user=request.user)
        .values_list("sticker", flat=True)
    )

    return render(request, "_partials/_react_row.html", {
        "post": post,
        "counts": counts,
        "total": sum(counts.values()),
        "mine": mine,
        "board_react": getattr(getattr(request.user, "preference", None), "board_react", "tray"),
    })
