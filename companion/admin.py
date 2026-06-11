from django.contrib import admin
from django.utils.html import format_html

from .models import ChatSession, AIChatLog, SOSLog


def mood_badge(score):
    """把情緒分數轉成帶顏色的標籤。"""
    if score is None:
        return "—"
    if score <= 2:
        color, label = "#E47B72", f"⚠️ {score}"   # 危機
    elif score <= 4:
        color, label = "#E6B85B", f"😔 {score}"   # 低落
    elif score <= 6:
        color, label = "#B4A491", f"😐 {score}"   # 平淡
    else:
        color, label = "#86AC7C", f"😊 {score}"   # 正向
    return format_html(
        '<span style="background:{};color:#fff;padding:3px 9px;border-radius:20px;'
        'font-weight:700;font-size:12px">{}</span>',
        color, label,
    )


class AIChatLogInline(admin.TabularInline):
    model = AIChatLog
    fields = ["sender", "message_preview", "mood_badge_display", "mood_reasoning",
              "crisis_flagged", "created_at"]
    readonly_fields = ["sender", "message_preview", "mood_badge_display", "mood_reasoning",
                       "crisis_flagged", "created_at"]
    extra = 0
    can_delete = False

    def message_preview(self, obj):
        text = obj.message_content or ""
        return text[:60] + ("…" if len(text) > 60 else "")
    message_preview.short_description = "內容預覽"

    def mood_badge_display(self, obj):
        if obj.sender != "user":
            return "—"
        return mood_badge(obj.mood_score)
    mood_badge_display.short_description = "情緒分數"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AIChatLog)
class AIChatLogAdmin(admin.ModelAdmin):
    list_display  = ["session_user", "sender", "message_preview", "mood_badge_display",
                     "crisis_flagged", "created_at"]
    list_filter   = ["sender", "crisis_flagged"]
    search_fields = ["session__user__email"]
    readonly_fields = ["session", "sender", "message_content", "mood_badge_display",
                       "mood_score", "mood_reasoning", "crisis_flagged", "created_at"]
    date_hierarchy = "created_at"

    def session_user(self, obj):
        return obj.session.user.email
    session_user.short_description = "使用者"

    def message_preview(self, obj):
        text = obj.message_content or ""
        return text[:60] + ("…" if len(text) > 60 else "")
    message_preview.short_description = "內容預覽"

    def mood_badge_display(self, obj):
        if obj.sender != "user":
            return "—"
        return mood_badge(obj.mood_score)
    mood_badge_display.short_description = "情緒分數"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True    # 允許（讓刪除上層 session 時可以級聯刪除）


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display  = ["user", "latest_mood_display", "crisis_mode", "crisis_since",
                     "created_at", "end_time"]
    list_filter   = ["crisis_mode"]
    search_fields = ["user__email"]
    readonly_fields = ["crisis_since", "created_at", "updated_at"]
    raw_id_fields = ["user"]
    inlines = [AIChatLogInline]

    def latest_mood_display(self, obj):
        last = obj.logs.filter(sender="user", mood_score__isnull=False).order_by("-created_at").first()
        return mood_badge(last.mood_score) if last else "—"
    latest_mood_display.short_description = "最新情緒"

    def has_change_permission(self, request, obj=None):
        return False   # 不允許編輯欄位

    def has_delete_permission(self, request, obj=None):
        return True    # 但允許刪除整個 session


@admin.register(SOSLog)
class SOSLogAdmin(admin.ModelAdmin):
    list_display  = ["user", "triggering_keyword", "detector", "action_taken", "created_at"]
    list_filter   = ["detector"]
    search_fields = ["user__email", "triggering_keyword"]
    readonly_fields = ["user", "chat_log", "triggering_keyword", "detector",
                       "action_taken", "created_at"]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
