from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.postgres.fields import ArrayField
from django.db import models

from core.models import TimeStampedModel


class UserManager(BaseUserManager):
    """以 email 取代 username 的使用者管理器。"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("必須提供電子郵件")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """自訂使用者：以 email 取代 username 作為登入識別。"""
    username = None
    email = models.EmailField("電子郵件", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "使用者"
        verbose_name_plural = "使用者"

    def __str__(self):
        return self.email


class UserProfile(TimeStampedModel):
    """使用者個人檔案。"""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    nickname = models.CharField("暱稱", max_length=40, blank=True)
    self_description_tags = ArrayField(
        models.CharField(max_length=20), default=list, blank=True, verbose_name="自我描述標籤"
    )
    interested_topics = ArrayField(
        models.CharField(max_length=20), default=list, blank=True, verbose_name="關注主題"
    )
    emergency_contact_name = models.CharField("緊急聯絡人姓名", max_length=40, blank=True)
    emergency_contact_phone = models.CharField("緊急聯絡人電話", max_length=20, blank=True)
    emergency_contact_relation = models.CharField("關係", max_length=20, blank=True)
    # 使用者層級危機狀態（跨 session）：到期時間；None 表示非危機
    crisis_until = models.DateTimeField("危機狀態到期時間", null=True, blank=True)

    @property
    def is_in_crisis(self) -> bool:
        """是否在 30 分鐘危機窗口內（跨所有 session）。"""
        if not self.crisis_until:
            return False
        from django.utils import timezone
        return self.crisis_until > timezone.now()

    def enter_crisis(self, minutes: int = 30):
        """觸發危機：設定有效期（預設 30 分鐘，最長 24 小時）。"""
        from django.utils import timezone
        from datetime import timedelta
        minutes = min(minutes, 60 * 24)  # 安全上限：24 小時
        self.crisis_until = timezone.now() + timedelta(minutes=minutes)
        self.save(update_fields=["crisis_until"])

    def clear_crisis(self):
        """手動解除危機狀態（供 Admin 操作）。"""
        self.crisis_until = None
        self.save(update_fields=["crisis_until"])

    class Meta:
        verbose_name = "個人檔案"
        verbose_name_plural = "個人檔案"

    def __str__(self):
        return f"{self.user.email} 的個人檔案"


class UserPreference(TimeStampedModel):
    """使用者外觀與互動偏好（取代原型 Tweaks 旋鈕）。"""
    ACCENT_CHOICES = [
        ("peach", "蜜桃"),
        ("sage", "鼠尾草綠"),
        ("sky", "天空藍"),
        ("lilac", "薰衣草紫"),
    ]
    BOARD_REACT_CHOICES = [
        ("tray", "回應盤"),
        ("quick", "常駐"),
    ]
    TREE_STYLE_CHOICES = [
        ("tree", "心情樹"),
        ("garden", "花園"),
        ("jar", "感謝罐"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="preference"
    )
    accent = models.CharField(
        "主題色", max_length=10, choices=ACCENT_CHOICES, default="peach"
    )
    font_scale = models.PositiveSmallIntegerField("字級 (%)", default=100)
    board_react = models.CharField(
        "看板互動模式", max_length=10, choices=BOARD_REACT_CHOICES, default="tray"
    )
    tree_style = models.CharField(
        "成長視覺", max_length=10, choices=TREE_STYLE_CHOICES, default="tree"
    )
    soft_bg = models.BooleanField("柔光漸層背景", default=True)

    class Meta:
        verbose_name = "使用者偏好"
        verbose_name_plural = "使用者偏好"

    def __str__(self):
        return f"{self.user.email} 的偏好設定"
