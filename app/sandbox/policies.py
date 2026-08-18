"""Security and Resource Policies for Sandbox Execution."""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set

# Environment variable keys that must NEVER be passed into the execution sandbox
SENSITIVE_ENV_PREFIXES: List[str] = [
    "AWS_",
    "GITHUB_",
    "GEMINI_",
    "OPENAI_",
    "ANTHROPIC_",
    "GOOGLE_",
    "DATABASE_",
    "DB_",
    "SECRET_",
    "KEY_",
    "PASSWORD_",
    "TOKEN_",
]

SENSITIVE_EXACT_KEYS: Set[str] = {
    "PATH",
    "HOME",
    "USER",
    "SHELL",
    "API_KEY",
    "AUTH_TOKEN",
    "ACCESS_KEY",
    "SECRET_KEY",
}

# Maximum bytes to capture from command output (50 KB)
MAX_STDOUT_BYTES: int = 50_000
MAX_STDERR_BYTES: int = 50_000

# Default execution timeout
DEFAULT_TIMEOUT_SECONDS: int = 60

# Dangerous command patterns prohibited from unconstrained execution
FORBIDDEN_COMMAND_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b(shutdown|reboot|poweroff|halt)\b", re.IGNORECASE),
    re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", re.IGNORECASE),  # Fork bomb
    re.compile(r"\brm\s+-[a-zA-Z]*[rf][a-zA-Z]*\s+/(?:\s|$|\*)", re.IGNORECASE),  # Root delete (e.g. rm -rf / or rm -rf /*)
    re.compile(r"\bmkfs(\.[a-z0-9]+)?\b", re.IGNORECASE),
    re.compile(r"\bdd\s+if=.*\bof=/dev/([sh]d[a-z]|nvme)", re.IGNORECASE),
]


def sanitize_environment(
    custom_env: Dict[str, str] | None = None,
    allow_safe_system_paths: bool = True,
) -> Dict[str, str]:
    """Generate a clean, sanitized environment for sandbox execution, stripping all host credentials."""
    safe_env: Dict[str, str] = {
        "PYTHONUNBUFFERED": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }

    if allow_safe_system_paths:
        base_path = os.environ.get(
            "PATH",
            "/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin",
        )
        # Prepend the current python runtime directory (e.g. .venv/bin)
        runtime_bin = str(Path(sys.executable).parent)
        safe_env["PATH"] = f"{runtime_bin}:{base_path}"

    # Add custom variables only if they do not match sensitive prefixes/keys
    if custom_env:
        for k, v in custom_env.items():
            key_upper = k.upper()
            if any(key_upper.startswith(prefix) for prefix in SENSITIVE_ENV_PREFIXES):
                continue
            if key_upper in SENSITIVE_EXACT_KEYS and key_upper != "PATH":
                continue
            safe_env[k] = v

    return safe_env


def validate_command_safety(command: str) -> None:
    """Raise ValueError if the command contains explicitly malicious or destructive patterns."""
    for pattern in FORBIDDEN_COMMAND_PATTERNS:
        if pattern.search(command):
            raise ValueError(
                f"Execution blocked by safety policy: command matches forbidden pattern '{pattern.pattern}'"
            )


def truncate_output(output: str, max_bytes: int = MAX_STDOUT_BYTES) -> str:
    """Truncate output if it exceeds max allowed size, appending a warning indicator."""
    encoded = output.encode("utf-8", errors="replace")
    if len(encoded) <= max_bytes:
        return output

    truncated_bytes = encoded[:max_bytes]
    truncated_str = truncated_bytes.decode("utf-8", errors="ignore")
    return (
        f"{truncated_str}\n\n"
        f"[... Output truncated by Sandbox Guard: exceeded {max_bytes} bytes ...]"
    )
