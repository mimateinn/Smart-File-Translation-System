#!/usr/bin/env python3
"""
Smart File Translation — local Streamlit UI.
Run: streamlit run app.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import streamlit as st

from src.batch import translate_single_file, translate_tree, translate_zip
from src.config import get_default_provider, list_available_providers, outputs_dir
from src.extractors import SUPPORTED_SUFFIXES, is_supported
from src.game_text import SCRIPT_SUFFIXES
from src.glossary import ensure_project, list_projects, load_glossary, save_glossary
from src.i18n import DEFAULT_LANG, available_languages, language_display_name, t
from src.providers.base import TranslationError
from src.security.hosts import HostNotAllowed, assert_public_https_url
from src.security.secrets import load_secret, mask_secret, redact_secrets, save_secret_to_env

UPLOAD_TYPES = sorted(
    {s.lstrip(".") for s in SUPPORTED_SUFFIXES} | {"zip", "markdown"}
)


if "ui_lang" not in st.session_state:
    st.session_state.ui_lang = DEFAULT_LANG
if "provider" not in st.session_state:
    st.session_state.provider = get_default_provider()
if "project" not in st.session_state:
    st.session_state.project = "default"
if "glossary_pairs" not in st.session_state:
    st.session_state.glossary_pairs = load_glossary(st.session_state.project)
if "result_path" not in st.session_state:
    st.session_state.result_path = None
if "result_text" not in st.session_state:
    st.session_state.result_text = None
if "source_preview" not in st.session_state:
    st.session_state.source_preview = None
if "batch_report" not in st.session_state:
    st.session_state.batch_report = None


def L(key: str, **kwargs) -> str:
    return t(key, st.session_state.ui_lang, **kwargs)


st.set_page_config(
    page_title="Smart File Translation",
    page_icon="📄",
    layout="wide",
)

with st.sidebar:
    st.header(L("sidebar.section_settings"))

    langs = available_languages()
    lang_labels = {code: language_display_name(code, st.session_state.ui_lang) for code in langs}
    current = st.session_state.ui_lang if st.session_state.ui_lang in langs else DEFAULT_LANG
    idx = langs.index(current) if current in langs else 0
    chosen = st.selectbox(
        L("sidebar.language"),
        options=langs,
        index=idx,
        format_func=lambda c: lang_labels.get(c, c),
        key="ui_lang_select",
    )
    if chosen != st.session_state.ui_lang:
        st.session_state.ui_lang = chosen
        st.rerun()

    available = list_available_providers()
    if available:
        st.caption(L("sidebar.keys_status", providers=", ".join(available)))
    else:
        st.warning(L("sidebar.no_key_hint"))

    st.subheader(L("sidebar.connect_how"))
    st.caption(L("sidebar.connect_official_only"))
    st.caption(L("sidebar.connect_no_websites"))

    for label, env_name in (
        ("OpenAI Platform", "OPENAI_API_KEY"),
        ("Anthropic Console", "ANTHROPIC_API_KEY"),
        ("Gemini API", "GEMINI_API_KEY"),
    ):
        val = load_secret(env_name)
        if val:
            st.caption(f"{label}: {mask_secret(val)}")
        else:
            st.caption(f"{label}: {L('sidebar.not_connected')}")

    with st.expander(L("sidebar.save_key_title"), expanded=False):
        save_which = st.selectbox(
            L("sidebar.save_key_which"),
            options=["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"],
        )
        new_key = st.text_input(L("sidebar.save_key_value"), type="password")
        if st.button(L("sidebar.save_key_btn")) and new_key.strip():
            save_secret_to_env(save_which, new_key.strip())
            st.success(L("sidebar.save_key_ok"))
            st.rerun()

    custom_base = st.text_input(L("sidebar.custom_base"), value="")
    if st.button(L("sidebar.save_base_btn")) and custom_base.strip():
        try:
            checked = assert_public_https_url(custom_base.strip())
            save_secret_to_env("OPENAI_BASE_URL", checked)
            st.success(L("sidebar.save_base_ok"))
        except HostNotAllowed as e:
            st.error(redact_secrets(str(e)))

    st.caption(L("sidebar.oauth_note"))

    provider_options = ["auto", "openai", "anthropic", "gemini"]
    provider_labels = {
        "auto": L("sidebar.provider_auto"),
        "openai": L("sidebar.provider_openai"),
        "anthropic": L("sidebar.provider_anthropic"),
        "gemini": L("sidebar.provider_gemini"),
    }
    p_idx = provider_options.index(st.session_state.provider) if st.session_state.provider in provider_options else 0
    st.session_state.provider = st.selectbox(
        L("sidebar.provider"),
        options=provider_options,
        index=p_idx,
        format_func=lambda x: provider_labels.get(x, x),
    )

    target_codes = [
        "zh-Hant", "zh-Hans", "en", "ja", "ko", "es", "fr", "de", "pt", "vi", "th", "id", "other"
    ]
    target_labels = {c: L(f"target.{c}") for c in target_codes if c != "other"}
    target_labels["other"] = L("target.other")
    target_choice = st.selectbox(
        L("sidebar.target_lang"),
        options=target_codes,
        index=0,
        format_func=lambda c: target_labels.get(c, c),
    )
    if target_choice == "other":
        target_lang = st.text_input(L("sidebar.target_other"), value="en")
    else:
        target_lang = target_choice

    source_options = ["auto"] + [c for c in target_codes if c != "other"]
    source_labels = {"auto": L("sidebar.source_auto"), **{c: L(f"target.{c}") for c in target_codes if c != "other"}}
    source_choice = st.selectbox(
        L("sidebar.source_lang"),
        options=source_options,
        index=0,
        format_func=lambda c: source_labels.get(c, c),
    )
    source_lang = None if source_choice == "auto" else source_choice

    st.divider()
    st.subheader(L("glossary.title"))

    projects = list_projects()
    if "default" not in projects:
        ensure_project("default")
        projects = list_projects()

    col_p1, col_p2 = st.columns([2, 1])
    with col_p1:
        if projects:
            p_idx = projects.index(st.session_state.project) if st.session_state.project in projects else 0
            selected_project = st.selectbox(L("sidebar.project"), options=projects, index=p_idx)
            if selected_project != st.session_state.project:
                st.session_state.project = selected_project
                st.session_state.glossary_pairs = load_glossary(selected_project)
                st.rerun()
    with col_p2:
        new_name = st.text_input(L("sidebar.new_project"), label_visibility="collapsed", placeholder="name")
        if st.button(L("sidebar.create_project")) and new_name.strip():
            ensure_project(new_name.strip())
            st.session_state.project = new_name.strip()
            st.session_state.glossary_pairs = []
            st.rerun()

    pairs = st.session_state.glossary_pairs
    if not pairs:
        st.caption(L("glossary.empty"))

    edited = []
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

    if st.button(L("sidebar.add_term")):
        pairs.append(("", ""))
        st.session_state.glossary_pairs = pairs
        st.rerun()

    if st.button(L("sidebar.save_glossary")):
        save_glossary(st.session_state.project, edited)
        st.session_state.glossary_pairs = edited
        st.success(L("glossary.saved", name=st.session_state.project))

st.title(L("app.title"))
st.caption(L("app.subtitle"))

# Local overlay only — the browser never talks to GitHub.
if st.button(L("update.button")):
    script = Path(__file__).resolve().parent / "scripts" / "sfts_overlay.py"
    try:
        proc = subprocess.run(
            [sys.executable, str(script), "--apply"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).resolve().parent),
            check=False,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        if "STATUS=UPDATED" in out:
            st.warning(L("update.reopen"))
        elif "STATUS=UP_TO_DATE" in out:
            st.info(L("update.up_to_date"))
        else:
            st.info(L("update.failed"))
    except Exception:
        st.info(L("update.failed"))

source_type = st.radio(
    L("main.source_type"),
    options=["file", "folder", "zip"],
    format_func=lambda x: {
        "file": L("main.source_file"),
        "folder": L("main.source_folder"),
        "zip": L("main.source_zip"),
    }[x],
    horizontal=True,
)
content_mode = st.radio(
    L("main.content_mode"),
    options=["document", "game"],
    format_func=lambda x: {
        "document": L("main.mode_document"),
        "game": L("main.mode_game"),
    }[x],
    horizontal=True,
)
game_mode = content_mode == "game"

status_placeholder = st.empty()
translate_kw = dict(
    target_lang=target_lang,
    source_lang=source_lang,
    project=st.session_state.project,
    provider_choice=st.session_state.provider,
    game_mode=game_mode,
)


def _need_key() -> bool:
    if list_available_providers():
        return False
    status_placeholder.error(L("main.status_no_key"))
    return True


if source_type == "file":
    uploaded = st.file_uploader(L("main.upload"), type=UPLOAD_TYPES)
    preview_col1, preview_col2 = st.columns(2)
    if uploaded is None:
        status_placeholder.info(L("main.status_ready"))
    else:
        suffix = Path(uploaded.name).suffix.lower()
        if suffix == ".zip":
            status_placeholder.info(L("main.zip_use_zip_mode"))
        elif not is_supported(uploaded.name) and suffix not in SCRIPT_SUFFIXES:
            status_placeholder.error(L("error.unsupported_format"))
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.getvalue())
                tmp_path = Path(tmp.name)
            try:
                preview = tmp_path.read_text(encoding="utf-8", errors="replace")[:4000]
            except Exception:
                preview = L("main.binary_preview")
            st.session_state.source_preview = preview
            with preview_col1:
                st.subheader(L("main.preview_src"))
                st.text_area("src", value=preview, height=240, label_visibility="collapsed")
            if st.button(L("main.translate_btn"), type="primary"):
                if not _need_key():
                    status_placeholder.info(L("main.status_translating"))
                    try:
                        out_name = Path(uploaded.name).stem + f".{target_lang}" + suffix
                        out_path = outputs_dir() / out_name
                        translate_single_file(tmp_path, out_path, **translate_kw)
                        st.session_state.result_path = str(out_path)
                        if out_path.suffix.lower() not in {".docx", ".pdf", ".xlsx"}:
                            st.session_state.result_text = out_path.read_text(encoding="utf-8", errors="replace")
                        else:
                            st.session_state.result_text = L("main.saved_binary")
                        status_placeholder.success(L("main.status_done"))
                    except TranslationError as e:
                        status_placeholder.error(L("main.status_error", msg=redact_secrets(str(e))))
                    except Exception as e:
                        status_placeholder.error(L("main.status_error", msg=redact_secrets(str(e))))
            if st.session_state.result_text:
                with preview_col2:
                    st.subheader(L("main.preview_out"))
                    st.text_area(
                        "out",
                        value=st.session_state.result_text[:4000],
                        height=240,
                        label_visibility="collapsed",
                    )
                if st.session_state.result_path and Path(st.session_state.result_path).is_file():
                    data = Path(st.session_state.result_path).read_bytes()
                    st.download_button(
                        L("main.download"),
                        data=data,
                        file_name=Path(st.session_state.result_path).name,
                        mime="application/octet-stream",
                    )

elif source_type == "folder":
    st.caption(L("main.folder_hint"))
    folder_path = st.text_input(L("main.folder_path"), value="")
    if st.button(L("main.translate_btn"), type="primary"):
        root = Path(folder_path).expanduser()
        if not folder_path.strip() or not root.is_dir():
            status_placeholder.error(L("main.folder_missing"))
        elif not _need_key():
            status_placeholder.info(L("main.status_translating"))
            try:
                report = translate_tree(root, job_name=root.name, **translate_kw)
                st.session_state.batch_report = report
                status_placeholder.success(
                    L("main.batch_done", n=len(report.written), k=len(report.skipped))
                )
            except TranslationError as e:
                status_placeholder.error(L("main.status_error", msg=redact_secrets(str(e))))
            except Exception as e:
                status_placeholder.error(L("main.status_error", msg=redact_secrets(str(e))))

else:
    zipped = st.file_uploader(L("main.zip_upload"), type=["zip"])
    if zipped is None:
        status_placeholder.info(L("main.status_ready_zip"))
    elif st.button(L("main.translate_btn"), type="primary"):
        if not _need_key():
            status_placeholder.info(L("main.status_translating"))
            try:
                with tempfile.TemporaryDirectory(prefix="sfts_zip_") as tmp:
                    zpath = Path(tmp) / "upload.zip"
                    zpath.write_bytes(zipped.getvalue())
                    extract_to = Path(tmp) / "tree"
                    report = translate_zip(
                        zpath,
                        extract_to,
                        job_name=Path(zipped.name).stem,
                        **translate_kw,
                    )
                    st.session_state.batch_report = report
                    status_placeholder.success(
                        L("main.batch_done", n=len(report.written), k=len(report.skipped))
                    )
            except TranslationError as e:
                status_placeholder.error(L("main.status_error", msg=redact_secrets(str(e))))
            except Exception as e:
                status_placeholder.error(L("main.status_error", msg=redact_secrets(str(e))))

report = st.session_state.batch_report
if report is not None:
    if report.written:
        st.subheader(L("main.done_list"))
        for item in report.written:
            st.write(f"{item.rel} → {item.out}")
    if report.skipped:
        st.subheader(L("main.skip_list"))
        for item in report.skipped:
            why = item.skipped or item.error
            st.write(f"{item.rel} — {redact_secrets(why)}")

st.divider()
st.caption(L("about.footer"))
