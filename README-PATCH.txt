NEWS_STOCK v4.7.5 主角新聞模式修補包

請把本 ZIP 內容覆蓋到 GitHub Repository 根目錄。
本 PATCH 不含 stock-news.json，不會把目前已抓到的新聞洗成空檔。

覆蓋後：
1. GitHub → Actions → Update Taiwan stock news → Run workflow。
2. 展開 Validate non-empty stock news。
3. 應看到：relevance 2330: primary=...、2317、2454。
4. 等 Pages 部署後 Ctrl+F5。
5. 新聞情報中心指定個股後，可勾選「只看主角新聞」。

主角新聞採嚴格規則：標題直接且唯一聚焦該公司。若是多股整理／族群新聞，即使標題提到該股票，也不列為主角新聞。
