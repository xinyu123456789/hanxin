from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import ProfileForm, AppearanceForm


@login_required
def settings_profile(request):
    """個人檔案設定頁。支援 ?next= 在儲存後導回指定頁面（例如發文頁）。"""
    profile = request.user.profile
    next_url = request.POST.get("next") or request.GET.get("next") or ""

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "個人檔案已更新。")
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect("settings_profile")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "settings_profile.html", {"form": form, "next": next_url})


@login_required
def settings_appearance(request):
    """外觀偏好設定頁。"""
    pref = request.user.preference

    if request.method == "POST":
        form = AppearanceForm(request.POST, instance=pref)
        if form.is_valid():
            form.save()
            messages.success(request, "外觀偏好已儲存。")
            return redirect("settings_appearance")
    else:
        form = AppearanceForm(instance=pref)

    return render(request, "settings_appearance.html", {"form": form})


@login_required
@require_POST
def account_delete(request):
    """帳號刪除（遺忘權）：級聯刪除所有加密資料。"""
    user = request.user
    # Django CASCADE 自動刪除 Profile / KudosNote / AIChatLog 等
    user.delete()
    messages.info(request, "你的帳號與所有資料已永久刪除。希望未來能再見到你。")
    return redirect("account_login")


@login_required
@require_POST
def clear_chat_history(request):
    """清除所有聊天記錄（軟刪除，帳號保留）。"""
    from companion.models import ChatSession
    ChatSession.objects.filter(user=request.user, is_deleted=False).update(
        is_deleted=True,
    )
    messages.success(request, "所有聊天記錄已清除。")
    return redirect("settings_profile")


@login_required
@require_POST
def clear_kudos(request):
    """清除所有誇誇筆記（軟刪除，帳號保留）。"""
    from growth.models import KudosNote
    KudosNote.objects.filter(user=request.user, is_deleted=False).update(
        is_deleted=True,
        deleted_at=timezone.now(),
    )
    messages.success(request, "所有誇誇筆記已清除。")
    return redirect("settings_profile")
