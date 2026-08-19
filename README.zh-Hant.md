# 智能檔案翻譯系統（Smart File Translation System）

AI 驅動的文件與檔案在地化翻譯系統，支援多 API 路由、上下文記憶（用語表）與 12 種原生介面語言。

**聯絡：** laevataincheng@gmail.com

## 功能

1. **AI 文件／檔案翻譯**  
   支援 `.txt`、`.md`、`.docx`、`.pdf`。抽出文字、翻譯後寫回（docx 盡力保留版式；pdf 產出乾淨譯文 PDF）。失敗時顯示清楚錯誤訊息。

2. **多 API 路由**  
   至少兩個供應商：**OpenAI**（或任何 OpenAI 相容端點）與 **Anthropic Claude**。金鑰只從環境變數讀取，永不寫入倉庫。無金鑰時介面仍可開啟；翻譯會給出明確錯誤。路由可選 `auto` 或指定供應商。

3. **上下文記憶（用語表）**  
   每個專案有本地 `glossary.json`（英文檔名）。用語會注入翻譯提示，後續翻譯保持一致。

4. **12 種介面語言**  
   訊息目錄在 `locales/`。之後加語言＝加一份 JSON catalog，不硬編碼 UI 字串。  
   語言：`zh-Hant`（預設）、`zh-Hans`、`en`、`ja`、`ko`、`es`、`fr`、`de`、`pt`、`vi`、`th`、`id`。可在側邊欄切換。

## 需求

- Python 3.10+
- 至少一個供應商的 API 金鑰（OpenAI 相容或 Anthropic）

## 快速開始

```bash
cd smart-file-translation
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# 編輯 .env，填入 OPENAI_API_KEY 與／或 ANTHROPIC_API_KEY
streamlit run app.py
```

開啟 Streamlit 顯示的網址（通常是 http://localhost:8501）。

## 設定

| 變數 | 說明 |
|------|------|
| `OPENAI_API_KEY` | OpenAI 或相容 API 金鑰 |
| `OPENAI_BASE_URL` | 可選 base URL（如 DeepSeek、Groq） |
| `OPENAI_MODEL` | 模型 id（預設 `gpt-4o-mini`） |
| `ANTHROPIC_API_KEY` | Anthropic API 金鑰 |
| `ANTHROPIC_MODEL` | 模型 id |
| `DEFAULT_PROVIDER` | `auto` \| `openai` \| `anthropic` |
| `TRANSLATE_CHUNK_SIZE` | 每次 API 呼叫最大字元數（預設 3000） |

密鑰只放在 `.env`（已被 gitignore）。絕不要把 token 寫進倉庫。

## 專案用語表

- 專案位於 `projects/<name>/glossary.json`。
- 在側邊欄建立專案、加入「用語 → 偏好譯法」後儲存。
- 該專案每次翻譯都會把用語表傳給模型。

## 輸出

譯文寫入 `data/outputs/`，並可在介面下載。

## 新增介面語言

1. 複製 `locales/en.json` 為 `locales/<code>.json`。
2. 翻譯 value（key 保持不變）。
3. 若 `src/i18n.py` 的 `SUPPORTED_LANGS` 尚未包含該 code，可自行加入。
4. 重啟應用，選擇器會出現新語言。

## 授權

本專案以本機使用為主。授權檔由維護者後續放入倉庫。

## 聯絡

僅使用：**laevataincheng@gmail.com**
