"""
Gemini 情緒評分層（危機偵測第二層）。

呼叫順序：
  1. Gemini（settings.GEMINI_MODEL_EMOTION，JSON 模式）
  2. 關鍵字偵測 — 呼叫端降級（Gemini 失敗時，見 crisis.py）

分數 1-10：
  1-2：極度痛苦／有自傷念頭（< 3 → 觸發危機）
  3-4：情緒非常低落、需要關注
  5-6：情緒低落或平淡
  7-8：情緒穩定
  9-10：情緒正向
"""
import json
import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)

CRISIS_THRESHOLD = 3  # 分數 < 此值即進入危機模式

SYSTEM_PROMPT = """你是心理健康對話的情緒評估助手。
根據提供的對話歷史，評估「使用者」目前的情緒狀態。

評分標準（1-10 整數）：
  1-2：極度痛苦、有自傷或自殺念頭、危機狀態
  3-4：情緒非常低落、明顯悲傷或焦慮、需要持續關注
  5-6：情緒有些低落或平淡、一般狀態
  7-8：情緒穩定、尚好
  9-10：情緒正向、愉快

注意事項：
- 重點放在最新的訊息，但要考慮整體對話脈絡與情緒趨勢
- 即使使用者說「沒事了」，若先前有高危訊號，不應立即給高分
- 只回傳合法 JSON，不要任何其他文字

輸出格式：{"score": <1-10整數>, "reasoning": "<中文簡短說明，20字以內>"}"""


def build_history_messages(logs, current_text: str) -> list[dict]:
    """
    把歷史 logs + 目前訊息組成 messages 陣列。
    用結構化格式（role/content 分離）防止 prompt injection。
    """
    messages = []
    for log in logs:
        role = "user" if log.sender == "user" else "assistant"
        messages.append({"role": role, "content": log.message_content})
    messages.append({"role": "user", "content": current_text})
    return messages


def _extract_json(text: str) -> dict | None:
    """
    從回應文字中提取 JSON。
    處理模型可能夾帶 <think>...</think> 或其他前置文字的情況。
    """
    # 先嘗試直接解析
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # 去除 thinking 標籤後再試
    clean = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # 用 regex 從任意位置找 {...}
    match = re.search(r"\{[^{}]*\}", clean or text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


def score_emotion(session, current_text: str) -> tuple[int | None, str]:
    """
    呼叫 Gemini（JSON 模式）評估使用者情緒分數。

    Returns:
        (score: int | None, reasoning: str)
        失敗時回傳 (None, "") → 呼叫端降級到關鍵字偵測。
    """
    from google import genai
    from google.genai import types

    recent_logs = list(session.logs.order_by("-created_at")[:20])[::-1]
    history_messages = build_history_messages(recent_logs, current_text)

    role_map = {"user": "user", "assistant": "model"}
    contents = [
        types.Content(
            role=role_map[m["role"]],
            parts=[types.Part.from_text(text=m["content"])],
        )
        for m in history_messages
    ]

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        resp = client.models.generate_content(
            model=settings.GEMINI_MODEL_EMOTION,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
                max_output_tokens=256,
                response_mime_type="application/json",
            ),
        )

        data = _extract_json(resp.text or "")
        if data is None:
            logger.warning("Gemini 情緒評分回應無法解析為 JSON：%s", (resp.text or "")[:200])
            return None, ""

        score = max(1, min(10, int(data.get("score", 5))))
        reasoning = str(data.get("reasoning", ""))[:100]
        return score, reasoning
    except Exception:
        logger.warning("Gemini 情緒評分失敗，降級到關鍵字偵測", exc_info=True)
        return None, ""


def is_crisis_by_score(score: int) -> bool:
    """分數低於閾值即判定為危機。"""
    return score < CRISIS_THRESHOLD
