NEWS_STOCK v4.7.18 持股最新收盤價自動同步修正版

覆蓋檔案：
- index.html
- 404.html
- service-worker.js

news-center.js / news-center.css 也放在包內，內容沿用 v4.7.17.2；若你已是 v4.7.17.2，可不必重新覆蓋這兩個檔案。

修正內容：
1. 開啟系統後一定嘗試同步最新 market-close.json（線上時）。
2. 頁面從背景切回前景時會再檢查；每 15 分鐘最多自動檢查一次。
3. 網路重新連線時自動補同步。
4. 官方收盤價同步成功後立即更新 React 狀態與 localStorage，不需重開頁面。
5. 持股頁新增「最新收盤日期 / 同步覆蓋數 / 來源」狀態列與立即同步按鈕。
6. 不改買入成本，只更新 marketPrices（現價與日期）。
7. market-close.json / market-history.json 繼續使用 network-first + no-store，避免 PWA 舊快取。
