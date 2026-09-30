NEWS_STOCK v4.7.7 主角新聞內容抽樣校正 PATCH

只需覆蓋 Repository 根目錄中的：
- scripts/update_stock_news.py
- scripts/validate_stock_news.py
- scripts/selftest_news_pipeline.py

不包含 stock-news.json，不會覆蓋目前已抓到的新聞。

主要修正：
1. 主角新聞不再只看「標題唯一提及公司」，新增公司主體判定。
2. 台股/大盤/加權指數/權值股/盤中盤後等市場盤勢標題，即使提到個股，也不標成主角新聞。
3. 營收、財報、法說、展望、訂單、股利、重大訊息等具體公司事件仍可判定為主角。
4. GitHub Actions 驗證會直接列出 2330/2317/2454 的真實新聞抽樣：
   - PRIMARY 主角新聞最多 8 則
   - HIGH_ONLY 高度相關但非主角最多 5 則
   - MENTION 順帶提及最多 3 則
   方便直接人工檢視準確度。
5. 新增回歸測試，防止市場盤勢新聞誤標主角。

上傳後：
Actions -> Update Taiwan stock news -> Run workflow
再展開 Validate non-empty stock news，將 PRIMARY / HIGH_ONLY / MENTION 樣本截圖回傳即可繼續精準校正。
