"""Optional LLM distiller (Onda 3, item 7).

Local-first: defaults to Ollama on localhost. Only used when explicitly
configured (`llm = "ollama"` or `"auto"` in cortex.toml); never a network
call in the default heuristic mode. Any failure falls back to heuristics
(PRD §42) — this module returns None instead of raising.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.request
from typing import Any

from cortex.distillation.extractors import Candidate

_log = logging.getLogger("cortex.llm")

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

    def _openai_client(self):
        """Build an OpenAI-compatible client for Ollama lazily."""
        from openai import OpenAI

        base_url = self.url if self.url.endswith("/v1") else self.url + "/v1"
        return OpenAI(api_key="ollama", base_url=base_url, timeout=self.timeout)

    def available(self) -> bool:
        try:
            client = self._openai_client()
            client.models.list()
            return True
        except Exception:
            try:
                req = urllib.request.Request(self.url + "/api/tags", method="GET")
                urllib.request.urlopen(req, timeout=2.0)
                return True
            except Exception:
                _log.info("ollama unavailable at %s", self.url)
                return False
        except Exception:
            _log.info("ollama unavailable at %s", self.url)
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
            return self._extract_openai(transcript)
        except ImportError:
            pass
        except Exception:
            _log.info("OpenAI-compatible Ollama client failed; trying urllib fallback", exc_info=True)

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
            _log.warning("ollama extract failed (model=%s)", self.model, exc_info=True)
            return None

    def _extract_openai(self, transcript: str) -> list[dict[str, Any]]:
        client = self._openai_client()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ]
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,
                response_format={"type": "json_object"},
            )
        except TypeError:
            # Older Ollama OpenAI-compatible servers do not accept
            # response_format; the prompt still requires JSON.
            response = client.chat.completions.create(
                model=self.model, messages=messages, temperature=0
            )
        content = response.choices[0].message.content or ""
        parsed = json.loads(content)
        items = parsed if isinstance(parsed, list) else parsed.get("candidates", [])
        return [item for item in items if isinstance(item, dict) and item.get("statement")]


VALID_TYPES = {"intention", "adr", "fix", "negative_knowledge"}


def llm_candidates(raw: list[dict[str, Any]] | None, events: list[dict[str, Any]]) -> list[Candidate]:
    """Convert LLM output into Candidates. LLM inference sits at the bottom of
    the inference hierarchy (PRD §8.3) — source=llm_inference, lower priority
    than any explicit statement, and deduplicated against heuristics later."""
    if not raw:
        return []
    from cortex.knowledge.models import ArtifactType
    valid_ids = {e["id"] for e in events if e.get("id")}
    out: list[Candidate] = []
    for item in raw:
        etype_name = str(item.get("type", "")).lower()
        if etype_name not in VALID_TYPES:
            continue
        details = item.get("details") or {}
        scope = [str(s) for s in (item.get("scope") or [])][:5]
        # Honest provenance (PRD: provenance-first): an LLM candidate only
        # carries event ids it explicitly and validly references — never the
        # first N events of the transcript wholesale.
        raw_refs = item.get("event_ids")
        item_ids = ([i for i in raw_refs if i in valid_ids][:5]
                    if isinstance(raw_refs, list) else [])
        out.append(Candidate(
            etype=ArtifactType(etype_name),
            statement=re.sub(r"\s+", " ", str(item["statement"]))[:200],
            details={k: v for k, v in details.items() if isinstance(v, (str, list))},
            scope=scope,
            source="llm_inference",
            session_id=events[0].get("session_id") if events else None,
            event_ids=item_ids,
            files=scope,
        ))
    return out
