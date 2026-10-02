NEWS_STOCK v4.7.27.1 緊急修正版

修正：
1. 還原 v4.7.27 誤刪的 buildOptions()。
2. 修復「最新新聞檢查失敗：buildOptions is not defined」。
3. 修復新聞資料載入後初始化中斷，造成新聞中心分頁與按鈕無法操作。
4. 保留 v4.7.27 的即時新聞重新檢查、台灣今日篩選與 freshness banner。
5. JS / CSS / Service Worker 版本統一為 4.7.27.1。

覆蓋：news-center.js、news-center.css、service-worker.js
部署後 Ctrl+F5。
