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
    """內建暖心語錄：首頁「今日暖心語」、成長頁「私人暖心小卡」隨機抽取，
    以及看板發文時可選作貼文內容（BoardPost.preset_message）。"""
    CATEGORY_CHOICES = [
        ("self_encourage", "自我鼓勵"),
        ("companionship", "陪伴支持"),
        ("self_acceptance", "接納自己"),
        ("facing_setbacks", "面對挫折"),
        ("hope_future", "希望與未來"),
        ("gratitude", "感恩珍惜"),
        ("stress_relief", "壓力舒緩"),
        ("relationships", "人際關係"),
        ("courage_growth", "勇氣成長"),
        ("depression_relief", "憂鬱與低潮療癒"),
    ]

    content = models.CharField("內容", max_length=60)
    category = models.CharField(
        "分類", max_length=20, choices=CATEGORY_CHOICES, default="self_encourage"
    )
    is_active = models.BooleanField("啟用", default=True)

    class Meta:
        verbose_name = "暖心語錄"
        verbose_name_plural = "暖心語錄"
        ordering = ["category", "content"]

    def __str__(self):
        return self.content[:30]


class BoardPost(TimeStampedModel):
    """心情貼文（去文字化：天氣圖示與/或暖心語，皆從預設清單選擇，無自由文字欄位）。"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="board_posts"
    )
    preset_icon = models.ForeignKey(
        PresetIcon, on_delete=models.PROTECT, related_name="posts",
        null=True, blank=True,
    )
    preset_message = models.ForeignKey(
        PresetMessage, on_delete=models.PROTECT, related_name="posts",
        null=True, blank=True,
    )
    is_anonymous = models.BooleanField("匿名發布", default=True)
    # 軟刪除：用戶可撤回，後台保留稽核紀錄
    is_deleted = models.BooleanField("已撤回", default=False)
    deleted_at  = models.DateTimeField("撤回時間", null=True, blank=True)

    class Meta:
        verbose_name = "看板貼文"
        verbose_name_plural = "看板貼文"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(preset_icon__isnull=False) | models.Q(preset_message__isnull=False),
                name="board_post_icon_or_message_required",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.preset_icon_id is None and self.preset_message_id is None:
            raise ValidationError("貼文必須至少包含天氣圖示或暖心語其中一項。")

    def __str__(self):
        if self.preset_icon and self.preset_message:
            content = f"「{self.preset_icon.label}」+「{self.preset_message.content[:15]}」"
        elif self.preset_icon:
            content = f"「{self.preset_icon.label}」"
        else:
            content = f"「{self.preset_message.content[:15]}」"
        return f"{self.user.email} 發布了 {content}"


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
