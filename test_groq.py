"""
Groq 連線測試腳本
用法：python test_groq.py
"""
import os
import sys
import django

# 設定 Django 環境
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "hanxin_mental_health_support_site.settings.dev")
django.setup()

from django.conf import settings

print("=" * 50)
print("Groq 連線測試")
print("=" * 50)

# 1. 檢查金鑰是否有讀到
key = getattr(settings, "GROQ_API_KEY", "")
model = getattr(settings, "GROQ_EMOTION_MODEL", "llama3-8b-8192")

print(f"\n[1] GROQ_API_KEY  : {key[:12]}{'...' if len(key) > 12 else ''!r}")
print(f"[1] GROQ_EMOTION_MODEL: {model}")

if not key or key == "gsk_你的金鑰":
    print("\n❌ 金鑰未設定或仍是範本值，請檢查 .env 檔案")
    sys.exit(1)

# 2. 測試基本連線
print("\n[2] 測試基本連線...")
try:
    from groq import Groq
    client = Groq(api_key=key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "說「連線成功」三個字"}],
        max_completion_tokens=20,
    )
    print(f"✅ 連線成功：{resp.choices[0].message.content.strip()}")
except Exception as e:
    print(f"❌ 連線失敗：{e}")
    sys.exit(1)

# 3. 測試情緒評分（正常情緒）
print("\n[3] 測試情緒評分 - 正常情緒...")
try:
    import json
    from companion.emotion import SYSTEM_PROMPT
    is_reasoning = any(x in model for x in ("gpt-oss", "o1", "o3", "r1"))
    kw = dict(max_completion_tokens=2048, response_format={"type": "json_object"}, stream=False)
    if is_reasoning:
        kw["reasoning_effort"] = "medium"
    else:
        kw["temperature"] = 0.1

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content":
            f"{SYSTEM_PROMPT}\n\n以下是對話記錄：\n\n使用者: 今天天氣不錯\n\n請輸出 JSON 情緒評分。"}],
        **kw,
    )
    raw = (resp.choices[0].message.content or "").strip()
    if not raw:
        raw = getattr(resp.choices[0].message, "reasoning_content", "") or ""
    print(f"   原始回應: {raw[:200]}")
    data = json.loads(raw)
    score = data.get("score")
    print(f"✅ 正常情緒分數：{score}（預期 6-10）")
    print(f"   說明：{data.get('reasoning', '')}")
except Exception as e:
    print(f"❌ 評分失敗：{e}")
    print(f"   原始回應：{raw if 'raw' in dir() else '無'}")

# 4. 測試情緒評分（危機情緒）
print("\n[4] 測試情緒評分 - 危機情緒...")
try:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content":
            f"{SYSTEM_PROMPT}\n\n以下是對話記錄：\n\n使用者: 害我一整個超難過，超級想要割手\n\n請輸出 JSON 情緒評分。"}],
        **kw,
    )
    raw = (resp.choices[0].message.content or "").strip()
    if not raw:
        raw = getattr(resp.choices[0].message, "reasoning_content", "") or ""
    print(f"   原始回應: {raw[:200]}")
    data = json.loads(raw)
    score = data.get("score")
    status = "✅" if score and score <= 2 else "⚠️"
    print(f"{status} 危機情緒分數：{score}（預期 1-2）")
    print(f"   說明：{data.get('reasoning', '')}")
except Exception as e:
    print(f"❌ 評分失敗：{e}")
    print(f"   原始回應：{raw if 'raw' in dir() else '無'}")

print("\n" + "=" * 50)
print("測試完成")
