#!/usr/bin/env python3
"""
Smart File Translation — local Streamlit UI.
Run: streamlit run app.py
"""

from __future__ import annotations

import base64
import subprocess
import sys
import tempfile
from pathlib import Path

import streamlit as st

from src.batch import (
    DEFAULT_CONCURRENCY,
    MAX_CONCURRENCY,
    MIN_CONCURRENCY,
    clamp_concurrency,
    translate_single_file,
    translate_tree,
    translate_zip,
)
from src.config import get_default_provider, list_available_providers, outputs_dir
from src.extractors import SUPPORTED_SUFFIXES, is_supported
from src.game_text import SCRIPT_SUFFIXES
from src.glossary import ensure_project, list_projects, load_glossary, save_glossary
from src.i18n import FALLBACK_LANG, available_languages, detect_ui_language, language_display_name, t
from src.models import default_model, models_for, resolve_model
from src.providers.base import TranslationError
from src.providers.codex_cli import INSTALL_HINT as CODEX_HINT
from src.providers.codex_cli import codex_cli_path_setting, probe_codex_cli
from src.providers.grok_cli import INSTALL_HINT as GROK_HINT
from src.providers.grok_cli import grok_cli_path_setting, probe_grok_cli
from src.security.secrets import load_secret, redact_secrets, save_secret_to_env
from src.theme import css_for
from src.ui_prefs import load_prefs, save_prefs

ROOT = Path(__file__).resolve().parent
ICON_PATH = ROOT / "icon.png"
UPLOAD_TYPES = sorted({s.lstrip(".") for s in SUPPORTED_SUFFIXES} | {"zip", "markdown", "htm"})
TARGET_CODES = [
    "zh-Hant", "zh-Hans", "en", "ja", "ko", "es", "fr", "de", "pt", "vi", "th", "id", "other",
]
PROVIDER_OPTIONS = ["auto", "openai", "anthropic", "gemini", "xai", "grok_cli", "codex_cli"]
SETTINGS_PANES = ("appearance", "translation", "keys", "glossary")
KEY_ROWS = (
    ("OpenAI", "OPENAI_API_KEY", "keys.openai"),
    ("Anthropic", "ANTHROPIC_API_KEY", "keys.anthropic"),
    ("Gemini API", "GEMINI_API_KEY", "keys.gemini"),
    ("Grok / xAI API key", "XAI_API_KEY", "keys.xai"),
)


def _browser_accept_language() -> str:
    try:
        headers = getattr(getattr(st, "context", None), "headers", None) or {}
        return str(headers.get("Accept-Language") or headers.get("accept-language") or "")
    except Exception:
        return ""


def _init_state() -> None:
    prefs = load_prefs()
    langs = available_languages()
    follow = prefs.get("ui_lang_follow")
    if follow is None:
        follow = prefs.get("ui_lang") not in langs
    saved_lang = prefs.get("ui_lang")
    if follow or saved_lang not in langs:
        saved_lang = detect_ui_language(_browser_accept_language())
        if saved_lang not in langs:
            saved_lang = FALLBACK_LANG if FALLBACK_LANG in langs else langs[0]
        follow = True if prefs.get("ui_lang_follow") is None else bool(follow)
    saved_provider = prefs.get("provider") if prefs.get("provider") in PROVIDER_OPTIONS else get_default_provider()
    saved_models = prefs.get("model_by_provider") if isinstance(prefs.get("model_by_provider"), dict) else {}
    defaults = {
        "ui_lang": saved_lang,
        "ui_lang_follow": bool(follow),
        "theme": prefs.get("theme") if prefs.get("theme") in {"light", "dark"} else "light",
        "uploader_nonce": 0,
        "picked_name": None,
        "picked_size": 0,
        "picked_bytes": None,
        "translate_note": None,
        "source_type": "file",
        "content_mode": "document",
        "page": "translate",
        "settings_pane": "appearance",
        "provider": saved_provider,
        "model_by_provider": dict(saved_models),
        "model": saved_models.get(saved_provider) or default_model(saved_provider),
        "concurrency": clamp_concurrency(prefs.get("concurrency", DEFAULT_CONCURRENCY)),
        "target_lang": "en",
        "source_choice": "auto",
        "project": "default",
        "glossary_pairs": None,
        "result_path": None,
        "result_text": None,
        "source_preview": None,
        "batch_report": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
    if st.session_state.glossary_pairs is None:
        st.session_state.glossary_pairs = load_glossary(st.session_state.project)


_init_state()


def L(key: str, **kwargs) -> str:
    return t(key, st.session_state.ui_lang, **kwargs)


st.set_page_config(
    page_title="Smart File Translation",
    page_icon=str(ICON_PATH) if ICON_PATH.is_file() else "📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)
_qp = st.query_params
if _qp.get("page") in {"translate", "settings"}:
    st.session_state.page = str(_qp.get("page"))
if _qp.get("theme") in {"light", "dark"}:
    st.session_state.theme = str(_qp.get("theme"))
if _qp.get("pane") in SETTINGS_PANES:
    st.session_state.settings_pane = str(_qp.get("pane"))
st.markdown(
    css_for(st.session_state.theme, st.session_state.page, st.session_state.settings_pane),
    unsafe_allow_html=True,
)


def _sync_query() -> None:
    st.query_params["page"] = st.session_state.page
    st.query_params["theme"] = st.session_state.theme
    if st.session_state.page == "settings":
        st.query_params["pane"] = st.session_state.settings_pane


def _go(page: str, pane: str | None = None) -> None:
    st.session_state.page = page
    if pane in SETTINGS_PANES:
        st.session_state.settings_pane = pane
    _sync_query()
    st.rerun()


def _persist_prefs() -> None:
    save_prefs(
        theme=st.session_state.theme,
        ui_lang=st.session_state.ui_lang,
        ui_lang_follow=bool(st.session_state.get("ui_lang_follow", True)),
        provider=st.session_state.provider,
        model_by_provider=dict(st.session_state.model_by_provider or {}),
        concurrency=st.session_state.concurrency,
    )


def _set_theme(theme: str) -> None:
    if theme not in {"light", "dark"}:
        return
    st.session_state.theme = theme
    _persist_prefs()
    _sync_query()
    st.rerun()


def _set_lang(lang: str, *, follow: bool = False) -> None:
    st.session_state.ui_lang = lang
    st.session_state.ui_lang_follow = follow
    _persist_prefs()
    st.rerun()


def _icon_data_uri() -> str:
    raw = ICON_PATH.read_bytes() if ICON_PATH.is_file() else b""
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii") if raw else ""


def _fmt_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


def _quiet_update(key: str = "update_quiet") -> None:
    if st.button(L("update.button"), key=key):
        _show_overlay_result(_run_overlay())


def _target_lang() -> str:
    choice = st.session_state.target_lang
    return choice if choice != "other" else st.session_state.get("target_other", "en")


def _source_lang() -> str | None:
    choice = st.session_state.source_choice
    return None if choice == "auto" else choice


def _run_overlay() -> str:
    script = ROOT / "scripts" / "sfts_overlay.py"
    try:
        proc = subprocess.run(
            [sys.executable, str(script), "--apply"],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            check=False,
        )
        return (proc.stdout or "") + (proc.stderr or "")
    except Exception:
        return ""


def _show_overlay_result(out: str) -> None:
    if "STATUS=UPDATED" in out:
        st.warning(L("update.reopen"))
    elif "STATUS=UP_TO_DATE" in out:
        st.info(L("update.up_to_date"))
    else:
        st.info(L("update.failed"))


def render_chrome() -> None:
    _pad, tab_t, tab_s, _gap, sun, tog, moon = st.columns([1.8, 0.7, 0.7, 1.5, 0.28, 0.72, 0.28])
    with tab_t:
        if st.button(L("nav.translate"), key="nav_translate"):
            _go("translate")
    with tab_s:
        if st.button(L("nav.settings"), key="nav_settings"):
            _go("settings")
    dark = st.session_state.theme == "dark"
    with sun:
        st.markdown('<div class="sfts-sunmoon">☀</div>', unsafe_allow_html=True)
    with tog:
        knob = "  ●" if dark else "●  "
        if st.button(knob, key="theme_toggle"):
            _set_theme("light" if dark else "dark")
    with moon:
        st.markdown('<div class="sfts-sunmoon">☾</div>', unsafe_allow_html=True)

    if st.session_state.page != "translate":
        return
    uri = _icon_data_uri()
    img = f'<img src="{uri}" width="88" height="88" alt="">' if uri else ""
    st.markdown(
        f'<div class="sfts-hero">{img}<div class="sfts-product">{L("app.title")}</div>'
        f'<div class="sfts-tagline">{L("app.tagline")}</div></div>',
        unsafe_allow_html=True,
    )
    _quiet_update("update_hero")


def render_appearance_pane() -> None:
    langs = available_languages()
    detected = detect_ui_language(_browser_accept_language())
    if detected not in langs:
        detected = FALLBACK_LANG if FALLBACK_LANG in langs else langs[0]
    now_name = language_display_name(detected, st.session_state.ui_lang)
    st.markdown(f'<div class="sfts-pane-title">{L("card.appearance")}</div>', unsafe_allow_html=True)
    with st.container(border=True):
        lab, ctl = st.columns([1.1, 2.2], vertical_alignment="center")
        with lab:
            st.markdown(f'<div class="sfts-row-label">{L("card.theme")}</div>', unsafe_allow_html=True)
        with ctl:
            theme = st.segmented_control(
                L("card.theme"),
                options=["light", "dark"],
                default=st.session_state.theme,
                format_func=lambda x: L("theme.light") if x == "light" else L("theme.dark"),
                key="theme_seg",
                label_visibility="collapsed",
            )
        if theme in {"light", "dark"} and theme != st.session_state.theme:
            _set_theme(theme)
        st.markdown('<hr class="sfts-divider">', unsafe_allow_html=True)
        lang_labels = {code: language_display_name(code, st.session_state.ui_lang) for code in langs}
        options = ["__system__"] + langs
        current = "__system__" if st.session_state.get("ui_lang_follow") else (
            st.session_state.ui_lang if st.session_state.ui_lang in langs else "__system__"
        )
        chosen = st.selectbox(
            L("sidebar.language"),
            options=options,
            index=options.index(current) if current in options else 0,
            format_func=lambda c: L("lang.follow_system", name=now_name) if c == "__system__" else lang_labels.get(c, c),
            key="ui_lang_select",
        )
        if chosen == "__system__":
            if not st.session_state.get("ui_lang_follow") or st.session_state.ui_lang != detected:
                _set_lang(detected, follow=True)
        elif chosen != st.session_state.ui_lang or st.session_state.get("ui_lang_follow"):
            _set_lang(chosen, follow=False)
        st.markdown(f'<div class="sfts-muted">{L("card.lang_fallback")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sfts-lang-count">🌐  {L("card.lang_count")}</div>', unsafe_allow_html=True)


def render_translation_pane() -> None:
    st.markdown(f'<div class="sfts-pane-title">{L("card.translation")}</div>', unsafe_allow_html=True)
    with st.container(border=True):
        target_labels = {c: L(f"target.{c}") for c in TARGET_CODES if c != "other"}
        target_labels["other"] = L("target.other")
        st.selectbox(
            L("sidebar.target_lang"),
            options=TARGET_CODES,
            index=TARGET_CODES.index(st.session_state.target_lang) if st.session_state.target_lang in TARGET_CODES else 2,
            format_func=lambda c: target_labels.get(c, c),
            key="target_lang",
        )
        if st.session_state.target_lang == "other":
            st.text_input(L("sidebar.target_other"), value="en", key="target_other")
        source_options = ["auto"] + [c for c in TARGET_CODES if c != "other"]
        source_labels = {"auto": L("sidebar.source_auto"), **{c: L(f"target.{c}") for c in TARGET_CODES if c != "other"}}
        st.selectbox(
            L("sidebar.source_lang"),
            options=source_options,
            index=source_options.index(st.session_state.source_choice) if st.session_state.source_choice in source_options else 0,
            format_func=lambda c: source_labels.get(c, c),
            key="source_choice",
        )
        provider_labels = {
            "auto": L("sidebar.provider_auto"),
            "openai": L("sidebar.provider_openai"),
            "anthropic": L("sidebar.provider_anthropic"),
            "gemini": L("sidebar.provider_gemini"),
            "xai": L("sidebar.provider_xai"),
            "grok_cli": L("sidebar.provider_grok_cli"),
            "codex_cli": L("sidebar.provider_codex_cli"),
        }
        chosen_provider = st.selectbox(
            L("sidebar.provider"),
            options=PROVIDER_OPTIONS,
            index=PROVIDER_OPTIONS.index(st.session_state.provider) if st.session_state.provider in PROVIDER_OPTIONS else 0,
            format_func=lambda x: provider_labels.get(x, x),
            key="provider_select",
        )
        if chosen_provider != st.session_state.provider:
            st.session_state.provider = chosen_provider
            stored = (st.session_state.model_by_provider or {}).get(chosen_provider)
            st.session_state.model = resolve_model(chosen_provider, stored) or default_model(chosen_provider)
            _persist_prefs()
            st.rerun()
        model_options = models_for(st.session_state.provider)
        if not model_options:
            st.caption(L("sidebar.model_auto"))
        else:
            current_model = resolve_model(st.session_state.provider, st.session_state.get("model"))
            if current_model not in model_options:
                current_model = model_options[0]
            picked = st.selectbox(
                L("sidebar.model"),
                options=model_options,
                index=model_options.index(current_model),
                key="model_select",
            )
            if picked != st.session_state.model:
                st.session_state.model = picked
                models = dict(st.session_state.model_by_provider or {})
                models[st.session_state.provider] = picked
                st.session_state.model_by_provider = models
                _persist_prefs()
                st.rerun()
        conc = st.slider(
            L("sidebar.concurrency"),
            min_value=MIN_CONCURRENCY,
            max_value=MAX_CONCURRENCY,
            value=clamp_concurrency(st.session_state.concurrency),
            key="concurrency_slider",
        )
        if conc != st.session_state.concurrency:
            st.session_state.concurrency = conc
            _persist_prefs()
            st.rerun()
        st.markdown(f'<div class="sfts-muted">{L("sidebar.concurrency_hint")}</div>', unsafe_allow_html=True)


def _key_label(fallback: str, locale_key: str) -> str:
    text = L(locale_key)
    return fallback if text == locale_key else text


def render_keys_pane() -> None:
    st.markdown(f'<div class="sfts-pane-title">{L("card.keys")}</div>', unsafe_allow_html=True)
    with st.container(border=True):
        grok = probe_grok_cli()
        grok_label = _key_label("Official Grok CLI", "keys.grok_cli")
        if grok.usable:
            st.markdown(
                f"**{grok_label}** &nbsp; <span class='sfts-pill-on'>✓ {L('keys.connected_cli')}</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"**{grok_label}** &nbsp; <span class='sfts-pill-off'>● {L('keys.unset')}</span>",
                unsafe_allow_html=True,
            )
            if grok.hint == "login":
                st.caption(L("keys.grok_cli_login"))
            else:
                st.caption(L("keys.grok_cli_missing", url=GROK_HINT))
        path_val = st.text_input(
            L("keys.grok_cli_path"),
            value=grok_cli_path_setting(),
            key="grok_cli_path_input",
        )
        if st.button(L("keys.save_local"), key="save_grok_cli_path") and path_val.strip():
            save_secret_to_env("GROK_CLI_PATH", path_val.strip())
            st.success(L("sidebar.save_key_ok"))
            st.rerun()
        st.markdown(f'<div class="sfts-muted">{L("keys.grok_cli_hint")}</div>', unsafe_allow_html=True)

        codex = probe_codex_cli()
        codex_label = _key_label("Official Codex CLI", "keys.codex_cli")
        if codex.usable:
            st.markdown(
                f"**{codex_label}** &nbsp; <span class='sfts-pill-on'>✓ {L('keys.connected_cli')}</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"**{codex_label}** &nbsp; <span class='sfts-pill-off'>● {L('keys.unset')}</span>",
                unsafe_allow_html=True,
            )
            if codex.hint == "login":
                st.caption(L("keys.codex_cli_login"))
            else:
                st.caption(L("keys.codex_cli_missing", url=CODEX_HINT))
        codex_path = st.text_input(
            L("keys.codex_cli_path"),
            value=codex_cli_path_setting(),
            key="codex_cli_path_input",
        )
        if st.button(L("keys.save_local"), key="save_codex_cli_path") and codex_path.strip():
            save_secret_to_env("CODEX_CLI_PATH", codex_path.strip())
            st.success(L("sidebar.save_key_ok"))
            st.rerun()
        st.markdown(f'<div class="sfts-muted">{L("keys.codex_cli_hint")}</div>', unsafe_allow_html=True)

        for fallback, env_name, locale_key in KEY_ROWS:
            label = _key_label(fallback, locale_key)
            val = load_secret(env_name)
            if val:
                tail = val[-4:] if len(val) >= 4 else ""
                status = L("keys.connected", tail=tail) if tail else L("keys.set")
                st.markdown(
                    f"**{label}** &nbsp; <span class='sfts-pill-on'>✓ {status}</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"**{label}** &nbsp; <span class='sfts-pill-off'>● {L('keys.unset')}</span>",
                    unsafe_allow_html=True,
                )
                pasted = st.text_input(
                    L("keys.paste_api"),
                    type="password",
                    key=f"paste_{env_name}",
                    placeholder=env_name,
                )
                if st.button(L("keys.save_local"), key=f"save_{env_name}") and pasted.strip():
                    save_secret_to_env(env_name, pasted.strip())
                    st.success(L("sidebar.save_key_ok"))
                    st.rerun()
        st.markdown(f'<div class="sfts-muted">{L("keys.xai_hint")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sfts-muted">{L("keys.local_only")}</div>', unsafe_allow_html=True)
        st.caption(L("sidebar.connect_official_only"))
        st.caption(L("sidebar.connect_no_websites"))


def render_glossary_pane() -> None:
    st.markdown(f'<div class="sfts-pane-title">{L("card.glossary")}</div>', unsafe_allow_html=True)
    with st.container(border=True):
        projects = list_projects()
        if "default" not in projects:
            ensure_project("default")
            projects = list_projects()
        p_idx = projects.index(st.session_state.project) if st.session_state.project in projects else 0
        selected = st.selectbox(L("sidebar.project"), options=projects, index=p_idx, key="project_select")
        if selected != st.session_state.project:
            st.session_state.project = selected
            st.session_state.glossary_pairs = load_glossary(selected)
            st.rerun()
        new_name = st.text_input(L("sidebar.new_project"), placeholder="name")
        if st.button(L("sidebar.create_project")) and new_name.strip():
            ensure_project(new_name.strip())
            st.session_state.project = new_name.strip()
            st.session_state.glossary_pairs = []
            st.rerun()

        pairs = list(st.session_state.glossary_pairs or [])
        if not pairs:
            st.caption(L("glossary.empty"))
        edited = []
        st.markdown(f"**{L('glossary.col_src')}** · **{L('glossary.col_dst')}**")
        for i, (term, trans) in enumerate(pairs):
            c1, c2, c3 = st.columns([2, 2, 0.5])
            with c1:
                nt = st.text_input(L("glossary.term"), value=term, key=f"term_{i}", label_visibility="collapsed")
            with c2:
                ntr = st.text_input(L("glossary.translation"), value=trans, key=f"tr_{i}", label_visibility="collapsed")
            with c3:
                if st.button("✕", key=f"del_{i}"):
                    pairs.pop(i)
                    st.session_state.glossary_pairs = pairs
                    st.rerun()
            if nt.strip():
                edited.append((nt.strip(), ntr.strip()))
        b1, b2 = st.columns(2)
        with b1:
            if st.button(L("sidebar.add_term")):
                pairs.append(("", ""))
                st.session_state.glossary_pairs = pairs
                st.rerun()
        with b2:
            if st.button(L("sidebar.save_glossary"), type="primary"):
                save_glossary(st.session_state.project, edited)
                st.session_state.glossary_pairs = edited
                st.success(L("glossary.saved", name=st.session_state.project))


def render_settings() -> None:
    rail, pane = st.columns([1, 3.2])
    labels = {
        "appearance": "🖥  " + L("card.appearance"),
        "translation": "文  " + L("card.translation"),
        "keys": "🔑  " + L("card.keys"),
        "glossary": "📖  " + L("card.glossary"),
    }
    with rail:
        for pane_id in SETTINGS_PANES:
            active = st.session_state.settings_pane == pane_id
            if st.button(labels[pane_id], use_container_width=True, key=f"pane_{pane_id}"):
                _go("settings", pane_id)
        _quiet_update("update_settings")
    with pane:
        current = st.session_state.settings_pane
        if current == "appearance":
            render_appearance_pane()
        elif current == "translation":
            render_translation_pane()
        elif current == "keys":
            render_keys_pane()
        else:
            render_glossary_pane()


def _need_key(status) -> bool:
    if list_available_providers():
        return False
    status.error(L("main.status_no_key"))
    return True


def _has_source(source_type: str) -> bool:
    if source_type == "file":
        return st.session_state.get("uploaded_file") is not None
    if source_type == "folder":
        return bool(str(st.session_state.get("folder_path") or "").strip())
    return st.session_state.get("zip_file") is not None


def _clear_picked() -> None:
    st.session_state.picked_name = None
    st.session_state.picked_size = 0
    st.session_state.picked_bytes = None
    st.session_state.source_preview = None
    st.session_state.result_text = None
    st.session_state.result_path = None
    st.session_state.translate_note = None
    st.session_state.uploader_nonce = int(st.session_state.get("uploader_nonce") or 0) + 1
    st.rerun()


def _show_file_chip() -> None:
    name = st.session_state.picked_name
    size = _fmt_size(int(st.session_state.picked_size or 0))
    left, right = st.columns([8, 1])
    with left:
        st.markdown(
            f'<div class="sfts-filechip"><span class="sfts-filechip-ico">📄</span>'
            f'<span class="sfts-filechip-name">{name}</span>'
            f'<span class="sfts-filechip-size">{size}</span></div>',
            unsafe_allow_html=True,
        )
    with right:
        if st.button("✕", key="clear_picked"):
            _clear_picked()


def _seg_row(label: str, control):
    lab, ctl = st.columns([1.15, 2.35], vertical_alignment="center")
    with lab:
        st.markdown(f'<div class="sfts-row-label">{label}</div>', unsafe_allow_html=True)
    with ctl:
        return control()


def render_translate() -> None:
    with st.container(border=True):
        source_type = _seg_row(
            L("main.source_type"),
            lambda: st.segmented_control(
                L("main.source_type"),
                options=["file", "folder", "zip"],
                format_func=lambda x: {
                    "file": "📄  " + L("main.seg_file"),
                    "folder": "📁  " + L("main.seg_folder"),
                    "zip": "🗜  " + L("main.seg_zip"),
                }[x],
                key="source_type",
                required=True,
            ),
        ) or "file"
        content_mode = _seg_row(
            L("main.content_mode"),
            lambda: st.segmented_control(
                L("main.content_mode"),
                options=["document", "game"],
                format_func=lambda x: {
                    "document": "💬  " + L("main.seg_doc"),
                    "game": "🎮  " + L("main.seg_game"),
                }[x],
                key="content_mode",
                required=True,
            ),
        ) or "document"
        game_mode = content_mode == "game"
        status = st.empty()
        translate_kw = dict(
            target_lang=_target_lang(),
            source_lang=_source_lang(),
            project=st.session_state.project,
            provider_choice=st.session_state.provider,
            game_mode=game_mode,
            model=resolve_model(st.session_state.provider, st.session_state.get("model")),
            concurrency=clamp_concurrency(st.session_state.concurrency),
        )
        nonce = int(st.session_state.get("uploader_nonce") or 0)
        has_source = False

        if source_type == "file":
            if not st.session_state.picked_name:
                uploaded = st.file_uploader(
                    L("main.upload"),
                    type=UPLOAD_TYPES,
                    key=f"file_up_{nonce}",
                    label_visibility="collapsed",
                )
                if uploaded is not None:
                    st.session_state.picked_name = uploaded.name
                    st.session_state.picked_size = int(getattr(uploaded, "size", 0) or len(uploaded.getvalue()))
                    st.session_state.picked_bytes = uploaded.getvalue()
                    st.rerun()
            else:
                _show_file_chip()
                has_source = True
                name = st.session_state.picked_name
                suffix = Path(name).suffix.lower()
                raw = st.session_state.picked_bytes or b""
                if suffix == ".zip":
                    status.error(L("main.zip_use_zip_mode"))
                    has_source = False
                elif not is_supported(name) and suffix not in SCRIPT_SUFFIXES:
                    status.error(L("error.unsupported_format"))
                    has_source = False
                else:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(raw)
                        tmp_path = Path(tmp.name)
                    try:
                        preview = tmp_path.read_text(encoding="utf-8", errors="replace")[:4000]
                    except Exception:
                        preview = L("main.binary_preview")
                    st.session_state.source_preview = preview
                    if has_source:
                        go = st.button(
                            L("main.translate_btn"),
                            type="primary",
                            use_container_width=True,
                            key="start_translate",
                        )
                        if go and not _need_key(status):
                            try:
                                out_name = Path(name).stem + f".{_target_lang()}" + suffix
                                out_path = outputs_dir() / out_name
                                translate_single_file(tmp_path, out_path, **translate_kw)
                                st.session_state.result_path = str(out_path)
                                if out_path.suffix.lower() not in {".docx", ".pdf", ".xlsx"}:
                                    st.session_state.result_text = out_path.read_text(encoding="utf-8", errors="replace")
                                else:
                                    st.session_state.result_text = L("main.saved_binary")
                                st.session_state.translate_note = L("main.status_done")
                            except TranslationError as e:
                                status.error(L("main.status_error", msg=redact_secrets(str(e))))
                            except Exception as e:
                                status.error(L("main.status_error", msg=redact_secrets(str(e))))

        elif source_type == "folder":
            st.caption(L("main.folder_hint"))
            folder_path = st.text_input(L("main.folder_path"), value="", label_visibility="collapsed")
            has_source = bool(folder_path.strip())
            if has_source:
                go = st.button(
                    L("main.translate_btn"),
                    type="primary",
                    use_container_width=True,
                    key="start_translate",
                )
                if go:
                    root = Path(folder_path).expanduser()
                    if not root.is_dir():
                        status.error(L("main.folder_missing"))
                    elif not _need_key(status):
                        try:
                            report = translate_tree(root, job_name=root.name, **translate_kw)
                            st.session_state.batch_report = report
                            st.session_state.translate_note = L(
                                "main.batch_done", n=len(report.written), k=len(report.skipped)
                            )
                        except TranslationError as e:
                            status.error(L("main.status_error", msg=redact_secrets(str(e))))
                        except Exception as e:
                            status.error(L("main.status_error", msg=redact_secrets(str(e))))

        else:
            if not st.session_state.picked_name:
                zipped = st.file_uploader(
                    L("main.zip_upload"),
                    type=["zip"],
                    key=f"zip_up_{nonce}",
                    label_visibility="collapsed",
                )
                if zipped is not None:
                    st.session_state.picked_name = zipped.name
                    st.session_state.picked_size = int(getattr(zipped, "size", 0) or len(zipped.getvalue()))
                    st.session_state.picked_bytes = zipped.getvalue()
                    st.rerun()
            else:
                _show_file_chip()
                has_source = True
                go = st.button(
                    L("main.translate_btn"),
                    type="primary",
                    use_container_width=True,
                    key="start_translate",
                )
                if go and not _need_key(status):
                    try:
                        with tempfile.TemporaryDirectory(prefix="sfts_zip_") as tmp:
                            zpath = Path(tmp) / "upload.zip"
                            zpath.write_bytes(st.session_state.picked_bytes or b"")
                            report = translate_zip(
                                zpath,
                                Path(tmp) / "tree",
                                job_name=Path(st.session_state.picked_name).stem,
                                **translate_kw,
                            )
                            st.session_state.batch_report = report
                            st.session_state.translate_note = L(
                                "main.batch_done", n=len(report.written), k=len(report.skipped)
                            )
                    except TranslationError as e:
                        status.error(L("main.status_error", msg=redact_secrets(str(e))))
                    except Exception as e:
                        status.error(L("main.status_error", msg=redact_secrets(str(e))))

    if st.session_state.translate_note:
        st.markdown(f'<div class="sfts-ok">{st.session_state.translate_note}</div>', unsafe_allow_html=True)

    show_src = bool(st.session_state.source_preview) and source_type == "file" and st.session_state.picked_name
    show_out = bool(st.session_state.result_text) and source_type == "file"
    if show_src or show_out:
        c1, c2 = st.columns(2)
        if show_src:
            with c1:
                with st.container(border=True):
                    st.markdown(f"**{L('main.preview_src')}**")
                    st.text_area("src", value=st.session_state.source_preview, height=220, label_visibility="collapsed")
        if show_out:
            with c2:
                with st.container(border=True):
                    st.markdown(f"**{L('main.preview_out')}**")
                    out = (st.session_state.result_text or "")[:4000]
                    st.text_area("out", value=out, height=220, label_visibility="collapsed")
                    if st.session_state.result_path and Path(st.session_state.result_path).is_file():
                        data = Path(st.session_state.result_path).read_bytes()
                        st.download_button(
                            L("main.download") + "  " + Path(st.session_state.result_path).name,
                            data=data,
                            file_name=Path(st.session_state.result_path).name,
                            mime="application/octet-stream",
                        )

    report = st.session_state.batch_report
    if report is not None:
        if report.written:
            st.markdown(f"**{L('main.done_list')}**")
            for item in report.written:
                st.write(f"{item.rel} → {item.out}")
        if report.skipped:
            st.markdown(f"**{L('main.skip_list')}**")
            for item in report.skipped:
                st.write(f"{item.rel} — {redact_secrets(item.skipped or item.error)}")


render_chrome()
_sync_query()
if st.session_state.page == "settings":
    render_settings()
else:
    render_translate()

st.markdown(f'<div class="sfts-footer">{L("about.footer")}</div>', unsafe_allow_html=True)
