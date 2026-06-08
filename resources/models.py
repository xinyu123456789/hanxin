from django.db import models
from urllib.parse import quote

from core.models import TimeStampedModel
from django.conf import settings


class PsychoArticle(TimeStampedModel):
    """心理科普文章。"""
    CATEGORY_CHOICES = [
        ("壓力管理", "壓力管理"),
        ("情緒覺察", "情緒覺察"),
        ("焦慮", "焦慮"),
        ("睡眠", "睡眠"),
        ("人際關係", "人際關係"),
        ("自我照顧", "自我照顧"),
        ("AI 小說", "AI 小說"),
        ("逐字稿", "逐字稿"),
    ]
    # 分類對應的標籤樣式（CSS class 後綴 / 顏色）
    CATEGORY_STYLE = {
        "AI 小說": ("lilac", "✍️"),
        "逐字稿":  ("sky",   "🎙️"),
    }
    title = models.CharField("標題", max_length=120)
    category = models.CharField("分類", max_length=30, choices=CATEGORY_CHOICES, db_index=True)
    read_minutes = models.PositiveSmallIntegerField("閱讀分鐘", default=4)
    excerpt = models.TextField("摘要")
    content_markdown = models.TextField("正文（Markdown）", blank=True)
    view_count = models.PositiveIntegerField("點擊次數", default=0)
    is_active = models.BooleanField("啟用", default=True)

    class Meta:
        verbose_name = "心理科普文章"
        verbose_name_plural = "心理科普文章"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class PsychoScale(TimeStampedModel):
    """專業心理量表連結。"""
    name = models.CharField("量表名稱", max_length=120)
    org = models.CharField("提供機構", max_length=80)
    external_url = models.URLField("外部連結")
    note = models.TextField("說明", blank=True)
    is_active = models.BooleanField("啟用", default=True)

    class Meta:
        verbose_name = "心理量表"
        verbose_name_plural = "心理量表"

    def __str__(self):
        return self.name


class PsychoVideo(TimeStampedModel):
    """心理健康影片頻道。"""
    name = models.CharField("頻道/影片名稱", max_length=80)
    lang = models.CharField("語言", max_length=10, default="中文")
    url = models.URLField("連結")
    desc = models.CharField("說明", max_length=120, blank=True)
    is_active = models.BooleanField("啟用", default=True)

    class Meta:
        verbose_name = "心理影片"
        verbose_name_plural = "心理影片"

    def __str__(self):
        return self.name


class PsychoPodcast(TimeStampedModel):
    """心理健康 Podcast。"""
    name = models.CharField("Podcast 名稱", max_length=80)
    url = models.URLField("連結")
    desc = models.CharField("說明", max_length=120, blank=True)
    is_active = models.BooleanField("啟用", default=True)

    class Meta:
        verbose_name = "心理 Podcast"
        verbose_name_plural = "心理 Podcast"

    def __str__(self):
        return self.name


class Clinic(TimeStampedModel):
    """地區診所指南。"""
    TYPE_CHOICES = [("諮商所", "諮商所"), ("身心科", "身心科")]

    name = models.CharField("診所名稱", max_length=120)
    clinic_type = models.CharField("類型", max_length=10, choices=TYPE_CHOICES, db_index=True)
    county = models.CharField("縣市", max_length=10, db_index=True)
    district = models.CharField("行政區", max_length=20)
    address = models.CharField("地址", max_length=120, blank=True)
    phone = models.CharField("電話", max_length=20, blank=True)
    website_url = models.URLField("官網", blank=True)
    is_active = models.BooleanField("啟用", default=True)

    class Meta:
        verbose_name = "診所"
        verbose_name_plural = "診所"
        ordering = ["county", "name"]

    def __str__(self):
        return f"【{self.clinic_type}】{self.county} {self.name}"

    @property
    def maps_url(self) -> str:
        query = quote(f"{self.county}{self.district}{self.name}")
        return f"https://www.google.com/maps/search/?api=1&query={query}"


class ArticleView(models.Model):
    """記錄登入用戶讀了哪篇文章（週回顧用）。"""
    user    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="article_views"
    )
    article = models.ForeignKey(
        PsychoArticle, on_delete=models.CASCADE, related_name="views"
    )
    first_viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "文章閱讀記錄"
        verbose_name_plural = "文章閱讀記錄"
        unique_together = ("user", "article")   # 每篇只記一次
        ordering = ["-first_viewed_at"]

    def __str__(self):
        return f"{self.user} 讀了《{self.article.title}》"
