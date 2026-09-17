# Handoff para o próximo agente

## Prioridade 0 — `cortex_init` trava no transporte MCP stdio

Não aceite uma chamada direta da função Python como validação de MCP. Em
2026-09-16 foram observados os seguintes fatos distintos no workspace
`C:\Users\Sergio\Documents\GitHub\cortex`:

1. O servidor inicia com `python -m cortex.server.mcp_server` e um cliente
   oficial (`mcp.client.stdio`) completa `initialize()`.
2. `cortex_status` respondeu pelo mesmo transporte MCP, retornando a
   configuração e seis entidades persistidas.
3. `cortex_init(task="mcp init probe")`, chamado pelo cliente MCP após
   `initialize()`, não retorna em 15 segundos. O stderr do servidor mostra
   `Processing request of type CallToolRequest`; no encerramento por timeout,
   o cliente expõe `anyio.BrokenResourceError` no reader do stdout.
4. A mesma função, chamada diretamente em um processo isolado com
   `CORTEX_ROOT` definido, retorna rapidamente um bloco `CORTEX CONTEXT`.

Assim, a evidência atual aponta para uma falha na execução/resposta de
`cortex_init` sob FastMCP/stdio, não para descoberta do workspace nem para a
função de compilação isolada. A causa ainda é desconhecida.

### Reprodução controlada

Use o SDK MCP, não JSON-RPC escrito manualmente. Crie um
`StdioServerParameters(command="python", args=["-m",
"cortex.server.mcp_server"], env={**os.environ, "CORTEX_ROOT": workspace})`,
abra `stdio_client`, inicialize `ClientSession` e aplique
`asyncio.wait_for(..., timeout=15)` em:

```python
session.call_tool("cortex_init", arguments={"task": "mcp init probe"})
```

Compare com `cortex_status` usando o mesmo cliente. Preserve stderr e stdout
do filho separadamente. Não matar o processo `mcp_server` que já existir antes
da reprodução; ele pode pertencer ao host. Os processos filhos das sondas deste
trabalho foram encerrados.

### Próximos passos de diagnóstico

1. Adicionar um teste de integração stdio mínimo que chama `cortex_status` e
   `cortex_init`, com timeout curto e limpeza do processo filho.
2. Instrumentar temporariamente, em ordem, `_store()`, `_active_session()`,
   `capture_event()` e `compile_context()` dentro de `cortex_init` para achar o
   último ponto concluído sob FastMCP. Remover a instrumentação ou convertê-la
   em logging para stderr antes de concluir.
3. Verificar a compatibilidade da versão instalada de `mcp` com o fallback
   `FastMCP`/`MCPServer` em `cortex/server/mcp_server.py`, especialmente a
   execução de handlers síncronos e o encaminhamento de strings Unicode.
4. Depois da correção, executar o ciclo MCP completo exigido por `AGENTS.md`:
   `cortex_init`, `cortex_status`, `cortex_phase`, `cortex_recall`, captura e
   emissão durante o trabalho, seguido de `cortex_distill`, `cortex_review`,
   `cortex_retrieval_trace`, `cortex_verify` quando aplicável e `cortex_why`.

## Fase A do roadmap — estado

Concluído parcialmente nesta mudança:

- `--experiment-registry` acrescenta uma linha JSONL por execução, separada
  dos artefatos G0 determinísticos;
- cada registro traz commit/dirty state, manifesto e hash, corpus declarado e
  congelado, adapters, modelos, tokenizer, budget, ambiente, classificação,
  resultado e hashes de artefatos;
- `evidence_classification` agora é obrigatória nos manifestos versionados.

Ainda pendente, nesta ordem:

1. Gerar trechos de `README.md` e `docs/DOGFOODING_EVALUATION.md` a partir de
   registros e artefatos, eliminando números copiados manualmente.
2. Corrigir badge de testes, contagem de task types e divergências entre os
   relatórios publicados e uma execução rastreável.
3. Tornar `vector_rag` uma baseline com encoder local fixado e identificável;
   o fallback n-grama deve permanecer explícito e não ser apresentado como
   embedding denso.

Não promover resultados internos sintéticos, dogfooding, LongMemEval ou a
sonda adversarial a claim externo. A execução adversarial desta mudança teve
zero falhas de runner, mas sua decisão continua `recalibrar`.

## Validação já realizada

- `pytest` direcionado: 16 passed (runner, schema e reports afetados).
- `ruff check` dos arquivos alterados e `git diff --check`: passaram.
- MVP executado duas vezes: `summary.json` byte-idêntico.
- Adversarial executado com `cortex bm25 raw_context no_memory oracle`: zero
  erros/leakage de runner e decisão `recalibrar`.

Os artefatos de smoke estão em `artifacts/` (ignorado pelo Git); não são
resultados publicados.
