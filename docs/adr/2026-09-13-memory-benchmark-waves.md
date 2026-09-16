# ADR — Benchmark de memória v1: ondAs 0 a 5 do plano executável

**Data:** 2026-09-13
**Status:** aceito
**Referência:** `PLANO_BENCHMARK_MEMORIA_ENGINEERING.md` v3.1

## Contexto

O MVP vertical (Onda −1) já estava commitado, mas o `CortexAdapter` era um
subclass de BM25 com bandeiras de ablação apenas decorativas, o corpus era um
fixture com checksums placeholders e o runner reparava silenciosamente uma
convenção de cutoff inválida. As ondas seguintes do plano exigiam congelamento,
corpus MEME-like de verdade, gate de SWE-bench, ablações efetivas e CI.

## Decisão

### Onda 0 — Congelamento

- `manifest.py` ganhou `FrozenCorpus`, `freeze_corpus()`,
  `assert_declared_revisions()`, `assert_endpoint_table()` e `select_split()`.
  Revisão não declarada, revisão mista numa mesma fonte, endpoint primário
  alterado sem ADR e hash de corpus divergente são **erros**, não avisos.
- O runner grava o congelamento em `run_manifest.json` e passa a aceitar
  `--split`.
- A convenção implícita de cutoff do MVP virou dado: o fixture foi migrado para
  `corpora/normalized/mvp_v1.jsonl`, com sessão de fronteira explícita e
  checksums derivados. O repair silencioso foi removido do runner.

### Onda 1 — MEME end-to-end

- `adapters/cortex.py` roda o pipeline real: `KnowledgeStore` efêmero por caso →
  `DistillationEngine` (heurístico, sem rede) → política temporal →
  `rank()`/`compile_context_with_trace()` → envelope com trace e ledger.
- A política temporal tem dois sinais independentes: **recência** (mesmo
  assunto, observação posterior vence) e **contradição** (negação explícita
  posterior invalida a afirmação anterior). Cada sinal é dono de uma bandeira
  de ablação.
- Corpus interno (`corpora/build_internal.py` + arquivos commitados) cobre os
  6 task types em `dev`/`eval`/`regression`, com variante `filler32k` e corpus
  adversarial separado.
- Extração e ranking são medidos separadamente (`extraction_recall`,
  `extraction_spurious_rate` só quando o adapter reporta o que destilou).

### Onda 2 — SWE-bench

- O loader exige `repo`, `instance_id`, `base_commit`, `problem_statement`,
  `patch` e `test_patch`; sem isso o caso não entra no corpus.
- O patch é dado de avaliação (`gold.answer`) e a ausência dele é provada
  re-serializando a projeção visível ao adapter.
- Protocolo de anotação: κ ≥ 0.6 (binário) e κ ≥ 0.5 (ordinal); abaixo disso o
  caso é `exploratory` e nunca suporta claim confirmatório.

### Onda 3 — Ablações e eficiência

- `--ablation` roda o Cortex uma vez por bandeira, com rótulo estável
  `cortex[<flag>]`.
- As ablações recalculam o score a partir da própria decomposição do compiler
  (`RankedItem.reasons`), então uma bandeira não altera outro sinal.
- `latency.jsonl` guarda latência por fase e tokens; p50/p95 e custo por token
  ficam em `pareto.json`.

### Onda 4 — Controle externo

- `loaders/longmemeval.py` carrega como controle secundário, sempre
  `exploratory` sem κ humano, e nunca bloqueia release.

### Onda 5 — CI

- Workflow de benchmark: regressão rápida (corpus sem filler) em PR e
  benchmark completo (filler32k + adversarial) em job agendado/manual.

## Consequências e limitações honestas

- **Resultado observado:** no corpus confirmatório (`memory_v1`, com e sem
  filler) o Cortex não vaza estado obsoleto (`stale_leak_rate` 0.0 contra 0.4
  de BM25 e raw_context) e a decisão é `promover_com_reservas`. No corpus
  adversarial a decisão é `recalibrar` (stale leak 0.5), pela lacuna abaixo.
- **Lacuna documentada, correção proposta (não verificada em execução):**
  declarações quase idênticas no mesmo escopo eram fundidas pelo dedup da
  destilação, que absorvia a atualização de estado em vez de preservar a
  linhagem. O caso `adv-dedup-absorbs-update` existe para manter essa falha
  visível em vez de escondê-la numa média.
  Causa raiz identificada: `statement_tokens()` (`extractors.py`) descarta
  tokens com ≤2 caracteres, então `"s3-artifacts"` e `"s3-artifacts-v2"`
  colapsam para o mesmo conjunto de tokens e `statement_similarity` retorna
  1.0 — acima do limiar de dedup (0.75) — apesar de o sufixo de versão ser
  exatamente o que mudou. Patch aplicado em `_find_duplicate`
  (`distillation/engine.py`): além do limiar de similaridade, agora exige
  que os tokens curtos descartados (`short_identifier_tokens`) sejam iguais
  entre candidato e entidade existente antes de mesclar; quando divergem,
  a nova observação vira uma entidade própria, e `_apply_temporal_policy`
  (que já roda depois de `distill_all` com `SUPERSESSION_SIMILARITY = 0.5`)
  passa a poder supersedê-la corretamente. **Este patch foi rastreado
  manualmente linha a linha, não executado** — o ambiente de rede
  restrita usado para escrevê-lo não tinha `pydantic` instalável para rodar
  `pytest`. `test_dedup_no_longer_absorbs_a_state_update` (antigo
  `test_known_gap_dedup_absorbs_a_state_update`) documenta os valores
  esperados pós-fix e deve ser a primeira coisa a rodar antes de aceitar
  esta ADR como resolvida.
- `corpus_hash` do manifesto é o hash do **arquivo**; o congelamento por caso
  (`frozen.corpus_hash`) é o hash do conteúdo normalizado. São dois níveis de
  verificação, ambos gravados no `run_manifest.json`.
- O corpus filler32k tem ~4 MB de ruído sintético internamente gerado. É
  commitado porque G0 exige hash congelado verificável; não há transcript de
  terceiros no repositório.
- `summary.json` é determinístico (G0); latência e o gate G4 ficam em
  `pareto.json`/`latency.jsonl`, como o plano §7 determina.
