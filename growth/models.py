from django.db import models

from core.models import TimeStampedModel
from accounts.models import User
from accounts.crypto import LenientEncryptedTextField


class KudosNote(TimeStampedModel):
    """誇誇筆記（私人、加密）。"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="kudos"
    )
    praise_content = LenientEncryptedTextField("內容")
    is_deleted = models.BooleanField("已刪除", default=False)
    deleted_at  = models.DateTimeField("刪除時間", null=True, blank=True)

    class Meta:
        verbose_name = "誇誇筆記"
        verbose_name_plural = "誇誇筆記"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} 的誇誇 #{self.pk}"


class DailyTask(TimeStampedModel):
    """每日任務定義（管理員維護）。"""
    label = models.CharField("任務名稱", max_length=60)
    icon = models.CharField("圖示（emoji）", max_length=8)
    sort_order = models.PositiveSmallIntegerField("排序", default=0)
    is_active = models.BooleanField("啟用", default=True)

    class Meta:
        verbose_name = "每日任務"
        verbose_name_plural = "每日任務"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.icon} {self.label}"


class DailyTaskLog(TimeStampedModel):
    """使用者完成每日任務的記錄。"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="task_logs"
    )
    task = models.ForeignKey(
        DailyTask, on_delete=models.CASCADE, related_name="logs"
    )
    date = models.DateField("日期")

    class Meta:
        verbose_name = "任務完成記錄"
        verbose_name_plural = "任務完成記錄"
        unique_together = ("user", "task", "date")

    def __str__(self):
        return f"{self.user.email} · {self.task.label} · {self.date}"


class WeeklyReviewVersion(models.Model):
    """每次生成的週回顧版本（保留所有歷史，不刪除）。"""
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="review_versions")
    week_start = models.DateField("週開始")
    summary_data = models.JSONField("回顧資料", default=dict)
    generated_at = models.DateTimeField("生成時間", auto_now_add=True)

    class Meta:
        verbose_name = "週回顧版本"
        verbose_name_plural = "週回顧版本"
        ordering = ["-generated_at"]

    def __str__(self):
        return f"{self.user.email} 第 {self.pk} 版 {self.week_start}"


class DailyMood(TimeStampedModel):
    """每日心情打卡（每人每天一筆，可當天更新）。"""
    MOOD_CHOICES = [
        ("awful",   "😭 很難過"),
        ("sad",     "😢 有點低落"),
        ("neutral", "😐 普通"),
        ("good",    "🙂 還不錯"),
        ("great",   "😄 很開心"),
    ]
    MOOD_EMOJI = {
        "awful":   "😭",
        "sad":     "😢",
        "neutral": "😐",
        "good":    "🙂",
        "great":   "😄",
    }

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="daily_moods"
    )
    date = models.DateField("打卡日期")
    mood = models.CharField("心情", max_length=10, choices=MOOD_CHOICES)

    class Meta:
        verbose_name = "每日心情"
        verbose_name_plural = "每日心情"
        ordering = ["-date"]
        unique_together = ("user", "date")

    def __str__(self):
        return f"{self.user.email} · {self.date} · {self.get_mood_display()}"

    @property
    def emoji(self):
        return self.MOOD_EMOJI.get(self.mood, "")


class WeeklyReview(TimeStampedModel):
    """每週回顧摘要（Celery Beat 自動產生）。"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="weekly_reviews"
    )
    start_date = models.DateField("週開始")
    end_date = models.DateField("週結束")
    summary_data = models.JSONField(
        "摘要資料", default=dict,
        help_text="心情樹/花園/罐視覺化資料與統計"
    )

    class Meta:
        verbose_name = "每週回顧"
        verbose_name_plural = "每週回顧"
        ordering = ["-start_date"]
        unique_together = ("user", "start_date")

    def __str__(self):
        return f"{self.user.email} 的週回顧 {self.start_date} ~ {self.end_date}"
