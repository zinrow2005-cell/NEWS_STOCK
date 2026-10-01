NEWS_STOCK v4.7.20 — 新聞收藏股票快捷列

主要變更
1. 新聞上方股票快捷列不再由「交易紀錄 / 股利 / 公司行動」自動混入。
2. 改成獨立的「⭐ 新聞收藏」清單。
3. 搜尋並選定任一股票後，可按「☆ 收藏代號」加入快捷列。
4. 已收藏股票顯示「★ 已收藏・點擊取消」，可一鍵移除。
5. 第一次升級時，若主系統原本有「我的最愛」，會一次性匯入新聞收藏；歷史交易不會自動加入。
6. 收藏存在 localStorage：安心股票簿-news-favorites-v1。
7. 收藏快捷列支援橫向滾動，不會把工具列撐成多行。
8. 不改 GitHub Actions、stock-news.json 或市場收盤資料。

建議覆蓋
- news-center.js
- news-center.css
- service-worker.js

部署後 Ctrl+F5。
