v4.7.10 市場題材收斂校正 PATCH

請覆蓋：
- scripts/update_stock_news.py
- scripts/selftest_news_pipeline.py
- scripts/validate_stock_news.py

本 PATCH 不含 stock-news.json，不會把線上 3000 則新聞洗掉。
覆蓋後執行 GitHub Actions > Update Taiwan stock news > Run workflow。
