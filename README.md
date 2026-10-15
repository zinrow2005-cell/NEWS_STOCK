# 安心股票簿｜NEWS_STOCK v4.7.27 Stable

這是一份可直接部署到 **GitHub Pages** 的完整正式版，不需要 Node.js、不需要 npm，也不需要付費 API。

## 目前整合功能

- 交易紀錄、持股、股利、公司行動與損益統計
- TWSE／TPEx 官方收盤價自動更新
- 持股最新收盤價與交易日期加大醒目顯示、持有成本、目前市值、未實現損益、報酬率
- **V4.7.27** 持股／總覽新增含息回本價；反映既有交易及領息、配股、券商轉撥
- 總覽每檔個股額外顯示最近一個已同步交易日的收盤價、收盤日期與含息回本價
- 持股情報中心與新聞收藏股票
- 台股公開新聞自動抓取與 GitHub Actions 更新
- 個股新聞相關性、公司事件／股價行情／市場題材分類
- 核心事件、重大事件、同事件多來源合併
- 個股新聞總覽、每日市場情報、事件研究與跨股比較
- PWA，可加入手機／iPad 主畫面
- Google Sheet + Apps Script 研究資料同步（選用）

## 版本

- 正式整合版：**v4.7.27**
- 新聞中心原始功能：**v4.7.26**（持股介面及 Service Worker 更新為 v4.7.27）
- 部署方式：GitHub Pages `main / (root)`

## 重要資料說明

你的交易、持股、股利、公司行動等個人資料主要儲存在瀏覽器本機（localStorage），**不會因為把這個 ZIP 上傳 GitHub 就自動包含你的個人紀錄**。

如果要換 Repository、換 GitHub Pages 網址、換裝置或清除瀏覽器資料，請先在目前系統內匯出完整 JSON 備份，再到新網址匯入。

## 第一次部署後要做的事

1. 啟用 GitHub Pages。
2. 到 Actions 手動執行 **Update Taiwan stock news**。
3. 再手動執行 **Update Taiwan market close**。
4. 確認兩個 workflow 都出現綠色成功標記。
5. 打開 GitHub Pages 網址，主系統標題含 `v4.7.27`；新聞中心沿用原有功能。

完整步驟請看：

**`GITHUB_重新部署操作說明.md`**

## 主要檔案

```text
index.html                         主程式
404.html                           GitHub Pages 路由備援
offline.html                       PWA 離線頁面
news-center.js / news-center.css   新聞情報中心
portfolio-intelligence.js / .css   持股情報中心
service-worker.js                  PWA / 快取控制
manifest.webmanifest               PWA manifest
stock-directory.json               股票代號資料
stock-news.json                    新聞資料（Actions 產生）
market-close.json                  最新收盤價（Actions 產生）
market-history.json                歷史行情（Actions 累積）
scripts/                           GitHub Actions Python 程式
.github/workflows/                 自動更新工作流程
google-apps-script/                選用的跨裝置同步
assets/                            主系統建置資源
```

## 不要刪除

請保留 `.github`、`.nojekyll`、`scripts`、`assets`。尤其 `.github/workflows` 被刪除後，新聞與收盤價就不會自動更新。

## v4.7.27 含息回本價說明

**含息回本價／股 = MAX(0, (剩餘持有成本 − 分攤給現有持股的已收現金股利 − 現金返還) ÷ 現在持有股數)**。

- 原平均成本保留不變，**不會改寫任何交易、股利或舊持股資料**。
- 無償配股按照原有除權/發放公司行動紀錄變動股數；配股沒有重複加到買進成本。
- 現金股利以系統登錄的發放日為收到日期，未到發放日不先折抵；已核對金額優先使用實際核對結果。未核對的自動紀錄仍以登錄的預計金額估算，請對照實際入帳明細。
- 發生部分賣出時，已收現金收益按剩餘股數比例保留。已到除息日但未到發放日的股利歸屬，以除息當時資格股數追蹤，不會把除息後買進的新股錯當成原持股股利；券商轉撥會保留歸屬。
- 歷史「實際股利」不再加回配股股數，避免期初庫存重複入帳。
- 若在建立期初持股之前的股利沒有紀錄或期初成本已包含折抵，系統無法自行判斷歷史回本，請避免重複扣減。
- 顯示數字為**未計未來賣出手續費及證交稅的現金調整後參考回本價**，不是保證成交的實際損益；精確損益請以券商成交及現金入帳單為準。

**自我測試：** `node tests/test_breakeven.cjs`（需電腦上已有 Node.js；正常使用系統不需要安裝 Node）。
