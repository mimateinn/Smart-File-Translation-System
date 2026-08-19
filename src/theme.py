"""v2 chrome CSS. Hides default Streamlit look. Local fonts only.

Streamlit does not nest widgets inside markdown wrappers, so chrome
rules target widget keys (``.st-key-*`` / ``[class*="st-key-"]``).
"""

from __future__ import annotations

_SHARED = """
html, body, [class*="css"], .stApp, .stMarkdown, button, input, label {
  font-family: "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", "Noto Sans", sans-serif !important;
}
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
#MainMenu, footer,
.stDeployButton, .stAppDeployButton,
[data-testid="stAppDeployButton"],
div[data-testid="stToolbarActions"],
[data-testid="stHeaderActionElements"] {
  visibility: hidden !important;
  display: none !important;
  height: 0 !important;
  min-height: 0 !important;
  max-height: 0 !important;
  opacity: 0 !important;
  pointer-events: none !important;
}
header[data-testid="stHeader"] { padding: 0 !important; }
.stApp { background: var(--sfts-bg); color: var(--sfts-text); }
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main, section.main {
  background: var(--sfts-bg) !important;
}
.block-container {
  padding-top: 0.7rem !important;
  padding-bottom: 2rem !important;
  max-width: 860px !important;
}
iframe { color-scheme: auto; }

/* Hero: pictorial icon + small centered name */
.sfts-hero { text-align: center; margin: 0.2rem 0 0.1rem 0; }
.sfts-hero img {
  display: block; margin: 0 auto;
  width: 88px; height: 88px;
  object-fit: contain;
  border-radius: 18px;
}
.sfts-product {
  font-size: 0.98rem !important; font-weight: 600 !important;
  margin-top: 0.4rem; letter-spacing: 0.01em;
  color: var(--sfts-text);
}
.sfts-tagline {
  color: var(--sfts-muted); font-size: 0.86rem;
  margin-top: 0.2rem; line-height: 1.45;
}
.sfts-row-label {
  color: var(--sfts-text); font-size: 0.92rem; font-weight: 500;
  padding-top: 0.35rem;
}
.sfts-pane-title {
  font-size: 1.45rem; font-weight: 700; margin: 0 0 0.85rem 0; color: var(--sfts-text);
}
.sfts-filechip {
  display: flex; align-items: center;
  background: var(--sfts-chip); border: 1px solid var(--sfts-chip-line);
  border-radius: 10px; padding: 0.55rem 0.85rem; margin: 0.15rem 0;
}
.sfts-filechip-ico { margin-right: 0.55rem; font-size: 1.15rem; }
.sfts-filechip-name { font-weight: 600; color: var(--sfts-text); }
.sfts-filechip-size { color: var(--sfts-muted); font-size: 0.82rem; margin-left: 0.6rem; }
.sfts-ok {
  background: var(--sfts-ok-bg); color: #047857; border-radius: 10px;
  padding: 0.5rem 0.85rem; font-size: 0.92rem; margin: 0.7rem 0;
}
.sfts-muted { color: var(--sfts-muted); font-size: 0.82rem; }
.sfts-lang-count { color: #0f766e; font-size: 0.82rem; margin-top: 0.35rem; }
.sfts-pill-on {
  display: inline-block; padding: 0.12rem 0.7rem; border-radius: 999px;
  border: 1px solid #14b8a6; color: #0f766e; font-size: 0.85rem;
}
.sfts-pill-off {
  display: inline-block; padding: 0.12rem 0.7rem; border-radius: 999px;
  border: 1px solid var(--sfts-line); color: var(--sfts-muted); font-size: 0.85rem;
}
.sfts-footer { text-align: center; color: var(--sfts-muted); font-size: 0.72rem; margin-top: 1.6rem; }
.sfts-divider { height: 1px; background: var(--sfts-line); margin: 1rem 0; border: 0; }
.sfts-sunmoon { color: var(--sfts-muted); font-size: 0.95rem; text-align: center; padding-top: 0.35rem; }

[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--sfts-card) !important;
  border-radius: 16px !important;
  border: 1px solid var(--sfts-line) !important;
  box-shadow: none !important;
}

/* Hide leftover radio dots */
div[data-testid="stRadio"] [data-baseweb="radio"] > div:first-child { display: none !important; }
div[data-testid="stRadio"] label {
  border: 1px solid var(--sfts-line);
  border-radius: 999px;
  padding: 0.28rem 0.85rem;
  margin-right: 0.35rem;
}
div[data-testid="stRadio"] label:has(input:checked) {
  background: #14b8a6; color: #fff; border-color: #14b8a6;
}

/* Compact file pick — no 200MB / extension dump */
[data-testid="stFileUploaderDropzoneInstructions"],
[data-testid="stFileUploaderDropzoneInstructions"] *,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] [data-testid="stCaptionContainer"],
[data-testid="stFileUploaderFile"],
[data-testid="stFileUploaderFileData"] {
  display: none !important;
  height: 0 !important;
  overflow: hidden !important;
}
[data-testid="stFileUploader"] section,
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {
  background: var(--sfts-card) !important;
  border: 1px dashed var(--sfts-line) !important;
  border-radius: 12px !important;
  padding: 0.45rem 0.7rem !important;
  min-height: 52px !important;
}
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button {
  background: transparent !important;
  border: 1px solid #14b8a6 !important;
  color: #0f766e !important;
  border-radius: 999px !important;
  box-shadow: none !important;
}

[data-testid="stWidgetLabel"] p { color: var(--sfts-text) !important; font-size: 0.92rem !important; font-weight: 500 !important; }
[class*="st-key-source_type"] [data-testid="stWidgetLabel"],
[class*="st-key-content_mode"] [data-testid="stWidgetLabel"],
[class*="st-key-theme_seg"] [data-testid="stWidgetLabel"] {
  display: none !important; height: 0 !important; overflow: hidden !important;
}
button[kind="headerNoPadding"],
[data-testid="stHeader"] button {
  display: none !important;
}
"""

LIGHT = f"""
<style>
:root {{
  --sfts-bg: #f7f8f9;
  --sfts-text: #1f2937;
  --sfts-muted: #6b7280;
  --sfts-card: #ffffff;
  --sfts-line: #e6eaee;
  --sfts-seg-bg: #f3f5f6;
  --sfts-track: #e5e7eb;
  --sfts-chip: #eef6ff;
  --sfts-chip-line: #dbeafe;
  --sfts-rail-on: #ccfbf1;
  --sfts-ok-bg: #ecfdf5;
}}
{_SHARED}
.stApp {{ background: #f7f8f9; }}
</style>
"""

DARK = f"""
<style>
:root {{
  --sfts-bg: #121417;
  --sfts-text: #f3f4f6;
  --sfts-muted: #9ca3af;
  --sfts-card: #1b1e24;
  --sfts-line: #2a2e35;
  --sfts-seg-bg: #16181c;
  --sfts-track: #2a2e35;
  --sfts-chip: #1a2740;
  --sfts-chip-line: #243656;
  --sfts-rail-on: #134e4a;
  --sfts-ok-bg: #052e2b;
}}
{_SHARED}
.stApp {{ background: #121417; color: #e5e7eb; }}
[data-testid="stAppViewContainer"] {{ background: #121417; }}
.sfts-lang-count {{ color: #5eead4; }}
.sfts-ok {{ color: #5eead4; }}
.sfts-pill-on {{ color: #5eead4; }}
</style>
"""


def _chrome_keys(page: str, pane: str) -> str:
    active_tab = "nav_translate" if page == "translate" else "nav_settings"
    active_pane = f"pane_{pane}" if pane else "pane_appearance"
    return f"""
<style>
/* Plain text tabs + teal underline (not fat pills) */
[class*="st-key-nav_translate"] button,
[class*="st-key-nav_settings"] button {{
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
  border-radius: 0 !important;
  min-height: 0 !important;
  height: auto !important;
  padding: 0.15rem 0.1rem 0.38rem !important;
  font-size: 1.02rem !important;
  font-weight: 500 !important;
  color: var(--sfts-muted) !important;
}}
[class*="st-key-{active_tab}"] button {{
  color: var(--sfts-text) !important;
  font-weight: 700 !important;
  border-bottom: 3px solid #14b8a6 !important;
}}

/* Sun / moon track */
[class*="st-key-theme_toggle"] button {{
  background: var(--sfts-track) !important;
  border: 1px solid var(--sfts-line) !important;
  border-radius: 999px !important;
  min-height: 28px !important;
  height: 28px !important;
  box-shadow: none !important;
  padding: 0 0.55rem !important;
  color: var(--sfts-text) !important;
  font-size: 0.78rem !important;
}}

/* Quiet dotted update link — must not steal the hero */
[class*="st-key-update_hero"] button,
[class*="st-key-update_settings"] button {{
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: #14b8a6 !important;
  font-size: 0.78rem !important;
  font-weight: 400 !important;
  text-decoration: underline !important;
  text-decoration-style: dotted !important;
  text-underline-offset: 3px !important;
  min-height: 0 !important;
  height: auto !important;
  padding: 0 !important;
}}

/* Segmented pills — teal fill when selected */
[class*="st-key-source_type"] [data-testid="stButtonGroup"],
[class*="st-key-content_mode"] [data-testid="stButtonGroup"],
[class*="st-key-theme_seg"] [data-testid="stButtonGroup"],
[class*="st-key-source_type"] [data-testid="stSegmentedControl"] > div,
[class*="st-key-content_mode"] [data-testid="stSegmentedControl"] > div,
[class*="st-key-theme_seg"] [data-testid="stSegmentedControl"] > div {{
  background: var(--sfts-seg-bg) !important;
  border: 1px solid var(--sfts-line) !important;
  border-radius: 999px !important;
  padding: 3px !important;
  gap: 2px !important;
}}
[class*="st-key-source_type"] button,
[class*="st-key-content_mode"] button,
[class*="st-key-theme_seg"] button {{
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 999px !important;
  color: var(--sfts-muted) !important;
  font-weight: 500 !important;
}}
[class*="st-key-source_type"] button[aria-pressed="true"],
[class*="st-key-source_type"] button[aria-checked="true"],
[class*="st-key-source_type"] button[data-selected="true"],
[class*="st-key-source_type"] button[kind="primary"],
[class*="st-key-content_mode"] button[aria-pressed="true"],
[class*="st-key-content_mode"] button[aria-checked="true"],
[class*="st-key-content_mode"] button[data-selected="true"],
[class*="st-key-content_mode"] button[kind="primary"],
[class*="st-key-theme_seg"] button[aria-pressed="true"],
[class*="st-key-theme_seg"] button[aria-checked="true"],
[class*="st-key-theme_seg"] button[data-selected="true"],
[class*="st-key-theme_seg"] button[kind="primary"] {{
  background: #14b8a6 !important;
  background-color: #14b8a6 !important;
  color: #ffffff !important;
}}

/* Settings rail */
[class*="st-key-pane_appearance"] button,
[class*="st-key-pane_translation"] button,
[class*="st-key-pane_keys"] button,
[class*="st-key-pane_glossary"] button {{
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  justify-content: flex-start !important;
  text-align: left !important;
  border-radius: 10px !important;
  color: var(--sfts-text) !important;
  border-left: 3px solid transparent !important;
}}
[class*="st-key-{active_pane}"] button {{
  background: var(--sfts-rail-on) !important;
  border-left: 3px solid #14b8a6 !important;
  color: #0f766e !important;
  font-weight: 600 !important;
}}

/* Wide teal start */
[class*="st-key-start_translate"] button {{
  background: #14b8a6 !important;
  border: none !important;
  color: #fff !important;
  border-radius: 12px !important;
  min-height: 48px !important;
  height: 48px !important;
  font-size: 1.05rem !important;
  font-weight: 600 !important;
  box-shadow: none !important;
}}
[class*="st-key-clear_picked"] button {{
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: var(--sfts-muted) !important;
  min-height: 0 !important;
  height: 32px !important;
}}
[class*="st-key-source_type"] [data-testid="stWidgetLabel"],
[class*="st-key-content_mode"] [data-testid="stWidgetLabel"],
[class*="st-key-theme_seg"] [data-testid="stWidgetLabel"] {{
  display: none !important;
  height: 0 !important;
  overflow: hidden !important;
}}
</style>
"""


def css_for(theme: str, page: str = "translate", pane: str = "appearance") -> str:
    base = DARK if theme == "dark" else LIGHT
    return base + _chrome_keys(page, pane)
