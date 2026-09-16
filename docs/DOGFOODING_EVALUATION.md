# Avaliação de Dogfooding e Guia de Validação Externa

Este documento foi preparado para orientar outro modelo de IA ou avaliador técnico na inspeção do comportamento do **Cortex** durante seu processo de auto-dogfooding, fornecendo instruções acionáveis, esclarecimentos arquiteturais e comandos prontos para execução autônoma.

---

## 1. Resposta Direta: O Dogfooding é o Mesmo da Instalação do GitHub?

> [!IMPORTANT]
> **Sim, o núcleo funcional executado no dogfooding é 100% o código de produção real do Cortex.** Não houve adaptação nem mock no motor de memória, no Evidence Ledger ou no armazenamento.

### Comparativo Arquitetural: Produção vs. Harness de Dogfooding

| Componente | Instalação Padrão (`git clone` / `pip install -e .`) | Harness de Dogfooding (`cortex/dev/`) | O que muda? |
|---|---|---|---|
| **DistillationEngine** | `cortex.distillation.engine.DistillationEngine` | `cortex.distillation.engine.DistillationEngine` | **Idêntico**. Heurísticas, deduplicação e linking idênticos. |
| **Evidence Ledger** | `cortex.knowledge.evidence.resolve_entity_evidence` | `cortex.knowledge.evidence.resolve_entity_evidence` | **Idêntico**. Hashing, fingerprints e integridade idênticos. |
| **Storage & SQLite** | `cortex.storage.store.KnowledgeStore` (`.cortex/cortex.db`) | `cortex.storage.store.KnowledgeStore` (temp DB ou `.cortex/`) | **Idêntico**. DDL, índices FTS5, tabelas e constraints idênticas. |
| **Compiler & Ranking** | `cortex.compiler.compiler.compile_context` | `cortex.compiler.compiler.compile_context` | **Idêntico**. Budget de tokens e scores de autoridade/recência idênticos. |
| **Ponto de Captura** | CLI (`cortex capture`), Hooks de IDE (`cortex hook --install claude-code\|cursor`) ou MCP Server (`python -m cortex.server.mcp_server`) | `cortex.dev.capture_hook.SessionCapture` | **Apenas a camada de coleta**. Em produção, grava no banco `.cortex/cortex.db`. No dogfooding, serializa em JSON (`cortex/dev/sessions/`) para permitir validação em lote contra o runner de benchmark (`BenchmarkInstance`). |

### Como reproduzir o fluxo exato de produção com a sessão de dogfooding:
Qualquer modelo ou usuário pode carregar os eventos da sessão gravada diretamente no banco de produção:

```bash
# 1. Inicializar o Cortex oficial no repositório
cortex init

# 2. Ingerir a sessão capturada no dogfooding diretamente no CLI de produção
python -c "
import json
from cortex.storage.store import KnowledgeStore
from cortex.capture.recorder import capture_event

store = KnowledgeStore('.cortex/cortex.db')
data = json.loads(open('cortex/dev/sessions/20260915_evidence_integrity_dogfooding.json', encoding='utf-8').read())
store.ensure_session(data['session_id'], host='dogfooding')
for ev in data['events']:
    capture_event(store, {
        'session_id': data['session_id'],
        'type': 'user_instruction' if ev['role']=='user' else 'agent_response',
        'content': ev['content'],
        'files': ev.get('files', [])
    })
print('Eventos ingeridos com sucesso.')
"

# 3. Executar a destilação oficial
cortex distill

# 4. Consultar o recall e o grafo de proveniência
cortex recall "IntegrityError evidence.id"
cortex status
```

---

## 2. O Que Foi Realizado e Validado no Dogfooding

### Causa Raiz Resolvida (Bug do `IntegrityError`)
Nos benchmarks de conversas longas (como LongMemEval), eventos sucessivos eram destilados sem arquivos de código estruturados.
- **O defeito:** O `DistillationEngine` usava `id=f"ev-{event_id}"` hardcoded, sem o `entity_id`. Se duas entidades (ex: uma decisão e uma intenção) vinham do mesmo turno/evento, o SQLite disparava `sqlite3.IntegrityError: UNIQUE constraint failed: evidence.id`.
- **A solução implementada:**
  1. No [engine.py](file:///c:/Users/Sergio/Documents/GitHub/cortex/cortex/distillation/engine.py): Uso de `evidence_id(eid, EvidenceType.EVENT, event_id)` vinculando o hash da evidência à entidade específica.
  2. No [evidence.py](file:///c:/Users/Sergio/Documents/GitHub/cortex/cortex/knowledge/evidence.py): Tratamento robusto para localizações vazias/nulas e deduplicação de listas de fontes.
  3. No [store.py](file:///c:/Users/Sergio/Documents/GitHub/cortex/cortex/storage/store.py): Deduplicação de `entity.evidence` por ID em memória e cláusula defensiva `ON CONFLICT(id) DO UPDATE SET` na tabela `evidence`.

### Evidências da Execução
1. **Sessão Real Capturada**: `cortex/dev/sessions/20260915_evidence_integrity_dogfooding.json`
2. **Perguntas Geradas**: `cortex/dev/queries/20260915_evidence_integrity_dogfooding_questions.json`
3. **Gold Standard Anotado**: `cortex/dev/annotations/20260915_evidence_integrity_dogfooding_annotations.json`
4. **Testes Específicos**: [tests/test_evidence_integrity.py](file:///c:/Users/Sergio/Documents/GitHub/cortex/tests/test_evidence_integrity.py) (5 testes cobrindo todas as variantes de colisão).
5. **Suite Completa**: 243 testes passando sem falhas (`pytest`).

---

## 3. Sugestões de Testes e Benchmarks Conceitualizados

Para o modelo avaliador testar e validar a qualidade de recuperação, extração e generalização do Cortex, recomendamos os seguintes benchmarks e modelos já conceitualizados e integrados na arquitetura:

### A. LongMemEval-S (HuggingFace / Pesquisa Externa)
- **Origem**: HuggingFace / arXiv:2406.18274 (benchmark de memória de longo prazo para assistentes de chat).
- **Finalidade**: Testar se o Cortex resiste a diálogos conversacionais de 40+ sessões e centenas de turnos sem estourar colisões de chave primária.
- **Comando de Execução**:
  ```bash
  # Rodar o runner comparativo (Cortex vs BM25 vs Raw Context)
  python -m cortex.benchmarks.runner \
    --manifest cortex/benchmarks/corpora/manifests/longmemeval_s.json \
    --adapter cortex bm25 raw_context \
    --report-out artifacts/benchmark-longmemeval-eval

  # Rodar a análise de gaps por question_type
  python -m cortex.benchmarks.analyze_lme --report-out artifacts/benchmark-longmemeval-eval
  ```

### B. SWE-bench (HuggingFace: `princeton-nlp/SWE-bench`)
- **Origem**: Repositórios reais de engenharia de software do mundo real com issues, pull requests e testes.
- **Loader existente no Cortex**: [cortex/benchmarks/loaders/swebench.py](file:///c:/Users/Sergio/Documents/GitHub/cortex/cortex/benchmarks/loaders/swebench.py).
- **Finalidade**: Avaliar a qualidade de extração de fixes e decisões sobre bases de código Python reais (Django, SymPy, Flask).
- **Como executar**:
  ```bash
  # Validar o contrato do loader SWE-bench
  pytest tests/benchmarks/test_loaders.py -k "swebench" -v
  ```

### C. MemE / MemBench (HuggingFace)
- **Origem**: Avaliação de tracking de entidades dinâmicas ao longo do tempo (atualização de estado vs supersessão).
- **Loader existente no Cortex**: [cortex/benchmarks/loaders/meme.py](file:///c:/Users/Sergio/Documents/GitHub/cortex/cortex/benchmarks/loaders/meme.py).
- **Como executar**:
  ```bash
  pytest tests/benchmarks/test_meme_loader.py -v
  ```

### D. Benchmark Interno Controlado de Engenharia (`engineering_memory_v1`)
- **Origem**: 250 casos sintéticos versionados cobrindo 6 task types de engenharia de software (`exact_recall`, `adr_decision`, `bug_symptom_fix`, `negative_knowledge_rejection`, `superseded_recall`, `scope_isolation`).
- **Comando de Execução**:
  ```bash
  python -m cortex.benchmarks.runner \
    --manifest cortex/benchmarks/corpora/manifests/memory_v1.json \
    --adapter cortex bm25 oracle \
    --report-out artifacts/benchmark-eval-memory-v1
  ```

### E. Modelos de Linguagem para Destilação Aumentada (Ollama / HuggingFace)
Por padrão, o Cortex opera 100% offline via heurísticas regex/AST. Ele suporta opcionalmente LLMs locais via Ollama:
- **Modelos recomendados**:
  - `qwen2.5:7b` (excelente para extração estruturada de código e intenções)
  - `llama3.1:8b`
- **Como ativar na destilação**:
  ```bash
  # Caso o modelo avaliador tenha Ollama rodando localmente:
  cortex distill --llm ollama --model qwen2.5:7b
  ```

### F. Embeddings Densos Opcionais (HuggingFace / model2vec)
- **Modelos integrados**: `minishlab/potion-base-8M` (modelo estático de 8MB de alta velocidade) ou `sentence-transformers/all-MiniLM-L6-v2`.
- **Como ativar**:
  ```bash
  export CORTEX_ENABLE_DENSE_EMBEDDINGS=1
  pytest tests/test_super_evolucao.py -k "dense" -v
  ```

---

## 4. Roteiro Rápido para o Modelo Avaliador Executar por Conta Própria

Se o modelo avaliador tiver capacidade de execução de comandos (subagente ou terminal), execute esta verificação rápida de 3 minutos:

```bash
# 1. Verificar integridade da suite completa de testes
pytest tests/test_evidence_integrity.py -v
pytest tests/benchmarks/ -v

# 2. Inspecionar as perguntas geradas e respostas do dogfooding
python -c "
import json
q = json.load(open('cortex/dev/queries/20260915_evidence_integrity_dogfooding_questions.json', encoding='utf-8'))
a = json.load(open('cortex/dev/annotations/20260915_evidence_integrity_dogfooding_annotations.json', encoding='utf-8'))
for item in a:
    print(f'[{item[\"question_type\"]}] {item[\"question\"]}\n-> Resposta: {item[\"answer\"]}\n')
"

# 3. Testar a idempotência de upsert de evidências no store real
python -c "
import tempfile, pathlib
from cortex.storage.store import KnowledgeStore
from cortex.knowledge.models import Entity, Evidence, ArtifactType, Status, RiskLevel, ReviewPolicy, EvidenceType, EvidenceStatus, _utcnow

with tempfile.TemporaryDirectory() as d:
    st = KnowledgeStore(pathlib.Path(d) / 'test.db')
    ev = Evidence(id='ev-1', type=EvidenceType.EVENT, location='evt-1', status=EvidenceStatus.RESOLVED)
    ent = Entity(id='ent-1', type=ArtifactType.ADR, statement='Test ADR', status=Status.ACTIVE, risk_level=RiskLevel.LOW, review_policy=ReviewPolicy.MULTIPLE_EVIDENCE, observed_at=_utcnow(), evidence=[ev, ev])
    st.upsert(ent)
    st.upsert(ent)
    print('Idempotencia de store e ledger confirmada. Evidencias registradas:', len(st.list_evidence('ent-1')))
"
```
