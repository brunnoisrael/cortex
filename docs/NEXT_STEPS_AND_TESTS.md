# Próximos passos e testes do Cortex

Este documento executa o plano do [`AGENTS.md`](../AGENTS.md) e do
[`RESEARCH_ROADMAP.md`](RESEARCH_ROADMAP.md). Ele não substitui essas regras.
O objetivo é avançar a hipótese do Cortex: memória governada por evidência,
com autoridade, escopo, validade temporal, supersessão, linhagem e abstenção
mensuráveis.

## 1. Ativar o MCP local no Codex

O Cortex já possui servidor stdio. No PowerShell, a partir de qualquer
diretório, registre-o no cliente Codex:

```powershell
codex mcp add cortex --env CORTEX_ROOT=C:\Users\Sergio\Documents\GitHub\cortex -- python -m cortex.server.mcp_server
codex mcp get cortex
codex mcp list
```

Se houver mais de um Python instalado, use o executável absoluto retornado por
`(Get-Command python).Source` no lugar de `python`. O repositório deve estar
instalado no mesmo ambiente:

```powershell
python -m pip install -e .
python -m cortex.cli.app init
```

Depois de registrar o servidor, reinicie o Codex Desktop ou abra uma nova
task. A configuração local não altera o inventário de ferramentas de uma task
já em execução. A primeira verificação da nova task deve chamar, nesta ordem:

```text
cortex_init
cortex_status
cortex_phase
cortex_recall
```

Durante o trabalho, registre eventos com `cortex_capture` e decisões/riscos
com `cortex_emit`. Ao terminar, execute `cortex_distill`, `cortex_review`,
`cortex_retrieval_trace`, `cortex_verify` quando aplicável e `cortex_why` ou
`cortex_evidence_export` antes do relatório final.

Diagnóstico mínimo se falhar:

```powershell
codex mcp get cortex
python -c "import mcp; print(mcp.__file__)"
$env:CORTEX_ROOT='C:\Users\Sergio\Documents\GitHub\cortex'
python -m cortex.server.mcp_server
```

O último comando deve permanecer aguardando entrada stdio; não é um teste de
sucesso por si só. A validação real deve usar um cliente MCP SDK e comparar
`cortex_status` com `cortex_init`, preservando stdout e stderr separados. Não
usar JSON-RPC escrito manualmente como evidência de integração.

## 2. Ordem de execução

### P0 — fechar o transporte MCP

1. Reproduzir `initialize`, `cortex_status` e `cortex_init` com
   `mcp.client.stdio` e timeout de 15 s.
2. Se `cortex_init` travar, instrumentar somente em stderr `_store`,
   `_active_session`, `capture_event` e `compile_context`.
3. Adicionar teste de integração que encerre o processo filho sempre, sem
   matar um servidor MCP pré-existente.
4. Corrigir o ponto de bloqueio e repetir o ciclo MCP completo do `AGENTS.md`.

Aceitação: `cortex_init` e `cortex_status` respondem pelo mesmo transporte,
sem chamar funções Python diretamente como substituto.

Diagnóstico reproduzido em 2026-09-17: com `mcp` 1.29.1, o servidor completou
`cortex_init` e enviou JSON-RPC válido, mas o cliente stdio deixou o leitor de
stdout bloqueado na primeira chamada após `initialize`. O harness reproduzível
deve disparar `list_tools()` concorrente durante a chamada e manter
`stdio_client` em `async with`, garantindo que o processo filho seja encerrado.
Isso é uma limitação observada do SDK/harness; não deve ser apresentada como
registro do servidor no Codex Desktop.

### P1 — Fase B: contexto para resposta

Implementar um leitor determinístico que receba exclusivamente o contexto
compilado. Cada afirmação verificável deve carregar IDs de evidência. O leitor
deve produzir uma saída estruturada com:

- resposta ou `abstention`;
- afirmações e IDs citados;
- suporte `supported`, `partial` ou `unsupported`;
- motivo da abstenção;
- trace do conjunto de evidências recebido.

Implementado em `cortex/reader.py`; a resposta final e as métricas do leitor
ficam no trace do `CortexAdapter`, sem contaminar as métricas de recuperação.

Testes obrigatórios:

1. não citar ID ausente no contexto;
2. não responder com certeza quando só há evidência obsoleta;
3. aceitar pergunta histórica quando o cutoff pedir histórico;
4. preservar autoridade inferida sem promovê-la a confirmação humana;
5. reproduzir a mesma saída para histórico, cutoff e configuração iguais.

### P2 — Fase C: propriedades da tese

Adicionar histórias geradas com updates, negações, duplicatas, eventos fora de
ordem e consultas históricas. Cada propriedade precisa de caso positivo,
adversarial e contraexemplo documentado quando falhar:

| Propriedade | Invariante | Métrica/teste |
|---|---|---|
| Proveniência | todo item compilado alcança uma fonte observável | cobertura de linhagem |
| Não-ressurreição | supersedido não aparece no estado atual | `stale_leak_rate` |
| Autoridade | inferência não vira confirmação sem transição autorizada | teste de transição |
| Abstenção | falta de suporte produz abstention | recall/precisão de abstention |
| Reprodutibilidade | mesmo input produz mesmo conjunto e trace | hash byte a byte |

## 3. Testes locais e benchmarks

Rodar primeiro a suíte determinística:

```powershell
python -m pytest -q
ruff check cortex/benchmarks tests/benchmarks
git diff --check
```

Depois, o benchmark interno confirmatório, sem promover automaticamente seu
resultado a evidência externa:

```powershell
python -m cortex.benchmarks.corpora.build_internal
python -m cortex.benchmarks.runner `
  --manifest cortex/benchmarks/corpora/manifests/memory_v1.json `
  --adapter cortex bm25 bm25_temporal raw_context vector_rag no_memory oracle `
  --report-out artifacts/benchmark-memory-v1 `
  --experiment-registry docs/experiments.jsonl
```

O registro deve conter commit, estado dirty, manifesto, hashes do corpus,
adapters, encoder, orçamento, ambiente, classificação e hashes dos artefatos.
Resultados com corpus sintético continuam confirmatórios somente para aquela
hipótese e aquele corpus.

Dogfooding:

```powershell
python -m cortex.benchmarks.runner `
  --manifest cortex/benchmarks/corpora/manifests/dogfooding_v1.json `
  --adapter cortex bm25 bm25_temporal raw_context vector_rag no_memory oracle `
  --report-out artifacts/benchmark-dogfooding-v1 `
  --experiment-registry docs/experiments.jsonl
```

## 4. Dados externos: o que baixar e como usar

A prioridade é usar dados com histórico, cutoff e resposta gold explícitos.
Kaggle não é prioridade neste ciclo: sem revisão de licença, versão,
timestamps e gold auditável, ele pode aumentar volume sem testar a tese.

### LongMemEval-S — controle externo de memória

Usar o repositório dos autores e a versão cleaned-S. O loader existente deve
normalizar o arquivo local e marcar cada caso como `exploratory`; não usar esse
domínio de conversas pessoais para claim confirmatório de engenharia.

```powershell
python -m cortex.benchmarks.loaders.longmemeval_native `
  data/longmemeval_s_cleaned.json `
  cortex/benchmarks/corpora/external/longmemeval_s.jsonl
python -m cortex.benchmarks.runner `
  --manifest cortex/benchmarks/corpora/manifests/longmemeval_s.json `
  --adapter cortex bm25 raw_context vector_rag `
  --report-out artifacts/benchmark-longmemeval-s `
  --experiment-registry docs/experiments.jsonl
```

### LongMemEval-V2 — próximo controle agentivo

Entrará depois do P0/P1. Ele é mais próximo da tese por incluir trajetórias de
agente e estado dinâmico, mas exige um adapter que preserve eventos, ações,
ambiente e cutoff. Primeiro implementar um subconjunto pequeno e reproduzível;
não baixar o corpus completo sem definir custo, licença, hash e orçamento.

### SWE-bench / SWE-bench Verified — resultado downstream

Baixar pelo Hugging Face `datasets` ou pelo repositório oficial e selecionar
um split pequeno para desenvolvimento. O patch gold, testes gold e qualquer
resposta futura ficam fora da memória no cutoff. O caso só é contado quando a
memória é construída com episódios anteriores e o agente resolve a issue sob
o mesmo modelo, ferramentas, tempo e orçamento do controle sem memória.

```powershell
python -m pip install datasets
python -c "from datasets import load_dataset; ds=load_dataset('princeton-nlp/SWE-bench', split='dev'); print(ds)"
pytest tests/benchmarks/test_loaders.py -k swebench -q
```

Aceitação externa mínima:

1. fonte, licença, revisão e hash registrados;
2. transformação determinística e testada;
3. cutoff impede vazamento de patch/testes gold;
4. anotações e acordo entre anotadores reportados, ou classe explicitamente
   `exploratory`;
5. comparação pareada com sem memória, full-context controlado, BM25,
   vector-RAG, baseline estruturada e Cortex;
6. casos de falha publicados individualmente, sem `skip` ou média que esconda
   leakage, falta de suporte ou falha de extração.

## 5. Critério de parada

Não declarar a tarefa concluída enquanto faltar qualquer item abaixo:

- MCP real validado ou indisponibilidade explicitamente registrada;
- teste determinístico e teste adversarial da propriedade alterada;
- artefato de benchmark com manifesto e hashes;
- documentação derivada do artefato;
- resultado classificado como `confirmatory` ou `exploratory`;
- regressões da tese e limitações listadas no relatório final.

O objetivo do próximo ciclo não é maximizar uma média de retrieval. É medir se
o Cortex reduz stale leakage e falsa certeza sem perder utilidade downstream,
com menos contexto e com uma cadeia de evidência que possa ser auditada.
