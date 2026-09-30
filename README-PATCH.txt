NEWS_STOCK v4.7.8 PATCH

目的：把「新聞是否以公司為主角」與「事件是否屬投資研究核心」拆成兩層。

請覆蓋到 GitHub Repository 根目錄：
- scripts/update_stock_news.py
- scripts/validate_stock_news.py
- scripts/selftest_news_pipeline.py
- news-center.js
- news-center.css
- service-worker.js

stock-directory.json 若你原本已有，不需要覆蓋；本 PATCH 不包含 stock-news.json，不會清空目前已抓到的新聞。

上傳後：
1. GitHub > Actions > Update Taiwan stock news > Run workflow
2. 查看 Validate non-empty stock news
3. 應看到：
   relevance 2330: core=..., general=..., primary=..., high=..., related=..., mention=...
4. 必須滿足 core <= primary <= high；若不滿足，Action 會失敗、不提交錯誤資料。
5. 網站 Ctrl+F5；手機/iPad PWA 完全關閉後重開，以更新 news-v47.8 Service Worker。

前端：
- 只看主角新聞：核心主角 + 一般主角
- 只看核心主角：只保留營收/財報/法說/訂單/展望/獲利等核心公司事件
