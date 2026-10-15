# 安心股票簿 NEWS_STOCK — V4.7.29 完整 GitHub 部署版

> 本 ZIP 是可直接上傳 **GitHub Pages** 的完整網站檔案，不是增量更新，不需 npm、不需 Node.js 或付費 API 才能使用。  
> 版本基礎：V4.7.28（排版與含息回本價已修復）＋ V4.7.29（程式與文件整理）。

## 功能

- 交易紀錄、持股／總覽、平均成本與含息回本價、股利、配股、公司行動、損益分析。
- 台灣證交所／櫃買中心收盤行情（由 GitHub Actions 同步），附最後交易日期。
- 新聞情報中心：股票消息、自動更新、重大事件、分類與收藏。
- 持股情報中心：連結持股與市場新聞。
- PWA 手機／iPad 主畫面、離線提示及快取更新。
- 選用的 Google Apps Script / Sheet 整合。

## GitHub 部署（重要）

1. **先備份資料：** 在舊網站「設定 → 資料備份／匯出」匯出完整 JSON。舊資料主要在**原瀏覽器 localStorage**，不在 ZIP 內。
2. 解壓縮 ZIP，將**資料夾內的所有檔案與隱藏資料夾**放在 GitHub Repository 的**根目錄**（不要多包一層資料夾）。
3. 保留 `.github/workflows/`、`scripts/`、`assets/`，並確認 `index.html`、`404.html` 與各資源上傳完整。
4. 進入 GitHub → Settings → Pages：選 Deploy from a branch → `main` / `/(root)`。
5. 進入 Actions 手動跑 `Update Taiwan stock news` 與 `Update Taiwan market close`，初次更新初始化資料。
6. 用原網址重新整理，若仍見舊版，關閉所有舊分頁後重新開啟／重新整理（PWA 快取可能延遲更新）。

完整操作與疑難排解：[`GITHUB_重新部署操作說明.md`](GITHUB_重新部署操作說明.md)。

**重要：** GitHub 網頁「Upload files」不會自動刪除遠端原本存在但新版 ZIP 已清除的檔案（舊 `CHANGELOG-v*.txt` 與 `assets/index-*`）。它們不影響新版執行；若需要 Repository 完全乾淨，可另外刪除這些舊檔。不要刪除個人已儲存的資料備份。

## 程式／檔案結構

```text
index.html                         主入口（共用 JS/CSS，不再內嵌幾 MB 程式）
404.html                           GitHub Pages 入口備援（與主入口一致）
assets/app.js                      持股主應用程式（已建置 bundle）
assets/app-core.css                主程式基礎樣式
assets/app-overrides.css           持股卡片響應式修正、歷史顯示修正
news-center.js / news-center.css   新聞系統
portfolio-intelligence.js / .css   持股情報中心
service-worker.js                  PWA 更新／快取管理
manifest.webmanifest               安裝至主畫面設定
stock-directory.json               股票代碼資料
stock-news.json                    Actions 更新的新聞資料
market-close.json                  Actions 更新的官方收盤價
market-history.json                Actions 累積的市場歷史
scripts/                           行情及新聞更新腳本／部署檢查工具
.github/workflows/                 GitHub Actions 定期更新排程
tests/test_breakeven.cjs           股利與回本價計算測試
google-apps-script/                選用外部同步
CHANGELOG.md                       本次更新紀錄
docs/changelog/                    完整歷史版本紀錄
docs/程式結構與維護說明.md             維護方式與注意事項
SHA256SUMS.txt                     ZIP 內檔案完整性雜湊清單
```

**維護提醒：** `assets/app.js` 是上一版已建置、壓縮的 React bundle，並非完整可重新編譯的 JSX/TSX 專案。這次把原版共用程式抽離，不冒險重寫運算邏輯。保留原有計算與資料相容性；想進一步恢復元件原始碼，應取得原 React 專案的 source。原有 `assets/index-*.js/css` 是未被引用的舊建置產物，已清除。

## 含息回本價規則

公式：`max(0, (剩餘持股成本 - 已歸屬現存股數的現金股利 - 資本返還) / 現存股數)`。
無償配股會影響持股數量；部分賣出時已收股利依剩餘持股比例保留；未入帳及缺失歷史股利不會憑空列入；已登錄但未核對的股利可能是估算，請依實際入帳資料確認。

## 測試

開發驗證用（一般正常使用免執行）：

```bash
node tests/test_breakeven.cjs
python scripts/check_release.py
```

其他細節見 `CHANGELOG.md`。
