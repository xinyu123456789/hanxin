"""
欄位加密輔助層。

使用 django-cryptography-django5，它以 Fernet（對稱加密）包裹 Django ORM 欄位。
加密/解密完全透明：model.field 直接存取已解密的值。
"""
from django_cryptography.fields import encrypt  # noqa: F401  重新匯出，供 models.py 使用


def decrypt(value: str | None) -> str:
    """
    加密欄位在 attribute access 時已自動解密，此函式為語意明確的 no-op。
    companion/gemini_chat.py 等地方呼叫 decrypt(log.message_content)，
    實際上直接回傳已解密的值。
    """
    return value if value is not None else ""
