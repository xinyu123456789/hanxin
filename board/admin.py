from django.contrib import admin

from .models import PresetIcon, PresetMessage, BoardPost, BoardReaction


@admin.register(PresetIcon)
class PresetIconAdmin(admin.ModelAdmin):
    list_display = ["label", "emotion_type", "is_active", "image_path"]
    list_editable = ["is_active"]
    list_filter = ["is_active"]


@admin.register(PresetMessage)
class PresetMessageAdmin(admin.ModelAdmin):
    list_display = ["content", "is_active"]
    list_editable = ["is_active"]


@admin.register(BoardPost)
class BoardPostAdmin(admin.ModelAdmin):
    list_display = ["user", "preset_icon", "created_at"]
    list_filter = ["preset_icon__emotion_type"]
    search_fields = ["user__email"]
    raw_id_fields = ["user", "preset_icon"]
    date_hierarchy = "created_at"

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(BoardReaction)
class BoardReactionAdmin(admin.ModelAdmin):
    list_display = ["user", "post", "sticker", "created_at"]
    list_filter = ["sticker"]
    raw_id_fields = ["user", "post"]

    def has_change_permission(self, request, obj=None):
        return False
