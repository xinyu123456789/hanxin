"""
驗證使用者提供的 Gemini API 金鑰是否可用。
用最小的 API 呼叫（max_output_tokens=1）減少延遲與消耗。
"""
from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from django.conf import settings


def validate_key(api_key: str) -> tuple[bool, str]:
    """
    打一次極小的呼叫驗證金鑰。
    回傳 (True, "") 表示成功；(False, error_msg) 表示失敗。
    """
    try:
        client = genai.Client(api_key=api_key.strip())
        client.models.generate_content(
            model=settings.GEMINI_DEFAULT_MODEL,
            contents="ping",
            config=types.GenerateContentConfig(max_output_tokens=1),
        )
        return True, ""
    except genai_errors.APIError as e:
        return False, getattr(e, "message", str(e))
    except Exception as e:
        return False, str(e)
