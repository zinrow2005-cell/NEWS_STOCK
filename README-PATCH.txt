NEWS_STOCK v4.7.6 Relevance Hierarchy Fix

Purpose
- Fix impossible diagnostics such as primary > high.
- Recompute matchedStocks/relevance/isPrimary for ALL retained articles, including 120-day cached history, on every update.
- Add hard validation: every isPrimary relation must have relevanceLevel=high; smoke-stock primary count cannot exceed high count.

Upload these files over the same paths in your repository:
- scripts/update_stock_news.py
- scripts/validate_stock_news.py
- scripts/selftest_news_pipeline.py

Then run:
Actions -> Update Taiwan stock news -> Run workflow

Expected invariant in logs:
primary <= high for 2330 / 2317 / 2454.
If violated, the workflow now fails instead of committing inconsistent data.

This PATCH intentionally does NOT include stock-news.json.
