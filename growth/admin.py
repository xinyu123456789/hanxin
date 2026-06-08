from django.contrib import admin

from .models import KudosNote, DailyTask, DailyTaskLog, WeeklyReview, WeeklyReviewVersion, DailyMood


@admin.register(KudosNote)
class KudosNoteAdmin(admin.ModelAdmin):
    list_display = ["user", "praise_preview", "created_at"]
    search_fields = ["user__email", "praise_content"]
    raw_id_fields = ["user"]
    date_hierarchy = "created_at"
    readonly_fields = ["created_at"]

    def praise_preview(self, obj):
        return obj.praise_content[:50] + ("…" if len(obj.praise_content) > 50 else "")
    praise_preview.short_description = "內容預覽"

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DailyMood)
class DailyMoodAdmin(admin.ModelAdmin):
    list_display  = ["user", "date", "mood", "created_at"]
    list_filter   = ["mood", "date"]
    search_fields = ["user__email"]
    date_hierarchy = "date"
    raw_id_fields = ["user"]
    readonly_fields = ["user", "date", "mood", "created_at", "updated_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DailyTask)
class DailyTaskAdmin(admin.ModelAdmin):
    list_display = ["icon", "label", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]
    ordering = ["sort_order"]


@admin.register(DailyTaskLog)
class DailyTaskLogAdmin(admin.ModelAdmin):
    list_display = ["user", "task", "date"]
    list_filter = ["task", "date"]
    search_fields = ["user__email"]
    date_hierarchy = "date"
    raw_id_fields = ["user", "task"]

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(WeeklyReview)
class WeeklyReviewAdmin(admin.ModelAdmin):
    list_display = ["user", "start_date", "end_date"]
    search_fields = ["user__email"]
    date_hierarchy = "start_date"
    raw_id_fields = ["user"]
    readonly_fields = ["summary_data"]


@admin.register(WeeklyReviewVersion)
class WeeklyReviewVersionAdmin(admin.ModelAdmin):
    list_display  = ["user", "week_start", "narrative_preview", "generated_at"]
    list_filter   = ["week_start"]
    search_fields = ["user__email"]
    raw_id_fields = ["user"]
    readonly_fields = ["user", "week_start", "summary_data", "generated_at"]
    date_hierarchy = "generated_at"

    def narrative_preview(self, obj):
        text = obj.summary_data.get("narrative", "") or ""
        return text[:60] + ("…" if len(text) > 60 else "")
    narrative_preview.short_description = "敘事預覽"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
