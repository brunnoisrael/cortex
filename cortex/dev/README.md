# Dogfooding do Cortex

Esta pasta contém ferramentas para capturar sessões de desenvolvimento real do Cortex e usá-las para validação externa do sistema de memória.

## Objetivo

Validar o sistema de memória do Cortex em sessões reais de desenvolvimento, fornecendo evidência externa real sobre recall e precision em conversas que não foram escritas especificamente para os extratores.

## Estrutura

```
cortex/dev/
├── capture_hook.py          # Hook para capturar sessões
├── validation_questions.py  # Gerador de perguntas de validação
├── sessions/                # Sessões capturadas (gitignored)
├── queries/                 # Perguntas de validação (gitignored)
└── annotations/             # Gold standard manual (gitignored)
```

## Uso

### 1. Capturar uma Sessão

```python
from cortex.dev.capture_hook import create_capture

# Criar capturador
capture = create_capture()

# Capturar eventos durante desenvolvimento
capture.capture_user_instruction("Adicionar suporte para PostgreSQL")
capture.capture_assistant_response("Vou implementar o suporte...")
capture.capture_tool_result("file_read", "Lendo arquivo schema.py")
capture.capture_commit("abc123", "Add PostgreSQL support", ["schema.py"])

# Salvar sessão
session_file = capture.save_session()
print(f"Sessão salva: {session_file}")
```

### 2. Gerar Perguntas de Validação

```python
from cortex.dev.validation_questions import batch_generate_questions
from pathlib import Path

# Gerar perguntas para todas as sessões
questions = batch_generate_questions(
    Path("cortex/dev/sessions"),
    Path("cortex/dev/queries")
)
print(f"Geradas {len(questions)} perguntas")
```

### 3. Anotar Gold Standard

1. Abra os arquivos em `cortex/dev/queries/`
2. Para cada pergunta, preencha o campo `answer` com a resposta correta
3. Salve as anotações em `cortex/dev/annotations/`

### 4. Converter para Benchmark

Use o loader apropriado para converter as sessões anotadas para o formato BenchmarkInstance do benchmark.

## Benefícios

- **Validação real**: Testa o sistema no domínio que foi desenhado (engenharia de software)
- **Feedback imediato**: Problemas são descobertos durante uso real
- **Custo acessível**: Alguns dias de uso + 2-3 horas de anotação
- **Evidência externa**: Sessões não são controladas pelo desenvolvedor

## Próximos Passos

1. Usar o Cortex em 5-10 sessões de desenvolvimento reais
2. Anotar manualmente o gold standard
3. Converter para o formato do benchmark
4. Rodar o runner com os adapters
5. Analisar resultados e identificar gaps nos extratores

## Integração com IDE

Para integração automática com Claude Code/Cursor, considere:

- Criar plugins que interceptam comandos e respostas
- Capturar automaticamente contexto de arquivos modificados
- Gerar perguntas de validação automaticamente após cada sessão
- Integrar com o fluxo de trabalho de desenvolvimento existente
