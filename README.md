# Smart File Translation System

AI-powered document & file localization translation system supporting multiple API routing, context memory (glossary), and 12 native interface languages.

**Contact:** laevataincheng@gmail.com

## Features

1. **AI document / file translation**  
   Supports `.txt`, `.md`, `.docx`, `.pdf`. Text is extracted, translated, and written back (best-effort layout for docx; clean PDF for translated content). Failures surface clear error messages.

2. **Multi-API routing**  
   At least two providers: **OpenAI** (or any OpenAI-compatible endpoint) and **Anthropic Claude**. Keys are read from environment variables only — never committed. Without a key the UI still opens; translation shows an explicit error. Routing can be `auto` or a specific provider.

3. **Context memory (glossary)**  
   Each project has a local `glossary.json` (English filename). Terms are injected into the translation prompt so subsequent runs stay consistent.

4. **12 interface languages**  
   Message catalogs under `locales/`. Adding a language = add one JSON catalog; UI strings are not hard-coded.  
   Languages: `zh-Hant` (default), `zh-Hans`, `en`, `ja`, `ko`, `es`, `fr`, `de`, `pt`, `vi`, `th`, `id`. Switchable in the sidebar.

## Requirements

- Python 3.10+
- API key for at least one provider (OpenAI-compatible or Anthropic)

## Quick start

```bash
cd smart-file-translation
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set OPENAI_API_KEY and/or ANTHROPIC_API_KEY
streamlit run app.py
```

Open the URL shown by Streamlit (usually http://localhost:8501).

## Configuration

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI or compatible API key |
| `OPENAI_BASE_URL` | Optional base URL (e.g. DeepSeek, Groq) |
| `OPENAI_MODEL` | Model id (default `gpt-4o-mini`) |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `ANTHROPIC_MODEL` | Model id |
| `DEFAULT_PROVIDER` | `auto` \| `openai` \| `anthropic` |
| `TRANSLATE_CHUNK_SIZE` | Max characters per API call (default 3000) |

Secrets stay in `.env` (gitignored). Never put tokens in the repository.

## Project glossary

- Projects live under `projects/<name>/glossary.json`.
- Create a project in the sidebar, add term → preferred translation pairs, and save.
- The glossary is passed to the model on every translation for that project.

## Output

Translated files are written under `data/outputs/` and can be downloaded from the UI.

## Adding a UI language

1. Copy `locales/en.json` to `locales/<code>.json`.
2. Translate the values (keep keys unchanged).
3. Optionally add the code to `SUPPORTED_LANGS` in `src/i18n.py` if it is not already listed.
4. Restart the app; the new language appears in the selector.

## License

This project is intended for local use. See the repository for any license file added by the maintainer.

## Contact

Only: **laevataincheng@gmail.com**
