"""Hook para capturar sessões de desenvolvimento real do Cortex.

Este módulo captura interações de desenvolvimento para usar no dogfooding
do sistema de memória, fornecendo evidência externa real sobre recall e
precision em conversas que não foram escritas especificamente para os extratores.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_SESSIONS_DIR = Path(__file__).parent / "sessions"


class SessionCapture:
    """Captura eventos de uma sessão de desenvolvimento em formato estruturado."""
    
    def __init__(
        self,
        output_dir: Path | str | None = None,
        session_id: str | None = None,
        auto_save: bool = False,
    ):
        self.output_dir = Path(output_dir) if output_dir is not None else DEFAULT_SESSIONS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.auto_save = auto_save
        self.current_session = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "events": [],
        }
    
    def capture_event(self, role: str, content: str, files: list[str] | None = None) -> None:
        """Captura um evento (user/assistant/tool/commit/etc) da sessão atual."""
        self.current_session["events"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "files": files or []
        })
        if self.auto_save:
            self.save_session()
    
    def capture_user_instruction(self, instruction: str, files: list[str] | None = None) -> None:
        """Captura uma instrução do usuário."""
        self.capture_event("user", instruction, files)
    
    def capture_assistant_response(self, response: str, files: list[str] | None = None) -> None:
        """Captura uma resposta do assistente."""
        self.capture_event("assistant", response, files)
    
    def capture_tool_result(self, tool_name: str, result: str, files: list[str] | None = None) -> None:
        """Captura um resultado de ferramenta."""
        content = f"[{tool_name}] {result}"
        self.capture_event("tool", content, files)
    
    def capture_commit(self, commit_hash: str, message: str, files: list[str]) -> None:
        """Captura um commit git."""
        content = f"commit {commit_hash}: {message}"
        self.capture_event("commit", content, files)
    
    def save_session(self) -> Path:
        """Salva a sessão atual em um arquivo JSON."""
        self.current_session["end_time"] = datetime.now().isoformat()
        session_file = self.output_dir / f"{self.current_session['session_id']}.json"
        session_file.write_text(json.dumps(self.current_session, indent=2, ensure_ascii=False), encoding="utf-8")
        return session_file
    
    def reset_session(self) -> None:
        """Inicia uma nova sessão."""
        self.current_session = {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "start_time": datetime.now().isoformat(),
            "events": []
        }


def create_capture(
    output_dir: Path | str | None = None,
    session_id: str | None = None,
    auto_save: bool = False,
) -> SessionCapture:
    """Factory function para criar uma instância de SessionCapture."""
    return SessionCapture(output_dir, session_id=session_id, auto_save=auto_save)


if __name__ == "__main__":
    # Exemplo de uso
    capture = create_capture()
    
    # Simular uma sessão de desenvolvimento
    capture.capture_user_instruction("Adicionar suporte para PostgreSQL no Cortex")
    capture.capture_assistant_response("Vou implementar o suporte para PostgreSQL. Primeiro preciso atualizar o schema...")
    capture.capture_tool_result("file_read", "Lendo arquivo cortex/storage/schema.py")
    capture.capture_commit("abc123", "Add PostgreSQL support", ["cortex/storage/schema.py", "cortex/storage/postgres.py"])
    
    session_file = capture.save_session()
    print(f"Sessão salva em: {session_file}")
