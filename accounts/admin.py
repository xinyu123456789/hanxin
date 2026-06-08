from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserProfile, AISetting, UserPreference


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "date_joined", "is_active", "is_staff"]
    search_fields = ["email"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("權限", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("日期", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2"),
        }),
    )


def clear_crisis(modeladmin, request, queryset):
    for profile in queryset:
        profile.clear_crisis()
    modeladmin.message_user(request, f"已清除 {queryset.count()} 位用戶的危機狀態。")
clear_crisis.short_description = "清除危機狀態"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ["user", "nickname", "is_in_crisis_display", "crisis_until"]
    search_fields = ["user__email", "nickname"]
    raw_id_fields = ["user"]
    actions       = [clear_crisis]

    def is_in_crisis_display(self, obj):
        return "⚠️ 危機中" if obj.is_in_crisis else "—"
    is_in_crisis_display.short_description = "危機狀態"


@admin.register(AISetting)
class AISettingAdmin(admin.ModelAdmin):
    list_display = ["user", "has_key_display", "model_name", "key_verified_at"]
    search_fields = ["user__email"]
    readonly_fields = ["key_verified_at", "key_masked_display"]
    raw_id_fields = ["user"]

    def has_key_display(self, obj):
        return "✓ 已設定" if obj.has_key else "✗ 未設定"
    has_key_display.short_description = "金鑰狀態"

    def key_masked_display(self, obj):
        return obj.key_masked
    key_masked_display.short_description = "遮罩金鑰"

    def get_fields(self, request, obj=None):
        return ["user", "key_masked_display", "model_name", "key_verified_at"]


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ["user", "accent", "font_scale", "board_react", "tree_style"]
    raw_id_fields = ["user"]
