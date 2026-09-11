<div align="center">

# 🧠 Cortex

### Conhecimento de engenharia para coding agents — com evidência e governança.

**Um protótipo local-first que captura sessões de desenvolvimento, destila decisões e compila contexto útil para a próxima sessão.**

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-142%20passing-brightgreen)
![Package](https://img.shields.io/badge/package-0.1.0-orange)
![Local first](https://img.shields.io/badge/default-local--first-lightgrey)

</div>

> **Estado real:** o ciclo principal está implementado e coberto por testes, mas o
> Cortex ainda é um MVP técnico. A extração heurística é limitada, a validação
> comparativa é incompleta e o projeto não deve ser tratado como produto de produção
> ou como uma nova categoria de memória para agentes.

## O problema

Coding agents começam novas sessões com pouca memória operacional do projeto. Decisões,
tentativas rejeitadas, correções e pendências ficam espalhadas em chats, commits e
arquivos de instrução.

Esse problema já possui soluções parciais e produtos consolidados. O Cortex explora uma
especialização: representar parte dessa experiência como **conhecimento de engenharia**,
com escopo, evidência, confiança, autoridade e ciclo de vida explícitos.

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
- artefatos tipados: `intention`, `adr`, `fix`, `correnda`, `review` e
  `negative_knowledge`;
- proveniência por sessão, evento, arquivo, commit e entidade relacionada;
- `authority` separado de `confidence` no modelo e no ranking;
- deduplicação, detecção de contradições e supersessão sem sobrescrever o histórico do
  artefato;
- verificação de referências contra o repositório, usando AST de Python e tree-sitter
  quando disponível;
- busca SQLite FTS5 e sinais híbridos locais, com integrações densas opcionais;
- compilação de um bloco de contexto limitado por orçamento de tokens;
- exportação de um grafo HTML de proveniência;
- importação/exportação opt-in de padrões via Correnda Commons;
- federação read-only entre stores.
- um Evidence Ledger separado das citações de proveniência, com fingerprint, método de
  verificação, status `resolved`/`unverifiable` e exportação reproduzível;
- validade temporal (`valid_from`, `valid_until`) e recibos idempotentes para transições de
  governança, com fila de revisão para propostas, alto risco e contradições;
- trace estável de retrieval, com sinais, penalidades, filtros, seleção e exclusões por
  budget;
- verificação de impacto por diff e um corpus versionado para medir recall, precision, MRR,
  nDCG, latência e tokens injetados.

O fluxo completo está distribuído principalmente entre
[capture](C:/Users/Sergio/Documents/GitHub/cortex/cortex/capture),
[distillation](C:/Users/Sergio/Documents/GitHub/cortex/cortex/distillation),
[knowledge](C:/Users/Sergio/Documents/GitHub/cortex/cortex/knowledge),
[storage](C:/Users/Sergio/Documents/GitHub/cortex/cortex/storage) e
[compiler](C:/Users/Sergio/Documents/GitHub/cortex/cortex/compiler).

## O que ele não é

O Cortex não é:

- a primeira memória persistente para agentes;
- um substituto de Git, ADRs, issues, code review ou documentação humana;
- um knowledge graph geral;
- um RAG pronto para qualquer domínio;
- um framework de agentes;
- um serviço SaaS ou uma plataforma de telemetria;
- uma garantia de que a heurística entendeu corretamente uma conversa;
- uma solução de equipe multiusuário: permissões, CRDT e sincronização ainda não estão
  implementados.

Ele é uma composição específica de captura, extração, armazenamento, governança e
recuperação voltada a projetos de software.

## Artefatos de conhecimento

| Tipo | Papel atual | Exemplo |
|---|---|---|
| `intention` | motivação de uma estrutura ou abordagem | “isolar autenticação para trocar o provider sem tocar nos handlers” |
| `adr` | decisão, contexto e alternativas rejeitadas | “usar PostgreSQL; MongoDB foi rejeitado por não haver necessidade de schema flexível” |
| `fix` | sintoma, causa provável e resolução | “payload nulo causava TypeError; adicionar validação antes do destructuring” |
| `correnda` | regra ou padrão aprendido, sujeito a confirmação | “validar payload externo antes de usá-lo” |
| `negative_knowledge` | abordagem rejeitada ou falha que não deve ser repetida | “não usar MongoDB neste domínio” |
| `review` | resumo do que a sessão produziu e deixou pendente | “2 decisões registradas; estratégia de cache ainda aberta” |

Os nomes e a ontologia são uma escolha do Cortex, mas as capacidades correspondem a
padrões já presentes em projetos de memória, knowledge graphs e ferramentas de coding
agents. O diferencial pretendido está na combinação e na governança, não na invenção de
cada mecanismo individual.

### Autoridade não é confiança

`confidence` representa o quanto uma inferência parece correta. `authority` representa
quanto ela deve influenciar o contexto. Uma inferência do agente pode ter confiança alta,
mas não deve automaticamente virar regra confirmada por humano.

### Ledger e governança

Cada artefato mantém suas citações em `provenance` e suas provas resolvidas em um ledger
separado. Uma prova pode ser evento, arquivo/símbolo/linha, commit, teste ou review; cada
registro guarda fingerprint, data, método e status `resolved`, `stale` ou `unverifiable`.
`cortex why` exibe a cadeia e `cortex evidence export` gera um pacote JSON auditável.

O fluxo de governança é `candidate → proposed → active`, com saídas reversíveis para
`rejected`, `quarantined`, `deprecated` ou `superseded`. Promoções registram ator, data,
motivo e evidências usadas. Artefatos `high` exigem recibo humano; artefatos com política
`multiple_evidence` exigem ao menos duas provas resolvidas. Repetir a mesma ação é
idempotente e não cria um segundo recibo.

Esse princípio é aplicado no ranking. Ainda assim, a extração atual é majoritariamente
heurística; os campos não transformam uma afirmação em verdade.

### Histórico e retenção

Artefatos superseded, rejected ou contraditos continuam consultáveis no store, embora
normalmente saiam do contexto padrão. Isso preserva a linhagem das decisões.

Eventos brutos têm retenção configurável e podem ser removidos após a destilação. Portanto,
“não apagar histórico” refere-se ao histórico de conhecimento persistido, não a uma
retenção indefinida de todos os transcripts.

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

Os imports são lazy e os fallbacks locais continuam disponíveis. Embeddings densos
exigem explicitamente `CORTEX_ENABLE_DENSE_EMBEDDINGS=1`.

## Uso mínimo

Dentro do projeto que receberá a memória:

```bash
cortex init
cortex status
cortex doctor
```

Captura manual e destilação:

```bash
cortex capture user_instruction "Vamos usar PostgreSQL por causa de ACID" --files src/db
cortex capture agent_response "MongoDB foi rejeitado porque o schema é previsível" --files src/db
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
cortex benchmark --corpus cortex/benchmarks/corpus/engineering_v1.jsonl
```

Por padrão, o store fica em `.cortex/cortex.db`. A configuração padrão é local-only:
sem telemetria e sem chamadas para serviços externos. Ollama local pode ser habilitado;
chamadas de rede não-loopback exigem configuração explícita.

## Integração com agentes

Os adaptadores implementados hoje são Claude Code e Cursor:

```bash
cortex hook --install claude-code
cortex hook --install cursor
```

O Cortex também expõe um servidor MCP stdio para qualquer host compatível:

```bash
python -m cortex.server.mcp_server
```

Exemplo de configuração:

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

O servidor expõe ferramentas MCP para bootstrap, captura, destilação, governança,
retrieval trace e exportação do ledger:

`cortex_init` · `cortex_recall` · `cortex_remember` · `cortex_emit` ·
`cortex_capture` · `cortex_distill` · `cortex_review` · `cortex_status` ·
`cortex_verify` · `cortex_phase` · `cortex_intention` · `cortex_adr` ·
`cortex_fix` · `cortex_correnda` · `cortex_diff` · `cortex_why` ·
`cortex_retrieval_trace` · `cortex_review_queue` · `cortex_evidence_export`

`cortex_emit` permite que o agente registre uma decisão, fix ou regra estruturada no
momento em que ela acontece. Ainda é uma emissão feita pelo agente: o Cortex não consegue
provar, sozinho, que houve confirmação humana.

Falhas de captura, destilação ou compilação são tratadas como best effort e não devem
bloquear a sessão do agente. Isso melhora a tolerância do host, mas também significa que
falhas precisam ser observadas por logs, `status` e `doctor`.

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
├── verification.py verificação contra AST/tree-sitter
├── commons.py      export/import opt-in de padrões
└── visualizer.py   grafo HTML standalone
```

O banco é SQLite local. A instalação mínima não requer servidor, vector database, modelo
ou serviço externo. As integrações enriquecidas são opt-in e não substituem o caminho
local de fallback.

## Limitações conhecidas

- Os extratores heurísticos reconhecem padrões de linguagem e não entendem todas as formas
  de expressar uma decisão ou causa-raiz.
- O benchmark CCB contém uma fixture sintética; a própria documentação do projeto registra
  que a fixture original era próxima dos gatilhos dos extratores.
- O modo adversarial melhora a honestidade do benchmark, mas ainda não equivale a uma
  avaliação independente em repositórios reais.
- A busca híbrida opcional ainda precisa de avaliação externa de precisão, recall e custo.
- A verificação estrutural melhora a evidência de referências, mas não prova que uma decisão
  arquitetural é boa.
- A retenção e a governança são locais; não existe ainda fluxo de equipe com permissões,
  merge, revisão distribuída ou resolução de conflitos entre máquinas.
- O pacote publicado continua em versão `0.1.0`; o badge de “v0.3” não representa uma versão
  publicada do pacote.

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
[Rembric](https://github.com/susomejias/rembric),
[agent-memory](https://github.com/xChuCx/agent-memory) e
[Continuum](https://github.com/redstone-md/Continuum). Existe ainda outro projeto com o
nome [Cortex](https://github.com/cdeust/Cortex), o que deve ser considerado antes de publicar
ou distribuir este projeto com esse nome.

O Cortex não reivindica ser o primeiro nem o melhor sistema de memória. A hipótese que ainda
vale investigar é mais estreita:

> coding agents podem se beneficiar de um registro de decisões e lições de engenharia que
> preserve evidência, explicite autoridade, trate contradições como histórico e compile
> somente o contexto aplicável à tarefa.

Essa hipótese ainda precisa ser demonstrada por benchmarks comparativos e uso em projetos
reais.

## Testes e qualidade

```bash
python -m pytest tests/ -q
python -m pytest tests/ -q --cov=cortex --cov-report=term-missing
ruff check .
mypy
pip-audit . --skip-editable
```

No estado atual, a suíte local passa com 142 testes. O CI executa testes, Ruff, mypy,
coverage e pip-audit em Windows e Ubuntu, em múltiplas versões de Python. As integrações
enhanced possuem contratos próprios, mas o dogfooding contra repositórios externos ainda não
é uma etapa obrigatória do CI.

## Roadmap atual

### Implementado

- ciclo captura → destilação → store → recall → contexto;
- artefatos tipados, proveniência, confiança, autoridade e frescor;
- Correnda proposta e governança por confirmação/rejeição;
- deduplicação e matriz de contradições;
- verificação AST/tree-sitter opcional;
- busca híbrida com fallback local;
- limites de contexto e de listagem MCP;
- hooks Claude Code/Cursor com falha best effort;
- grafo de proveniência, Commons e federação read-only;
- integrações opcionais maduras com fallbacks.

### Próximas prioridades

O plano detalhado está em [PLANO_MELHORIA_DIFERENCIACAO.md](C:/Users/Sergio/Documents/GitHub/cortex/PLANO_MELHORIA_DIFERENCIACAO.md). Em resumo:

1. medir Cortex contra soluções próximas, usando o mesmo corpus e métricas;
2. fortalecer evidência verificável por commit, teste, símbolo e revisão;
3. tornar contradição, supersessão e stale state operacionalmente confiáveis;
4. provar se `authority != confidence` melhora decisões recuperadas;
5. integrar o ciclo de conhecimento a branch, diff, review e mudança arquitetural;
6. só depois considerar memória de equipe, permissões e sincronização.

## Licença

MIT.

<div align="center">

**O Cortex não tenta lembrar tudo o que aconteceu.**
**Ele tenta registrar o que o projeto aprendeu — e mostrar de onde veio.**

</div>
