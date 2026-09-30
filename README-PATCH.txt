v4.7.4 個股新聞精準度再校正 PATCH

請將本壓縮檔內容覆蓋到 GitHub Repository 根目錄。
不包含 stock-news.json，因此不會把目前已抓到的 2657+ 則新聞覆蓋成空檔。

覆蓋完成後：
1. GitHub > Actions > Update Taiwan stock news > Run workflow
2. 展開 Validate non-empty stock news
3. 確認會多看到：
   relevance 2330: high=..., related=..., mention=...
   relevance 2317: high=..., related=..., mention=...
   relevance 2454: high=..., related=..., mention=...
4. 等 GitHub Pages 重新部署後 Ctrl+F5。

預設個股搜尋只顯示 high + related；要看產業型順帶新聞再勾「顯示順帶提及」。
