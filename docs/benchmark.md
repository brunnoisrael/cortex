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
com uma implementação RAG convencional. Ele calcula similaridade semântica
entre a consulta e cada chunk de sessão, ordena os resultados e retorna os
cinco primeiros. Por padrão usa o fallback local de n-gramas; embeddings
`model2vec` só são usados quando `CORTEX_ENABLE_DENSE_EMBEDDINGS=1`, mantendo
as execuções do benchmark offline por padrão.

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
