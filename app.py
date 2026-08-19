#!/usr/bin/env python3
"""
Smart File Translation — local Streamlit UI.
Run: streamlit run app.py
"""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

import streamlit as st

from src.config import list_available_providers, outputs_dir, get_default_provider
from src.i18n import t, available_languages, DEFAULT_LANG, language_display_name
from src.glossary import list_projects, ensure_project, load_glossary, save_glossary
from src.extractors import extract_text, write_translated, is_supported
from src.translator import translate_document
from src.providers.base import TranslationError

# ---------------------------------------------------------------------------
# Session defaults
# ---------------------------------------------------------------------------
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


def L(key: str, **kwargs) -> str:
    return t(key, st.session_state.ui_lang, **kwargs)


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Smart File Translation",
    page_icon="📄",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header(L("sidebar.section_settings"))

    langs = available_languages()
    lang_labels = {code: language_display_name(code, st.session_state.ui_lang) for code in langs}
    # Keep current selection if possible
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

    provider_options = ["auto", "openai", "anthropic"]
    provider_labels = {
        "auto": L("sidebar.provider_auto"),
        "openai": L("sidebar.provider_openai"),
        "anthropic": L("sidebar.provider_anthropic"),
    }
    p_idx = provider_options.index(st.session_state.provider) if st.session_state.provider in provider_options else 0
    st.session_state.provider = st.selectbox(
        L("sidebar.provider"),
        options=provider_options,
        index=p_idx,
        format_func=lambda x: provider_labels.get(x, x),
    )

    # Target language
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
        target_lang = st.text_input("Target language code / name", value="en")
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

    # Project selector + create
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

    # Editable glossary
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

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.title(L("app.title"))
st.caption(L("app.subtitle"))

uploaded = st.file_uploader(
    L("main.upload"),
    type=["txt", "md", "markdown", "docx", "pdf"],
)

status_placeholder = st.empty()
preview_col1, preview_col2 = st.columns(2)

if uploaded is None:
    status_placeholder.info(L("main.status_ready"))
else:
    if not is_supported(uploaded.name):
        status_placeholder.error(L("error.unsupported_format"))
    else:
        # Save upload to temp for extractors that need a path
        suffix = Path(uploaded.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = Path(tmp.name)

        try:
            source_text = extract_text(tmp_path)
        except Exception as e:
            status_placeholder.error(L("error.extract_failed", detail=str(e)))
            source_text = None

        if source_text is not None:
            if not source_text.strip():
                status_placeholder.error(L("error.empty_file"))
            else:
                st.session_state.source_preview = source_text[:4000] + ("…" if len(source_text) > 4000 else "")
                with preview_col1:
                    st.subheader(L("main.preview_src"))
                    st.text_area("src", value=st.session_state.source_preview, height=240, label_visibility="collapsed")

                if st.button(L("main.translate_btn"), type="primary"):
                    if not list_available_providers():
                        status_placeholder.error(L("main.status_no_key"))
                    else:
                        status_placeholder.info(L("main.status_translating"))
                        try:
                            translated, n_chunks = translate_document(
                                text=source_text,
                                target_lang=target_lang,
                                source_lang=source_lang,
                                project=st.session_state.project,
                                provider_choice=st.session_state.provider,
                            )
                            # Write output
                            out_name = Path(uploaded.name).stem + f".{target_lang}" + suffix
                            if suffix.lower() == ".pdf":
                                # keep pdf
                                pass
                            out_path = outputs_dir() / out_name
                            write_translated(tmp_path, translated, out_path)
                            st.session_state.result_path = str(out_path)
                            st.session_state.result_text = translated
                            status_placeholder.success(
                                L("main.status_done") + " " + L("main.chunk_info", n=n_chunks)
                            )
                        except TranslationError as e:
                            status_placeholder.error(L("main.status_error", msg=str(e)))
                        except Exception as e:
                            status_placeholder.error(L("main.status_error", msg=str(e)))

                if st.session_state.result_text:
                    with preview_col2:
                        st.subheader(L("main.preview_out"))
                        preview = st.session_state.result_text[:4000] + (
                            "…" if len(st.session_state.result_text) > 4000 else ""
                        )
                        st.text_area("out", value=preview, height=240, label_visibility="collapsed")

                    if st.session_state.result_path and Path(st.session_state.result_path).is_file():
                        data = Path(st.session_state.result_path).read_bytes()
                        st.download_button(
                            L("main.download"),
                            data=data,
                            file_name=Path(st.session_state.result_path).name,
                            mime="application/octet-stream",
                        )

st.divider()
st.caption(L("about.footer"))
