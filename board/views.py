import random

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from .models import BoardPost, BoardReaction, PresetIcon, PresetMessage

STICKER_KEYS = ["hug", "pat", "highfive", "warm"]


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
            .select_related("preset_icon", "user")
            .prefetch_related("reactions")
            .order_by("-created_at")[:100]
        )

        all_words = _load_warm_words()   # 只查一次
        posts_data = []
        for post in posts:
            counts = {s: 0 for s in STICKER_KEYS}
            mine = set()
            for r in post.reactions.all():
                counts[r.sticker] = counts.get(r.sticker, 0) + 1
                if r.user_id == user.id:
                    mine.add(r.sticker)
            posts_data.append({
                "post": post,
                "counts": counts,
                "total": sum(counts.values()),
                "mine": mine,
                "warm_words": _warm_words_for_post(post.id, all_words),
            })

        ctx["posts_data"] = posts_data
        ctx["preset_icons"] = PresetIcon.objects.filter(is_active=True)
        ctx["warm_word"] = all_words[0] if all_words else "你不孤單"
        pref = getattr(user, "preference", None)
        ctx["board_react"] = pref.board_react if pref else "tray"
        return ctx


DAILY_POST_LIMIT = 50  # 每位用戶每天最多發幾則心情


@login_required
@require_POST
def board_post(request):
    today = timezone.localdate()
    today_count = BoardPost.objects.filter(
        user=request.user,
        created_at__date=today,
    ).count()
    if today_count >= DAILY_POST_LIMIT:
        return render(request, "_partials/_board_limit.html", {
            "limit": DAILY_POST_LIMIT,
        })

    icon_id = request.POST.get("preset_icon_id")
    icon = get_object_or_404(PresetIcon, pk=icon_id, is_active=True)
    post = BoardPost.objects.create(user=request.user, preset_icon=icon)
    counts = {s: 0 for s in STICKER_KEYS}
    all_words = _load_warm_words()
    return render(request, "_partials/_board_post.html", {
        "pd": {"post": post, "counts": counts, "total": 0, "mine": set(),
               "warm_words": _warm_words_for_post(post.id, all_words)},
        "board_react": getattr(getattr(request.user, "preference", None), "board_react", "tray"),
    })


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
    user = self_user = request.user
    my_posts = (
        BoardPost.objects
        .filter(user=user, is_deleted=False)
        .select_related("preset_icon")
        .prefetch_related("reactions")
        .order_by("-created_at")[:50]
    )
    all_words = _load_warm_words()
    posts_data = []
    for post in my_posts:
        counts = {s: 0 for s in STICKER_KEYS}
        mine = set()
        for r in post.reactions.all():
            counts[r.sticker] = counts.get(r.sticker, 0) + 1
            if r.user_id == user.id:
                mine.add(r.sticker)
        posts_data.append({
            "post": post,
            "counts": counts,
            "total": sum(counts.values()),
            "mine": mine,
            "warm_words": _warm_words_for_post(post.id, all_words),
        })
    pref = getattr(user, "preference", None)
    return render(request, "_partials/_board_mine.html", {
        "posts_data": posts_data,
        "board_react": pref.board_react if pref else "tray",
        "warm_word": all_words[0] if all_words else "你不孤單",
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
        "warm_words": _warm_words_for_post(post.id, _load_warm_words()),
    })


def _load_warm_words() -> list[str]:
    """一次性撈所有暖心語（給 BoardView 用，查一次傳給所有貼文）。"""
    words = list(PresetMessage.objects.filter(is_active=True).values_list("content", flat=True))
    return words or ["你不孤單", "謝謝你願意說出來", "慢慢來，沒關係的"]


def _warm_words_for_post(post_id: int, all_words: list[str], count: int = 3) -> list[str]:
    """依貼文 ID 從已載入的暖心語列表中輪換取 count 條。"""
    return [all_words[(post_id + i) % len(all_words)] for i in range(count)]


