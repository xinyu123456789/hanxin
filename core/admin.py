from django.contrib import admin

from .models import SituationQuestion, SituationResponse


@admin.register(SituationQuestion)
class SituationQuestionAdmin(admin.ModelAdmin):
    list_display  = ["content_preview", "active_date", "is_active", "created_at"]
    list_editable = ["active_date", "is_active"]
    list_filter   = ["is_active"]
    search_fields = ["content"]
    ordering      = ["-created_at"]

    def content_preview(self, obj):
        return obj.content[:40] + ("…" if len(obj.content) > 40 else "")
    content_preview.short_description = "情境描述"


@admin.register(SituationResponse)
class SituationResponseAdmin(admin.ModelAdmin):
    list_display  = ["user_label", "question_preview", "mode", "choice", "text_preview", "created_at"]
    list_filter   = ["mode", "created_at"]
    search_fields = ["text_answer", "user__email"]
    ordering      = ["-created_at"]
    # 可查看、可刪除不當回答，但不可編輯內容
    readonly_fields = ["user", "question", "mode", "text_answer", "choice", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def user_label(self, obj):
        return obj.user.email if obj.user else "訪客"
    user_label.short_description = "用戶"

    def question_preview(self, obj):
        return obj.question.content[:20] + "…"
    question_preview.short_description = "題目"

    def text_preview(self, obj):
        return obj.text_answer[:30] + ("…" if len(obj.text_answer) > 30 else "")
    text_preview.short_description = "簡答內容"
