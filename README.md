<p align="center">
  <img src="icon.png" alt="Smart File Translation System" width="128">
</p>

# Smart File Translation System

This app helps you translate files on your own computer. It can read `.txt`, `.md`, `.docx`, and `.pdf` files.

## How to use

1. Download this folder from GitHub (green **Code** button → **Download ZIP**).
2. Unzip the folder.
3. Open the unzipped folder.
4. On Windows, double-click `start.bat`. On a Mac or Linux computer, open Terminal in this folder and run `./start.sh`.
5. Wait until a browser page opens. The first start can take a few minutes.
6. If the app asks for a key, open the `.env` file in the same folder, paste your key after the `=` sign, save the file, and start again.

You do not need to type any other commands. The starter makes a local work folder, installs what it needs, and opens the app. If a `.env` file is already there, it is left alone.

## What you can do

1. Translate one file, a whole folder, or a zip.
2. Use game-text mode so only words players read are changed.
3. Save words you care about so later files use the same wording.
4. Change the on-screen language. Twelve languages are included.
5. Press **Check for official updates**, or just start the app — it looks for a newer official package at most once a day.

Translated files are saved in `data/outputs/` and can also be downloaded in the browser. Your keys and your own folders stay on this computer.

## Optional settings

If you want extra options later, they live in the `.env` file:

| Name | What it is |
|------|------------|
| `OPENAI_API_KEY` | Key for OpenAI or a compatible service |
| `OPENAI_BASE_URL` | Optional custom address |
| `OPENAI_MODEL` | Model name (default `gpt-4o-mini`) |
| `ANTHROPIC_API_KEY` | Key for Anthropic |
| `ANTHROPIC_MODEL` | Model name |
| `DEFAULT_PROVIDER` | `auto`, `openai`, or `anthropic` |
| `TRANSLATE_CHUNK_SIZE` | How much text to send at a time (default 3000) |

Keep keys only in `.env`. Never put them in the repository.

## Changelog / Updates

### v0.1.1

- Added `start.bat` (Windows) and `start.sh` (Mac / Linux) so you can start the app with one click.
- Public listing is now English on top and Traditional Chinese below in this same file.
- Personal mailbox lines were removed from the listing.
- Folder and zip batch: one output file for each input file, same folder shape.
- More file types: json, csv, tsv, yaml, po, xliff, xlsx, html, srt, vtt.
- Game text mode: only words players read.
- Official developer APIs only. Chat websites cannot be connected.
- Official-package updater: start scripts and the in-app button share one local overlay helper.

### v0.1.0

- First public version of the app.

---

# 智能檔案翻譯系統

這個小程式可以在你自己的電腦上翻譯檔案，支援 `.txt`、`.md`、`.docx`、`.pdf`。

## 怎麼使用

1. 從 GitHub 下載這個資料夾（綠色 **Code** 按鈕 → **Download ZIP**）。
2. 解壓縮。
3. 打開解壓後的資料夾。
4. Windows：連按兩下 `start.bat`。Mac 或 Linux：在這個資料夾打開 Terminal，輸入 `./start.sh` 後按 Enter。
5. 等瀏覽器自己打開。第一次啟動可能要等幾分鐘。
6. 如果程式要你填金鑰，打開同一個資料夾裡的 `.env`，在 `=` 後面貼上金鑰，存檔後再啟動一次。

你不用打其他指令。啟動檔會自己準備需要的東西並打開程式。如果 `.env` 已經存在，不會被覆蓋。

## 你可以做什麼

1. 翻譯一個檔案、整個資料夾，或一個 zip。
2. 遊戲文字模式只改玩家會看到的句子。
3. 把重要用詞存下來，之後翻譯會比較一致。
4. 切換畫面語言。內建十二種語言。
5. 按「檢查官方更新」，或直接啟動程式——一天最多查一次官方包裝。

譯好的檔案會放在 `data/outputs/`，也可以在瀏覽器下載。金鑰和你自己的資料夾都留在這台電腦。

## 選擇性設定

之後如果要改更多選項，都寫在 `.env`：

| 名稱 | 說明 |
|------|------|
| `OPENAI_API_KEY` | OpenAI 或相容服務的金鑰 |
| `OPENAI_BASE_URL` | 可選的自訂網址 |
| `OPENAI_MODEL` | 模型名稱（預設 `gpt-4o-mini`） |
| `ANTHROPIC_API_KEY` | Anthropic 金鑰 |
| `ANTHROPIC_MODEL` | 模型名稱 |
| `DEFAULT_PROVIDER` | `auto`、`openai` 或 `anthropic` |
| `TRANSLATE_CHUNK_SIZE` | 一次送出的文字量（預設 3000） |

金鑰只放在 `.env`。不要寫進倉庫。

## 更新紀錄 / Changelog

### v0.1.1

- 新增 `start.bat`（Windows）與 `start.sh`（Mac / Linux），按一下就能啟動。
- 公開說明改為同一份檔案：英文在上、繁體中文在下。
- 公開說明已不再放任何信箱。
- 資料夾與 zip 批次：一個輸入檔對一個輸出檔，資料夾形狀相同。
- 更多檔案種類：json、csv、tsv、yaml、po、xliff、xlsx、html、srt、vtt。
- 遊戲文字模式：只翻譯玩家會看到的句子。
- 只能接官方開發者 API。不能連接聊天網站。
- 官方包裝更新：啟動檔與程式內按鈕共用同一個本機 overlay。

### v0.1.0

- 第一個公開版本。
