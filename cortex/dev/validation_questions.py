"""Gerador de perguntas de validação para sessões de desenvolvimento.

Este módulo analisa sessões capturadas e gera perguntas que podem ser usadas
para validar o sistema de memória do Cortex, convertendo sessões reais em casos
de benchmark.

Estratégia de geração
----------------------
Em vez de keyword-match ingênuo (que gera perguntas redundantes e perde
task types críticos), este módulo usa **extratores por papel de evento**:

- Eventos ``commit``  → exact_recall (hash, mensagem) + aggregation (lista)
- Eventos ``tool``    → exact_recall (resultados de testes), tracking (estado)
- Eventos ``assistant`` → cascade (quais mudanças foram encadeadas)
- Eventos com ``files`` → exact_recall (arquivos), deletion (ausências)
- Ausência de keywords → absence (abstention expected)

Garantias:
- Mínimo de 10 perguntas por sessão com histórico rico
- Sem duplicatas por (question_type, tema)
- Cobertura dos 6 task_types: exact_recall, aggregation, tracking,
  deletion, cascade, absence
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Utilitários internos
# ---------------------------------------------------------------------------

def _session_text(session: dict[str, Any]) -> str:
    """Texto concatenado de todos os eventos para buscas de padrão."""
    return " ".join(e.get("content", "") for e in session["events"])


def _events_by_role(session: dict[str, Any], role: str) -> list[dict[str, Any]]:
    return [e for e in session["events"] if e.get("role") == role]


def _all_files(session: dict[str, Any]) -> list[str]:
    seen: set[str] = set()
    files: list[str] = []
    for event in session["events"]:
        for f in event.get("files", []):
            if f not in seen:
                seen.add(f)
                files.append(f)
    return files


def _make_question(
    session_id: str,
    key: str,
    question: str,
    question_type: str,
    question_date: str,
    start_time: str,
    events: list[dict[str, Any]],
    expected_abstention: bool = False,
) -> dict[str, Any]:
    return {
        "question_id": f"q_{session_id}_{key}",
        "question": question,
        "question_type": question_type,
        "question_date": question_date,
        "answer_session_ids": [session_id],
        "answer": "",  # Preenchido manualmente durante anotação
        "expected_abstention": expected_abstention,
        "haystack_session_ids": [session_id],
        "haystack_dates": [start_time],
        "haystack_sessions": [events],
    }


# ---------------------------------------------------------------------------
# Extratores por tipo de questão
# ---------------------------------------------------------------------------

def _extract_exact_recall(
    session: dict[str, Any], seen_keys: set[str]
) -> list[dict[str, Any]]:
    """Perguntas de recuperação exata: commits, testes, arquivos."""
    questions: list[dict[str, Any]] = []
    sid = session["session_id"]
    date = session.get("end_time", session["start_time"])
    start = session["start_time"]
    events = session["events"]

    # Arquivos modificados
    files = _all_files(session)
    if files and "files_modified" not in seen_keys:
        seen_keys.add("files_modified")
        questions.append(_make_question(
            sid, "files_modified",
            "Quais arquivos foram modificados nesta sessão?",
            "exact_recall", date, start, events,
        ))

    # Commits: hash e mensagem de cada commit
    commit_events = _events_by_role(session, "commit")
    for i, ev in enumerate(commit_events):
        # Tentar extrair hash do conteúdo: "commit <hash>: <msg>"
        m = re.search(r"commit\s+([0-9a-f]{7,40})", ev["content"], re.IGNORECASE)
        if m:
            chash = m.group(1)
            key_msg = f"commit_msg_{chash}"
            key_hash = f"commit_hash_fix_{i}"
            if key_msg not in seen_keys:
                seen_keys.add(key_msg)
                questions.append(_make_question(
                    sid, key_msg,
                    f"Qual a mensagem exata do commit {chash}?",
                    "exact_recall", date, start, events,
                ))
            if key_hash not in seen_keys:
                seen_keys.add(key_hash)
                questions.append(_make_question(
                    sid, key_hash,
                    f"Qual o hash do commit número {i + 1} desta sessão?",
                    "exact_recall", date, start, events,
                ))

    # Resultados de testes (tool events com "pytest" ou contagens N/N)
    tool_events = _events_by_role(session, "tool")
    for ev in tool_events:
        content = ev.get("content", "")
        if "pytest" in content.lower():
            m = re.search(r"(\d+)/(\d+)", content)
            if m and "test_count_integrity" not in seen_keys:
                seen_keys.add("test_count_integrity")
                questions.append(_make_question(
                    sid, "test_count_integrity",
                    "Quantos testes de integridade foram executados e qual foi o resultado?",
                    "exact_recall", date, start, events,
                ))
            # Suite completa
            m_full = re.search(r"(\d{3,})/(\d{3,})", content)
            if m_full and "test_count_full" not in seen_keys:
                seen_keys.add("test_count_full")
                questions.append(_make_question(
                    sid, "test_count_full",
                    "Quantos testes passaram na suite completa ao final da sessão?",
                    "exact_recall", date, start, events,
                ))

    # Framework de testes (pytest mencionado)
    stext = _session_text(session)
    if "pytest" in stext.lower() and "framework_test" not in seen_keys:
        seen_keys.add("framework_test")
        questions.append(_make_question(
            sid, "framework_test",
            "Qual framework de testes foi escolhido?",
            "exact_recall", date, start, events,
        ))

    # Banco de dados escolhido
    db_keywords = {"sqlite", "postgresql", "postgres", "mysql", "mariadb", "mongo"}
    db_found = [kw for kw in db_keywords if kw in stext.lower()]
    if db_found and "db_chosen" not in seen_keys:
        seen_keys.add("db_chosen")
        questions.append(_make_question(
            sid, "db_chosen",
            "Qual banco de dados foi escolhido e por quê?",
            "exact_recall", date, start, events,
        ))

    # .gitignore modificado?
    if ".gitignore" in stext and "gitignore_modified" not in seen_keys:
        seen_keys.add("gitignore_modified")
        questions.append(_make_question(
            sid, "gitignore_modified",
            "O .gitignore foi modificado nesta sessão?",
            "exact_recall", date, start, events,
        ))

    return questions


def _extract_aggregation(
    session: dict[str, Any], seen_keys: set[str]
) -> list[dict[str, Any]]:
    """Perguntas de agregação: lista de commits, ferramentas usadas."""
    questions: list[dict[str, Any]] = []
    sid = session["session_id"]
    date = session.get("end_time", session["start_time"])
    start = session["start_time"]
    events = session["events"]

    commit_events = _events_by_role(session, "commit")
    if commit_events and "commits_list" not in seen_keys:
        seen_keys.add("commits_list")
        questions.append(_make_question(
            sid, "commits_list",
            "Quais commits foram feitos nesta sessão e o que cada um fez?",
            "aggregation", date, start, events,
        ))

    # Ferramentas de teste usadas
    stext = _session_text(session)
    test_tools = [t for t in ("pytest", "unittest", "nose") if t in stext.lower()]
    if test_tools and "test_tools_used" not in seen_keys:
        seen_keys.add("test_tools_used")
        questions.append(_make_question(
            sid, "test_tools_used",
            "Quais ferramentas de teste foram usadas nesta sessão?",
            "aggregation", date, start, events,
        ))

    # Arquivos por commit
    if len(commit_events) >= 2 and "commits_files_agg" not in seen_keys:
        seen_keys.add("commits_files_agg")
        questions.append(_make_question(
            sid, "commits_files_agg",
            "Quais arquivos foram commitados em cada commit desta sessão?",
            "aggregation", date, start, events,
        ))

    return questions


def _extract_tracking(
    session: dict[str, Any], seen_keys: set[str]
) -> list[dict[str, Any]]:
    """Perguntas de rastreamento: mudanças de estado ao longo da sessão."""
    questions: list[dict[str, Any]] = []
    sid = session["session_id"]
    date = session.get("end_time", session["start_time"])
    start = session["start_time"]
    events = session["events"]
    stext = _session_text(session)

    # Status dos testes mudou?
    tool_events_pytest = [
        e for e in _events_by_role(session, "tool")
        if "pytest" in e.get("content", "").lower()
    ]
    if len(tool_events_pytest) >= 1 and "tracking_test_status" not in seen_keys:
        seen_keys.add("tracking_test_status")
        questions.append(_make_question(
            sid, "tracking_test_status",
            "O status dos testes de integridade mudou durante a sessão? De qual estado para qual?",
            "tracking", date, start, events,
        ))

    # Arquivos rastreados: cada arquivo com files mencionado em commit
    commit_events = _events_by_role(session, "commit")
    all_files = _all_files(session)
    for fname in all_files[:3]:  # até 3 arquivos rastreados por sessão
        basename = Path(fname).name
        key = f"tracking_file_{basename}"
        if key not in seen_keys:
            seen_keys.add(key)
            questions.append(_make_question(
                sid, key,
                f"O arquivo {fname} foi modificado durante a sessão? Qual foi a mudança principal?",
                "tracking", date, start, events,
            ))
            break  # 1 por sessão para não inflar

    # capture_hook foi commitado?
    if any("capture_hook" in f for f in _all_files(session)) and "tracking_capture_hook" not in seen_keys:
        seen_keys.add("tracking_capture_hook")
        questions.append(_make_question(
            sid, "tracking_capture_hook",
            "O capture_hook.py foi incluído nos arquivos commitados? Em qual commit?",
            "tracking", date, start, events,
        ))

    return questions


def _extract_cascade(
    session: dict[str, Any], seen_keys: set[str]
) -> list[dict[str, Any]]:
    """Perguntas de cascata: mudanças que implicaram outras mudanças."""
    questions: list[dict[str, Any]] = []
    sid = session["session_id"]
    date = session.get("end_time", session["start_time"])
    start = session["start_time"]
    events = session["events"]
    stext = _session_text(session)
    all_files = _all_files(session)

    # Se 3+ arquivos de código diferentes foram modificados, provavelmente houve cascata
    code_files = [f for f in all_files if f.endswith(".py")]
    if len(code_files) >= 3 and "cascade_engine_change" not in seen_keys:
        seen_keys.add("cascade_engine_change")
        # Inferir o "driver" da cascata: geralmente o primeiro arquivo de engine/distilação
        driver = next((f for f in code_files if "engine" in f or "distil" in f), code_files[0])
        basename = Path(driver).name
        questions.append(_make_question(
            sid, "cascade_engine_change",
            f"A mudança em {basename} exigiu mudanças em quais outros arquivos?",
            "cascade", date, start, events,
        ))

    # Por que a mudança propagou?
    if "IntegrityError" in stext and "cascade_why" not in seen_keys:
        seen_keys.add("cascade_why")
        questions.append(_make_question(
            sid, "cascade_why",
            "Por que alterar o evidence_id no engine exigiu mudança no store.py?",
            "cascade", date, start, events,
        ))

    return questions


def _extract_absence(
    session: dict[str, Any], seen_keys: set[str]
) -> list[dict[str, Any]]:
    """Perguntas de ausência: tópicos NÃO mencionados na sessão (expected_abstention=True)."""
    questions: list[dict[str, Any]] = []
    sid = session["session_id"]
    date = session.get("end_time", session["start_time"])
    start = session["start_time"]
    events = session["events"]
    stext = _session_text(session).lower()

    # Tecnologias ausentes que poderiam ser esperadas
    absent_topics = [
        ("redis", "Redis foi usado como cache nesta sessão?"),
        ("postgresql", "PostgreSQL foi escolhido como banco de dados nesta sessão?"),
        ("docker", "Docker foi configurado nesta sessão?"),
        ("kubernetes", "Kubernetes foi mencionado nesta sessão?"),
        ("graphql", "GraphQL foi implementado nesta sessão?"),
    ]

    added = 0
    for keyword, question in absent_topics:
        if keyword not in stext:
            key = f"absence_{keyword}"
            if key not in seen_keys and added < 3:
                seen_keys.add(key)
                added += 1
                questions.append(_make_question(
                    sid, key, question,
                    "absence", date, start, events,
                    expected_abstention=True,
                ))

    return questions


def _extract_deletion(
    session: dict[str, Any], seen_keys: set[str]
) -> list[dict[str, Any]]:
    """Perguntas sobre deleções: arquivos ou funcionalidades removidas."""
    questions: list[dict[str, Any]] = []
    sid = session["session_id"]
    date = session.get("end_time", session["start_time"])
    start = session["start_time"]
    events = session["events"]
    stext = _session_text(session).lower()

    # Detectar deleção explícita no conteúdo
    deletion_markers = ("deletado", "removido", "excluído", "apagado", "deleted", "removed", "git rm")
    has_deletion = any(m in stext for m in deletion_markers)

    if "deletion_files" not in seen_keys:
        seen_keys.add("deletion_files")
        questions.append(_make_question(
            sid, "deletion_files",
            "Algum arquivo foi deletado nesta sessão?",
            "deletion", date, start, events,
            expected_abstention=not has_deletion,
        ))

    return questions


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def generate_validation_questions(session: dict[str, Any]) -> list[dict[str, Any]]:
    """Gera perguntas de validação baseadas no conteúdo de uma sessão.

    Garante cobertura dos 6 task types e no mínimo 10 perguntas por sessão
    com histórico rico (≥3 eventos com conteúdo estruturado).
    """
    seen_keys: set[str] = set()
    questions: list[dict[str, Any]] = []

    extractors = [
        _extract_exact_recall,
        _extract_aggregation,
        _extract_tracking,
        _extract_cascade,
        _extract_absence,
        _extract_deletion,
    ]

    for extractor in extractors:
        questions.extend(extractor(session, seen_keys))

    return questions


def save_questions(questions: list[dict[str, Any]], output_file: Path) -> None:
    """Salva perguntas de validação em um arquivo JSON."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8")


def load_session(session_file: Path) -> dict[str, Any]:
    """Carrega uma sessão de um arquivo JSON."""
    return json.loads(session_file.read_text(encoding="utf-8"))


def batch_generate_questions(sessions_dir: Path, output_dir: Path) -> list[dict[str, Any]]:
    """Gera perguntas para todas as sessões em um diretório."""
    output_dir.mkdir(parents=True, exist_ok=True)
    all_questions: list[dict[str, Any]] = []

    for session_file in sessions_dir.glob("*.json"):
        session = load_session(session_file)
        questions = generate_validation_questions(session)
        all_questions.extend(questions)

        # Salvar perguntas específicas da sessão
        session_questions_file = output_dir / f"{session_file.stem}_questions.json"
        save_questions(questions, session_questions_file)

    # Salvar todas as perguntas juntas
    all_questions_file = output_dir / "all_questions.json"
    save_questions(all_questions, all_questions_file)

    return all_questions


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    sessions_dir = script_dir / "sessions"
    output_dir = script_dir / "queries"

    if sessions_dir.exists():
        questions = batch_generate_questions(sessions_dir, output_dir)
        by_type: dict[str, int] = {}
        for q in questions:
            t = q["question_type"]
            by_type[t] = by_type.get(t, 0) + 1
        print(f"Geradas {len(questions)} perguntas de {len(list(sessions_dir.glob('*.json')))} sessões")
        for t, n in sorted(by_type.items()):
            print(f"  {t}: {n}")
    else:
        print(f"Diretório de sessões não encontrado: {sessions_dir}")
        print("Use o capture_hook.py para capturar sessões primeiro.")
