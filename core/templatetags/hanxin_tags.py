import bleach
import markdown as _md
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# bleach 白名單：允許的 HTML 標籤和屬性
_ALLOWED_TAGS = [
    "p", "br", "strong", "em", "b", "i", "u",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "blockquote", "code", "pre",
    "hr", "a",
]
_ALLOWED_ATTRS = {
    "a": ["href", "title", "rel"],
}


@register.filter
def split(value, sep=","):
    """{{ "a,b,c"|split:"," }} → ["a","b","c"]"""
    return value.split(sep)


@register.filter
def markdown(value):
    """把 Markdown 渲染成 HTML，並用 bleach 白名單過濾惡意標籤。"""
    if not value:
        return ""
    html = _md.markdown(
        value,
        extensions=["extra", "nl2br", "sane_lists"],
    )
    clean = bleach.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        strip=True,
    )
    return mark_safe(clean)


@register.filter
def anim_delay(value, step=0.06):
    """把 forloop.counter0 換算成動畫 delay 秒數。
    預設步長 0.06s（18 顆約 1.1 秒全部長出）。
    用法：{{ forloop.counter0|anim_delay }} 或 {{ forloop.counter0|anim_delay:'0.04' }}
    """
    return round(int(value) * float(step), 3)


@register.filter
def floatformat_delay(value, decimals=2):
    """舊版 alias，保留相容性。"""
    return round(int(value) * 0.04, 2)
