# Benchmark de memória de engenharia

Execução do plano `PLANO_BENCHMARK_MEMORIA_ENGINEERING.md` (v3.1), ondAs −1 a 5.
Tudo roda **offline**: `network_enabled=false` é obrigatório e a destilação é
heurística.

## Comandos

```bash
# Onda 1 — corpus interno, sem filler (rápido; é o que roda em PR)
python -m cortex.benchmarks.runner \
  --manifest cortex/benchmarks/corpora/manifests/memory_v1.json \
  --adapter cortex bm25 bm25_temporal raw_context vector_rag no_memory oracle \
  --report-out artifacts/benchmark-memory-v1

# Onda 3 — com ablações do Cortex, uma execução por bandeira
python -m cortex.benchmarks.runner \
  --manifest cortex/benchmarks/corpora/manifests/memory_v1.json \
  --adapter cortex bm25 raw_context --ablation \
  --report-out artifacts/benchmark-memory-v1-ablations

# Onda 1 — variante com filler (~32k tokens por caso; lenta, ~3 min)
python -m cortex.benchmarks.runner \
  --manifest cortex/benchmarks/corpora/manifests/memory_v1_filler32k.json \
  --adapter cortex bm25 raw_context no_memory oracle \
  --report-out artifacts/benchmark-memory-v1-filler32k

# Corpus adversarial (diagnóstico; separado do corpus confirmatório)
python -m cortex.benchmarks.runner \
  --manifest cortex/benchmarks/corpora/manifests/memory_v1_adversarial.json \
  --adapter cortex bm25 raw_context no_memory oracle \
  --report-out artifacts/benchmark-memory-adversarial

# Controle externo LongMemEval-S (diagnóstico; annotation_quality=exploratory)
# Requer data/longmemeval_s_cleaned.json (gitignored) normalizado uma vez:
#   python -m cortex.benchmarks.loaders.longmemeval_native \
#     data/longmemeval_s_cleaned.json \
#     cortex/benchmarks/corpora/external/longmemeval_s.jsonl
python -m cortex.benchmarks.runner \
  --manifest cortex/benchmarks/corpora/manifests/longmemeval_s.json \
  --adapter cortex bm25 raw_context \
  --report-out artifacts/benchmark-longmemeval-s
python -m cortex.benchmarks.analyze_lme --report-out artifacts/benchmark-longmemeval-s

# MVP congelado (Onda −1) e benchmark legado
python -m cortex.benchmarks.runner --manifest cortex/benchmarks/corpora/manifests/mvp.json \
  --adapter cortex bm25 oracle --report-out artifacts/benchmark-mvp
cortex benchmark --corpus cortex/benchmarks/corpus/engineering_v1.jsonl

# Só um split
python -m cortex.benchmarks.runner --manifest ... --adapter cortex --split eval --report-out ...

# Qualidade
pytest tests/benchmarks -q
ruff check cortex tests && mypy
```

## Artefatos de uma execução

| Arquivo | Conteúdo | Determinístico |
|---|---|---|
| `run_manifest.json` | manifesto + congelamento (hashes por caso, splits, revisões) | sim |
| `metrics.jsonl` | uma linha por (caso, adapter, métrica) | sim |
| `summary.json` | agregados por task type, IC pareado, gates G0–G3, decisão | sim |
| `errors.jsonl` | falhas explícitas (nunca viram zero) | sim |
| `leakage.jsonl` | eventos de leakage detectados | sim |
| `latency.jsonl` | latência por fase e tokens | **não** |
| `pareto.json` | qualidade × tokens × latência, p50/p95, gate G4 | **não** |
| `report.md` | relatório humano | sim |

G0 exige que duas execuções limpas produzam `metrics.jsonl` byte-idêntico; por
isso latência vive em arquivo separado (plano §7).

### Registro versionável de experimentos

Para um resultado que será citado, forneça um registro JSONL versionado pelo
repositório ou pelo estudo. O runner acrescenta **uma linha por execução** com
o commit e estado dirty, manifesto e seus hashes, corpus congelado, adapters,
modelo de embedding/leitor, orçamento de contexto, ambiente, classificação de
evidência e hashes dos artefatos. Ele fica fora dos artefatos determinísticos,
pois hora e hardware variam entre execuções.

```bash
python -m cortex.benchmarks.runner \
  --manifest cortex/benchmarks/corpora/manifests/memory_v1.json \
  --adapter cortex bm25 bm25_temporal raw_context vector_rag no_memory oracle \
  --report-out artifacts/benchmark-memory-v1 \
  --experiment-registry benchmarks/experiment_registry.jsonl
```

O arquivo só é alterado quando `--experiment-registry` é fornecido; assim os
testes e execuções exploratórias locais não modificam silenciosamente um
registro publicado. `evidence_classification` no manifesto é obrigatório como
metadado semântico do estudo: `confirmatory` vale apenas para a hipótese e o
corpus explicitamente delimitados; controles externos, dogfooding e diagnósticos
adversariais permanecem `exploratory`.

## Corpora

| Arquivo | Uso |
|---|---|
| `corpora/normalized/mvp_v1.jsonl` | MVP (Onda −1) congelado |
| `corpora/normalized/engineering_memory_v1.nofiller.jsonl` | corpus principal (PR/CI) |
| `corpora/normalized/engineering_memory_v1.filler32k.jsonl` | mesmo gold, ~32k tokens de ruído por caso |
| `corpora/adversarial/superseded_abstention.jsonl` | sondas de falha conhecidas |
| `corpora/external/longmemeval_s.jsonl` | LongMemEval-S normalizado (gitignored; diagnostic only) |
| `corpora/manifests/*.json` | manifests que pinam revisões, hash e a tabela de endpoints |

Os corpora internos são **sintéticos e autorais** (sem transcript de
terceiros). O gerador `corpora/build_internal.py` está commitado junto com a
saída; um teste garante que ambos coincidem. Para regenerar:

```bash
python -m cortex.benchmarks.corpora.build_internal
```

Alterar um corpus muda o `corpus_hash` pinado no manifesto e a execução falha
até o manifesto ser atualizado conscientemente.

## Endpoints pré-registrados

A tabela de `manifest.py::PRIMARY_ENDPOINTS` é congelada por
`endpoint_table_digest()`; um manifesto pode pinar o digest (os de `memory_v1`
pinam). Mudar um endpoint sem ADR derruba a execução.

## Decisão de produto

`summary.json` termina em uma de quatro decisões do plano §17: `promover`,
`recalibrar`, `reduzir_claim`, `bloquear_expansao`. Leitura atual:

| Execução | Decisão | `stale_leak_rate` cortex / bm25 |
|---|---|---|
| `benchmark-memory-v1` (nofiller, 250 casos) | `promover_com_reservas` | 0.0 / 0.50 |
| `benchmark-memory-v1-filler32k` (10 casos) | `reduzir_claim` | 0.0 / 0.40 |
| `benchmark-memory-adversarial` (4 casos) | `recalibrar` | 0.25 / 0.75 |

A lacuna do ADR de 2026-09-13 (dedup absorve atualização de estado com identificadores
curtos como v1/v2) foi sanada com `short_identifier_tokens()`, reduzindo o
`stale_leak_rate` no corpus adversarial de 0.50 para 0.25 (o caso remanescente
trata de abstenção em supersessão sem evidência direta).

## Baseline `vector_rag`

O adapter `vector_rag` é uma baseline densa e determinística para comparação
com uma implementação RAG convencional. Usa o encoder local fixo
`hash-ngrams/v1`, calcula similaridade cosseno entre a consulta e cada chunk
de sessão e retorna os cinco primeiros. O encoder não baixa pesos e seu nome
é registrado no trace e no registro de experimentos.

O fallback n-grama de `dense_semantic_similarity` continua disponível para
componentes de produção, mas não é usado silenciosamente como baseline
vetorial e não deve ser descrito como embedding denso.

Essa baseline é deliberadamente ingênua: não aplica autoridade, supersessão,
invalidação, Evidence Ledger ou abstenção epistemológica. Assim, ela mede o
ganho da governança do Cortex contra recuperação densa sem interpretação de
estado, e não representa uma integração com um banco vetorial externo.

Para executá-la isoladamente:

```bash
python -m cortex.benchmarks.runner \
  --manifest cortex/benchmarks/corpora/manifests/memory_v1.json \
  --adapter vector_rag \
  --report-out artifacts/benchmark-memory-v1-vector-rag
```

## Leitor fixo da Fase B

O adapter `cortex` compila o contexto e o entrega exclusivamente ao leitor
determinístico `cortex.reader/v1`. O leitor só pode citar IDs presentes no
bloco compilado; afirmações sem suporte lexical suficiente tornam-se
abstenções e evidências marcadas como superseded, stale ou deleted não são
respondidas como estado atual. `summary.json` registra separadamente
`reader_support_factual`, `reader_fidelity`, `reader_abstention_accuracy`,
`reader_final_response_accuracy` e `reader_citation_validity`, sem misturá-las
às métricas de recuperação.

Na execução `benchmark-memory-v1-phase-b-reader` (250 casos, corpus congelado
`sha256:7736bdcacccffc20ffdb5b520aee45fda302b813a2aecb94ab9dd006e720e73e`,
budget 4096), as médias do adapter Cortex foram: suporte factual 1.000,
fidelidade 1.000, validade de citação 1.000, acurácia de abstenção 0.828 e
acurácia da resposta final 0.824. A execução foi classificada como
`confirmatory` apenas para as invariantes deste corpus interno; não é claim
geral sobre agentes ou datasets externos.

## Leitor fixo da Fase B

O adapter `cortex` compila o contexto e o entrega exclusivamente ao leitor
determinístico `cortex.reader/v1`. O leitor só pode citar IDs presentes no
bloco compilado; afirmações sem suporte lexical suficiente tornam-se
abstenções e evidências marcadas como superseded, stale ou deleted não são
respondidas como estado atual. `summary.json` registra separadamente
`reader_support_factual`, `reader_fidelity`, `reader_abstention_accuracy`,
`reader_final_response_accuracy` e `reader_citation_validity`, sem misturá-las
às métricas de recuperação.

Esses resultados internos validam apenas as invariantes do corpus congelado e
continuam confirmatórios para esse corpus, não constituindo claim geral sobre
agentes ou datasets externos.
