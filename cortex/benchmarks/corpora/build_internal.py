"""Deterministic builder for the internal engineering-memory corpora.

The internal corpus is *not* an external dataset: it is a small, hand-written
set of software-project conversations (Portuguese, mirroring how the Cortex
extractors are calibrated) that covers every pre-registered task type.  The
builder is committed next to its output so a reviewer can verify that:

* the gold is derivable from the visible history only;
* the filler variant adds noise without touching any gold event id;
* checksums are materialised from the exact bytes that get committed.

Regenerate with::

    python -m cortex.benchmarks.corpora.build_internal

The output files are committed, so this command is part of the audit trail,
not a runtime dependency of the runner.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ..errors import SchemaError
from ..schema import instance_from_dict

REVISION = "engineering-memory-v1"
SOURCE = "internal"
DOMAIN = "software_project"

CORPORA_DIR = Path(__file__).resolve().parent
MANIFESTS_DIR = CORPORA_DIR / "manifests"
NORMALIZED_DIR = CORPORA_DIR / "normalized"
ADVERSARIAL_DIR = CORPORA_DIR / "adversarial"

FILLER_TOKEN_BUDGET = 32_000

# Deterministic filler: realistic engineering chatter with no decision,
# negation, intention, fix or error marker, and no overlap with any query.
FILLER_LINES = [
    "Revisamos o pull request #{n} e aprovamos as mudancas propostas.",
    "Lemos o arquivo src/modulo_{n}.py e organizamos os imports do pacote.",
    "Atualizamos a documentacao da release {n} com as notas da sprint.",
    "Rodamos o formatador no diretorio src/pacote_{n} e nenhuma linha mudou.",
    "Discutimos o cronograma da iteracao {n} na reuniao de sincronizacao.",
    "Registramos a reuniao da semana {n} na ata do time de plataforma.",
    "Conferimos a configuracao do ambiente de desenvolvimento {n}.",
    "Arquivamos a conversa da tarefa {n} apos o encerramento do ciclo.",
]
FILLER_TIMESTAMPS = [
    ("2026-01-0{n}T09:{m:02d}:00Z", "2026-01-0{n}T09:{m:02d}:30Z"),
    ("2026-01-1{n}T14:{m:02d}:00Z", "2026-01-1{n}T14:{m:02d}:30Z"),
]

# Each case: sessions are given in order; the last session is the cutoff
# boundary and stays empty, so every gold event is strictly pre-cutoff.
CASES: list[dict[str, Any]] = [
    {
        "id": "mem-db-postgres",
        "task_type": "exact_recall",
        "split": "dev",
        "hop": 0,
        "sessions": [
            ("s0", "2026-01-05T10:00:00Z", [
                ("user", "Vamos usar PostgreSQL para o armazenamento principal porque precisamos de transações ACID.", "2026-01-05T10:01:00Z", ["src/storage"]),
            ]),
            ("s1", "2026-01-06T10:00:00Z", [
                ("assistant", "Confirmado: o armazenamento principal continua sendo o PostgreSQL.", "2026-01-06T10:01:00Z", ["src/storage"]),
            ]),
            ("s2", "2026-01-07T00:00:00Z", []),
        ],
        "query": "qual banco usar para transações ACID",
        "gold": {"answer": "PostgreSQL", "current_entities": ["s0:0"], "invalid_entities": [],
                 "gold_evidence": ["s0:0"], "expected_abstention": False},
        "notes": "Decisão única, sem competição temporal.",
    },
    {
        "id": "mem-cache-global",
        "task_type": "exact_recall",
        "split": "dev",
        "hop": 0,
        "sessions": [
            ("s0", "2026-01-05T10:00:00Z", [
                ("user", "Não usar cache global para sessões porque gera inconsistência entre os nós.", "2026-01-05T10:01:00Z", ["src/cache"]),
            ]),
            ("s1", "2026-01-06T00:00:00Z", []),
        ],
        "query": "por que não usar cache global nas sessões",
        "gold": {"answer": "cache global", "current_entities": ["s0:0"], "invalid_entities": [],
                 "gold_evidence": ["s0:0"], "expected_abstention": False},
        "notes": "Conhecimento negativo deve ser recuperável como decisão vigente.",
    },
    {
        "id": "mem-aggregation-ci",
        "task_type": "aggregation",
        "split": "dev",
        "hop": 0,
        "sessions": [
            ("s0", "2026-01-05T10:00:00Z", [
                ("user", "Vamos usar ruff para lint no pipeline de CI.", "2026-01-05T10:01:00Z", ["ci"]),
                ("user", "Vamos usar pytest para testes no pipeline de CI.", "2026-01-05T10:02:00Z", ["ci"]),
            ]),
            ("s1", "2026-01-06T10:00:00Z", [
                ("user", "Vamos usar docker para builds no pipeline de CI.", "2026-01-06T10:01:00Z", ["ci"]),
            ]),
            ("s2", "2026-01-07T00:00:00Z", []),
        ],
        "query": "quais ferramentas vamos usar no pipeline de CI",
        "gold": {"answer": "ruff, pytest e docker", "current_entities": ["s0:0", "s0:1", "s1:0"],
                 "invalid_entities": [], "gold_evidence": ["s0:0", "s0:1", "s1:0"],
                 "expected_abstention": False},
        "notes": "Resposta exige o conjunto completo, distribuído em duas sessões.",
    },
    {
        "id": "mem-tracking-api",
        "task_type": "tracking",
        "split": "eval",
        "hop": 1,
        "sessions": [
            ("s0", "2026-01-05T10:00:00Z", [
                ("user", "Decidimos manter a API pública na versão v1 por enquanto.", "2026-01-05T10:01:00Z", ["src/api"]),
            ]),
            ("s1", "2026-01-06T10:00:00Z", [
                ("user", "Vamos migrar para a versão v2 da API pública porque precisamos de paginação.", "2026-01-06T10:01:00Z", ["src/api"]),
            ]),
            ("s2", "2026-01-07T00:00:00Z", []),
        ],
        "query": "qual a versão atual da API pública",
        "gold": {"answer": "v2", "current_entities": ["s1:0"], "invalid_entities": ["s0:0"],
                 "gold_evidence": ["s1:0"], "supersession_pairs": [["s0:0", "s1:0"]],
                 "expected_abstention": False},
        "notes": "A versão antiga continua no histórico e deve deixar de ser vigente.",
    },
    {
        "id": "mem-deletion-logs",
        "task_type": "deletion",
        "split": "eval",
        "hop": 1,
        "sessions": [
            ("s0", "2026-01-05T10:00:00Z", [
                ("user", "Vamos usar Datadog para logs, alertas, traces e on-call no ambiente de produção.", "2026-01-05T10:01:00Z", ["infra/logs"]),
            ]),
            ("s1", "2026-01-06T10:00:00Z", [
                ("user", "Vamos usar Grafana Loki para logs no ambiente de produção porque o Datadog ficou caro.", "2026-01-06T10:01:00Z", ["infra/logs"]),
                ("user", "Não usar Datadog para logs a partir desta data.", "2026-01-06T10:02:00Z", ["infra/logs"]),
            ]),
            ("s2", "2026-01-07T00:00:00Z", []),
        ],
        "query": "qual ferramenta de logs vamos usar no ambiente de produção",
        "gold": {"answer": "Grafana Loki", "current_entities": ["s1:0"], "invalid_entities": ["s0:0"],
                 "gold_evidence": ["s1:0"], "supersession_pairs": [["s0:0", "s1:0"]],
                 "expected_abstention": False},
        "notes": "O item invalidado é reforçado por conhecimento negativo explícito.",
    },
    {
        "id": "mem-cascade-auth",
        "task_type": "cascade",
        "split": "regression",
        "hop": 2,
        "sessions": [
            ("s0", "2026-01-05T10:00:00Z", [
                ("user", "Vamos usar Auth0 como provedor de autenticação do produto web e do app mobile.", "2026-01-05T10:01:00Z", ["src/auth"]),
            ]),
            ("s1", "2026-01-06T10:00:00Z", [
                ("user", "Vamos usar Keycloak como provedor de autenticação do produto porque o custo do Auth0 subiu.", "2026-01-06T10:01:00Z", ["src/auth"]),
            ]),
            ("s2", "2026-01-06T18:00:00Z", [
                ("user", "Precisamos atualizar os testes de login do provedor de autenticação.", "2026-01-06T18:01:00Z", ["src/auth"]),
            ]),
            ("s3", "2026-01-07T00:00:00Z", []),
        ],
        "query": "qual provedor de autenticação vigente",
        "gold": {"answer": "Keycloak", "current_entities": ["s1:0"], "invalid_entities": ["s0:0"],
                 "gold_evidence": ["s1:0", "s2:0"], "supersession_pairs": [["s0:0", "s1:0"]],
                 "expected_abstention": False},
        "notes": "A troca arrasta um dependente (testes de login) no hop 2.",
    },
    {
        "id": "mem-absence-provider",
        "task_type": "absence",
        "split": "eval",
        "hop": 0,
        "sessions": [
            ("s0", "2026-01-05T10:00:00Z", [
                ("user", "Vamos usar PostgreSQL para o armazenamento principal porque precisamos de transações ACID.", "2026-01-05T10:01:00Z", ["src/storage"]),
            ]),
            ("s1", "2026-01-06T00:00:00Z", []),
        ],
        "query": "qual provedor de observabilidade foi contratado",
        "gold": {"answer": None, "current_entities": [], "invalid_entities": [],
                 "gold_evidence": [], "expected_abstention": True},
        "notes": "Pergunta sem evidência no histórico: a resposta correta é abster-se.",
    },
    {
        "id": "mem-recall-tests",
        "task_type": "exact_recall",
        "split": "regression",
        "hop": 0,
        "sessions": [
            ("s0", "2026-01-05T10:00:00Z", [
                ("user", "Vamos usar pytest como executor de testes no CI.", "2026-01-05T10:01:00Z", ["tests"]),
            ]),
            ("s1", "2026-01-06T00:00:00Z", []),
        ],
        "query": "qual executor de testes o CI usa",
        "gold": {"answer": "pytest", "current_entities": ["s0:0"], "invalid_entities": [],
                 "gold_evidence": ["s0:0"], "expected_abstention": False},
        "notes": "Caso pequeno de regressão.",
    },
    {
        "id": "mem-absence-queue",
        "task_type": "absence",
        "split": "regression",
        "hop": 0,
        "sessions": [
            ("s0", "2026-01-05T10:00:00Z", [
                ("user", "Vamos usar Redis para o cache de sessões porque o acesso é frequente.", "2026-01-05T10:01:00Z", ["src/cache"]),
            ]),
            ("s1", "2026-01-06T00:00:00Z", []),
        ],
        "query": "qual broker de mensagens foi escolhido",
        "gold": {"answer": None, "current_entities": [], "invalid_entities": [],
                 "gold_evidence": [], "expected_abstention": True},
        "notes": "Histórico tem conhecimento próximo, mas não sobre o assunto pedido.",
    },
    {
        "id": "mem-tracking-version",
        "task_type": "tracking",
        "split": "regression",
        "hop": 1,
        "sessions": [
            ("s0", "2026-01-05T10:00:00Z", [
                ("user", "Vamos usar a biblioteca httpx para o cliente HTTP interno legado.", "2026-01-05T10:01:00Z", ["src/client"]),
            ]),
            ("s1", "2026-01-06T10:00:00Z", [
                ("user", "Vamos usar requests na camada de cliente HTTP interno porque o time já domina essa biblioteca.", "2026-01-06T10:01:00Z", ["src/client"]),
            ]),
            ("s2", "2026-01-07T00:00:00Z", []),
        ],
        "query": "qual biblioteca de cliente HTTP vamos usar",
        "gold": {"answer": "requests", "current_entities": ["s1:0"], "invalid_entities": ["s0:0"],
                 "gold_evidence": ["s1:0"], "supersession_pairs": [["s0:0", "s1:0"]],
                 "expected_abstention": False},
        "notes": "Troca de biblioteca no mesmo escopo.",
    },
]

ADVERSARIAL_CASES: list[dict[str, Any]] = [
    {
        "id": "adv-dedup-absorbs-update",
        "task_type": "tracking",
        "split": "regression",
        "hop": 1,
        "sessions": [
            ("s0", "2026-01-05T10:00:00Z", [
                ("user", "Vamos usar o bucket s3-artifacts para os artefatos de build.", "2026-01-05T10:01:00Z", ["infra/build"]),
            ]),
            ("s1", "2026-01-06T10:00:00Z", [
                ("user", "Vamos usar o bucket s3-artifacts-v2 para os artefatos de build.", "2026-01-06T10:01:00Z", ["infra/build"]),
            ]),
            ("s2", "2026-01-07T00:00:00Z", []),
        ],
        "query": "qual bucket guarda os artefatos de build",
        "gold": {"answer": "s3-artifacts-v2", "current_entities": ["s1:0"], "invalid_entities": ["s0:0"],
                 "gold_evidence": ["s1:0"], "supersession_pairs": [["s0:0", "s1:0"]],
                 "expected_abstention": False},
        "notes": "Sonda da lacuna conhecida: duas declarações do mesmo escopo com frases quase "
                 "idênticas são fundidas pelo dedup, que absorve a atualização de estado em vez "
                 "de preservar a linhagem. A falha deve aparecer no relatório, não ser escondida.",
    },
    {
        "id": "adv-superseded-reassert",
        "task_type": "deletion",
        "split": "regression",
        "hop": 1,
        "sessions": [
            ("s0", "2026-01-05T10:00:00Z", [
                ("user", "Vamos usar MongoDB para a fila de tarefas porque é simples de operar.", "2026-01-05T10:01:00Z", ["src/queue"]),
            ]),
            ("s1", "2026-01-06T10:00:00Z", [
                ("user", "Vamos usar RabbitMQ para a fila de tarefas porque precisamos de confirmação de entrega.", "2026-01-06T10:01:00Z", ["src/queue"]),
            ]),
            ("s2", "2026-01-07T00:00:00Z", []),
        ],
        "query": "MongoDB ainda é a fila de tarefas que devemos usar",
        "gold": {"answer": "RabbitMQ", "current_entities": ["s1:0"], "invalid_entities": ["s0:0"],
                 "gold_evidence": ["s1:0"], "supersession_pairs": [["s0:0", "s1:0"]],
                 "expected_abstention": False},
        "notes": "A pergunta tenta reafirmar o item invalidado; afirmar o MongoDB vaza estado "
                 "obsoleto, a resposta correta corrige a premissa.",
    },
    {
        "id": "adv-contradiction-open",
        "task_type": "absence",
        "split": "regression",
        "hop": 0,
        "sessions": [
            ("s0", "2026-01-05T10:00:00Z", [
                ("user", "Vamos usar SQLite para o armazenamento local do aplicativo.", "2026-01-05T10:01:00Z", ["src/local"]),
            ]),
            ("s1", "2026-01-06T10:00:00Z", [
                ("user", "Não usar SQLite para o armazenamento local do aplicativo porque não suporta escrita concorrente.", "2026-01-06T10:01:00Z", ["src/local"]),
            ]),
            ("s2", "2026-01-07T00:00:00Z", []),
        ],
        "query": "podemos seguir com o armazenamento local planejado",
        "gold": {"answer": "não", "current_entities": ["s1:0"], "invalid_entities": ["s0:0"],
                 "gold_evidence": ["s1:0"], "supersession_pairs": [["s0:0", "s1:0"]],
                 "expected_abstention": False},
        "notes": "Par contraditório sem resolução humana: afirmar o plano antigo vazia estado "
                 "obsoleto; a resposta segura recupera a negação explícita.",
    },
    {
        "id": "adv-filler-drowning",
        "task_type": "exact_recall",
        "split": "regression",
        "hop": 0,
        "sessions": [
            ("s0", "2026-01-05T10:00:00Z", [
                ("user", "Vamos usar Caddy como proxy reverso do cluster interno.", "2026-01-05T10:01:00Z", ["infra/proxy"]),
            ]),
            ("s1", "2026-01-06T10:00:00Z", []),
        ],
        "query": "qual proxy reverso o cluster interno usa",
        "gold": {"answer": "Caddy", "current_entities": ["s0:0"], "invalid_entities": [],
                 "gold_evidence": ["s0:0"], "expected_abstention": False},
        "notes": "Caso pequeno usado com a variante filler para medir degradação por ruído.",
    },
]


def _session_dicts(case: dict[str, Any], filler_sessions: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Case sessions followed by filler, with the boundary session last."""
    sessions = []
    for session_id, timestamp, events in case["sessions"]:
        sessions.append({
            "session_id": session_id,
            "timestamp": timestamp,
            "events": [{"role": role, "content": content, "timestamp": event_ts, "files": files}
                       for role, content, event_ts, files in events],
        })
    if not filler_sessions:
        return sessions
    # Filler must stay strictly before the cutoff boundary: it is inserted
    # between the last real session and the boundary, with monotonically
    # increasing timestamps inside that window.
    return sessions[:-1] + filler_sessions + [sessions[-1]]


def build_case(case: dict[str, Any], *, filler: str = "nofiller") -> dict[str, Any]:
    filler_sessions = _filler_sessions(case) if filler == "filler32k" else []
    history = _session_dicts(case, filler_sessions)
    raw = {
        "schema": "cortex_memory_benchmark/v1",
        "id": case["id"] if filler == "nofiller" else f"{case['id']}-{filler}",
        "source": SOURCE,
        "source_revision": REVISION,
        "split": case["split"],
        "domain": DOMAIN,
        "history": history,
        "cutoff": {"session_index": len(history) - 1, "branch": "main"},
        "query": {"text": case["query"].strip(), "files": [], "symbols": []},
        "task_type": case["task_type"],
        "gold": _gold(case),
        "constraints": {"max_context_tokens": 4096, "allowed_future_data": False},
        "metadata": {"transform": "cortex/benchmarks/corpora/build_internal.py",
                     "task_type": case["task_type"], "hop": case["hop"], "filler": filler,
                     "notes": case["notes"]},
        "checksums": {"history": "sha256:" + "0" * 64, "gold": "sha256:" + "0" * 64},
    }
    return instance_from_dict(raw, materialize=True).model_dump(by_alias=True, mode="json")


def _gold(case: dict[str, Any]) -> dict[str, Any]:
    gold = dict(case["gold"])
    gold.setdefault("accepted_answers", [])
    gold.setdefault("current_entities", [])
    gold.setdefault("invalid_entities", [])
    gold.setdefault("gold_evidence", [])
    gold.setdefault("supersession_pairs", [])
    gold.setdefault("contradiction_pairs", [])
    gold.setdefault("annotation_quality", "confirmatory")
    return gold


def _filler_sessions(case: dict[str, Any]) -> list[dict[str, Any]]:
    """Deterministic noise that adds tokens without changing any gold id."""
    from cortex.compiler.compiler import token_estimate

    per_line = max(1, token_estimate(FILLER_LINES[0].format(n=0)))
    count = max(1, FILLER_TOKEN_BUDGET // per_line)
    start = _parse(case["sessions"][-2][1])
    end = _parse(case["sessions"][-1][1])
    window = (end - start).total_seconds()
    step = window / (count + 1)
    sessions: list[dict[str, Any]] = []
    for index in range(count):
        moment = start + timedelta(seconds=step * (index + 1))
        stamp = moment.strftime("%Y-%m-%dT%H:%M:%SZ")
        sessions.append({
            "session_id": f"filler-{index:04d}",
            "timestamp": stamp,
            "events": [{"role": "user", "content": FILLER_LINES[index % len(FILLER_LINES)].format(n=index),
                        "timestamp": stamp, "files": [f"docs/notes_{index % 7}.md"]}],
        })
    return sessions


def _parse(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=datetime.UTC)


def _migrate_mvp() -> tuple[Path, int]:
    """Freeze the legacy MVP fixture into the normalized corpus layout.

    The MVP manifest used to rely on the runner appending an implicit
    post-cutoff sentinel; that inference is now materialised in the data and
    the checksums are derived instead of left as placeholders.
    """
    legacy = MANIFESTS_DIR / "mvp.json"
    if not legacy.exists():
        raise SchemaError("mvp.json is missing; the MVP fixture cannot be frozen")
    document = json.loads(legacy.read_text(encoding="utf-8"))
    cases = document.get("cases")
    if cases is None:
        return legacy, 0
    normalized: list[dict[str, Any]] = []
    for case in cases:
        history = case["history"]
        if case["cutoff"]["session_index"] >= len(history):
            # Explicit boundary session: same timestamp rule the runner used to
            # apply in code, now part of the committed corpus.
            last = history[-1]
            moment = datetime.fromisoformat(last["timestamp"].replace("Z", "+00:00"))
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=UTC)
            history.append({"session_id": "__cutoff__",
                            "timestamp": (moment + timedelta(days=1)).isoformat().replace("+00:00", "Z"),
                            "events": []})
        case = {**case, "history": history}
        normalized.append(instance_from_dict(case, materialize=True).model_dump(by_alias=True, mode="json"))
    corpus = NORMALIZED_DIR / "mvp_v1.jsonl"
    _write_jsonl(corpus, normalized)
    revisions = sorted({case["source"] for case in normalized})
    manifest = {
        "schema": "cortex_memory_benchmark_manifest/v1",
        "cortex_version": document.get("cortex_version", _cortex_version()),
        "python_version": document.get("python_version", "3.11"),
        "os": "portable", "hardware": "portable",
        "tokenizer": document.get("tokenizer", "whitespace/v1"),
        "embedding_model": "none", "embedding_version": "none",
        "embedding_cache_dir": "outside-repository",
        "seed": document.get("seed", 0),
        "retry_policy": document.get("retry_policy", "off"),
        "network_enabled": False,
        "corpus_hash": _hash_lines(corpus),
        "dataset_revisions": {source: str(normalized[0]["source_revision"]) for source in revisions},
        "splits": ["dev", "regression"],
        "corpus": os.path.relpath(corpus, MANIFESTS_DIR).replace("\\", "/"),
        "note": "MVP vertical (Onda -1) frozen as a normalized corpus; the cases are unchanged.",
    }
    (MANIFESTS_DIR / "mvp.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return corpus, len(normalized)


def write_corpora() -> dict[str, Any]:
    """Regenerate every committed corpus file.  Returns a summary for CI."""
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    ADVERSARIAL_DIR.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {}
    _, count = _migrate_mvp()
    summary["manifests/mvp.json"] = count
    for filler in ("nofiller", "filler32k"):
        path = NORMALIZED_DIR / f"engineering_memory_v1.{filler}.jsonl"
        rows = [build_case(case, filler=filler) for case in CASES]
        _write_jsonl(path, rows)
        summary[str(path.relative_to(CORPORA_DIR))] = len(rows)
    adversarial = ADVERSARIAL_DIR / "superseded_abstention.jsonl"
    rows = [build_case(case, filler="nofiller") for case in ADVERSARIAL_CASES]
    _write_jsonl(adversarial, rows)
    summary[str(adversarial.relative_to(CORPORA_DIR))] = len(rows)
    _write_manifest()
    return summary


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
                    encoding="utf-8", newline="\n")


def _write_manifest() -> None:
    nofiller = NORMALIZED_DIR / "engineering_memory_v1.nofiller.jsonl"
    filler = NORMALIZED_DIR / "engineering_memory_v1.filler32k.jsonl"
    adversarial = ADVERSARIAL_DIR / "superseded_abstention.jsonl"
    for name, corpus in (("memory_v1.json", nofiller), ("memory_v1_filler32k.json", filler),
                         ("memory_v1_adversarial.json", adversarial)):
        (MANIFESTS_DIR / name).write_text(
            json.dumps(_manifest(corpus, nofiller, filler, adversarial), ensure_ascii=False,
                       sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _manifest(corpus: Path, nofiller: Path, filler: Path, adversarial: Path) -> dict[str, Any]:
    from ..manifest import endpoint_table_digest

    manifest = {
        "schema": "cortex_memory_benchmark_manifest/v1",
        "cortex_version": _cortex_version(),
        "python_version": "3.11+",
        "os": "portable",
        "hardware": "portable",
        "tokenizer": "cortex.compiler.token_estimate/cl100k_base",
        "embedding_model": "none",
        "embedding_version": "none",
        "embedding_cache_dir": "outside-repository",
        "seed": 0,
        "retry_policy": "deterministic",
        "network_enabled": False,
        "corpus_hash": _hash_lines(corpus),
        "dataset_revisions": {SOURCE: REVISION},
        "expected_endpoint_digest": endpoint_table_digest(),
        "splits": ["dev", "eval", "regression"],
        "corpus": os.path.relpath(corpus, MANIFESTS_DIR).replace("\\", "/"),
        "filler_variants": {
            "nofiller": str(nofiller.relative_to(CORPORA_DIR)),
            "filler32k": str(filler.relative_to(CORPORA_DIR)),
            "adversarial": str(adversarial.relative_to(CORPORA_DIR)),
        },
        "license": "internal synthetic corpus; no third-party transcripts committed",
    }
    return manifest


def _hash_lines(path: Path) -> str:
    import hashlib

    payload = "".join(line for line in path.read_text(encoding="utf-8").splitlines(keepends=True))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _cortex_version() -> str:
    from cortex import __version__

    return __version__


if __name__ == "__main__":  # pragma: no cover - generator entry point
    print(json.dumps(write_corpora(), indent=2, sort_keys=True))
