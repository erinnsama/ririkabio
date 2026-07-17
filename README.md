# RIRIKA（莉莉卡）自我介紹站

追星用自介頁 — lit.link 風格單欄卡片，NMIXX Y2K 應援色。內容全部資料驅動，附後台可線上編輯＋上傳圖。

## 檔案結構
```
ririka-intro/
├── index.html          前台
├── style.css
├── script.js           讀 data/profile.json 動態渲染
├── admin.html          🔒 後台（改內容＋上傳圖）
├── data/profile.json   ← 所有內容
├── assets/             頭貼、應援圖
├── api/
│   ├── profile.py      GET 最新 profile.json
│   ├── save.py         POST 存 profile.json（需密碼）
│   └── upload.py       POST 上傳圖片（需密碼）
└── vercel.json
```

## 本機預覽
```
cd ririka-intro
python -m http.server 8899
```
開 http://127.0.0.1:8899 （後台 http://127.0.0.1:8899/admin.html ）
※ 本機沒有 serverless，後台可預覽 UI，但「儲存/上傳」要部署後才會實際寫入。

## 部署（Vercel，沿用 NMIXX 模式）
1. 把本資料夾推上一個 GitHub repo（例：`ririka-intro`）。
2. Vercel → New Project → 匯入該 repo。
3. Settings → Environment Variables 設定：
   - `ADMIN_PASSWORD`：自訂後台密碼
   - `GITHUB_PAT`：Fine-grained token，對本 repo `Contents: Read and write`
   - `GITHUB_OWNER`：你的 GitHub 帳號
   - `GITHUB_REPO`：`ririka-intro`
4. Deploy。之後綁自訂子網域（例：`ririka.erinsama.com`）。

## 更新內容
進 `/admin.html` → 輸入密碼 → 編輯 → 「儲存並發布」。
後台會把 `profile.json` / 圖片 commit 回 repo，Vercel 自動重佈署，約 1 分鐘後前台更新。
（也可以直接手改 `data/profile.json` 再 push。）
