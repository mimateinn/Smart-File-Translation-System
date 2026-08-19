"""Light / dark theme CSS for the Streamlit shell. Local fonts only."""

from __future__ import annotations

_SHARED = """
html, body, [class*="css"] { font-family: "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", sans-serif; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, .stDeployButton, .stAppDeployButton,
[data-testid="stToolbar"], [data-testid="stAppDeployButton"] {
  visibility: hidden !important; display: none !important; height: 0 !important;
}
.block-container { padding-top: 0.8rem; max-width: 1040px; }
.sfts-hero { text-align: center; margin: 0.2rem 0 0.4rem 0; }
.sfts-hero img { display: block; margin: 0 auto; }
.sfts-product { font-size: 0.95rem; font-weight: 600; margin-top: 0.35rem; letter-spacing: 0.01em; }
.sfts-tabs { margin: 0.4rem 0 1rem 0; }
.sfts-muted { font-size: 0.82rem; }
.sfts-pill-on {
  display: inline-block; padding: 0.12rem 0.7rem; border-radius: 999px;
  border: 1px solid #14b8a6; font-size: 0.85rem;
}
.sfts-pill-off {
  display: inline-block; padding: 0.12rem 0.7rem; border-radius: 999px;
  font-size: 0.85rem;
}
div.stButton > button[kind="primary"] {
  background: #14b8a6; border-color: #14b8a6; color: white;
}
.sfts-footer { text-align: center; font-size: 0.8rem; margin-top: 1.6rem; }
.sfts-update-link div.stButton > button {
  background: transparent !important; border: none !important; box-shadow: none !important;
  padding: 0 !important; font-size: 0.78rem !important; font-weight: 400 !important;
  text-decoration: underline; min-height: 0 !important; height: auto !important;
}
.sfts-rail div.stButton > button { text-align: left; justify-content: flex-start; }
"""

LIGHT = f"""
<style>
{_SHARED}
.stApp {{ background: #f3f5f6; }}
.sfts-product {{ color: #111827; }}
.sfts-muted {{ color: #6b7280; }}
.sfts-pill-on {{ color: #0f766e; }}
.sfts-pill-off {{ border: 1px solid #d1d5db; color: #6b7280; }}
.sfts-footer {{ color: #9ca3af; }}
.sfts-update-link div.stButton > button {{ color: #6b7280 !important; }}
[data-testid="stVerticalBlockBorderWrapper"] {{
  background: #fff; border-radius: 16px; border: 1px solid #eef0f2;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}}
</style>
"""

DARK = f"""
<style>
{_SHARED}
.stApp {{ background: #121417; color: #e5e7eb; }}
[data-testid="stAppViewContainer"] {{ background: #121417; }}
.sfts-product {{ color: #f3f4f6; }}
.sfts-muted {{ color: #9ca3af; }}
.sfts-pill-on {{ border-color: #2dd4bf; color: #5eead4; }}
.sfts-pill-off {{ border: 1px solid #4b5563; color: #9ca3af; }}
.sfts-footer {{ color: #6b7280; }}
.sfts-update-link div.stButton > button {{ color: #9ca3af !important; }}
[data-testid="stVerticalBlockBorderWrapper"] {{
  background: #1b1e24; border-radius: 16px; border: 1px solid #2a2e35;
  box-shadow: 0 8px 24px rgba(0,0,0,0.25);
}}
</style>
"""


def css_for(theme: str) -> str:
    return DARK if theme == "dark" else LIGHT
