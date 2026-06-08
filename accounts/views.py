from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import GeminiKeyForm, ProfileForm, AppearanceForm
from .gemini import validate_key


@login_required
def settings_ai(request):
    """BYOK 金鑰設定頁。"""
    ai = request.user.ai_setting

    if request.method == "POST":
        if request.POST.get("action") == "remove":
            ai.gemini_api_key = ""
            ai.key_verified_at = None
            ai.save()
            messages.info(request, "已移除你的 Gemini 金鑰。")
            return redirect("settings_ai")

        form = GeminiKeyForm(request.POST)
        if form.is_valid():
            key = form.cleaned_data["gemini_api_key"].strip()
            ok, err = validate_key(key)
            if ok:
                ai.gemini_api_key = key
                ai.key_verified_at = timezone.now()
                ai.save()
                messages.success(request, "金鑰驗證成功，可以開始和涵涵聊天了 🧸")
                return redirect("chat")
            messages.error(request, f"這支金鑰好像不能用：{err}")
    else:
        form = GeminiKeyForm()

    return render(request, "settings_ai.html", {"form": form, "ai": ai})


@login_required
def settings_profile(request):
    """個人檔案設定頁。"""
    profile = request.user.profile

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "個人檔案已更新。")
            return redirect("settings_profile")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "settings_profile.html", {"form": form})


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
    # Django CASCADE 自動刪除 Profile / AISetting / KudosNote / AIChatLog 等
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
