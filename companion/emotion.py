"""
Groq LLM 情緒評分層（危機偵測第二層）。

呼叫順序：
  1. NVIDIA NIM  — google/gemma-4-31b-it（主要，若 NVIDIA_API_KEY 已設定）
  2. Groq 主模型 — GROQ_EMOTION_MODEL（備援）
  3. Groq 次模型 — GROQ_EMOTION_MODEL_FALLBACK（二備援）
  4. 關鍵字偵測  — 呼叫端降級（所有 LLM 失敗時）

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


def _call_nvidia(api_key: str, history_messages: list):
    """
    用 NVIDIA NIM（google/gemma-4-31b-it）評估情緒。
    成功回傳 (score, reasoning)；失敗回傳 None。
    """
    import requests as req

    payload = {
        "model": "google/gemma-4-31b-it",
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history_messages,
        "max_tokens": 256,
        "temperature": 0.1,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }

    resp = req.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        json=payload,
        timeout=4,
    )
    resp.raise_for_status()

    raw = (resp.json().get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
    if not raw:
        return None

    data = _extract_json(raw)
    if data is None:
        logger.warning("NVIDIA 回應無法解析為 JSON：%s", raw[:200])
        return None

    score = max(1, min(10, int(data.get("score", 5))))
    reasoning = str(data.get("reasoning", ""))[:100]
    return score, reasoning


def _call_groq(api_key: str, model: str, history_messages: list):
    """
    用指定 Groq 模型評估情緒。
    成功回傳 (score, reasoning)；失敗或回應無效回傳 None。
    """
    from groq import Groq

    is_reasoning = any(x in model for x in ("gpt-oss", "o1", "o3", "r1"))

    if is_reasoning:
        final_messages = [
            {"role": "user", "content": f"{SYSTEM_PROMPT}\n\n請根據以下對話歷史評估情緒分數。"},
        ] + history_messages
    else:
        final_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ] + history_messages

    call_kwargs = dict(
        model=model,
        messages=final_messages,
        max_completion_tokens=256,
        response_format={"type": "json_object"},
        stream=False,
    )
    if is_reasoning:
        call_kwargs["reasoning_effort"] = "medium"
    else:
        call_kwargs["temperature"] = 0.1

    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(**call_kwargs)

    raw = (resp.choices[0].message.content or "").strip()
    if not raw:
        raw = getattr(resp.choices[0].message, "reasoning_content", "") or ""
    if not raw:
        return None

    data = _extract_json(raw)
    if data is None:
        return None

    score = max(1, min(10, int(data.get("score", 5))))
    reasoning = str(data.get("reasoning", ""))[:100]
    return score, reasoning


def score_emotion(session, current_text: str) -> tuple[int, str]:
    """
    依序嘗試 NVIDIA → Groq 主模型 → Groq 備援 評估情緒分數。

    Returns:
        (score: int | None, reasoning: str)
        全部失敗時回傳 (None, "") → 呼叫端降級到關鍵字偵測。
    """
    nvidia_key = getattr(settings, "NVIDIA_API_KEY", "")
    groq_key   = getattr(settings, "GROQ_API_KEY", "")

    if not nvidia_key and not groq_key:
        logger.debug("未設定任何情緒評分 API，降級到關鍵字偵測")
        return None, ""

    recent_logs = list(session.logs.order_by("-created_at")[:20])[::-1]
    history_messages = build_history_messages(recent_logs, current_text)

    # Layer 1：NVIDIA Gemma-4-31b
    if nvidia_key:
        try:
            result = _call_nvidia(nvidia_key, history_messages)
            if result is not None:
                return result
        except Exception:
            logger.warning("NVIDIA 情緒評分失敗，降級到 Groq", exc_info=True)

    # Layer 2 & 3：Groq 主模型 + 備援
    if groq_key:
        primary  = getattr(settings, "GROQ_EMOTION_MODEL",          "openai/gpt-oss-120b")
        fallback = getattr(settings, "GROQ_EMOTION_MODEL_FALLBACK", "openai/gpt-oss-20b")

        for model_name in (primary, fallback):
            try:
                result = _call_groq(groq_key, model_name, history_messages)
                if result is not None:
                    return result
            except Exception:
                logger.warning("Groq 模型 %s 失敗，嘗試下一個", model_name, exc_info=True)

    logger.warning("所有情緒評分模型均失敗，降級到關鍵字偵測")
    return None, ""


def is_crisis_by_score(score: int) -> bool:
    """分數低於閾值即判定為危機。"""
    return score < CRISIS_THRESHOLD
