"""Optional LLM distiller (Onda 3, item 7).

Local-first: defaults to Ollama on localhost. Only used when explicitly
configured (`llm = "ollama"` or `"auto"` in cortex.toml); never a network
call in the default heuristic mode. Any failure falls back to heuristics
(PRD §42) — this module returns None instead of raising.
"""

from __future__ import annotations

import json
import re
import urllib.request
from typing import Any

from cortex.distillation.extractors import Candidate

SYSTEM_PROMPT = """\
You are a distillation engine for engineering knowledge.
From the coding-agent session transcript, extract knowledge artifacts as JSON.
Respond with a JSON array (possibly empty). Each item:
{"type": "intention" | "adr" | "fix" | "negative_knowledge",
 "statement": "<one-sentence summary, imperative>",
 "details": {"motivation"? , "context"?, "decision"?, "alternatives_rejected"? ,
             "symptom"?, "root_cause"?, "resolution"?},
 "scope": ["<file path prefix from the events>"]}
Rules: only extract what the transcript actually supports; never invent
decisions (ADR items must reflect a decision actually taken); prefer fewer,
well-evidenced items."""


class OllamaDistiller:
    def __init__(self, url: str = "http://localhost:11434",
                 model: str = "qwen2.5:7b", timeout: float = 30.0):
        self.url = url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def available(self) -> bool:
        try:
            req = urllib.request.Request(self.url + "/api/tags", method="GET")
            urllib.request.urlopen(req, timeout=2.0)
            return True
        except Exception:
            return False

    def extract(self, events: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
        """Return raw candidate dicts, or None on any failure (caller falls
        back to heuristics)."""
        transcript = "\n".join(
            f"[{e['type']}] {(e.get('content') or '').strip()}"
            + (f" files={e['files']}" if e.get("files") else "")
            for e in events if (e.get("content") or "").strip()
        )[:8000]
        if not transcript:
            return []
        body = json.dumps({
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": transcript},
            ],
        }).encode()
        try:
            req = urllib.request.Request(
                self.url + "/api/chat", data=body,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read())
            content = (data.get("message") or {}).get("content", "")
            parsed = json.loads(content)
            items = parsed if isinstance(parsed, list) else parsed.get("candidates", [])
            return [i for i in items if isinstance(i, dict) and i.get("statement")]
        except Exception:
            return None


VALID_TYPES = {"intention", "adr", "fix", "negative_knowledge"}


def llm_candidates(raw: list[dict[str, Any]] | None, events: list[dict[str, Any]]) -> list[Candidate]:
    """Convert LLM output into Candidates. LLM inference sits at the bottom of
    the inference hierarchy (PRD §8.3) — source=llm_inference, lower priority
    than any explicit statement, and deduplicated against heuristics later."""
    if not raw:
        return []
    from cortex.knowledge.models import ArtifactType
    event_ids = [e["id"] for e in events][:10]
    out: list[Candidate] = []
    for item in raw:
        etype_name = str(item.get("type", "")).lower()
        if etype_name not in VALID_TYPES:
            continue
        details = item.get("details") or {}
        scope = [str(s) for s in (item.get("scope") or [])][:5]
        out.append(Candidate(
            etype=ArtifactType(etype_name),
            statement=re.sub(r"\s+", " ", str(item["statement"]))[:200],
            details={k: v for k, v in details.items() if isinstance(v, (str, list))},
            scope=scope,
            source="llm_inference",
            session_id=events[0].get("session_id") if events else None,
            event_ids=event_ids,
            files=scope,
        ))
    return out
