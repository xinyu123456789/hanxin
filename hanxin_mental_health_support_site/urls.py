from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core.views import HomeView
from core import views as corev
from companion import views as cv
from board import views as bv
from growth import views as gv
from resources import views as rv
from resources.views import ResourcesView, ClinicsView, ArticleDetailView
from accounts import views as av

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),

    # 首頁
    path("", HomeView.as_view(), name="home"),

    # 情境題
    path("situation/daily/",  corev.situation_daily,  name="situation_daily"),
    path("situation/submit/", corev.situation_submit, name="situation_submit"),
    path("situation/next/",   corev.situation_next,   name="situation_next"),

    # 涵涵聊天
    path("chat/", cv.ChatView.as_view(), name="chat"),
    path("chat/new/", cv.chat_new, name="chat_new"),
    path("chat/<int:session_id>/", cv.ChatView.as_view(), name="chat_session"),
    path("chat/stream/", cv.chat_stream_send, name="chat_stream"),
    path("chat/<int:session_id>/delete/", cv.session_delete, name="session_delete"),
    path("chat/sessions/", cv.session_list_partial, name="session_list_partial"),

    # 心情看板
    path("board/", bv.BoardView.as_view(), name="board"),
    path("board/post/", bv.board_post, name="board_post"),
    path("board/post/new/", bv.board_post_create_view, name="board_post_create"),
    path("board/search/", bv.board_search, name="board_search"),
    path("board/<int:post_id>/delete/", bv.board_delete, name="board_delete"),
    path("board/<int:post_id>/react/", bv.board_react, name="board_react"),
    path("board/mine/", bv.board_mine, name="board_mine"),

    # 誇誇成長
    path("grow/", gv.GrowView.as_view(), name="grow"),
    path("kudos/add/", gv.kudos_add, name="kudos_add"),
    path("kudos/<int:note_id>/delete/", gv.kudos_delete, name="kudos_delete"),
    path("tasks/<int:task_id>/toggle/", gv.task_toggle, name="task_toggle"),
    path("grow/review/generate/", gv.review_generate, name="review_generate"),
    path("mood/checkin/", gv.mood_checkin, name="mood_checkin"),

    # 心理資源 / 診所指南（訪客可看）
    path("resources/", ResourcesView.as_view(), name="resources"),
    path("resources/articles/<int:pk>/", ArticleDetailView.as_view(), name="article_detail"),
    path("resources/articles/filter/", rv.article_filter, name="article_filter"),
    path("clinics/", ClinicsView.as_view(), name="clinics"),

    # 帳號（django-allauth）
    path("accounts/", include("allauth.urls")),

    # 個人設定
    path("settings/profile/", av.settings_profile, name="settings_profile"),
    path("settings/appearance/", av.settings_appearance, name="settings_appearance"),
    path("settings/delete/", av.account_delete, name="account_delete"),
    path("settings/clear-chat/", av.clear_chat_history, name="clear_chat_history"),
    path("settings/clear-kudos/", av.clear_kudos, name="clear_kudos"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
