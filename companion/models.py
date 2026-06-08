from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel
from accounts.models import User
from accounts.crypto import encrypt


class ChatSession(TimeStampedModel):
    """一次連續的對話期間。"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sessions"
    )
    crisis_mode = models.BooleanField(
        "危機模式", default=False,
        help_text="True 表示已切換到安全模式 system prompt"
    )
    crisis_since = models.DateTimeField("進入危機時間", null=True, blank=True)
    end_time = models.DateTimeField("結束時間", null=True, blank=True)
    is_deleted = models.BooleanField("已刪除", default=False)
    summary = encrypt(models.TextField("摘要（加密）", blank=True))

    class Meta:
        verbose_name = "對話期間"
        verbose_name_plural = "對話期間"
        ordering = ["-created_at"]

    def __str__(self):
        status = "⚠️ 危機" if self.crisis_mode else "正常"
        return f"{self.user.email} [{status}] {self.created_at:%Y-%m-%d %H:%M}"

    def enter_crisis(self):
        if not self.crisis_mode:
            self.crisis_mode = True
            self.crisis_since = timezone.now()
            self.save(update_fields=["crisis_mode", "crisis_since"])


class AIChatLog(TimeStampedModel):
    """單則訊息記錄（加密）。"""
    SENDER_CHOICES = [("user", "使用者"), ("ai", "AI")]

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="logs"
    )
    sender = models.CharField("發送者", max_length=4, choices=SENDER_CHOICES)
    message_content = models.TextField("內容")
    crisis_flagged = models.BooleanField("危機標記", default=False)
    # Groq LLM 情緒評分（1-10，僅 sender='user' 時有值）
    mood_score     = models.SmallIntegerField("情緒分數", null=True, blank=True)
    mood_reasoning = models.CharField("評分說明", max_length=100, blank=True)

    class Meta:
        verbose_name = "對話記錄"
        verbose_name_plural = "對話記錄"
        ordering = ["created_at"]

    def __str__(self):
        flag = "⚠️ " if self.crisis_flagged else ""
        return f"{flag}[{self.sender}] {self.created_at:%H:%M:%S}"


class SOSLog(TimeStampedModel):
    """危機事件稽核日誌（v2：action 記錄切換 prompt + 浮現專線）。"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sos_events"
    )
    chat_log = models.ForeignKey(
        AIChatLog, on_delete=models.SET_NULL, null=True, blank=True
    )
    triggering_keyword = models.CharField("觸發關鍵字", max_length=80, blank=True)
    detector = models.CharField(
        "偵測器", max_length=20, default="keyword"
    )  # keyword / nlp
    action_taken = models.CharField(
        "採取動作", max_length=120,
        default="system_prompt_switched+hotlines_surfaced"
    )

    class Meta:
        verbose_name = "SOS 事件"
        verbose_name_plural = "SOS 事件"
        ordering = ["-created_at"]

    def __str__(self):
        return f"SOS {self.user.email} [{self.triggering_keyword}] {self.created_at:%Y-%m-%d %H:%M}"
