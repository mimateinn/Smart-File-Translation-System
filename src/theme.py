"""Light / dark theme CSS for the Streamlit shell. Local fonts only."""

from __future__ import annotations

LIGHT = """
<style>
html, body, [class*="css"] { font-family: "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", sans-serif; }
.stApp { background: #f3f5f6; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, .stDeployButton, [data-testid="stToolbar"] { visibility: hidden !important; display: none !important; }
.block-container { padding-top: 1.1rem; max-width: 1100px; }
.sfts-brand { font-size: 1.05rem; font-weight: 600; color: #111827; padding-top: 0.35rem; }
.sfts-card h3 { margin: 0 0 0.7rem 0; font-size: 1.08rem; color: #111827; }
.sfts-muted { color: #6b7280; font-size: 0.82rem; }
.sfts-pill-on {
  display: inline-block; padding: 0.12rem 0.7rem; border-radius: 999px;
  border: 1px solid #14b8a6; color: #0f766e; font-size: 0.85rem;
}
.sfts-pill-off {
  display: inline-block; padding: 0.12rem 0.7rem; border-radius: 999px;
  border: 1px solid #d1d5db; color: #6b7280; font-size: 0.85rem;
}
div.stButton > button[kind="primary"] {
  background: #14b8a6; border-color: #14b8a6; color: white;
}
.sfts-footer { text-align: center; color: #9ca3af; font-size: 0.8rem; margin-top: 1.6rem; }
[data-testid="stVerticalBlockBorderWrapper"] {
  background: #fff; border-radius: 16px; border: 1px solid #eef0f2;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}
</style>
"""

DARK = """
<style>
html, body, [class*="css"] { font-family: "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", sans-serif; }
.stApp { background: #121417; color: #e5e7eb; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, .stDeployButton, [data-testid="stToolbar"] { visibility: hidden !important; display: none !important; }
[data-testid="stAppViewContainer"] { background: #121417; }
.block-container { padding-top: 1.1rem; max-width: 1100px; }
.sfts-brand { font-size: 1.05rem; font-weight: 600; color: #f3f4f6; padding-top: 0.35rem; }
.sfts-card h3 { margin: 0 0 0.7rem 0; font-size: 1.08rem; color: #f3f4f6; }
.sfts-muted { color: #9ca3af; font-size: 0.82rem; }
.sfts-pill-on {
  display: inline-block; padding: 0.12rem 0.7rem; border-radius: 999px;
  border: 1px solid #2dd4bf; color: #5eead4; font-size: 0.85rem;
}
.sfts-pill-off {
  display: inline-block; padding: 0.12rem 0.7rem; border-radius: 999px;
  border: 1px solid #4b5563; color: #9ca3af; font-size: 0.85rem;
}
div.stButton > button[kind="primary"] {
  background: #14b8a6; border-color: #14b8a6; color: white;
}
.sfts-footer { text-align: center; color: #6b7280; font-size: 0.8rem; margin-top: 1.6rem; }
[data-testid="stVerticalBlockBorderWrapper"] {
  background: #1b1e24; border-radius: 16px; border: 1px solid #2a2e35;
  box-shadow: 0 8px 24px rgba(0,0,0,0.25);
}
</style>
"""


def css_for(theme: str) -> str:
    return DARK if theme == "dark" else LIGHT
