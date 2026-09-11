"""Secret redaction before persistence (PRD §25.2)."""

from __future__ import annotations

import re
from collections.abc import Iterable

PATTERNS = [
    (re.compile(r"(sk-[A-Za-z0-9_-]{4,})"), "<REDACTED_API_KEY>"),
    (re.compile(r"(sk_live_[A-Za-z0-9_]{4,})"), "<REDACTED_API_KEY>"),
    (re.compile(r"(ghp_[A-Za-z0-9]{36,})"), "<REDACTED_GITHUB_TOKEN>"),
    (re.compile(r"(gho_[A-Za-z0-9]{36,})"), "<REDACTED_GITHUB_TOKEN>"),
    (re.compile(r"(AKIA[0-9A-Z]{16})"), "<REDACTED_AWS_KEY>"),
    (re.compile(r"(?i)(api[_-]?key\s*[=:]\s*['\"]?)([A-Za-z0-9_\-\.]{16,})"), r"\1<REDACTED>"),
    (re.compile(r"(?i)(token\s*[=:]\s*['\"]?)([A-Za-z0-9_\-\.]{16,})"), r"\1<REDACTED>"),
    (re.compile(r"(?i)(password\s*[=:]\s*['\"]?)(\S{6,})"), r"\1<REDACTED>"),
    (re.compile(r"(?i)(secret\s*[=:]\s*['\"]?)([A-Za-z0-9_\-\.]{16,})"), r"\1<REDACTED>"),
    (re.compile(r"(?i)(Bearer\s+)([A-Za-z0-9_\-\.]{16,})"), r"\1<REDACTED>"),
    (re.compile(r"(-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----).*(-----END [A-Z ]*PRIVATE KEY-----)",
                re.DOTALL), "<REDACTED_PRIVATE_KEY>"),
]


# REFINAMENTO P2.4: redaction without an allowlist turns illustrative
# examples ("password=changeme" in a README snippet, "api_key=your_api_key_here"
# in a .env.example) into <REDACTED>, which silently destroys evidence that
# was never a real secret. This allowlist is intentionally narrow — only
# exact, well-known placeholder tokens are exempt. Anything that isn't an
# exact match (e.g. "SuperSecret9") is still redacted like before.
PLACEHOLDER_VALUES = {
    "changeme", "change_me", "change-me",
    "yourpassword", "your_password", "your-password", "your_password_here",
    "password123", "xxxxxxxx", "placeholder", "example", "example_key",
    "your_api_key_here", "your-api-key-here", "sua_senha_aqui",
    "senha123", "senha_aqui", "trocar", "trocar_depois", "n/a", "todo",
    "<password>", "<senha>", "<api_key>", "<token>", "<secret>",
}


def _is_placeholder(value: str) -> bool:
    return value.strip().strip("'\"<>").lower() in PLACEHOLDER_VALUES


def _detect_secrets_findings(text: str) -> Iterable[tuple[int, object]]:
    """Run detect-secrets on text when the optional extra is installed.

    The import is intentionally lazy: capture must remain usable with the
    minimal installation.  API differences between detect-secrets releases
    are contained here; any unavailable integration simply yields no findings
    and the regex fallback remains active.
    """
    try:
        from detect_secrets.core.scan import scan_line
    except Exception:
        return ()

    findings: list[tuple[int, object]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        try:
            # Current detect-secrets exposes scan_line(line); older releases
            # accepted scanner context arguments, so retain a compatible
            # fallback signature for the optional integration.
            findings.extend((line_number, finding) for finding in scan_line(line))
        except Exception:
            continue
    return findings


def _redact_detected_lines(text: str) -> str:
    """Mask complete lines flagged by detect-secrets.

    The library intentionally returns finding metadata rather than a stable
    character span across plugin versions.  Replacing the affected line is
    conservative and prevents a secret from surviving due to span drift.
    """
    if not text:
        return text
    lines = text.splitlines(keepends=True)
    if not lines:
        return text
    findings = list(_detect_secrets_findings(text))
    if not findings:
        return text
    # Finding objects expose line_number in current releases; if a mock or an
    # older release only gives truthy findings, mask every scanned line.
    line_numbers = {line_number for line_number, _finding in findings}
    return "".join(
        ("<REDACTED_SECRET>" + ("\n" if line.endswith("\n") else ""))
        if index in line_numbers else line
        for index, line in enumerate(lines, start=1)
    )


def redact(text: str | None) -> str | None:
    if not text:
        return text
    for pattern, replacement in PATTERNS:
        def _maybe_redact(m: re.Match, _pattern=pattern, _replacement=replacement) -> str:
            secret = m.group(m.lastindex) if m.lastindex else m.group(0)
            if _is_placeholder(secret):
                return m.group(0)  # leave obvious placeholders untouched
            return _pattern.sub(_replacement, m.group(0))
        text = pattern.sub(_maybe_redact, text)
    return _redact_detected_lines(text)


redact_sensitive_content = redact
