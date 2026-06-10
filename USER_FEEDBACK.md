# 涵心 · 用戶測試回饋與待辦清單

> 來源：實際用戶測試（2026-06-02）+ 程式自我檢核（2026-06-03）  
> 狀態說明：- [ ] 未開始 / - [x] 已完成 / - [~] 進行中 / - [-] 決定略過

---

## 🔴 高優先（立刻影響使用者體驗或安全）

### 安全 / 危機流程
- [x] **危機漂浮條常駐 + 30分鐘後自動消失** ✅ 改為 user-level（跨 session），JS 計時 fade out
- [x] **Markdown 渲染加後端淨化** ✅ 聊天串流加 DOMPurify；Django `|markdown` filter 加 bleach 白名單

### 動畫流暢度
- [x] **growIn 動畫延遲縮短** ✅ 改用 `anim_delay` filter（步長 0.06s），18 顆約 1.1 秒全部長出
- [x] **聊天串流消除閃爍** ✅ `createAIBubble(initialText)` 在附加 DOM 前就設好第一個 chunk 文字

### 心情看板
- [x] **限制每個用戶每天最多發 50 則心情** ✅ 超過上限回傳友善提示卡片
- [x] **讓 Poster 可以撤回自己的心情貼文** ✅ 軟刪除 + 個人心情頁（🙋 我的心情）

### 誇誇成長
- [x] **誇誇筆記加刪除按鈕** ✅ 軟刪除，週回顧和樹點數不納入已刪除
- [x] **誇誇筆記列表加 max-height 限制** ✅ 420px 後捲動
- [x] **誇誇送出加 loading state + 防重複提交** ✅ `hx-disabled-elt` + `hx-indicator`

### 心理資源
- [x] **文章詳頁底部「同分類更多文章」最多 6 篇** ✅ 原本做了 chip 篩選後改回固定顯示同分類 6 篇
- [x] **心理科普 tab 加入分類篩選 chips** ✅ Alpine inline 篩選（壓力管理 / 情緒覺察 / 焦慮 / 睡眠 / 人際關係 / 自我照顧）
- [x] **分類篩選無結果空狀態** ✅ Alpine `hasResults` getter，無結果顯示 🌱 提示 + 「查看全部文章」按鈕

### 診所指南
- [x] ~~修正篩選後右上角數字不更新的問題~~ ✅ 已修

### 外觀設定
- [x] ~~字級 slider 旁的「目前：N%」即時更新~~ ✅ 已修（現在是即時但沒辦法顯示改變後的數字，需要再確認）
- [x] ~~首頁成長視覺跟隨用戶偏好設定~~ ✅ 已修

### 登入 / 登出
- [x] **密碼欄下方加規則說明** ✅ signup.html 密碼欄下方加淡色說明卡片（8字元／非全數字／非常見密碼／不與 email 相近）
- [-] **登出不需要確認頁**（保留現狀，Django allauth 確認頁是 CSRF 保護標準做法）

---

## 🟡 中優先（體驗有瑕疵，需規劃）

### 週回顧
- [x] **Gemini 生成失敗時顯示友善提示** ✅ 三狀態：有內容 / 失敗（data 非空但 narrative 空）/ 從未生成，失敗時顯示 😔 + 重新嘗試按鈕

### 聊天 / Session
- [-] **Session 刪除加 loading 動畫**（HTMX 2.x 空 response + outerHTML swap 有已知問題，嘗試多種方式仍需兩次點擊，暫時擱置）

### 手機版
- [x] **首頁任務+樹的斷點改為 900px** ✅ 2026-06-10：`.home-main-grid` 改用獨立的 `@media (max-width: 900px)`
- [x] **Drawer 開啟時鎖定背景捲動** ✅ 2026-06-10：新增 `openMobDrawer()`/`closeMobDrawer()`，開啟時 `document.body.style.overflow = 'hidden'`
- [x] **看板超小螢幕（<380px）天氣格子改 2 欄** ✅ 2026-06-10：新增 `@media (max-width: 380px) { .mood-grid { grid-template-columns: repeat(2, 1fr) !important; } }`

### 設定頁面
- [x] **改成左側 Menu 架構** ✅ `_settings_nav.html` partial，三頁共用，desktop 左側垂直 nav，mobile 頁頂 chip 列
- [x] **危險區域細分選項** ✅ ①清除聊天記錄（ChatSession 軟刪除）②清除誇誇筆記（KudosNote 軟刪除）③完全刪除帳號，各有 Alpine 確認
- [x] **刪除帳號改用更明確的二次確認** ✅ Alpine input 比對 email，完全符合才能送出，取消時清空輸入

### 登入頁
- [x] **登入 / 註冊頁隱藏側邊欄和 tabbar** ✅ `/accounts/` 路徑下隱藏 sidebar/topbar/tabbar，app--auth class 全寬置中，登出後導向首頁

### 每日任務
- [-] **讓用戶可以自訂任務 / 習慣**（決定不做：自由度過高在心理健康情境有風險，維持管理員控制的固定清單）

### 心理資源
- [-] **文章 model 加入作者和來源連結欄位**（非主要功能，暫不做）
- [-] **加入文章評分功能**（非主要功能，暫不做）
- [x] **加入排序功能** ✅ 最新（預設）/ 最多人看，`?sort=` query param，排序 chip 高亮

### 心情資源 tab 切換
- [x] **tab 切換改用輕量 transition** ✅ 加 `.enter-tab`（fadeIn 0.15s），resources.html 全部 tab panel 換用

---

## 🔵 架構層決策（需確認方向後才動）

### A. BYOK 金鑰設計
- [x] **改為平台統一 Gemini API Key** ✅ 2026-06-10：移除 `AISetting` model（含金鑰、`model_name`、`key_verified_at`）與其資料表、`/settings/ai/` 頁面、`GeminiKeyForm`、`accounts/gemini.py`、`requires_gemini_key` 裝飾器。改用 `settings.GEMINI_API_KEY`（單一平台金鑰），三個 AI 功能各自獨立指定模型：`GEMINI_MODEL_CHAT`（聊天）、`GEMINI_MODEL_EMOTION`（情緒評分）、`GEMINI_MODEL_REVIEW`（週回顧）。情緒評分同時由 NVIDIA NIM / Groq 三段降級鏈改為單一 Gemini JSON 模式呼叫，失敗時仍降級到關鍵字偵測。
- [-] ~~改善 AI 金鑰頁面的說明文案~~（頁面已隨 BYOK 移除一併刪除，不再適用）

### D. 欄位加密恢復（正式版前處理）
- [ ] **`accounts/crypto.py` 加密機制目前已無任何欄位在用**：移除 `ChatSession.summary`（最後一個 `encrypt()` 欄位，且本來就是死欄位）後，`FIELD_ENCRYPTION_KEY` / `DJANGO_CRYPTOGRAPHY_KEY` / `requirements.txt` 的 `django-cryptography-django5` / `growth/models.py` 裡的 `from accounts.crypto import encrypt`（本來就是死 import）目前都沒有任何實際作用。`KudosNote.praise_content`、`AIChatLog.message_content` 的 docstring 仍寫「加密」，但實際欄位早已是純 `TextField`（`growth/migrations/0002_kudosnote_remove_encryption.py`、`companion/migrations/0003_aichatlog_remove_encryption.py` 已拿掉加密）。
  - 正式版要重新替這些敏感欄位（誇誇筆記、聊天訊息等）加上 `encrypt()` 並補 migration；屆時再視情況決定是否保留/重啟整套 `accounts/crypto.py` + `FIELD_ENCRYPTION_KEY` 機制，或換新方案。

### B. 訪客模式 vs 完全會員制
- [x] **實作訪客模式** ✅
  - 首頁：訪客可瀏覽，任務可勾選（session 存瀏覽器 signed cookie，不碰 DB，今日重置）
  - 心情看板：訪客唯讀，發文 / 回應按鈕隱藏，登入才能互動
  - 涵涵 / 誇誇成長：維持需要登入（帳號功能）
  - 側邊欄 + tabbar：訪客顯示「🔑 登入 / 註冊」入口
  - 登入 / 註冊頁：加「← 返回」按鈕

### C. 心情看板設計問題
- [x] **看板暖意通知浮動條** ✅ 從外部進入且有暖意時顯示「❤️ 你發布的心情共收到 N 份暖意」，20 秒後淡出，可手動關
- [x] **看板改為每日刷新** ✅ 只顯示今天的貼文，避免無限累積 + 重複互動單調的問題（「我的心情」保留歷史）

---

## 🔧 技術債（效能 / 程式品質）

- [-] **週回顧 DB 查詢優化**（誤判：10 個查詢分打不同 table，select_related 已正確使用，瓶頸是 Gemini API 呼叫而非 DB）
- [-] **`task_toggle` 加 `transaction.atomic()`**（極小機率，遇到再改）
- [x] **暖心語快取 5 分鐘** ✅ 首頁 `home_warm_words` cache key，300 秒，隨機選詞仍每次獨立
- [x] **週回顧提醒改為 in-app 提示** ✅ 周日晚上 8 點後、本週無 narrative，首頁顯示「✨ 這週過得怎麼樣？」提示卡，點擊導向誇誇成長頁

---

## 🔴 深度檢查發現的 Bug（2026-06-03 逐 app 檢查）

### 心情看板（board）
- [-] **`board_post` 每日限制含被刪除的貼文**（設計正確：軟刪除不重置當日次數，防止發完再刪循環塞爆資料庫）
- [-] **`board_react` 可對已刪除貼文回應**（實務上不影響：feed 和週回顧都已過濾 `is_deleted=False`，react 按鈕根本不顯示，需刻意 API 呼叫才能觸發且 reaction 不會顯示給任何人）

## 🟡 深度檢查發現的小問題

- [x] **`growth/views.py` 的 `TREE_MAX_FRUITS = 18` 從未被使用** ✅ 2026-06-10：已刪除
- [x] **`board_mine` 有未使用變數 `self_user`** ✅ 已隨看板改版重寫，`self_user` 已不存在
- [x] **`HomeView` 的 `tasks.count()` 重複查 DB** ✅ 2026-06-10：改用 `len(ctx["tasks"])`
- [x] **`ArticleDetailView` 傳了 `all_categories` 但模板已不使用** ✅ 2026-06-10：已移除 dead context variable
- [x] **`board/_load_warm_words()` 每次 board_post / board_react 都打一次 DB 沒有快取** ✅ 已隨看板改版整個移除（暖心語回應模式不存在了）
- [x] **`review_generate` view 沒有 try/except** ✅ 確認已由 `generate_narrative()` 內的 try/except 處理（Gemini 失敗回傳空字串，模板顯示「😔 這次生成沒有成功」+ 重新嘗試按鈕），view 層不需額外處理
- [x] **文章瀏覽數每次重整都 +1** ✅ 2026-06-10：`ArticleDetailView.get()` 改用 session 記錄已計數的文章 id，同一瀏覽器重整不再重複累加

---

## 🟡 用戶測試回饋新增功能（2026-06-04）

### 每日心情 check-in + 日曆
- [x] **每日心情 check-in** ✅ `DailyMood` model（每人每天一筆，可當天更新），`grow.html` 今日心情打卡區，`mood_checkin` endpoint
- [x] **心情日曆** ✅ `grow.html` 本月心情月曆，`mood_calendar_weeks` context，與打卡共用 Alpine scope 即時更新

### 情境題互動（首頁卡片）
- [x] **情境題功能完整實作** ✅
  - `SituationQuestion` + `SituationResponse` model（core app，不加密）
  - 簡答 / 選擇題雙模式，切換按鈕，可反悔回簡答
  - 匿名用戶可作答（無 user FK），回答統計入 DB
  - 登入用戶 F5 不換題（session 追蹤），匿名 F5 可換
  - 每次送出建新紀錄（允許重複答，第二輪有意義）
  - 防連點：`hx-disabled-elt` 鎖送出按鈕
  - 空白文字不可送出（`hasText` Alpine 追蹤）
  - `is_public` checkbox 修正（unchecked 真的不公開）
  - 抽題排除當前題（不連抽同一題）
  - 結果畫面：選項百分比 + 他人簡答前 20 字
  - 週回顧整合：Gemini 可看到用戶的情境題作答，前端顯示統計卡

### 診所指南
- [x] **診所加行政區篩選** ✅ 選縣市後自動顯示該縣市的行政區 chips，只列有診所的區，不會有空結果

### 成長視覺
- [-] **果實改為歷史累積制**（目前每週重置，測試者覺得「可惜」；暫定維持現狀，之後再評估）

---

## ⚪ 先跳過（MVP 階段，留到正式版）

- 首頁模塊可拖拽自訂順序 / 開關
- 看板可加入自訂心情（非僅六種預設）
- 診所串接 Google Maps API、顯示距離
- 診所和文章的留言 / 評論功能
- 根據用戶定位自動顯示附近診所
- 管理員危機監控儀表板（SOSLog 有資料但 Admin 只有基本設定）
- 聊天 SSE 串流二次改善（逐字 Markdown 漸進渲染）

---

## ✅ 已完成項目

- [x] 心情看板去文字化（只有貼圖，防負評）
- [x] 貼圖回應改為單選（防重複灌數）
- [x] 診所縣市篩選 HTMX 局部更新
- [x] 字級和主題色可調整（即時預覽）
- [x] 誇誇成長視覺三種模式（心情樹/花園/感謝罐）
- [x] 首頁成長視覺與成長頁同步（含週計算）
- [x] 手機版帳號選單（個人設定 + 登出）
- [x] 看板心情數在篩選後同步更新
- [x] Session 軟刪除（對用戶隱藏，後端保留）
- [x] 危機偵測改為 Groq LLM 語意評分（含關鍵字備援）
- [x] 週回顧功能（含版本歷史）
- [x] 串流聊天（SSE）
- [x] Markdown 渲染（文章詳頁 + AI 週回顧）
- [x] 診所篩選筆數即時更新

---

*最後更新：2026-06-04（情境題功能、診所行政區篩選、聊天 session 修復、dead code 清理）*
