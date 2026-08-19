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
from src.security.secrets import load_secret, mask_secret, redact_secrets
from src.theme import css_for

UPLOAD_TYPES = sorted({s.lstrip(".") for s in SUPPORTED_SUFFIXES} | {"zip", "markdown", "htm"})
TARGET_CODES = [
    "zh-Hant", "zh-Hans", "en", "ja", "ko", "es", "fr", "de", "pt", "vi", "th", "id", "other",
]
PROVIDER_OPTIONS = ["auto", "openai", "anthropic", "gemini"]


def _init_state() -> None:
    defaults = {
        "ui_lang": DEFAULT_LANG,
        "theme": "light",
        "page": "translate",
        "provider": get_default_provider(),
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
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)
_qp = st.query_params
if _qp.get("page") in {"translate", "settings"}:
    st.session_state.page = str(_qp.get("page"))
if _qp.get("theme") in {"light", "dark"}:
    st.session_state.theme = str(_qp.get("theme"))
st.markdown(css_for(st.session_state.theme), unsafe_allow_html=True)


def _target_lang() -> str:
    choice = st.session_state.target_lang
    return choice if choice != "other" else st.session_state.get("target_other", "en")


def _source_lang() -> str | None:
    choice = st.session_state.source_choice
    return None if choice == "auto" else choice


def render_topbar() -> None:
    left, mid, right = st.columns([2.2, 2.2, 1.4])
    with left:
        st.markdown(f'<div class="sfts-brand">{L("app.title")}</div>', unsafe_allow_html=True)
    with mid:
        n1, n2 = st.columns(2)
        with n1:
            if st.button(L("nav.translate"), type="primary" if st.session_state.page == "translate" else "secondary", use_container_width=True):
                st.session_state.page = "translate"
                st.rerun()
        with n2:
            if st.button(L("nav.settings"), type="primary" if st.session_state.page == "settings" else "secondary", use_container_width=True):
                st.session_state.page = "settings"
                st.rerun()
    with right:
        if st.session_state.page == "translate":
            theme_label = "☾" if st.session_state.theme == "light" else "☀"
            if st.button(theme_label, use_container_width=True):
                st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
                st.rerun()


def render_settings() -> None:
    top, bot = st.columns(2)
    langs = available_languages()
    lang_labels = {code: language_display_name(code, st.session_state.ui_lang) for code in langs}

    with top:
        with st.container(border=True):
            st.markdown(f"### {L('card.appearance')}")
            theme = st.radio(
                L("card.theme"),
                options=["light", "dark"],
                index=0 if st.session_state.theme == "light" else 1,
                format_func=lambda x: L("theme.light") if x == "light" else L("theme.dark"),
                horizontal=True,
                key="theme_radio",
            )
            if theme != st.session_state.theme:
                st.session_state.theme = theme
                st.rerun()
            current = st.session_state.ui_lang if st.session_state.ui_lang in langs else DEFAULT_LANG
            chosen = st.selectbox(
                L("sidebar.language"),
                options=langs,
                index=langs.index(current) if current in langs else 0,
                format_func=lambda c: lang_labels.get(c, c),
                key="ui_lang_select",
            )
            if chosen != st.session_state.ui_lang:
                st.session_state.ui_lang = chosen
                st.rerun()
            st.markdown(f'<div class="sfts-muted">{L("card.lang_count")}</div>', unsafe_allow_html=True)

        st.write("")
        with st.container(border=True):
            st.markdown(f"### {L('card.keys')}")
            for label, env_name in (
                ("OpenAI", "OPENAI_API_KEY"),
                ("Anthropic", "ANTHROPIC_API_KEY"),
                ("Gemini API", "GEMINI_API_KEY"),
            ):
                val = load_secret(env_name)
                if val:
                    st.markdown(
                        f"**{label}** &nbsp; <span class='sfts-pill-on'>✓ {L('keys.set')} · {mask_secret(val)}</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"**{label}** &nbsp; <span class='sfts-pill-off'>● {L('keys.unset')}</span>",
                        unsafe_allow_html=True,
                    )
            st.markdown(f'<div class="sfts-muted">{L("keys.local_only")}</div>', unsafe_allow_html=True)
            st.caption(L("sidebar.connect_official_only"))
            st.caption(L("sidebar.connect_no_websites"))
            st.button(L("keys.connect_sub"), disabled=True)
            st.caption(L("keys.sub_wait"))

    with bot:
        with st.container(border=True):
            st.markdown(f"### {L('card.translation')}")
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
            }
            st.selectbox(
                L("sidebar.provider"),
                options=PROVIDER_OPTIONS,
                index=PROVIDER_OPTIONS.index(st.session_state.provider) if st.session_state.provider in PROVIDER_OPTIONS else 0,
                format_func=lambda x: provider_labels.get(x, x),
                key="provider",
            )

        st.write("")
        with st.container(border=True):
            st.markdown(f"### {L('card.glossary')}")
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

        with st.container(border=True):
            st.markdown(f"### {L('update.button')}")
            if st.button(L("update.run"), type="secondary"):
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


def _need_key(status) -> bool:
    if list_available_providers():
        return False
    status.error(L("main.status_no_key"))
    return True


def render_translate() -> None:
    st.title(L("app.title"))
    st.caption(L("app.subtitle"))
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
        key="source_type",
    )
    content_mode = st.radio(
        L("main.content_mode"),
        options=["document", "game"],
        format_func=lambda x: {
            "document": L("main.mode_document"),
            "game": L("main.mode_game"),
        }[x],
        horizontal=True,
        key="content_mode",
    )
    game_mode = content_mode == "game"
    status = st.empty()
    translate_kw = dict(
        target_lang=_target_lang(),
        source_lang=_source_lang(),
        project=st.session_state.project,
        provider_choice=st.session_state.provider,
        game_mode=game_mode,
    )

    if source_type == "file":
        uploaded = st.file_uploader(L("main.upload"), type=UPLOAD_TYPES)
        if uploaded is None:
            status.info(L("main.status_ready"))
        else:
            suffix = Path(uploaded.name).suffix.lower()
            if suffix == ".zip":
                status.info(L("main.zip_use_zip_mode"))
            elif not is_supported(uploaded.name) and suffix not in SCRIPT_SUFFIXES:
                status.error(L("error.unsupported_format"))
            else:
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.getvalue())
                    tmp_path = Path(tmp.name)
                try:
                    preview = tmp_path.read_text(encoding="utf-8", errors="replace")[:4000]
                except Exception:
                    preview = L("main.binary_preview")
                st.session_state.source_preview = preview
                if st.button(L("main.translate_btn"), type="primary"):
                    if not _need_key(status):
                        status.info(L("main.status_translating"))
                        try:
                            out_name = Path(uploaded.name).stem + f".{_target_lang()}" + suffix
                            out_path = outputs_dir() / out_name
                            translate_single_file(tmp_path, out_path, **translate_kw)
                            st.session_state.result_path = str(out_path)
                            if out_path.suffix.lower() not in {".docx", ".pdf", ".xlsx"}:
                                st.session_state.result_text = out_path.read_text(encoding="utf-8", errors="replace")
                            else:
                                st.session_state.result_text = L("main.saved_binary")
                            status.success(L("main.status_done"))
                        except TranslationError as e:
                            status.error(L("main.status_error", msg=redact_secrets(str(e))))
                        except Exception as e:
                            status.error(L("main.status_error", msg=redact_secrets(str(e))))
        if uploaded is None:
            pass

    elif source_type == "folder":
        st.caption(L("main.folder_hint"))
        folder_path = st.text_input(L("main.folder_path"), value="")
        if st.button(L("main.translate_btn"), type="primary"):
            root = Path(folder_path).expanduser()
            if not folder_path.strip() or not root.is_dir():
                status.error(L("main.folder_missing"))
            elif not _need_key(status):
                status.info(L("main.status_translating"))
                try:
                    report = translate_tree(root, job_name=root.name, **translate_kw)
                    st.session_state.batch_report = report
                    status.success(L("main.batch_done", n=len(report.written), k=len(report.skipped)))
                except TranslationError as e:
                    status.error(L("main.status_error", msg=redact_secrets(str(e))))
                except Exception as e:
                    status.error(L("main.status_error", msg=redact_secrets(str(e))))

    else:
        zipped = st.file_uploader(L("main.zip_upload"), type=["zip"])
        if zipped is None:
            status.info(L("main.status_ready_zip"))
        elif st.button(L("main.translate_btn"), type="primary"):
            if not _need_key(status):
                status.info(L("main.status_translating"))
                try:
                    with tempfile.TemporaryDirectory(prefix="sfts_zip_") as tmp:
                        zpath = Path(tmp) / "upload.zip"
                        zpath.write_bytes(zipped.getvalue())
                        report = translate_zip(
                            zpath,
                            Path(tmp) / "tree",
                            job_name=Path(zipped.name).stem,
                            **translate_kw,
                        )
                        st.session_state.batch_report = report
                        status.success(L("main.batch_done", n=len(report.written), k=len(report.skipped)))
                except TranslationError as e:
                    status.error(L("main.status_error", msg=redact_secrets(str(e))))
                except Exception as e:
                    status.error(L("main.status_error", msg=redact_secrets(str(e))))

    if source_type == "file":
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.subheader(L("main.preview_src"))
                src = st.session_state.source_preview or L("main.preview_empty")
                st.text_area("src", value=src, height=220, label_visibility="collapsed")
        with c2:
            with st.container(border=True):
                st.subheader(L("main.preview_out"))
                out = (st.session_state.result_text or L("main.preview_empty"))[:4000]
                st.text_area("out", value=out, height=220, label_visibility="collapsed")
                if st.session_state.result_path and Path(st.session_state.result_path).is_file():
                    data = Path(st.session_state.result_path).read_bytes()
                    st.download_button(
                        L("main.download"),
                        data=data,
                        file_name=Path(st.session_state.result_path).name,
                        mime="application/octet-stream",
                    )

    report = st.session_state.batch_report
    if report is not None:
        if report.written:
            st.subheader(L("main.done_list"))
            for item in report.written:
                st.write(f"{item.rel} → {item.out}")
        if report.skipped:
            st.subheader(L("main.skip_list"))
            for item in report.skipped:
                st.write(f"{item.rel} — {redact_secrets(item.skipped or item.error)}")


render_topbar()
if st.session_state.page == "settings":
    render_settings()
else:
    render_translate()

st.markdown(f'<div class="sfts-footer">{L("about.footer")}</div>', unsafe_allow_html=True)
