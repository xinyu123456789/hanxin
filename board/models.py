from django.db import models

from core.models import TimeStampedModel
from accounts.models import User


class PresetIcon(TimeStampedModel):
    """天氣心情圖示（管理員維護）。"""
    EMOTION_CHOICES = [
        ("sun", "晴朗"),
        ("breeze", "微風"),
        ("rainbow", "雨後彩虹"),
        ("cloud", "烏雲"),
        ("rain", "大雨"),
        ("storm", "閃電"),
    ]

    # 使用靜態檔路徑（相對 static/），避免 Pillow 依賴
    image_path = models.CharField(
        "圖片路徑", max_length=200,
        help_text="相對 static/ 的路徑，例如 img/assets/mood-sun.jpg"
    )
    emotion_type = models.CharField(
        "情緒類型", max_length=20, choices=EMOTION_CHOICES, unique=True
    )
    label = models.CharField("標籤", max_length=20)
    desc = models.CharField("描述", max_length=60, blank=True)
    tint_var = models.CharField(
        "色調 CSS 變數", max_length=40, blank=True,
        help_text="例如 var(--sage-tint)"
    )
    ring_var = models.CharField(
        "邊框 CSS 變數", max_length=40, blank=True,
        help_text="例如 var(--sage-deep)"
    )
    is_active = models.BooleanField("啟用", default=True)

    class Meta:
        verbose_name = "預設心情圖示"
        verbose_name_plural = "預設心情圖示"
        ordering = ["emotion_type"]

    def __str__(self):
        return f"{self.label}（{self.emotion_type}）"


class PresetMessage(TimeStampedModel):
    """內建暖心語錄（去文字化看板的「暖心語」互動模式用）。"""
    content = models.CharField("內容", max_length=60)
    is_active = models.BooleanField("啟用", default=True)

    class Meta:
        verbose_name = "暖心語錄"
        verbose_name_plural = "暖心語錄"

    def __str__(self):
        return self.content[:30]


class BoardPost(TimeStampedModel):
    """心情貼文（去文字化：只有天氣圖示，無任何自由文字欄位）。"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="board_posts"
    )
    preset_icon = models.ForeignKey(
        PresetIcon, on_delete=models.PROTECT, related_name="posts"
    )
    # 刻意無自由文字欄位——從資料結構杜絕負評
    # 軟刪除：用戶可撤回，後台保留稽核紀錄
    is_deleted = models.BooleanField("已撤回", default=False)
    deleted_at  = models.DateTimeField("撤回時間", null=True, blank=True)

    class Meta:
        verbose_name = "看板貼文"
        verbose_name_plural = "看板貼文"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} 發布了「{self.preset_icon.label}」"


class BoardReaction(TimeStampedModel):
    """貼文回應（貼圖送暖）。"""
    STICKER_CHOICES = [
        ("hug", "抱抱"),
        ("pat", "拍拍"),
        ("highfive", "擊掌加油"),
        ("warm", "暖暖的"),
    ]

    post = models.ForeignKey(
        BoardPost, on_delete=models.CASCADE, related_name="reactions"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reactions"
    )
    sticker = models.CharField("貼圖", max_length=10, choices=STICKER_CHOICES)

    class Meta:
        verbose_name = "看板回應"
        verbose_name_plural = "看板回應"
        unique_together = ("post", "user", "sticker")  # 同貼圖不重複灌（修正原型缺口）

    def __str__(self):
        return f"{self.user.email} 對 post#{self.post_id} 送了「{self.sticker}」"
