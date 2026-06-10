from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserProfile, UserPreference


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


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ["user", "accent", "font_scale", "board_react", "tree_style"]
    raw_id_fields = ["user"]
