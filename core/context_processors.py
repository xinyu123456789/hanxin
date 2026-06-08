def mood_reminder(request):
    """從外部進入且今天還沒有心情打卡時，提示用戶打卡。"""
    if not request.user.is_authenticated:
        return {}

    referer = request.META.get("HTTP_REFERER", "")
    is_external = not referer or request.get_host() not in referer
    if not is_external:
        return {}

    from django.utils import timezone
    from growth.models import DailyMood
    today = timezone.localdate()
    already_checked = DailyMood.objects.filter(user=request.user, date=today).exists()

    return {"show_mood_reminder": not already_checked}


def warmth_notification(request):
    """從外部進入網站且有暖意回應時，傳入通知數量給 base.html。"""
    if not request.user.is_authenticated:
        return {}

    referer = request.META.get("HTTP_REFERER", "")
    is_external = not referer or request.get_host() not in referer
    if not is_external:
        return {}

    from django.utils import timezone
    from board.models import BoardReaction
    today = timezone.localdate()
    count = BoardReaction.objects.filter(
        post__user=request.user,
        post__is_deleted=False,
        post__created_at__date=today,
    ).count()

    return {"notify_warmth": count} if count > 0 else {}
