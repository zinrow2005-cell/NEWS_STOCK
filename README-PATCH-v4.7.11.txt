NEWS_STOCK v4.7.11 個股新聞閱讀模式 PATCH

請覆蓋 GitHub Repository 根目錄：
- news-center.js
- news-center.css
- service-worker.js

本 PATCH 不包含 stock-news.json，不會覆蓋目前已成功抓取的新聞資料。
後端 scripts 維持 v4.7.10 即可，不需要重新調整新聞分類規則。

上傳後：
1. 等 GitHub Pages 重新部署。
2. 瀏覽器 Ctrl+F5；PWA 請完全關閉再開啟。
3. 進「新聞情報中心 → 新聞列表」。
4. 搜尋或選擇 2330 / 2317 / 2454。
5. 會看到「個股新聞閱讀模式」及各類別篇數。

預設：重點閱讀。
