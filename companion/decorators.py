"""
聊天頁的 Gating 裝飾器。
未設定 Gemini 金鑰的登入使用者，會被溫柔地引導到金鑰設定頁。
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def requires_gemini_key(view_func):
    """
    確保使用者已設定有效 Gemini 金鑰，否則導向設定頁。
    此裝飾器隱含 @login_required（未登入先導向登入頁）。
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        ai = getattr(request.user, "ai_setting", None)
        if not ai or not ai.has_key:
            messages.info(
                request,
                "先到個人設定貼上你的 Gemini 金鑰，就能和涵涵聊天 🧸",
            )
            return redirect("settings_ai")
        return view_func(request, *args, **kwargs)

    return wrapper
