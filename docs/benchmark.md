# Benchmark de memória de engenharia

Execução do plano `PLANO_BENCHMARK_MEMORIA_ENGINEERING.md` (v3.1), ondAs −1 a 5.
Tudo roda **offline**: `network_enabled=false` é obrigatório e a destilação é
heurística.

## Comandos

```bash
# Onda 1 — corpus interno, sem filler (rápido; é o que roda em PR)
python -m cortex.benchmarks.runner \
  --manifest cortex/benchmarks/corpora/manifests/memory_v1.json \
  --adapter cortex bm25 bm25_temporal raw_context no_memory oracle \
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
| `benchmark-memory-v1` (nofiller) | `promover_com_reservas` | 0.0 / 0.4 |
| `benchmark-memory-v1-filler32k` | `promover_com_reservas` | 0.0 / 0.4 |
| `benchmark-memory-adversarial` | `recalibrar` | 0.5 / 0.75 |

A lacuna que motiva `recalibrar` no corpus adversarial está no ADR de
2026-09-13: o dedup da destilação absorve atualizações de estado quando as
declarações são quase idênticas.
