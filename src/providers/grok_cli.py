"""Official local Grok CLI only. Never grok.com, never tokens, never downloads."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..security.secrets import redact_secrets
from .base import BaseProvider, TranslationError

INSTALL_HINT = "https://x.ai/cli"
_BANNED_FLAGS = (
    "--always-approve",
    "--yolo",
    "--dangerously-skip-permissions",
    "--oauth",
)
_REQUIRED_HELP = (
    "--permission-mode",
    "--disable-web-search",
    "--no-subagents",
    "--max-turns",
    "--cwd",
)
_GROK_NAMES = {"grok", "grok.exe"}


@dataclass(frozen=True)
class GrokCLIStatus:
    present: bool
    usable: bool
    binary: str | None
    hint: str


def grok_cli_path_setting() -> str:
    return (os.getenv("GROK_CLI_PATH") or "").strip()


def resolve_grok_binary(user_path: str | None = None) -> Path | None:
    """PATH or a user-specified official `grok` binary. Never download."""
    raw = (user_path if user_path is not None else grok_cli_path_setting()).strip()
    if raw:
        path = Path(raw).expanduser()
        if not path.is_file() or path.name.lower() not in _GROK_NAMES:
            return None
        return path.resolve()
    found = shutil.which("grok")
    if not found:
        return None
    path = Path(found)
    if path.name.lower() not in _GROK_NAMES:
        return None
    return path.resolve()


def _empty_temp_dir():
    return tempfile.TemporaryDirectory(prefix="sfts_grok_cwd_")


def _run_grok(
    argv: list[str],
    *,
    cwd: Path,
    timeout: float,
    stdin_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    for flag in _BANNED_FLAGS:
        if flag in argv:
            raise TranslationError("Refusing a Grok CLI flag that auto-approves tools.", "grok_cli")
    env = os.environ.copy()
    return subprocess.run(
        argv,
        cwd=str(cwd),
        env=env,
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        shell=False,
    )


def _help_text(binary: Path, cwd: Path) -> str:
    try:
        proc = _run_grok([str(binary), "--help"], cwd=cwd, timeout=8)
    except (OSError, subprocess.TimeoutExpired, TranslationError):
        return ""
    return f"{proc.stdout or ''}\n{proc.stderr or ''}"


def supported_flags(help_text: str) -> set[str]:
    found: set[str] = set()
    for token in (
        "-p",
        "--single",
        "--output-format",
        "--no-auto-update",
        "--permission-mode",
        "--disable-web-search",
        "--no-subagents",
        "--sandbox",
        "--cwd",
        "--max-turns",
        "--no-memory",
        "--no-plan",
        "--disallowed-tools",
        "--model",
        "-m",
    ):
        if token in help_text:
            found.add(token)
    if "agent stdio" in help_text or "agent" in help_text:
        found.add("agent")
    return found


def assert_safe_help(help_text: str) -> None:
    missing = [flag for flag in _REQUIRED_HELP if flag not in help_text]
    if missing:
        raise TranslationError(
            "This grok binary is missing required isolation flags "
            f"({', '.join(missing)}). Install the official CLI from {INSTALL_HINT}.",
            "grok_cli",
        )


def build_print_argv(
    binary: Path, prompt: str, cwd: Path, flags: set[str], model: str | None = None
) -> list[str]:
    argv = [str(binary)]
    if "-p" in flags or "--single" in flags or not flags:
        argv.extend(["-p", prompt])
    else:
        raise TranslationError(
            "This grok binary cannot run headless print mode (`grok -p`).",
            "grok_cli",
        )
    if model and ("--model" in flags or "-m" in flags):
        argv.extend(["-m", model])
    if "--output-format" in flags:
        argv.extend(["--output-format", "json"])
    if "--no-auto-update" in flags:
        argv.append("--no-auto-update")
    argv.extend(["--permission-mode", "dontAsk"])
    argv.append("--disable-web-search")
    argv.append("--no-subagents")
    if "--sandbox" in flags:
        argv.extend(["--sandbox", "strict"])
    argv.extend(["--cwd", str(cwd)])
    argv.extend(["--max-turns", "1"])
    if "--no-memory" in flags:
        argv.append("--no-memory")
    if "--no-plan" in flags:
        argv.append("--no-plan")
    if "--disallowed-tools" in flags:
        argv.extend(["--disallowed-tools", "Write,Edit,Bash,WebSearch,WebFetch,Terminal"])
    for banned in _BANNED_FLAGS:
        if banned in argv:
            raise TranslationError("Refusing a Grok CLI flag that auto-approves tools.", "grok_cli")
    return argv


def build_agent_argv(
    binary: Path, cwd: Path, flags: set[str], model: str | None = None
) -> list[str]:
    argv = [str(binary)]
    if model and ("--model" in flags or "-m" in flags):
        argv.extend(["-m", model])
    if "--no-auto-update" in flags:
        argv.append("--no-auto-update")
    argv.extend(["--permission-mode", "dontAsk"])
    argv.append("--disable-web-search")
    argv.append("--no-subagents")
    if "--sandbox" in flags:
        argv.extend(["--sandbox", "strict"])
    argv.extend(["--cwd", str(cwd)])
    argv.extend(["--max-turns", "1"])
    if "--no-memory" in flags:
        argv.append("--no-memory")
    argv.extend(["agent", "stdio"])
    for banned in _BANNED_FLAGS:
        if banned in argv:
            raise TranslationError("Refusing a Grok CLI flag that auto-approves tools.", "grok_cli")
    return argv


def _looks_like_login_error(text: str) -> bool:
    low = (text or "").lower()
    needles = (
        "grok login",
        "not logged in",
        "not authenticated",
        "unauthenticated",
        "please log in",
        "please login",
        "run `grok login`",
        "cached_token",
        "sign in",
    )
    return any(n in low for n in needles)


def _auth_error() -> TranslationError:
    return TranslationError(
        "The official Grok CLI is not logged in on this machine. "
        f"Install it yourself from {INSTALL_HINT} if needed, run `grok login` "
        "in your own terminal, then try again. This app does not open a browser "
        "and does not log in for you.",
        "grok_cli",
    )


def _missing_error() -> TranslationError:
    return TranslationError(
        "The official Grok CLI was not found on PATH. "
        f"Install it yourself from {INSTALL_HINT}, then run `grok login` "
        "in your own terminal. This app does not download the CLI.",
        "grok_cli",
    )


def _extract_text(payload: object) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, list):
        parts = [_extract_text(item) for item in payload]
        return "\n".join(p for p in parts if p).strip()
    if isinstance(payload, dict):
        for key in ("result", "text", "output", "content", "message", "completion"):
            if key in payload:
                got = _extract_text(payload[key])
                if got:
                    return got
        messages = payload.get("messages")
        if isinstance(messages, list):
            texts = []
            for item in messages:
                if isinstance(item, dict) and item.get("role") in {"assistant", "model"}:
                    texts.append(_extract_text(item.get("content")))
            joined = "\n".join(t for t in texts if t).strip()
            if joined:
                return joined
    return ""


def parse_print_output(stdout: str) -> str:
    raw = (stdout or "").strip()
    if not raw:
        return ""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                payload = json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                return raw
        else:
            return raw
    return _extract_text(payload) or raw


def probe_grok_cli(user_path: str | None = None) -> GrokCLIStatus:
    binary = resolve_grok_binary(user_path)
    if binary is None:
        return GrokCLIStatus(False, False, None, f"install:{INSTALL_HINT}")
    with _empty_temp_dir() as tmp:
        cwd = Path(tmp)
        try:
            proc = _run_grok([str(binary), "version"], cwd=cwd, timeout=8)
        except (OSError, subprocess.TimeoutExpired, TranslationError):
            proc = None
        if proc is None or proc.returncode != 0:
            try:
                proc = _run_grok([str(binary), "--version"], cwd=cwd, timeout=8)
            except (OSError, subprocess.TimeoutExpired, TranslationError):
                return GrokCLIStatus(False, False, None, f"install:{INSTALL_HINT}")
        if proc.returncode != 0:
            return GrokCLIStatus(False, False, None, f"install:{INSTALL_HINT}")
        blob = f"{proc.stdout or ''}\n{proc.stderr or ''}"
        if _looks_like_login_error(blob):
            return GrokCLIStatus(True, False, str(binary), "login")
    return GrokCLIStatus(True, True, str(binary), "")


def _acp_translate(
    binary: Path, prompt: str, cwd: Path, flags: set[str], model: str | None = None
) -> str:
    argv = build_agent_argv(binary, cwd, flags, model)
    proc = subprocess.Popen(
        argv,
        cwd=str(cwd),
        env=os.environ.copy(),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False,
    )
    assert proc.stdin is not None
    assert proc.stdout is not None

    next_id = 1
    collected = []

    def send(method: str, params: dict, timeout: float) -> dict:
        nonlocal next_id
        req_id = next_id
        next_id += 1
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}) + "\n")
        proc.stdin.flush()
        deadline = timeout
        import time

        start = time.time()
        while time.time() - start < deadline:
            line = proc.stdout.readline()
            if not line:
                break
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if message.get("method") == "session/update":
                update = (message.get("params") or {}).get("update") or {}
                if update.get("sessionUpdate") == "agent_message_chunk":
                    content = update.get("content") or {}
                    text = content.get("text") if isinstance(content, dict) else ""
                    if text:
                        collected.append(str(text))
                continue
            if message.get("id") != req_id:
                continue
            if message.get("error"):
                err = message["error"]
                raise TranslationError(redact_secrets(str(err.get("message") or err)), "grok_cli")
            result = message.get("result")
            return result if isinstance(result, dict) else {}
        raise TranslationError("Grok CLI agent timed out.", "grok_cli")

    try:
        init = send(
            "initialize",
            {
                "protocolVersion": 1,
                "clientCapabilities": {
                    "fs": {"readTextFile": False, "writeTextFile": False},
                    "terminal": False,
                },
            },
            20,
        )
        methods = {str(item.get("id")) for item in (init.get("authMethods") or []) if isinstance(item, dict)}
        if "cached_token" not in methods:
            raise _auth_error()
        send("authenticate", {"methodId": "cached_token", "_meta": {"headless": True}}, 20)
        session = send("session/new", {"cwd": str(cwd), "mcpServers": []}, 20)
        session_id = session.get("sessionId")
        if not session_id:
            raise TranslationError("Grok CLI did not open a session.", "grok_cli")
        send(
            "session/prompt",
            {"sessionId": session_id, "prompt": [{"type": "text", "text": prompt}]},
            180,
        )
        text = "".join(collected).strip()
        if not text:
            raise TranslationError("Empty response from the official Grok CLI.", "grok_cli")
        return text
    except TranslationError:
        raise
    except Exception as e:
        err_blob = ""
        try:
            if proc.stderr:
                err_blob = proc.stderr.read()
        except Exception:
            err_blob = ""
        if _looks_like_login_error(err_blob + str(e)):
            raise _auth_error() from e
        raise TranslationError(redact_secrets(str(e)), "grok_cli") from e
    finally:
        try:
            proc.kill()
        except Exception:
            pass


class GrokCLIProvider(BaseProvider):
    name = "grok_cli"

    def __init__(self, model: str | None = None) -> None:
        self.model = (model or "").strip() or None

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        glossary_block: str = "",
    ) -> str:
        binary = resolve_grok_binary()
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
            if cwd.resolve() == app_root.resolve() or cwd.resolve() == Path.cwd().resolve():
                raise TranslationError("Refusing to run Grok CLI in the app or source tree.", "grok_cli")
            help_text = _help_text(binary, cwd)
            assert_safe_help(help_text)
            flags = supported_flags(help_text)
            try:
                if "-p" in flags or "--single" in flags:
                    argv = build_print_argv(binary, prompt, cwd, flags, self.model)
                    proc = _run_grok(argv, cwd=cwd, timeout=180)
                    blob = f"{proc.stdout or ''}\n{proc.stderr or ''}"
                    if proc.returncode != 0 and _looks_like_login_error(blob):
                        raise _auth_error()
                    if proc.returncode != 0:
                        if "agent" in flags:
                            return _acp_translate(binary, prompt, cwd, flags, self.model)
                        raise TranslationError(
                            redact_secrets(proc.stderr or proc.stdout or "Grok CLI failed."),
                            "grok_cli",
                        )
                    out = parse_print_output(proc.stdout or "")
                    if out:
                        return out
                    if "agent" in flags:
                        return _acp_translate(binary, prompt, cwd, flags, self.model)
                    raise TranslationError("Empty response from the official Grok CLI.", "grok_cli")
                if "agent" in flags:
                    return _acp_translate(binary, prompt, cwd, flags, self.model)
                raise TranslationError(
                    "This grok binary supports neither `grok -p` nor `grok agent stdio`.",
                    "grok_cli",
                )
            except subprocess.TimeoutExpired as e:
                raise TranslationError("Grok CLI timed out.", "grok_cli") from e
