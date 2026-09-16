"""Gerador de perguntas de validação para sessões de desenvolvimento.

Este módulo analisa sessões capturadas e gera perguntas que podem ser usadas
para validar o sistema de memória do Cortex, convertendo sessões reais em casos
de benchmark.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def generate_validation_questions(session: dict[str, Any]) -> list[dict[str, Any]]:
    """Gera perguntas de validação baseadas no conteúdo de uma sessão."""
    questions = []
    session_text = str(session["events"])
    session_id = session["session_id"]
    
    # Perguntas sobre decisões técnicas
    technical_keywords = {
        "postgres": "Qual banco de dados foi escolhido e por quê?",
        "postgresql": "Qual banco de dados foi escolhido e por quê?",
        "mysql": "Qual banco de dados foi escolhido e por quê?",
        "sqlite": "Qual banco de dados foi escolhido e por quê?",
        "redis": "Qual cache foi implementado e por quê?",
        "api": "Qual framework de API foi escolhido?",
        "rest": "Qual estilo de API foi implementado?",
        "graphql": "GraphQL foi considerado? Por que sim/não?",
        "docker": "Docker foi usado? Para quê?",
        "kubernetes": "Kubernetes foi considerado? Por que sim/não?",
        "test": "Qual framework de testes foi escolhido?",
        "pytest": "Pytest foi escolhido? Por quê?",
        "unittest": "Por que unittest em vez de pytest?",
    }
    
    for keyword, question in technical_keywords.items():
        if keyword in session_text.lower():
            questions.append({
                "question_id": f"q_{session_id}_{keyword}",
                "question": question,
                "question_type": "single-session-user",
                "question_date": session.get("end_time", session["start_time"]),
                "answer_session_ids": [session_id],
                "answer": "",  # Preenchido manualmente durante anotação
                "haystack_session_ids": [session_id],
                "haystack_dates": [session["start_time"]],
                "haystack_sessions": [[session["events"]]]
            })
    
    # Perguntas sobre commits realizados
    commit_events = [e for e in session["events"] if e.get("role") == "commit"]
    if commit_events:
        questions.append({
            "question_id": f"q_{session_id}_commits",
            "question": "Quais commits foram feitos nesta sessão e o que cada um fez?",
            "question_type": "aggregation",
            "question_date": session.get("end_time", session["start_time"]),
            "answer_session_ids": [session_id],
            "answer": "",  # Preenchido manualmente
            "haystack_session_ids": [session_id],
            "haystack_dates": [session["start_time"]],
            "haystack_sessions": [[session["events"]]]
        })
    
    # Perguntas sobre arquivos modificados
    all_files = set()
    for event in session["events"]:
        all_files.update(event.get("files", []))
    
    if all_files:
        questions.append({
            "question_id": f"q_{session_id}_files",
            "question": "Quais arquivos foram modificados nesta sessão?",
            "question_type": "exact_recall",
            "question_date": session.get("end_time", session["start_time"]),
            "answer_session_ids": [session_id],
            "answer": "",  # Preenchido manualmente
            "haystack_session_ids": [session_id],
            "haystack_dates": [session["start_time"]],
            "haystack_sessions": [[session["events"]]]
        })
    
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
    all_questions = []
    
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
    # Exemplo de uso
    script_dir = Path(__file__).parent
    sessions_dir = script_dir / "sessions"
    output_dir = script_dir / "queries"
    
    if sessions_dir.exists():
        questions = batch_generate_questions(sessions_dir, output_dir)
        print(f"Geradas {len(questions)} perguntas de {len(list(sessions_dir.glob('*.json')))} sessões")
    else:
        print(f"Diretório de sessões não encontrado: {sessions_dir}")
        print("Use o capture_hook.py para capturar sessões primeiro.")
