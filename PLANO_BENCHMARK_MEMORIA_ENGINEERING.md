# Plano de Benchmark de Memória de Engenharia do Cortex — v3.1 (Spec Executável)

**Data:** 2026-09-13  
**Status:** spec executável, com trilha MVP compatível com o repositório atual  
**Escopo:** Cortex local-first, store SQLite, destilação, ranking, compilação de contexto, governança e Evidence Ledger
**Substitui:** `PLANO_BENCHMARK_MEMORIA_ENGINEERING.md` v1 e v2

---

## 0.1 — Auditoria de executabilidade (baseline do repositório)

Este plano está tecnicamente bem orientado: congela leakage, separa extração/ranking/
contexto, exige abstention e evidência, usa baselines, ablações e estatística pareada, e
proíbe transformar uma média única em claim. Isso é o que está mais forte nele.

Ele ainda não é uma implementação pronta. O repositório atual tem o harness legado em
`cortex/benchmarks/evaluation.py`, `adapters.py`, `extraction.py` e `ccb.py`; ainda não
possui os módulos `schema.py`, `runner.py`, `stats.py`, `reports.py`, os seis adapters
canônicos nem `tests/benchmarks/`. Portanto, esta versão passa a declarar explicitamente
duas trilhas:

- **Trilha A — compatibilidade:** preservar `cortex benchmark --corpus`, adaptar o corpus
  JSONL existente e provar o envelope/manifesto/leakage antes de importar datasets externos;
- **Trilha B — benchmark v1:** implementar os módulos da seção 1 e só então congelar o
  `eval` externo.

Não se deve afirmar que o Cortex já venceu BM25, SWE-bench ou LongMemEval: sem os artefatos
do runner e sem uma execução versionada, qualquer superioridade seria hipótese. Também é
preciso confirmar licenças e revisões dos datasets no manifesto local antes de distribuí-los;
o texto do plano não é prova de licença.

### Gate adicional G-compat — não quebrar o que já funciona

Antes da Onda −1, uma execução deve registrar:

1. `pytest tests/ -q` verde;
2. o comando legado de benchmark verde com seu corpus fixture;
3. um adaptador de compatibilidade que produza `AdapterResult` sem expor `gold` ao
   pipeline legado;
4. um manifesto mínimo apontando versão do Cortex, hash do corpus, seed e
   `network_enabled=false`;
5. relatório de lacunas, em vez de zeros, para endpoints ainda não suportados.

O status de cada endpoint deve ser `implemented`, `compatibility_only`, `blocked` ou
`not_applicable`; `not_applicable` nunca entra no denominador de uma comparação.

### Ajustes de precisão incorporados

- `Cutoff` deve ser comparado por uma chave temporal canônica (timestamp UTC + índice),
  não apenas por strings potencialmente inconsistentes.
- A unidade de tokenização e o nome/versão/hash do tokenizer precisam aparecer no
  manifesto; `max_context_tokens` sem tokenizer fixado não é reproduzível.
- `raw_context` e `bm25_temporal` devem documentar o tratamento de eventos empatados no
  cutoff e o desempate estável (`session_id`, `event_index`).
- Falhas de adapter geram status `error`/`timeout` e intervalo de cobertura; não podem ser
  interpretadas como abstention correta.
- O gate de stale leak precisa declarar se o intervalo pareado inclui zero e publicar o
  número de casos por task type; a frase “com IC pareado” sozinha é insuficiente.
- `oracle` é teto de depuração e sai da tabela de produto, como já previsto; o mesmo vale
  para qualquer loader com anotação `exploratory`.

## 0. Contrato de leitura para code agents

Este documento é uma **spec executável**, não um plano diretor. Toda seção é normativa. Onde há ambiguidade, o code agent deve:

1. Consultar `operational_definitions.py` (fonte única de verdade).
2. Se ainda houver ambiguidade, **falhar explicitamente** com erro `BenchmarkSpecAmbiguity` — nunca inferir.
3. Nunca alterar pesos, thresholds ou endpoints primários para fazer um teste passar.

**Regras invioláveis:**

- Nenhum dado futuro entra no input do sistema sob teste.
- Nenhum patch/test_patch de SWE-bench entra como memória disponível.
- Nenhum peso é calibrado no split `eval`.
- Nenhuma falha é convertida silenciosamente em zero.
- Todo resultado é determinístico dado o mesmo manifesto.

---

## 1. Estrutura de diretórios (obrigatória)

```text
cortex/benchmarks/
  __init__.py
  schema.py                     # BenchmarkInstance v1, validação, coerção
  operational_definitions.py    # stale leak, contradiction, unsupported claim
  manifest.py                   # versões, checksums, ambiente, seeds
  runner.py                     # execução pareada, isolamento por caso
  metrics.py                    # métricas temporais, abstention, evidência
  stats.py                      # bootstrap pareado, Holm-Bonferroni, poder
  reports.py                    # JSONL, tabela, Pareto, Markdown
  errors.py                     # BenchmarkError, LeakageError, SchemaError, AmbiguityError
  adapters/
    __init__.py
    base.py                     # contrato adapter-neutral (ABC)
    cortex.py
    bm25.py
    bm25_temporal.py
    raw_context.py
    no_memory.py
    oracle.py
  loaders/
    __init__.py
    meme.py
    swebench.py
    longmemeval.py
  corpora/
    manifests/
    normalized/
    regression/
    adversarial/

tests/benchmarks/
  test_schema.py
  test_operational_definitions.py
  test_runner_determinism.py
  test_leakage_guard.py
  test_metrics_temporal.py
  test_metrics_abstention.py
  test_adapters_contract.py
  test_stats_bootstrap.py
  test_meme_loader.py
  test_swebench_loader.py
  test_mvp_adversarial.py

artifacts/benchmark-mvp/
artifacts/benchmark-memory-v1/
```

**Proibido:** criar um segundo harness paralelo ao existente. `cortex/benchmarks/evaluation.py` e `cortex benchmark --corpus` continuam funcionando.

---

## 2. Tipos canônicos e schema

### 2.1 `BenchmarkInstance` v1 (`schema.py`)

```python
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

AnswerState = Literal["current", "superseded", "stale", "deleted", "unknown", "out_of_scope"]
TaskType = Literal["exact_recall", "aggregation", "tracking", "deletion", "cascade", "absence"]
Source = Literal["meme", "swebench", "longmemeval", "internal"]
Split = Literal["dev", "eval", "regression"]

class Cutoff(BaseModel):
    session_index: int
    branch: str
    commit: Optional[str] = None

class Query(BaseModel):
    text: str
    files: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)

class Event(BaseModel):
    role: Literal["user", "assistant", "system", "tool", "commit", "diff", "test"]
    content: str
    timestamp: Optional[str] = None

class Session(BaseModel):
    session_id: str
    timestamp: str
    events: list[Event]

class Gold(BaseModel):
    answer: str
    accepted_answers: list[str] = Field(default_factory=list)
    current_entities: list[str] = Field(default_factory=list)
    invalid_entities: list[str] = Field(default_factory=list)
    expected_abstention: bool
    gold_evidence: list[str]
    supersession_pairs: list[tuple[str, str]] = Field(default_factory=list)
    contradiction_pairs: list[tuple[str, str]] = Field(default_factory=list)
    annotation_agreement: Optional[dict] = None
    annotation_quality: Literal["confirmatory", "exploratory"] = "confirmatory"

class Constraints(BaseModel):
    max_context_tokens: int
    allowed_future_data: Literal[False] = False

class Checksums(BaseModel):
    history: str
    gold: str

class BenchmarkInstance(BaseModel):
    schema_: Literal["cortex_memory_benchmark/v1"] = Field(alias="schema")
    id: str
    source: Source
    source_revision: str
    split: Split
    domain: str
    history: list[Session]
    cutoff: Cutoff
    query: Query
    task_type: TaskType
    gold: Gold
    constraints: Constraints
    checksums: Checksums
```

**Validações obrigatórias em `model_validator`:**

- `cutoff.session_index < len(history)`.
- `checksums.history` e `checksums.gold` são SHA-256 no formato `sha256:<hex>`.
- Se `gold.expected_abstention is True`, `gold.current_entities` e `gold.answer` devem ser vazios ou `null`.
- Se `task_type == "cascade"`, `gold.supersession_pairs` não pode ser vazio.
- Se `gold.annotation_quality == "exploratory"`, `annotation_agreement.kappa` deve existir e estar abaixo do limiar.
- Nenhum evento em `history` pode ter timestamp posterior ao cutoff.

### 2.2 Envelope de saída do adapter (`base.py`)

```python
class AdapterResult(BaseModel):
    schema_: Literal["cortex_benchmark_result/v1"] = Field(alias="schema")
    case_id: str
    adapter: str
    status: Literal["ok", "error", "timeout", "abstained"]
    retrieved: list[str]
    selected: list[str]
    answer_state: AnswerState
    abstained: bool
    abstention_reason: Optional[str]
    missing_evidence: list[str]
    evidence: list[str]
    trace: dict
    latency_ms: dict[str, float]  # {"ingest", "query", "compile"}
    tokens: dict[str, int]        # {"input", "retrieved", "compiled"}
    errors: list[str]
```

**Contrato do adapter (ABC):**

```python
class Adapter(ABC):
    name: str

    @abstractmethod
    def setup(self, instance: BenchmarkInstance) -> None:
        """Prepara estado isolado por caso. Nunca reutiliza store entre casos."""

    @abstractmethod
    def ingest(self, instance: BenchmarkInstance) -> None:
        """Ingere history até cutoff. Deve levantar LeakageError se detectar dado futuro."""

    @abstractmethod
    def query(self, instance: BenchmarkInstance) -> AdapterResult:
        """Executa query e retorna envelope completo."""
```

**Invariantes do runner:**

- Um store efêmero por caso; nenhum adapter compartilha estado.
- `ingest` nunca recebe `gold`, `patch`, `test_patch` ou sessões pós-cutoff.
- `query` nunca recebe `gold` além do que está em `instance.query`.
- Se `AdapterResult.status == "error"`, o runner **não** registra zero; registra falha e aborta o caso.

---

## 3. Definições operacionais congeladas (`operational_definitions.py`)

Estas funções são a **única** fonte de verdade para as métricas subjetivas. Nenhum adapter ou relatório pode redefini-las.

```python
def is_stale_leak(result: AdapterResult, instance: BenchmarkInstance) -> bool:
    """
    True se um item invalid/superseded/deleted aparece como:
      - resposta afirmada (answer_state == 'current' e id em invalid_entities), OU
      - instrução ativa em selected (id em invalid_entities e não marcado como inválido no trace), OU
      - fato afirmado em evidence sem marcação de supersessão.
    Falso se o item aparece apenas em 'retrieved' sem seleção.
    """

def is_contradiction_exposure(result: AdapterResult, instance: BenchmarkInstance) -> bool:
    """
    True se existe par (a, b) em gold.contradiction_pairs tal que:
      - ambos aparecem em result.selected, E
      - result.trace não marca nenhum dos dois como vigente/inválido, E
      - result.answer_state não resolve a contradição.
    """

def count_unsupported_claims(result: AdapterResult) -> int:
    """
    Conta afirmações em result.selected cujo evidence_id não resolve em result.evidence.
    Afirmação = item com campo 'claim' ou 'content' textual.
    """

def is_abstention_correct(result: AdapterResult, instance: BenchmarkInstance) -> bool:
    """
    True se result.abstained == instance.gold.expected_abstention.
    Falso se abstained sem missing_evidence preenchido.
    """

def is_deletion_compliant(result: AdapterResult, instance: BenchmarkInstance) -> bool:
    """True se nenhum id em gold.invalid_entities aparece em result.selected."""

def is_cascade_correct(result: AdapterResult, instance: BenchmarkInstance, hop: int) -> bool:
    """
    True se todos os dependentes até hop foram atualizados, e nenhum dependente
    fora do caminho evidenciado foi alterado.
    """
```

**Testes obrigatórios em `test_operational_definitions.py`:** cada função com pelo menos 3 casos canônicos (positivo, negativo, borda).

---

## 4. Endpoints primários pré-registrados

Congelados em `manifest.py`. Nenhuma alteração após o primeiro run em `eval`.

| Task type | Endpoint primário | Secundária obrigatória |
|---|---|---|
| `exact_recall` | `recall_at_k` de entidades | `evidence_resolution_rate` |
| `aggregation` | `set_f1` | `scope_accuracy` |
| `tracking` | `current_state_accuracy` | `supersession_accuracy` |
| `deletion` | `deletion_compliance` | `stale_leak_rate` |
| `cascade` | `cascade_correctness_hop1` e `hop2` separados | `lineage_completeness` |
| `absence` | `abstention_recall` | `false_certainty_rate` |

**Gate global de segurança (bloqueia release):**

- `stale_leak_rate(cortex) <= stale_leak_rate(bm25)` com IC pareado.
- `stale_leak_rate(cortex) <= stale_leak_rate(raw_context)` com IC pareado.
- `false_certainty_rate` reportado por caso.

---

## 5. Análise estatística pré-registrada (`stats.py`)

```python
def paired_bootstrap_ci(
    a: list[float], b: list[float], n_resamples: int = 10_000, alpha: float = 0.05
) -> tuple[float, float, float]:
    """Retorna (diff, ci_low, ci_high). diff = mean(a) - mean(b)."""

def holm_bonferroni(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    """Retorna máscara de rejeição. Ordem preservada."""

def power_analysis(
    baseline_rate: float, mde: float, power: float = 0.8, alpha: float = 0.05
) -> int:
    """Retorna n mínimo por braço para detectar diferença mde em proporções pareadas."""
```

**Regras:**

- Se `n < power_analysis(...)`, o relatório marca `confirmatory=False` para aquele endpoint.
- Nenhuma decisão de produto baseada em endpoint não pré-registrado.
- Correção de Holm-Bonferroni aplicada dentro de cada família (recuperação, temporalidade, abstention, evidência).

---

## 6. Baselines (contratos exatos)

Todos implementam `Adapter`. Todos recebem a mesma `BenchmarkInstance`.

| Adapter | Comportamento |
|---|---|
| `no_memory` | Retorna só `instance.query`. `abstained=True` se resposta não está no query. |
| `raw_context` | Concatena `history[:cutoff]` com truncamento determinístico (último token primeiro) até `max_context_tokens`. |
| `bm25` | Indexa `(session_id, event_index)` como unidade. Top-k sem filtro de validade. |
| `bm25_temporal` | Igual a `bm25` + filtro: descarta itens com timestamp < cutoff - `freshness_window`. |
| `cortex` | Pipeline completo: ingestão, destilação, store, ranking, filtros temporais, contradição, compilação, trace. |
| `oracle` | Usa `gold.gold_evidence` diretamente. **Só controle, nunca comparação de produto.** |

**Ablações do Cortex (flags em `cortex.py`):**

- `disable_supersession: bool = False`
- `disable_contradiction_penalty: bool = False`
- `disable_authority: bool = False`
- `disable_dense: bool = False`
- `disable_graph_density: bool = False`
- `disable_evidence_ledger: bool = False`

Cada flag é testada isoladamente em `test_adapters_contract.py`.

---

## 7. Determinismo (obrigatório para o gate)

`manifest.py` congela e propaga:

```python
class RunManifest(BaseModel):
    schema_: Literal["cortex_benchmark_manifest/v1"]
    cortex_version: str
    python_version: str
    os: str
    hardware: str
    tokenizer: str
    embedding_model: str
    embedding_version: str
    embedding_cache_dir: str
    seed: int
    retry_policy: Literal["deterministic", "off"]
    network_enabled: Literal[False]
    corpus_hash: str
    dataset_revisions: dict[str, str]
```

**Regras:**

- `network_enabled=False` no gate. Qualquer chamada de rede levanta `LeakageError`.
- Embeddings com cache por hash do input; cache fora do repo.
- Seeds fixas em `random`, `numpy`, `torch` (se aplicável) e no tokenizer.
- Versão do modelo de embedding fixada por hash, não por tag.
- Retry determinístico: mesma política, mesmo número, sem jitter.

**Teste obrigatório em `test_runner_determinism.py`:** duas execuções limpas com o mesmo manifesto produzem `metrics.jsonl` byte-idêntico (exceto `latency_ms` e timestamps de log, que ficam em arquivo separado).

---

## 8. Guarda de leakage (`errors.py` + `runner.py`)

```python
class LeakageError(BenchmarkError): ...
class SchemaError(BenchmarkError): ...
class AmbiguityError(BenchmarkError): ...
class AdapterTimeoutError(BenchmarkError): ...
```

**Checks obrigatórios antes de cada `ingest`:**

1. Nenhum evento em `history` tem timestamp > `cutoff`.
2. Nenhum campo de `gold` está acessível ao adapter (verificado por inspeção do objeto passado).
3. `checksums.history` e `checksums.gold` batem com o conteúdo.
4. Para SWE-bench: `patch` e `test_patch` não estão no store, não estão no input, não estão no trace.

**Falha em qualquer check:** aborta o caso com `LeakageError`, registra em `errors.jsonl`, não conta como zero.

**Teste obrigatório em `test_leakage_guard.py`:** injetar dado futuro em `history` e verificar `LeakageError`.

---

## 9. Loaders

### 9.1 `loaders/meme.py`

- Lê JSON original do dataset (não o viewer).
- Filtra `domain == "software_project"`.
- Preserva transcript original em `history` sem reescrita.
- Registra transformação em `instance.metadata["transform"]` (não em `history`).
- Amostragem estratificada por: `task_type`, `hop`, `history_size`, `filler_count`.
- Splits: `dev` (depuração), `eval` (congelado), `regression` (pequeno).

### 9.2 `loaders/swebench.py`

- Lê `repo`, `instance_id`, `base_commit`, `problem_statement`, `patch`, `test_patch`, `FAIL_TO_PASS`, `PASS_TO_PASS`.
- Materializa repositório em `base_commit` em ambiente isolado (worktree temporário).
- Gera eventos de engenharia a partir de commits, mensagens, diffs históricos **anteriores ao `base_commit`**.
- **Nunca** coloca `patch` ou `test_patch` no input.
- `gold.gold_evidence` = lista de arquivos/commits/símbolos anotados.
- `gold.answer` = patch de referência (usado só para avaliação).
- Protocolo de anotação: 2 anotadores, κ ≥ 0.6 para binário, κ ≥ 0.5 para ordinal; adjudicação registrada em `annotation_agreement`.

### 9.3 `loaders/longmemeval.py`

- Controle externo secundário. Fora do gate principal.
- Se o schema for incompatível, marcar `exploratory` e não bloquear release.

---

## 10. Métricas (`metrics.py`)

### 10.1 Recuperação

```python
def recall_at_k(retrieved: list[str], gold: list[str], k: int) -> float: ...
def precision_at_k(retrieved: list[str], gold: list[str], k: int) -> float: ...
def mrr(retrieved: list[str], gold: list[str]) -> float: ...
def ndcg_at_k(retrieved: list[str], gold: list[str], k: int) -> float: ...
def answer_support_recall(result: AdapterResult, instance: BenchmarkInstance) -> float: ...
def scope_accuracy(result: AdapterResult, instance: BenchmarkInstance) -> float: ...
```

Reutilizar `cortex/benchmarks/evaluation.py` onde já existir.

### 10.2 Temporalidade e segurança

```python
def current_state_accuracy(result, instance) -> float: ...
def supersession_accuracy(result, instance) -> float: ...
def stale_leak_rate(result, instance) -> float: ...
def contradiction_exposure_rate(result, instance) -> float: ...
def deletion_compliance(result, instance) -> float: ...
def cascade_correctness(result, instance, hop: int) -> float: ...
```

### 10.3 Abstention

```python
def abstention_precision(result, instance) -> float: ...
def abstention_recall(result, instance) -> float: ...
def false_certainty_rate(result, instance) -> float: ...
def selective_accuracy(result, instance) -> float: ...
def risk_coverage_curve(results: list[AdapterResult], instances) -> list[tuple[float, float]]: ...
```

### 10.4 Evidência

```python
def evidence_resolution_rate(result, instance) -> float: ...
def provenance_coverage(result, instance) -> float: ...
def lineage_completeness(result, instance) -> float: ...
def explanation_faithfulness(result, instance, counterfactual_results) -> float: ...
def unsupported_claim_rate(result, instance) -> float: ...
```

### 10.5 Eficiência

Latência p50/p95 por fase (`ingest`, `query`, `compile`); tokens (`input`, `retrieved`, `compiled`, `per_correct_answer`); tamanho do store; custo de embeddings/LLM; falhas por categoria.

---

## 11. Relatórios (`reports.py`)

Toda execução gera, em `--report-out`:

- `run_manifest.json` — manifesto completo da execução.
- `metrics.jsonl` — uma linha por (caso, adapter, métrica).
- `summary.json` — agregados por endpoint, com IC pareado e correção de Holm-Bonferroni.
- `errors.jsonl` — falhas explícitas (nunca zero silencioso).
- `leakage.jsonl` — eventos de leakage detectados.
- `pareto.json` — curvas qualidade × tokens e qualidade × latência.
- `report.md` — relatório humano, com:
  - endpoints primários por task type;
  - gates de segurança (G0–G4);
  - decisão de produto (promover / recalibrar / reduzir claim / bloquear);
  - limitações honestas e backlog priorizado por falha observada.

**Regra:** média única nunca é reportada como resultado final. Sempre por task type e por split.

---

## 12. Critérios de aceite

### G0 — Reprodutibilidade

- Duas execuções limpas com o mesmo manifesto → `metrics.jsonl` byte-idêntico (excluindo latência e log timestamps).
- Toda execução gera os 7 artefatos acima.
- Dado futuro, checksum divergente ou campo ausente invalida a execução.

### G1 — Integridade do Cortex

- `cortex benchmark --corpus` continua verde.
- `pytest tests/ -q` verde.
- Zero stale leak nos fixtures determinísticos de supersessão, validade e deletion.
- Nenhuma exceção convertida em caso passado.

### G2 — Valor relativo

- Cortex supera BM25 no endpoint primário de Tracking/Deletion/Cascade/Absence com IC pareado que não atravessa zero, após Holm-Bonferroni.
- Se não superar: publicar como diagnóstico, **não** ajustar pesos no `eval`.

### G3 — Segurança da afirmação

- `false_certainty_rate` e `unsupported_claim_rate` por caso.
- Abstention acompanhada de `abstention_reason` e `missing_evidence`.
- ≥ 95% dos itens na amostra de auditabilidade têm trace e referência resolvível ou `unverifiable`.

### G4 — Custo operacional

- p95 de `compile` ≤ 300 ms para 1k eventos em hardware de referência.
- p95 de `query` ≤ 150 ms no mesmo hardware.
- Budget de tokens respeitado exatamente.
- Ganho > 20% de p95 sem melhoria mensurável → trade-off, não ganho puro.

---

## 13. Ondas de execução

### Onda −1 — MVP vertical (obrigatório antes de tudo)

**Entregável:** 10–15 MEME `nofiller` + 5 SWE-bench + 6 baselines + relatório em `artifacts/benchmark-mvp/`.

**Critério de saída:**

- `schema.py` valida todos os casos.
- Runner produz os 7 artefatos.
- Adapter Cortex retorna envelope completo.
- Oracle produz teto superior.
- Pelo menos uma métrica temporal por task type.
- Zero leakage nos testes.
- `pytest tests/benchmarks/ -q` verde.

**Se falhar: não avançar para Onda 0.**

### Onda 0 — Congelamento

- Fixar revisões dos datasets e hashes.
- Definir splits `dev`, `eval`, `regression`.
- Documentar ambiente e comandos.
- Testes de cutoff e não ingestão do futuro.
- Validar benchmark existente.
- Casos adversariais internos: superseded + abstention.

### Onda 1 — MEME end-to-end

- `nofiller` primeiro, depois `filler32k`.
- Extração medida separadamente do ranking.
- Cobertura dos 6 task types.
- Relatório por episódio, task type, hop, tamanho, filler.

### Onda 2 — SWE-bench

- Subconjunto pequeno e estável.
- Separação entre fatos observados e inferências.
- Anotação cega com κ e adjudicação.
- Gate: 100% dos casos com cutoff, repo, base_commit, gold de arquivos e prova de ausência do patch.

### Onda 3 — Ablações e eficiência

- 3 repetições de latência.
- Grade fixa de `k` e `max_tokens`.
- Qualidade por token.
- Identificar contribuição de dense, graph, authority, freshness.

### Onda 4 — Controle externo

- LongMemEval apenas.
- Resultados separados por domínio e task type.
- Juiz LLM calibrado com amostra humana cega (se aplicável).

### Onda 5 — CI e relatório final

- Regressão pequena em PR (`< 2 min`).
- Benchmark completo em workflow noturno/manual.
- ADR de decisão.

---

## 14. Comandos alvo

```bash
# MVP
python -m cortex.benchmarks.runner \
  --manifest cortex/benchmarks/corpora/manifests/mvp.json \
  --adapter cortex bm25 bm25_temporal raw_context no_memory oracle \
  --report-out artifacts/benchmark-mvp

# Benchmark completo
python -m cortex.benchmarks.runner \
  --manifest cortex/benchmarks/corpora/manifests/memory_v1.json \
  --adapter cortex bm25 bm25_temporal raw_context no_memory oracle \
  --report-out artifacts/benchmark-memory-v1

# Compatibilidade
cortex benchmark --corpus cortex/benchmarks/corpus/engineering_v1.jsonl

# Qualidade
pytest tests/ -q
ruff check cortex tests
mypy cortex
```

---

## 15. Governança e licença

- Guardar apenas metadados, manifests, checksums e subconjuntos permitidos.
- Não commitar transcripts externos grandes sem decisão explícita.
- Cache local fora do repositório, com instruções de reconstrução.
- MEME: CC BY 4.0. LongMemEval: MIT.
- Atribuição e versão na documentação.
- Redigir segredos e tokens em material derivado de repositórios.
- Separar dados de terceiros de dados reais do Cortex.
- Não enviar transcripts ou código de SWE-bench para serviços externos por padrão.
- LLM externo na Trilha B: registrar fornecedor, modelo, retenção, consentimento.

---

## 16. Riscos e mitigação (para o code agent)

| Risco | Detecção automática | Ação |
|---|---|---|
| Leakage do futuro | `LeakageError` em `ingest` | Abortar caso, registrar em `leakage.jsonl` |
| Schema inválido | `SchemaError` em `BenchmarkInstance` | Abortar run, não contar como zero |
| Adapter timeout | `AdapterTimeoutError` | Registrar em `errors.jsonl`, não mascarar |
| Não determinismo | `metrics.jsonl` divergente entre runs | Abortar run, exigir fix |
| Média escondendo falha | endpoint primário ruim com agregado bom | Reportar por task type; bloquear release |
| Otimização para `eval` | diff de pesos após ver `eval` | Rejeitar PR; exigir justificativa em ADR |
| Anotação subjetiva | κ abaixo do limiar | Marcar `annotation_quality: exploratory` |
| Contaminação de LLM | modelo com data de corte posterior ao dataset | Marcar `contaminated: true` no relatório |

---

## 17. Decisão de produto (no relatório final)

O relatório termina em uma destas decisões, com evidência:

1. **Promover** — ganho temporal e de segurança com custo aceitável.
2. **Recalibrar** — conceito funciona, mas componente específico é o gargalo.
3. **Reduzir claim** — útil como ledger/proveniência, sem superioridade de recuperação.
4. **Bloquear expansão** — não adicionar escopo antes de resolver leakage, stale e abstention.

**Proibido:** selecionar pesos no `eval`; transformar vitória pontual em claim geral; reportar média única como resultado.

---

## 18. Resultado esperado

Ao concluir Ondas −1 a 3, o Cortex terá um benchmark reproduzível e tecnicamente defensável para sua tese: preservação de **estado, linhagem e governança** ao longo do tempo. O produto é uma curva de trade-offs com limitações honestas e backlog priorizado por falhas observadas — não um número mágico.

---

## Apêndice A — Checklist de PR para o code agent

Antes de abrir PR que toca `cortex/benchmarks/`:

- [ ] `pytest tests/ -q` verde.
- [ ] `pytest tests/benchmarks/ -q` verde.
- [ ] `ruff check cortex tests` limpo.
- [ ] `mypy cortex` limpo.
- [ ] `cortex benchmark --corpus ...` continua funcionando.
- [ ] Nenhum peso ou threshold alterado sem ADR.
- [ ] Nenhum dado futuro no input de nenhum adapter.
- [ ] Nenhum `patch`/`test_patch` no store.
- [ ] Duas execuções limpas produzem `metrics.jsonl` byte-idêntico.
- [ ] `run_manifest.json` gerado com `network_enabled=False`.
- [ ] Testes novos cobrem o comportamento adicionado.
- [ ] `operational_definitions.py` não foi redefinido em outro lugar.
- [ ] Endpoints primários inalterados (ou ADR anexado).

## Apêndice B — Arquivos que o code agent deve criar primeiro

Ordem de implementação no MVP:

1. `cortex/benchmarks/errors.py`
2. `cortex/benchmarks/schema.py`
3. `cortex/benchmarks/operational_definitions.py`
4. `cortex/benchmarks/manifest.py`
5. `cortex/benchmarks/adapters/base.py`
6. `cortex/benchmarks/adapters/no_memory.py`
7. `cortex/benchmarks/adapters/raw_context.py`
8. `cortex/benchmarks/adapters/bm25.py`
9. `cortex/benchmarks/adapters/bm25_temporal.py`
10. `cortex/benchmarks/adapters/oracle.py`
11. `cortex/benchmarks/adapters/cortex.py`
12. `cortex/benchmarks/metrics.py`
13. `cortex/benchmarks/stats.py`
14. `cortex/benchmarks/runner.py`
15. `cortex/benchmarks/reports.py`
16. `cortex/benchmarks/loaders/meme.py`
17. `cortex/benchmarks/loaders/swebench.py`
18. `tests/benchmarks/*` (na mesma ordem, teste por módulo)
