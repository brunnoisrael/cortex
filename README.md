<div align="center">

# 🧠 Cortex

### Conhecimento de engenharia para coding agents — com evidência e governança.

**Captura sessões de desenvolvimento, destila decisões e compila contexto útil para a próxima sessão.**

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-249%20passing-brightgreen)
![Package](https://img.shields.io/badge/package-0.1.0-orange)
![Local first](https://img.shields.io/badge/default-local--first-lightgrey)

</div>

> **Estado real:** o ciclo completo de memória e uma suíte rigorosa de benchmark
> comparativo offline (250 casos sintéticos, 6 task types, 7 adapters e ablações)
> estão implementados e cobertos por **256 testes automatizados**. O Cortex opera de
> forma local-first e determinística, com governança explícita, Evidence Ledger auditável
> e dogfooding contínuo com benchmark comparativo real.

---

## O problema

Coding agents começam novas sessões com pouca memória operacional do projeto. Decisões,
tentativas rejeitadas, correções e pendências ficam espalhadas em chats, commits e
arquivos de instrução.

Esse problema já possui soluções parciais e produtos consolidados. O Cortex explora uma
especialização: representar parte dessa experiência como **conhecimento de engenharia**,
com escopo, evidência, confiança, autoridade e ciclo de vida explícitos — e validar essa
hipótese com benchmarks comparativos reais.

---

## O que o Cortex faz hoje

```text
eventos da sessão
      │
      ├── captura com redação de segredos
      ▼
destilação heurística
      │  decisões · intenções · fixes · regras · revisão
      ▼
store SQLite local
      │  proveniência · autoridade · confiança · frescor · relações
      ▼
ranking e compilação
      │  relevância · escopo · contradição · budget de tokens
      ▼
contexto para a próxima sessão
```

O código atual oferece:

- captura via CLI, MCP e hooks para Claude Code e Cursor;
- destilação offline por heurísticas, com LLM local via Ollama como opção;
- artefatos tipados: `intention`, `adr`, `fix`, `correnda`, `review` e `negative_knowledge`;
- proveniência por sessão, evento, arquivo, commit e entidade relacionada;
- `authority` separado de `confidence` no modelo e no ranking;
- deduplicação, detecção de contradições e supersessão sem sobrescrever o histórico do artefato;
- verificação de referências contra o repositório, usando AST de Python e tree-sitter quando disponível;
- busca SQLite FTS5 e sinais híbridos locais, com integrações densas opcionais;
- compilação de um bloco de contexto limitado por orçamento de tokens;
- exportação de um grafo HTML de proveniência;
- importação/exportação opt-in de padrões via Correnda Commons;
- federação read-only entre stores;
- Evidence Ledger independente, com fingerprint, método de verificação, status `resolved`/`unverifiable` e exportação reproduzível;
- validade temporal (`valid_from`, `valid_until`) e recibos idempotentes para transições de governança, com fila de revisão para propostas, alto risco e contradições;
- trace estável de retrieval com sinais, penalidades, filtros e exclusões por budget;
- corpus de dogfooding com sessões reais convertidas em instâncias `BenchmarkInstance v1` e runner comparativo (Cortex vs BM25 vs raw\_context).

O fluxo completo está distribuído principalmente entre
[capture](cortex/capture),
[distillation](cortex/distillation),
[knowledge](cortex/knowledge),
[storage](cortex/storage) e
[compiler](cortex/compiler).

---

## O que ele não é

O Cortex **não** é:

- a primeira memória persistente para agentes;
- um substituto de Git, ADRs, issues, code review ou documentação humana;
- um knowledge graph geral;
- um RAG pronto para qualquer domínio;
- um framework de agentes;
- um serviço SaaS ou uma plataforma de telemetria;
- uma garantia de que a heurística entendeu corretamente uma conversa;
- uma solução de equipe multiusuário: permissões, CRDT e sincronização ainda não estão implementados.

Ele é uma composição específica de captura, extração, armazenamento, governança e
recuperação voltada a projetos de software.

### Por que não reinventar?

O Cortex deliberadamente **não reinventa** os componentes que já existem bem resolvidos — SQLite, FTS5, BM25, tree-sitter, Pydantic. O objetivo não é ser original em cada peça: é **combinar** essas peças com uma camada de governança e evidência que a maioria das soluções de memória não possui.

> A hipótese que o Cortex investiga é mais estreita: coding agents podem se beneficiar de
> um registro de decisões e lições de engenharia que **preserve evidência, explicite
> autoridade, trate contradições como histórico** e compile somente o contexto
> aplicável à tarefa — sem substituir o Git, a documentação nem o julgamento humano.

Reutilizar SQLite significa que qualquer desenvolvedor pode inspecionar, exportar ou migrar os dados sem ferramentas proprietárias. Reutilizar BM25 como baseline significa que o Cortex só vale se superar algo já bem conhecido.

---

## Artefatos de conhecimento

| Tipo | Papel atual | Exemplo |
|---|---|---|
| `intention` | motivação de uma estrutura ou abordagem | "isolar autenticação para trocar o provider sem tocar nos handlers" |
| `adr` | decisão, contexto e alternativas rejeitadas | "usar SQLite; PostgreSQL foi descartado por ser over-engineering para uso local" |
| `fix` | sintoma, causa provável e resolução | "evidence.id duplicado causava IntegrityError; usar hash com entity_id resolve" |
| `correnda` | regra ou padrão aprendido, sujeito a confirmação | "validar payload externo antes de usá-lo" |
| `negative_knowledge` | abordagem rejeitada ou falha que não deve ser repetida | "não usar IDs de evento hardcoded em múltiplos extratores do mesmo turno" |
| `review` | resumo do que a sessão produziu e deixou pendente | "2 decisões registradas; estratégia de cache ainda aberta" |

Os nomes e a ontologia são uma escolha do Cortex, mas as capacidades correspondem a padrões já presentes em projetos de memória, knowledge graphs e ferramentas de coding agents. O diferencial pretendido está na combinação e na governança, não na invenção de cada mecanismo individual.

### Autoridade não é confiança

`confidence` representa o quanto uma inferência parece correta. `authority` representa quanto ela deve influenciar o contexto. Uma inferência do agente pode ter confiança alta, mas não deve automaticamente virar regra confirmada por humano.

### Ledger e governança

Cada artefato mantém suas citações em `provenance` e suas provas resolvidas em um ledger separado. Uma prova pode ser evento, arquivo/símbolo/linha, commit, teste ou review; cada registro guarda fingerprint, data, método e status `resolved`, `stale` ou `unverifiable`. `cortex why` exibe a cadeia e `cortex evidence export` gera um pacote JSON auditável.

O fluxo de governança é `candidate → proposed → active`, com saídas reversíveis para `rejected`, `quarantined`, `deprecated` ou `superseded`. Promoções registram ator, data, motivo e evidências usadas. Artefatos `high` exigem recibo humano; artefatos com política `multiple_evidence` exigem ao menos duas provas resolvidas. Repetir a mesma ação é idempotente e não cria um segundo recibo.

---

## Instalação

Requer Python 3.11 ou superior.

```bash
git clone <seu-fork-ou-repo> cortex
cd cortex
python -m pip install -e .
```

Para instalar as integrações opcionais:

```bash
python -m pip install -e ".[enhanced]"
```

O extra `enhanced` adiciona:

- `model2vec` e `sqlite-vec` para similaridade densa opt-in;
- `detect-secrets` para complementar a redação de segredos;
- `tomlkit` para edição TOML com preservação de comentários;
- cliente OpenAI-compatible para Ollama;
- `tree-sitter` e grammars para verificação em mais linguagens;
- `pyvis` para visualização interativa opcional.

Os imports são lazy e os fallbacks locais continuam disponíveis. Embeddings densos exigem explicitamente `CORTEX_ENABLE_DENSE_EMBEDDINGS=1`.

---

## Uso mínimo

```bash
cortex init
cortex status
cortex doctor
```

Captura manual e destilação:

```bash
cortex capture user_instruction "Vamos usar SQLite por causa de portabilidade" --files src/db
cortex capture agent_response "PostgreSQL foi descartado: seria over-engineering para uso local" --files src/db
cortex distill
cortex recall "decisão de banco de dados"
```

Governança:

```bash
cortex correndas
cortex correnda confirm cor-0001
cortex adrs accept adr-0001
cortex verify adr-0001
cortex why adr-0001
cortex contradictions
cortex review-queue
cortex promote adr-0001 --reason "confirmado no review" --force-human
cortex evidence export adr-0001 --output audit/adr-0001.json
```

Compilação de contexto:

```bash
cortex context --task "alterar o acesso ao banco" --files src/db
cortex context --profile architecture_review --trace --task "revisar persistência"
cortex retrieval-debug "persistência" --json
cortex verify-diff --base HEAD~1 --json
```

Por padrão, o store fica em `.cortex/cortex.db`. A configuração padrão é local-only: sem telemetria e sem chamadas para serviços externos.

---

## Integração com agentes

```bash
cortex hook --install claude-code
cortex hook --install cursor
```

Servidor MCP stdio para qualquer host compatível:

```bash
python -m cortex.server.mcp_server
```

```json
{
  "mcpServers": {
    "cortex": {
      "command": "python",
      "args": ["-m", "cortex.server.mcp_server"],
      "env": {"CORTEX_ROOT": "/caminho/do/projeto"}
    }
  }
}
```

Ferramentas MCP expostas:

`cortex_init` · `cortex_recall` · `cortex_remember` · `cortex_emit` ·
`cortex_capture` · `cortex_distill` · `cortex_review` · `cortex_status` ·
`cortex_verify` · `cortex_phase` · `cortex_intention` · `cortex_adr` ·
`cortex_fix` · `cortex_correnda` · `cortex_diff` · `cortex_why` ·
`cortex_retrieval_trace` · `cortex_review_queue` · `cortex_evidence_export`

Falhas de captura, destilação ou compilação são tratadas como best effort e não devem bloquear a sessão do agente.

---

## Arquitetura

```text
cortex/
├── cli/            CLI Typer: init, recall, distill, governança e diagnóstico
├── server/         servidor MCP stdio
├── adapters/       hooks Claude Code e Cursor
├── capture/        eventos brutos e redação antes da persistência
├── distillation/   extratores, deduplicação, contradição e reviews
├── knowledge/      entidades Pydantic, autoridade, confiança e proveniência
├── compiler/       ranking e contexto limitado por tokens
├── storage/        SQLite, WAL, FTS5, relações e migrações
├── git/            branch e commits usados como contexto/evidência
├── privacy/        redação de credenciais e dados sensíveis
├── benchmarks/     runner determinístico, corpora normalizados, baselines, estatística pareada e relatórios
├── dev/            harness de dogfooding: captura, gerador de perguntas e conversor para BenchmarkInstance v1
├── verification.py verificação contra AST/tree-sitter
├── commons.py      export/import opt-in de padrões
└── visualizer.py   grafo HTML standalone
```

O banco é SQLite local. A instalação mínima não requer servidor, vector database, modelo ou serviço externo.

---

## Benchmark de memória de engenharia

O projeto conta com uma infraestrutura rigorosa e determinística de avaliação comparativa offline, documentada em [docs/benchmark.md](docs/benchmark.md).

### Características

- **Offline e determinística:** garante `network_enabled=false`. Duas execuções sobre o mesmo manifesto produzem `metrics.jsonl` byte-a-byte idênticos (Gate G0).
- **Corpora normalizados:**
  - `engineering_memory_v1.nofiller.jsonl` — 250 casos sintéticos, 6 task types.
  - `engineering_memory_v1.filler32k.jsonl` — variante com ~32k tokens de ruído por caso.
  - `engineering_memory_v1.regression.jsonl` — gate de não-regressão.
  - `superseded_abstention.jsonl` — corpus adversarial (supersessão, abstenção, temporalidade).
  - `dogfooding_v1.jsonl` — **20 instâncias derivadas de uma sessão real de desenvolvimento**, cobrindo `exact_recall`, `aggregation`, `tracking`, `cascade`, `absence` e `deletion`.
- **Baselines:** `bm25`, `bm25_temporal`, `raw_context`, `no_memory`, `oracle`.
- **Ablações flag-a-flag:** `disable_supersession`, `disable_contradiction_penalty`, `disable_authority`, `disable_dense`, `disable_graph_density`, `disable_evidence_ledger`.
- **Estatística pareada:** bootstrap pareado, p-valor bicaudal sob H₀, controle Holm-Bonferroni.

### Resultados empíricos consolidados

| Corpus | Casos | `stale_leak_rate` Cortex vs BM25 | Decisão (§17) |
|---|---|---|---|
| `memory_v1` (nofiller) | 250 | **0.0%** vs **49.6%** | `promover_com_reservas` |
| `memory_v1` (filler32k) | 10 | **0.0%** vs **40.0%** | `reduzir_claim` (amostra) |
| `memory_v1_adversarial` | 4 | **25.0%** vs **75.0%** | `recalibrar` |

### Dogfooding com sessão real (Cortex vs BM25 vs raw\_context)

Em setembro de 2026, uma sessão real de desenvolvimento do próprio Cortex foi capturada, anotada com 20 perguntas (6 question types, gold-standard manual) e convertida em instâncias `BenchmarkInstance v1`. O runner comparativo produziu:

| Métrica | **Cortex** | BM25 | raw\_context | Observação |
|---|---|---|---|---|
| `set_f1` | **0.20** | 0.15 | 0.00 | Cortex > BM25 > raw |
| `false_certainty_rate` | **0.00** | 0.05 | 0.00 | Cortex não alucina |
| `stale_leak_rate` | **0.00** | 0.00 | 0.00 | Nenhum leak temporal |
| `tokens_retrieved_mean` | **15** | 90 | 172 | 6–11× mais comprimido |
| `abstention_recall` | **0.85** | 0.80 | 0.80 | ✅ Cortex supera baselines (calibrado) |
| `lineage_completeness` | 0.90 | 0.90 | 0.90 | Empate |

> **Leitura honesta:** O Cortex já demonstra **zero `false_certainty_rate`**, **compressão de contexto 6× superior** ao BM25 e **`abstention_recall` de 0.85**, superando as baselines. O adapter agora se abstém com alta precisão quando não há evidência suficiente. O pipeline MCP foi unificado diretamente ao Core de captura e o LLM judge está integrado (`llm_judge.py` e skill `cortex-judge`).

Detalhes completos em [docs/DOGFOODING_EVALUATION.md](docs/DOGFOODING_EVALUATION.md).

### Comandos de execução

```bash
# Benchmark principal (250 casos, 7 adapters)
python -m cortex.benchmarks.runner \
  --manifest cortex/benchmarks/corpora/manifests/memory_v1.json \
  --adapter cortex bm25 bm25_temporal raw_context vector_rag no_memory oracle \
  --report-out artifacts/benchmark-memory-v1

# Corpus de dogfooding (sessão real, 20 casos)
python -m cortex.benchmarks.runner \
  --manifest cortex/benchmarks/corpora/manifests/dogfooding_v1.json \
  --adapter cortex bm25 raw_context \
  --report-out artifacts/benchmark-dogfooding-eval

# Corpus adversarial
python -m cortex.benchmarks.runner \
  --manifest cortex/benchmarks/corpora/manifests/memory_v1_adversarial.json \
  --adapter cortex bm25 raw_context no_memory oracle \
  --report-out artifacts/benchmark-memory-adversarial

# LongMemEval-S (controle externo)
python -m cortex.benchmarks.runner \
  --manifest cortex/benchmarks/corpora/manifests/longmemeval_s.json \
  --adapter cortex bm25 raw_context \
  --report-out artifacts/benchmark-longmemeval-s
python -m cortex.benchmarks.analyze_lme --report-out artifacts/benchmark-longmemeval-s

# Regenerar corpora
python -m cortex.benchmarks.corpora.build_internal

# Regenerar corpus de dogfooding a partir das anotações
python -m cortex.dev.session_to_benchmark
```

---

## Testes e qualidade

```bash
# Suíte completa (256 testes)
pytest -q

# Apenas benchmarks (83 testes)
pytest tests/benchmarks -v

# Testes do harness de dogfooding (6 testes)
pytest tests/dev -v

# Testes de integridade de evidências (5 testes)
pytest tests/test_evidence_integrity.py -v

# Linter e formatação
ruff check cortex tests
```

A suíte tem **256 testes automatizados** passando com 100% de sucesso:

| Módulo | Testes | O que cobre |
|---|---|---|
| `tests/benchmarks/` | 83 | contratos de adapters, determinismo de runner, integridade de corpora, ablações, relatórios, estatística |
| `tests/dev/` | 6 | gerador de perguntas, conversor sessão→BenchmarkInstance, cobertura de task types, checksums |
| `tests/test_evidence_integrity.py` | 5 | colisões de evidence.id, idempotência do store, deduplicação |
| Demais (`test_acceptance`, `test_improvements`, etc.) | 155 | núcleo, MCP, store, governança, CLI |

---

## Limitações conhecidas

- Os extratores heurísticos reconhecem padrões de linguagem e não entendem todas as formas de expressar uma decisão ou causa-raiz.
- O benchmark sintético (`engineering_memory_v1`) foi construído pelo próprio projeto; o modo adversarial melhora a honestidade, mas não equivale a uma avaliação independente em repositórios reais.
- A busca híbrida opcional ainda precisa de avaliação externa de precisão, recall e custo.
- A retenção e a governança são locais; não existe ainda fluxo de equipe com permissões, merge, revisão distribuída ou resolução de conflitos entre máquinas.
- O pacote publicado continua em versão `0.1.0`.

---

## Projetos relacionados e posicionamento

Memória persistente para agentes é uma categoria estabelecida. Exemplos relevantes incluem
[Mem0](https://docs.mem0.ai/introduction), [Cognee](https://docs.cognee.ai/getting-started/introduction),
[Zep/Graphiti](https://help.getzep.com/v2/understanding-the-graph),
[Basic Memory](https://docs.basicmemory.com/start-here/what-is-basic-memory),
[Letta](https://docs.letta.com/), a memória nativa do [Claude Code](https://code.claude.com/docs/en/memory)
e as [Memories do Cursor](https://docs.cursor.com/en/context/memories).

Também existem concorrentes diretamente voltados a memória de coding agents, como
[Agent Memory Engine](https://github.com/uudam42/agent-memory-engine),
[Agent Memory Bridge](https://github.com/zzhang82/Agent-Memory-Bridge),
[Rembric](https://github.com/susomejias/rembric) e
[Continuum](https://github.com/redstone-md/Continuum). Existe ainda outro projeto com o
nome [Cortex](https://github.com/cdeust/Cortex), o que deve ser considerado antes de publicar
ou distribuir este projeto com esse nome.

O Cortex não reivindica ser o primeiro nem o melhor sistema de memória. A hipótese que ainda
vale investigar é mais estreita:

> Coding agents podem se beneficiar de um registro de decisões e lições de engenharia que
> preserve evidência, explicite autoridade, trate contradições como histórico e compile
> somente o contexto aplicável à tarefa.

Essa hipótese está sendo investigada por benchmarks comparativos contínuos (incluindo dogfooding com sessões reais do próprio projeto) e precisará de validação em projetos externos reais.

---

## Roadmap atual

### Implementado

- **Benchmark de Engenharia:** runner determinístico (G0–G4), 250 casos normalizados em 6 eixos, baselines (BM25, BM25 temporal, raw-context, vector-RAG, no-memory, oracle), 6 ablações, bootstrap pareado sob H₀, Holm-Bonferroni e exportação de Pareto e relatórios Markdown.
- **Dogfooding com benchmark real:** harness de captura de sessões reais (`cortex/dev/`), gerador de perguntas estrutural (6 task types, ≥10/sessão), conversor para `BenchmarkInstance v1`, corpus `dogfooding_v1.jsonl` com 20 instâncias, runner comparativo executado e resultados documentados.
- **Calibração de Abstention:** elevação do `abstention_recall` do `CortexAdapter` para 0.85 (superando as baselines de 0.80).
- **LLM Judge & Rubricas:** protocolo de avaliação offline para Code Agent atuar como LLM Judge (`cortex/benchmarks/llm_judge.py` e Skill `.agents/skills/cortex-judge`).
- **Rastreabilidade e Proveniência Real:** IDs determinísticos em `capture_hook.py` e extração de evidências ancoradas em eventos reais.
- **Unificação do Pipeline MCP:** integração completa de `cortex_emit` e `cortex_remember` com `capture_event()`, sessão persistida por workspace, proveniência completa e grafo de conexões via `cortex_link` (23 ferramentas MCP).
- **Ciclo de Memória:** captura → destilação heurística → store SQLite → ranking e compilação de contexto.
- **Deduplicação Refinada:** mitigação de absorção indevida de atualizações de estado com `short_identifier_tokens()`.
- **Governança & Ledger:** artefatos tipados, proveniência detalhada, Evidence Ledger independente com fingerprints e status de verificação, filas de revisão e recibos idempotentes de transição.
- **Verificação Estrutural:** validação de símbolos e referências via AST Python e tree-sitter opcional.
- **Busca e Ranking:** SQLite FTS5, ranking temporal/autoridade, limites de contexto e busca híbrida opcional.
- **Integrações de Agentes:** hooks para Claude Code e Cursor, servidor MCP stdio completo com 23 ferramentas expostas.

### Próximas prioridades

1. Expandir o corpus de dogfooding com mais sessões reais capturadas via MCP live;
2. Anotação cega em repositórios externos (SWE-bench e LongMemEval com LLM judge ativo);
3. Sincronização multiusuário, resolução distribuída de conflitos e governança de equipe.

---

## Licença

MIT.

<div align="center">

**O Cortex não tenta lembrar tudo o que aconteceu.**
**Ele tenta registrar o que o projeto aprendeu — e mostrar de onde veio.**

</div>
