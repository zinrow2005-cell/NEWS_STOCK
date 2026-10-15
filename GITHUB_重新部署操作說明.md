# 安心股票簿 v4.7.27｜重新部署到 GitHub 完整操作步驟

本說明適用於「Repository 被刪除後重新建立」、「換新的 Repository」或「想用完整正式版重新覆蓋」的情況。

---

## 一、重新部署前：先保護自己的股票資料

### 如果舊系統還能開啟

先在舊系統執行：

**設定 → 資料備份／匯出 → 下載完整 JSON 備份**

建議把備份檔另外存到電腦、Google Drive 或 iCloud。

### 為什麼一定要備份？

交易、持股、股利、公司行動等資料主要存在瀏覽器 localStorage。

- 同一個 GitHub Pages 網址：通常仍可讀到原本瀏覽器資料。
- Repository 名稱改變、GitHub 帳號改變或網址改變：瀏覽器會視為新的網站，原資料不會自動跟過去。
- 清除 Safari / Chrome 網站資料或重裝瀏覽器：localStorage 也可能消失。

---

## 二、建立新的 GitHub Repository

1. 登入 GitHub。
2. 右上角按 **+ → New repository**。
3. Repository name 可使用：`NEWS_STOCK`。
4. 建議選 **Public**，GitHub Pages 與 Actions 使用最直接。
5. 不需要勾選新增 README、.gitignore 或 License，因為完整包裡已經有需要的檔案。
6. 按 **Create repository**。

---

## 三、上傳完整檔案

### 最重要的規則

解壓縮 `NEWS_STOCK-v4.7.27-COMPLETE-GITHUB.zip` 後，**上傳「資料夾裡面的全部內容」**，不要把最外層資料夾本身再包一層。

GitHub Repository 最外層必須直接看到：

```text
index.html
404.html
news-center.js
news-center.css
portfolio-intelligence.js
portfolio-intelligence.css
service-worker.js
manifest.webmanifest
stock-news.json
market-close.json
market-history.json
assets/
scripts/
.github/
```

### 網頁上傳方法

1. 進入剛建立的 Repository。
2. 按 **Add file → Upload files**。
3. 將完整版資料夾內的檔案／資料夾拖入。
4. 確認 `.github` 也有上傳。
5. Commit message 可填：`Initial deploy NEWS_STOCK v4.7.27`。
6. 按 **Commit changes**。

> 注意：若你的瀏覽器拖曳上傳沒有保留 `.github` 隱藏資料夾，請另外建立 `.github/workflows/`，再把兩個 yml 工作流程放進去。

---

## 四、確認 GitHub Actions 工作流程存在

Repository 中必須有：

```text
.github/workflows/update-stock-news.yml
.github/workflows/update-market-close.yml
```

然後點 GitHub 上方 **Actions**，應該可以看到：

- **Update Taiwan stock news**
- **Update Taiwan market close**

如果 GitHub 第一次詢問是否啟用 Actions，請按允許。

---

## 五、啟用 GitHub Pages

1. Repository → **Settings**。
2. 左側 → **Pages**。
3. Build and deployment → Source 選 **Deploy from a branch**。
4. Branch 選：`main`。
5. Folder 選：`/(root)`。
6. 按 **Save**。
7. 等待約 1～數分鐘。
8. GitHub 會顯示 Pages 網址，例如：

```text
https://你的GitHub帳號.github.io/NEWS_STOCK/
```

打開後應直接進入「安心股票簿」。

---

## 六、第一次一定要手動更新新聞

完整包內的 `stock-news.json` 是安全初始化檔。重新建立 Repository 後，要讓 GitHub 自己產生最新新聞。

1. GitHub → **Actions**。
2. 點 **Update Taiwan stock news**。
3. 點 **Run workflow → Run workflow**。
4. 等待完成。

成功時應看到類似：

```text
Self-test parser and stock matching     ✓
Fetch public finance RSS feeds          ✓
Validate non-empty stock news           ✓
Commit news data when changed           ✓
```

驗證區通常會看到：

```text
news count=...
matched_articles=...
matched_symbols=...
sources=.../...
```

只要整個 workflow 是綠色即可。

---

## 七、第一次一定要手動更新收盤價

1. Actions → **Update Taiwan market close**。
2. **Run workflow → Run workflow**。
3. 等待完成。

成功時應看到：

```text
Fetch official TWSE and TPEx close prices ✓
Commit market data when changed            ✓
```

正常輸出類似：

```text
wrote 7000+ quotes; history=... days
```

Commit 區應看到：

```text
chore: update Taiwan market close
main -> main
```

之後持股頁就會讀取最新一個已完成交易日的官方收盤價。

---

## 八、如果 Action 抓到了資料但 push 失敗

到：

**Settings → Actions → General → Workflow permissions**

確認允許 workflow 寫入 Repository。若有選項，使用：

**Read and write permissions**

再重新執行 workflow。

工作流程本身已設定：

```yaml
permissions:
  contents: write
```

---

## 九、部署後的驗收清單

### 首頁／持股

- [ ] APP 可以正常開啟。
- [ ] 持股資料可正常顯示。
- [ ] 最新收盤日期正確。
- [ ] 最新收盤價正確。
- [ ] 持有成本正確。
- [ ] 目前市值 = 收盤價 × 實際股數。
- [ ] 未實現損益正負號正確。
- [ ] 報酬率正確。

### 新聞中心

- [ ] 新聞中心右上／標題附近顯示 **v4.7.27**。
- [ ] 每日市場情報有資料。
- [ ] 搜尋 2330／2317／2454 有新聞。
- [ ] 新聞收藏可以新增／取消。
- [ ] 新聞閱讀模式可切換。
- [ ] 公司事件、股價行情、市場題材可正常顯示。
- [ ] 字體在桌機與 iPad 都容易閱讀。

### GitHub Actions

- [ ] Update Taiwan stock news 成功。
- [ ] Update Taiwan market close 成功。
- [ ] `stock-news.json` 有最新 generatedAt。
- [ ] `market-close.json` 不再是空 quotes。

---

## 十、恢復自己的交易資料

如果是新網址或新裝置：

1. 打開新 GitHub Pages 網址。
2. 進入 **設定 → 資料備份／匯入**。
3. 選擇之前下載的完整 JSON 備份。
4. 匯入後重新檢查：
   - 交易紀錄
   - 持股
   - 股利
   - 公司行動
   - 券商設定
   - 收藏／研究資料

不要用 GitHub 上的 `stock-news.json` 當成個人資料備份，它只是新聞資料。

---

## 十一、PWA / 快取看到舊畫面時

先做：

### Windows / Chrome

`Ctrl + F5`

### iPhone / iPad PWA

1. 完全關閉 APP。
2. 用 Safari 打開 GitHub Pages 網址一次。
3. 重新整理。
4. 再開主畫面上的 PWA。

v4.7.27 已有版本一致性與 network-first 保護；正常情況下不需要頻繁清除所有網站資料。

---

## 十二、之後更新版本的安全方法

未來如果只拿到 PATCH：

1. **不要刪除** `stock-news.json`、`market-close.json`、`market-history.json`，除非新版明確要求。
2. 將 PATCH 中同名程式檔覆蓋到 Repository。
3. Commit。
4. 等 Pages 更新。
5. Ctrl + F5。
6. 確認新聞中心版本號已更新。

如果拿到新的 **COMPLETE 完整版**，可以整包覆蓋，但建議先下載 Repository 備份，並保留最新三個資料 JSON。

---

## 十三、自動排程

### 新聞

`.github/workflows/update-stock-news.yml`

平日會依排程輪巡更新，週末也有較低頻率更新。也可隨時手動 Run workflow。

### 收盤價

`.github/workflows/update-market-close.yml`

平日收盤後排程執行兩次，以降低第一次官方資料尚未完整時的風險。

---

## 十四、不要刪除的檔案／資料夾

```text
.github/
scripts/
assets/
.nojekyll
index.html
404.html
service-worker.js
manifest.webmanifest
news-center.js
news-center.css
portfolio-intelligence.js
portfolio-intelligence.css
stock-directory.json
stock-news.json
market-close.json
market-history.json
```

---

## 十五、Google Sheet / Apps Script 同步（選用）

如果未來要重新設定研究資料跨裝置同步，請參考：

`google-apps-script/SETUP.md`

股票簿基本使用、GitHub Pages、新聞與行情更新 **不需要** Apps Script 才能運作。

---

## 最後建議

重新部署後，先完成三件事再開始正式使用：

1. **新聞 Action 綠燈**
2. **收盤價 Action 綠燈**
3. **匯入自己的 JSON 備份並核對持股成本／股數／損益**

三項都正確後，就可以正常日常使用。
