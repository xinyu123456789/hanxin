# 涵心 · Hanxin

> 一個以「溫柔」與「安全」為核心的中文心理健康支持網站。
> 讓人能安心地說話、被好好接住，並在需要時被真正的資源接手。

[![Django](https://img.shields.io/badge/Django-5.1-092E20?logo=django)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-required-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![HTMX](https://img.shields.io/badge/HTMX-+Alpine.js-3366CC)](https://htmx.org/)

---

## 這是什麼

**涵心**是一個 Django 全端網站，目標是成為一個「不會傷人」的心理健康陪伴空間。它不追求功能堆疊，而是在每個設計決策上優先考慮使用者的情緒安全：

- 看板**從資料結構上就無法留下負評**（只能貼天氣圖示，沒有自由文字欄位）。
- AI 聊天有**雙層危機偵測安全網**，寧可誤報、不可漏報，觸發時切換安全模式並浮出求助專線。

---

## ✨ 特色功能

| 模組 | 功能 |
| --- | --- |
| 🏠 **首頁 / 情境題** | 每日任務打卡、成長視覺、每日情境題（匿名訪客也能作答、分享觀點） |
| 💬 **涵涵 AI 聊天** | 以 Google Gemini 為核心的串流對話（SSE） |
| 🌤️ **心情看板** | 去文字化設計，只用「天氣圖示」表達心情、用貼圖互相送暖，每日刷新 |
| 🌱 **誇誇成長** | 私人加密的誇誇筆記、每日心情打卡與日曆、AI 自動生成的每週回顧 |
| 📚 **心理資源** | 心理科普文章、專業量表、影片 / Podcast、含縣市與行政區篩選的診所指南 |
| 👤 **帳號 / 設定** | Email 登入（django-allauth）、主題色 / 字級 / 成長視覺偏好、訪客模式 |

---

## 🛡️ 安全與隱私設計

這是這個專案最用心的部分。

### 雙層危機偵測安全網
當使用者在聊天中透露危機訊號時，系統會層層把關（設計原則：**寧可誤報，不可漏報**）：

1. **關鍵字偵測** — 確定性、永遠可用，與 LLM 完全解耦（[`companion/crisis.py`](companion/crisis.py)）。
2. **Gemini 情緒評分** — 對對話脈絡評 1–10 分，分數 < 3 觸發危機（[`companion/emotion.py`](companion/emotion.py)）。

若 Gemini 暫時失效，系統會自動退回關鍵字層，安全網不會中斷。

觸發危機後：切換到安全模式 system prompt、浮出求助專線、並以**跨 session 的使用者層級狀態**維持 30 分鐘關懷窗口，所有事件寫入 `SOSLog` 稽核。

### 隱私優先
- **Argon2** 密碼雜湊、HTTPOnly + SameSite 的 signed-cookie session、生產環境強制 HTTPS + HSTS。
- **訪客模式**：未登入也能瀏覽與打卡，任務狀態只存在瀏覽器 signed cookie，不寫入資料庫。
- **軟刪除**：使用者撤回的看板貼文與誇誇筆記對外完全隱藏，後台仍保留稽核紀錄。

---

## 🧱 技術棧

- **後端**：Django 5.1、PostgreSQL（使用 `ArrayField` 等 PG 專屬功能）
- **非同步任務**：Celery + Celery Beat（每週日 20:00 自動產生週回顧）、Redis 作為 broker / 快取
- **前端**：Django Templates + [HTMX](https://htmx.org/) + [Alpine.js](https://alpinejs.dev/)，WhiteNoise 處理靜態檔
- **帳號**：django-allauth（以 **Email 取代 username** 登入）
- **AI**：Google Gemini（聊天、情緒評分、週回顧，平台統一金鑰，各功能可分別指定模型）
- **安全**：Argon2

---

## 📁 專案結構

```
hanxin_mental_health_support_site/
├── core/          # 首頁、情境題、共用基底 model、模板 tags
├── accounts/      # 自訂 User（email 登入）、個人檔案、偏好
├── companion/     # 涵涵 AI 聊天、三層危機偵測、SOS 稽核
├── board/         # 心情看板（去文字化、貼圖互動）
├── growth/        # 誇誇筆記、每日任務 / 心情、週回顧
├── resources/     # 心理科普文章、量表、診所指南
├── templates/     # 全站模板
├── static/        # CSS / JS / 圖片
└── hanxin_mental_health_support_site/
    └── settings/  # base / dev / prod 分層設定
```

---

## 🚀 快速開始

### 1. 前置需求
- Python 3.10+
- PostgreSQL 13+（**必要**，專案使用 PostgreSQL 專屬欄位，無法用 SQLite）
- Redis（**正式環境**才需要；開發模式預設用記憶體快取與同步 Celery，可不啟動）

### 2. 取得程式碼並建立虛擬環境

```bash
git clone https://github.com/xinyu123456789/hanxin.git
cd hanxin

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 設定環境變數

複製範本並填入真實值（`.env` 不會進版控）：

```bash
copy .env.template .env      # Windows
# cp .env.template .env      # macOS / Linux
```

產生兩把必要金鑰：

```bash
# DJANGO_SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# FIELD_ENCRYPTION_KEY（Fernet）
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

把產生的值與你的 PostgreSQL 連線字串填入 `.env`（詳見下方〈環境變數〉）。

### 4. 建立資料庫並載入種子資料

```bash
python manage.py migrate

# 載入預設資料（看板天氣圖示、每日任務、心理資源）
python manage.py loaddata board_presets growth_tasks resources_seed

# 建立管理員帳號
python manage.py createsuperuser
```

### 5. 啟動

```bash
python manage.py runserver
```

開啟 http://127.0.0.1:8000 ，後台在 http://127.0.0.1:8000/admin/ 。

### （選用）啟動 Celery 週回顧排程
開發模式預設讓 Celery 同步執行，免啟動。若要在本機跑真實的排程器：

```bash
celery -A hanxin_mental_health_support_site worker -l info
celery -A hanxin_mental_health_support_site beat   -l info
```

---

## ⚙️ 環境變數

| 變數 | 必要 | 說明 |
| --- | :---: | --- |
| `DJANGO_SECRET_KEY` | ✅ | Django 簽章金鑰 |
| `DATABASE_URL` | ✅ | PostgreSQL 連線字串，格式 `postgres://user:pass@host:5432/dbname` |
| `REDIS_URL` | ✅ | Redis 連線字串（開發模式不會實際連線，但設定載入時需要有值） |
| `FIELD_ENCRYPTION_KEY` | ✅ | Fernet 金鑰；設定載入時仍必填（與 `SECRET_KEY` 分開管理） |
| `DJANGO_DEBUG` | ⬜ | 預設 `False`；`dev` 設定會覆寫為 `True` |
| `GEMINI_API_KEY` | ✅ | Google Gemini API 金鑰（平台統一金鑰，全站功能共用） |
| `GEMINI_MODEL_CHAT` | ⬜ | 涵涵聊天使用的模型，預設 `gemini-2.5-flash` |
| `GEMINI_MODEL_EMOTION` | ⬜ | 情緒評分使用的模型，預設 `gemini-2.5-flash-lite` |
| `GEMINI_MODEL_REVIEW` | ⬜ | 週回顧敘事使用的模型，預設 `gemini-2.5-flash` |

---

## 🧪 測試

```bash
pytest
```

## ⚙️ 設定分層

| 設定檔 | 用途 |
| --- | --- |
| `settings/base.py` | 共用設定 |
| `settings/dev.py` | 開發（`DEBUG=True`、記憶體快取、Celery 同步、Email 印到 console）— 預設使用 |
| `settings/prod.py` | 生產（強制 HTTPS / HSTS、Redis、真實 SMTP）；部署時設 `DJANGO_SETTINGS_MODULE=hanxin_mental_health_support_site.settings.prod` |

---

## ⚠️ 重要聲明

涵心是一個**情緒支持與陪伴**工具，**並非醫療器材、也不能取代專業的心理諮商或精神醫療**。AI 的回應可能不準確，請勿將其作為診斷或治療依據。

**如果你或身邊的人正處於危機中，請立即尋求專業協助：**

| 台灣求助專線 | 號碼 |
| --- | --- |
| 安心專線（24 小時） | **1925** |
| 生命線 | **1995** |
| 張老師專線 | **1980** |

緊急情況請撥 **119 / 110**。

---

## 📄 授權

本專案目前未指定開放原始碼授權；如需使用請先聯絡作者。

---

<p align="center">用溫柔的方式，把每一個人好好接住。 🌿</p>
