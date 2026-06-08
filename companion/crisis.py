"""
危機偵測層（第一層：關鍵字，確定性，恆可用，與 LLM 完全解耦）。
第二層語意分類器為選配，即使缺席關鍵字層仍能觸發。
"""

SOS_KEYWORDS = [
    "不想活", "活不下去", "想死", "自殺", "結束生命", "撐不下去",
    "傷害自己", "自殘", "沒有意義", "消失", "解脫",
    "輕生", "了結", "尋死", "去死", "想消失",
    "活著沒意義", "活著好累", "不想撐了",
]


def detect_crisis(text: str) -> str | None:
    """
    掃描使用者輸入，命中任一關鍵字即回傳該關鍵字（供 SOSLog 記錄）。
    未命中回傳 None。

    設計原則：寧可誤報（false positive），不可漏報（false negative）。
    """
    for kw in SOS_KEYWORDS:
        if kw in text:
            return kw
    return None
