"""
注入使用者偏好的 CSS 變數到所有模板（base.html 的 :root{ } 用）。
"""

ACCENTS = {
    "peach": ("#F0A985", "#E58E64", "#FBE3D4"),
    "sage":  ("#A9C7A0", "#86AC7C", "#E1EDDA"),
    "sky":   ("#AAC8E0", "#7FA8CC", "#DEEAF4"),
    "lilac": ("#CDB8DE", "#AE93C6", "#EBE0F2"),
}


def user_prefs(request):
    user = getattr(request, "user", None)
    p = None
    if user and user.is_authenticated:
        p = getattr(user, "preference", None)

    accent = getattr(p, "accent", "peach") or "peach"
    a, d, t = ACCENTS.get(accent, ACCENTS["peach"])
    font_scale = getattr(p, "font_scale", 100) or 100

    css = (
        f"--accent:{a};--accent-deep:{d};--accent-tint:{t};"
        f"--peach:{a};--peach-deep:{d};--peach-tint:{t};"
    )

    return {
        "prefs": p,
        "prefs_css": css,
        "prefs_zoom": font_scale,  # 1–115，套在 body zoom 上
    }
