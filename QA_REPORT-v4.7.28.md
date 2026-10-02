# NEWS_STOCK v4.7.28 全介面巡檢與穩定化報告

日期：2026-10-02
版本：v4.7.28

## 這次巡檢範圍

新聞情報中心 9 個主要頁面：

1. 每日市場情報
2. 研究儀表板
3. 我的追蹤
4. 持股情報首頁
5. 新聞列表
6. 個股情報總覽
7. 事件案例庫
8. 跨股比較
9. 全台股事件雷達

另外檢查：

- 新聞中心開啟 / 關閉
- 重新讀取新聞 / 清除篩選
- 股票搜尋、自動完成與新聞收藏
- 日期、來源、事件、排序、自訂日期
- 重大新聞、事件合併、新聞閱讀模式
- 24 小時 / 3 天 / 7 天 / 30 天 / 90 天期間切換
- 追蹤、已讀、研究待辦、研究回顧
- 事件案例庫所有篩選及重設
- 跨股比較所有篩選及重設
- 全台股事件雷達所有篩選及個股跳轉
- 持股情報卡排序與「查看新聞情報」
- Service Worker、PWA 即時資料快取
- 新聞、收盤價資料 JSON
- GitHub Actions workflow 語法
- 新聞抓取與分類 Python self-test

## 本次實際修正

### 1. 移除對 DOM ID 隱式全域變數的依賴

舊版部分程式直接使用 `newsClose`、`newsList`、`newsOverviewWindow` 等 ID 作為瀏覽器全域變數。不同瀏覽器、重新 render 或未來瀏覽器政策變動時可能突然失效。

v4.7.28 改為明確 `getElementById()` 綁定，並檢查必要元件是否缺失。

### 2. 所有主要分頁 Active 狀態重新巡檢

修正「事件案例庫」切換時可能殘留「全台股事件雷達」仍為 active 的狀況。9 個頁面現在都會正確清掉其他分頁狀態。

### 3. 個股期間切換集中成同一個事件處理器

保留 v4.7.27.3 修正：

- 每日市場情報只處理 24 小時 / 3 天
- 個股總覽、持股情報處理 24 小時 / 3 天 / 7 天 / 30 天 / 90 天
- 不再由不同 render 函式互相覆寫 `onclick`

### 4. 個股總覽期間資料比對更嚴格

期間分析改用 `matchedStocks` 做個股比對，不再以標題 / 摘要單純文字包含判定，降低同名、相似公司名稱造成的誤配。

同時缺少合法 `publishedAt` 的新聞不再混入指定期間分析。

### 5. 舊版 localStorage 設定自動校正

若舊版留下不存在的：

- 分頁名稱
- 閱讀模式
- 日期期間
- 案例期間
- 雷達排序

現在啟動時會自動回到合法預設值，避免升級後畫面停在不存在的狀態而無法操作。

### 6. 研究 / 個股選單來源整理

研究相關頁面現在可使用：

- 主系統「我的最愛」
- 新聞收藏股票
- 目前實際持股

但不會重新把歷史交易、股利紀錄、公司行動全部塞回新聞收藏快捷列。

### 7. 事件案例庫重設副作用修正

重設「事件案例庫」篩選時不再誤動跨股比較相關狀態。

### 8. 我的追蹤搜尋改為即時輸入

搜尋框從 `change` 改為 `input`，輸入文字時立即篩選，不需要先離開欄位或按 Enter。

### 9. 無可選股票時提供明確說明

事件案例庫沒有任何可用持股 / 收藏股票時，不再留白，會顯示提示文字。

### 10. 動態按鈕補 `type="button"`

重要的動態按鈕補上明確 button type，避免未來放進 `<form>` 後意外觸發 submit。

### 11. 持股情報中心新聞快取過期修正

原本 `portfolio-intelligence.js` 首次抓到新聞後，頁面長時間開著可能一直使用同一份記憶體資料。

v4.7.28 改為：

- 15 分鐘後允許重新抓取
- 回到頁面 / 視窗重新 focus 時若資料過期會刷新
- 網路恢復時重新抓取
- 手動 refresh 會清除記憶體快取

### 12. 增加前端自動回歸檢查

新增：

- `scripts/selftest_frontend_static.py`
- `.github/workflows/frontend-selftest.yml`

之後只要 GitHub 上的新聞 / 持股前端程式有修改，GitHub Actions 會自動檢查：

- 關鍵函式是否被誤刪
- 9 個頁面 tab 狀態
- 5 個期間按鈕
- 期間事件委派
- DOM 明確綁定
- 新聞收藏 / 持股研究來源
- 持股張數轉股數與負號解析
- Service Worker 版本
- JSON 可解析性
- JavaScript 語法

這是為了避免再次發生 v4.7.27 那種 `buildOptions is not defined` / `updateReadModes is not defined` 的回歸。

## 自動檢查結果

- `news-center.js`：Node syntax OK
- `portfolio-intelligence.js`：Node syntax OK
- `service-worker.js`：Node syntax OK
- `index.html` inline JavaScript：OK
- `404.html` inline JavaScript：OK
- 前端靜態回歸自測：OK
- Python scripts compile：OK
- `selftest_news_pipeline.py`：OK
- v4.7.8 relevance tier tests：OK
- v4.7.9 company-event / price-action tests：OK
- v4.7.10 market-theme tests：OK
- `frontend-selftest.yml`：YAML OK
- `update-stock-news.yml`：YAML OK
- `update-market-close.yml`：YAML OK
- JSON files parse：OK
- CSS brace balance：OK

## 不變更的資料

此修補包不包含以下即時資料檔，因此覆蓋時不會把 GitHub 上最新資料清掉：

- `stock-news.json`
- `market-close.json`
- `market-history.json`

也不會修改使用者瀏覽器 localStorage 裡的交易與持股紀錄。

## 部署後建議確認

部署後 Ctrl + F5，一次確認：

- 新聞中心顯示 v4.7.28
- 9 個新聞分頁都能切換
- 個股總覽 24h / 3d / 7d / 30d / 90d 都能切換
- 新聞列表正常顯示
- 搜尋與收藏可操作
- 持股情報「查看新聞情報」可開到正確股票
- GitHub Actions 新增 `Frontend self-test` 並成功顯示綠色

