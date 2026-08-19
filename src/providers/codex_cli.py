"""Official local Codex CLI only. Never ChatGPT web, never tokens, never downloads."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..security.secrets import redact_secrets
from .base import BaseProvider, TranslationError

INSTALL_HINT = "https://developers.openai.com/codex/cli"
_BANNED_FLAGS = (
    "--full-auto",
    "--yolo",
    "--dangerously-bypass-approvals-and-sandbox",
    "danger-full-access",
    "workspace-write",
)
_CODEX_NAMES = {"codex", "codex.exe"}


@dataclass(frozen=True)
class CodexCLIStatus:
    present: bool
    usable: bool
    binary: str | None
    hint: str


def codex_cli_path_setting() -> str:
    return (os.getenv("CODEX_CLI_PATH") or "").strip()


def resolve_codex_binary(user_path: str | None = None) -> Path | None:
    raw = (user_path if user_path is not None else codex_cli_path_setting()).strip()
    if raw:
        path = Path(raw).expanduser()
        if not path.is_file() or path.name.lower() not in _CODEX_NAMES:
            return None
        return path.resolve()
    found = shutil.which("codex")
    if not found:
        return None
    path = Path(found)
    if path.name.lower() not in _CODEX_NAMES:
        return None
    return path.resolve()


def _empty_temp_dir():
    return tempfile.TemporaryDirectory(prefix="sfts_codex_cd_")


def _run_codex(argv: list[str], *, cwd: Path, timeout: float, stdin_text: str | None = None):
    joined = " ".join(argv)
    for flag in _BANNED_FLAGS:
        if flag in argv or flag in joined:
            raise TranslationError("Refusing a Codex CLI flag that widens the sandbox.", "codex_cli")
    return subprocess.run(
        argv,
        cwd=str(cwd),
        env=os.environ.copy(),
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        shell=False,
    )


def _help_text(binary: Path, cwd: Path) -> str:
    try:
        proc = _run_codex([str(binary), "exec", "--help"], cwd=cwd, timeout=8)
    except (OSError, subprocess.TimeoutExpired, TranslationError):
        return ""
    return f"{proc.stdout or ''}\n{proc.stderr or ''}"


def supported_flags(help_text: str) -> set[str]:
    found: set[str] = set()
    for token in (
        "--sandbox",
        "--cd",
        "--model",
        "-m",
        "--skip-git-repo-check",
        "--output-last-message",
        "--ask-for-approval",
        "--ephemeral",
    ):
        if token in help_text:
            found.add(token)
    return found


def build_exec_argv(binary: Path, cwd: Path, flags: set[str], model: str | None = None) -> list[str]:
    argv = [str(binary), "exec", "--sandbox", "read-only", "--cd", str(cwd)]
    if "--ask-for-approval" in flags:
        argv.extend(["--ask-for-approval", "never"])
    if "--skip-git-repo-check" in flags:
        argv.append("--skip-git-repo-check")
    if "--ephemeral" in flags:
        argv.append("--ephemeral")
    if model and ("--model" in flags or "-m" in flags):
        argv.extend(["-m", model])
    argv.append("-")
    joined = " ".join(argv)
    for banned in _BANNED_FLAGS:
        if banned in argv or banned in joined:
            raise TranslationError("Refusing a Codex CLI flag that widens the sandbox.", "codex_cli")
    if "--sandbox" not in argv or "read-only" not in argv:
        raise TranslationError("Codex CLI translation requires --sandbox read-only.", "codex_cli")
    return argv


def _looks_like_login_error(text: str) -> bool:
    low = (text or "").lower()
    return any(
        n in low
        for n in (
            "codex login",
            "not logged in",
            "not authenticated",
            "unauthenticated",
            "please log in",
            "please login",
            "sign in",
        )
    )


def _auth_error() -> TranslationError:
    return TranslationError(
        "The official Codex CLI is not logged in on this machine. "
        f"Install it yourself from {INSTALL_HINT} if needed, run `codex login` "
        "in your own terminal, then try again. This app does not open a browser "
        "and does not log in for you.",
        "codex_cli",
    )


def _missing_error() -> TranslationError:
    return TranslationError(
        "The official Codex CLI was not found on PATH. "
        f"Install it yourself from {INSTALL_HINT}, then run `codex login` "
        "in your own terminal. This app does not download the CLI.",
        "codex_cli",
    )


def probe_codex_cli(user_path: str | None = None) -> CodexCLIStatus:
    binary = resolve_codex_binary(user_path)
    if binary is None:
        return CodexCLIStatus(False, False, None, f"install:{INSTALL_HINT}")
    with _empty_temp_dir() as tmp:
        cwd = Path(tmp)
        try:
            proc = _run_codex([str(binary), "login", "status"], cwd=cwd, timeout=8)
        except (OSError, subprocess.TimeoutExpired, TranslationError):
            return CodexCLIStatus(True, False, str(binary), "login")
        blob = f"{proc.stdout or ''}\n{proc.stderr or ''}"
        if proc.returncode != 0 or _looks_like_login_error(blob):
            return CodexCLIStatus(True, False, str(binary), "login")
    return CodexCLIStatus(True, True, str(binary), "")


class CodexCLIProvider(BaseProvider):
    name = "codex_cli"

    def __init__(self, model: str | None = None) -> None:
        self.model = (model or "").strip() or None

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        glossary_block: str = "",
    ) -> str:
        binary = resolve_codex_binary()
        if binary is None:
            raise _missing_error()
        src = source_lang or "auto-detected"
        prompt = (
            "You are a professional localization translator. "
            "Translate the user's text accurately into the target language. "
            "Preserve markdown, code blocks, numbers, URLs, and formatting. "
            "Do not add explanations or notes. Output only the translation.\n"
        )
        if glossary_block:
            prompt += "\n" + glossary_block + "\n"
        prompt += f"\nSource language: {src}\nTarget language: {target_lang}\n\nText to translate:\n{text}"

        with _empty_temp_dir() as tmp:
            cwd = Path(tmp)
            app_root = Path(__file__).resolve().parents[2]
            if cwd.resolve() in {app_root.resolve(), Path.cwd().resolve()}:
                raise TranslationError("Refusing to run Codex CLI in the app or source tree.", "codex_cli")
            flags = supported_flags(_help_text(binary, cwd))
            if "--sandbox" not in flags and "--sandbox" not in _help_text(binary, cwd):
                # Fail closed unless the binary advertises sandbox control.
                help_blob = _help_text(binary, cwd)
                if "--sandbox" not in help_blob:
                    raise TranslationError(
                        "This codex binary cannot set --sandbox read-only. "
                        f"Install the official CLI from {INSTALL_HINT}.",
                        "codex_cli",
                    )
            argv = build_exec_argv(binary, cwd, flags, self.model)
            try:
                proc = _run_codex(argv, cwd=cwd, timeout=180, stdin_text=prompt)
            except subprocess.TimeoutExpired as e:
                raise TranslationError("Codex CLI timed out.", "codex_cli") from e
            blob = f"{proc.stdout or ''}\n{proc.stderr or ''}"
            if proc.returncode != 0 and _looks_like_login_error(blob):
                raise _auth_error()
            if proc.returncode != 0:
                raise TranslationError(
                    redact_secrets(proc.stderr or proc.stdout or "Codex CLI failed."),
                    "codex_cli",
                )
            out = (proc.stdout or "").strip()
            if not out:
                raise TranslationError("Empty response from the official Codex CLI.", "codex_cli")
            return out
