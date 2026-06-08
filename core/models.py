from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SituationQuestion(TimeStampedModel):
    """首頁情境題（管理員維護，供用戶分享觀點）。"""
    content   = models.TextField("情境描述")
    option_a  = models.CharField("選項 A", max_length=100)
    option_b  = models.CharField("選項 B", max_length=100)
    option_c  = models.CharField("選項 C", max_length=100)
    active_date = models.DateField(
        "每日顯示日期", null=True, blank=True,
        help_text="指定哪天作為當日題目，留空表示備用題庫"
    )
    is_active = models.BooleanField("啟用", default=True)

    class Meta:
        verbose_name = "情境題"
        verbose_name_plural = "情境題"
        ordering = ["-created_at"]

    @property
    def options(self):
        return [("a", self.option_a), ("b", self.option_b), ("c", self.option_c)]

    def __str__(self):
        return self.content[:40]


class SituationResponse(TimeStampedModel):
    """情境題的用戶回答（不加密，user 可為 null 代表匿名訪客）。"""
    MODE_CHOICES = [("text", "簡答"), ("choice", "選擇")]
    CHOICE_OPTIONS = [("a", "A"), ("b", "B"), ("c", "C")]

    user     = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="situation_responses"
    )
    question = models.ForeignKey(
        SituationQuestion, on_delete=models.CASCADE,
        related_name="responses"
    )
    mode        = models.CharField("回答模式", max_length=6, choices=MODE_CHOICES)
    text_answer = models.TextField("簡答內容", blank=True, max_length=200)
    choice      = models.CharField(
        "選擇", max_length=1, choices=CHOICE_OPTIONS,
        null=True, blank=True
    )
    is_public   = models.BooleanField(
        "公開簡答", default=True,
        help_text="關閉後此則簡答不會出現在其他人看到的範例中（僅 mode=text 有效）"
    )

    class Meta:
        verbose_name = "情境題回答"
        verbose_name_plural = "情境題回答"
        ordering = ["-created_at"]

    def __str__(self):
        who = self.user.email if self.user else "訪客"
        return f"{who} → {self.question.content[:20]}"
