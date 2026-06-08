from django.contrib import admin

from .models import PsychoArticle, PsychoScale, PsychoVideo, PsychoPodcast, Clinic, ArticleView


@admin.register(PsychoArticle)
class PsychoArticleAdmin(admin.ModelAdmin):
    list_display  = ["title", "category", "view_count", "read_minutes", "is_active"]
    list_filter   = ["category", "is_active"]
    list_editable = ["is_active"]
    search_fields = ["title", "excerpt"]
    ordering      = ["-view_count"]   # 預設按熱門排序


@admin.register(ArticleView)
class ArticleViewAdmin(admin.ModelAdmin):
    list_display  = ["user", "article", "first_viewed_at"]
    list_filter   = ["article__category"]
    search_fields = ["user__email", "article__title"]
    raw_id_fields = ["user", "article"]
    date_hierarchy = "first_viewed_at"
    ordering       = ["-first_viewed_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PsychoScale)
class PsychoScaleAdmin(admin.ModelAdmin):
    list_display = ["name", "org", "is_active"]
    list_editable = ["is_active"]
    search_fields = ["name", "org"]


@admin.register(PsychoVideo)
class PsychoVideoAdmin(admin.ModelAdmin):
    list_display = ["name", "lang", "is_active"]
    list_editable = ["is_active"]


@admin.register(PsychoPodcast)
class PsychoPodcastAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    list_editable = ["is_active"]


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display  = ["name", "clinic_type", "county", "district", "is_active"]
    list_filter   = ["clinic_type", "county", "is_active"]
    list_editable = ["is_active"]
    search_fields = ["name", "county", "district"]
