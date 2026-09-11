<div align="center">

# 🧠 Cortex

### Your codebase remembers why.

**O compilador de conhecimento de engenharia local-first para coding agents.**
Cursor · Claude Code · Codex · qualquer host que fale MCP.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-142%2B%20passing-brightgreen)
![Status](https://img.shields.io/badge/status-v0.3%20%2F%20Hybrid%20%26%20Contradiction-green)
![Local First](https://img.shields.io/badge/cloud-zero-lightgrey)

[Por que existe](#-o-problema-que-ninguém-resolveu-direito) ·
[O que é](#-o-que-é-o-cortex) ·
[Instalar](#-instalação-em-2-minutos) ·
[Usar](#-golden-path) ·
[CLI](#-referência-da-cli) ·
[MCP](#-referência-mcp) ·
[Por que Cortex e não X](#-por-que-cortex-em-vez-de-memória-genérica) ·
[Roadmap](#-roadmap--estado-real)

</div>

---

## 💭 O problema que ninguém resolveu direito

Coding agents em 2026 já escrevem código em velocidade impressionante. O que eles **não fazem** é lembrar.

Toda sessão de desenvolvimento produz decisões, hipóteses, tentativas, erros, correções e convenções que nascem organicamente. Quando a sessão termina, a maior parte desse raciocínio evapora — some no chat, se espalha em commits, ou depende inteiramente da memória do desenvolvedor.

O resultado é retrabalho cognitivo, todos os dias:

- Você explica a mesma decisão arquitetural pela terceira vez.
- O agente sugere de novo uma alternativa que já foi testada e rejeitada.
- Um bug "novo" é, na verdade, o mesmo bug de duas sprints atrás — só que ninguém reconheceu o padrão.
- A sessão anterior deixou algo pendente, e a próxima sessão não tem como saber disso.

Memória genérica (a que já existe em vários produtos de "AI memory") responde à pergunta *"o que aconteceu antes?"*. **Isso não é suficiente para engenharia de software.**

---

## 🎯 O que é o Cortex

> Cortex não é mais um logger de conversas, nem um RAG genérico, nem mais uma camada de "memória de IA".
> Ele é um **compilador**: sessão é a fonte de experiência, o Distillation Engine compila essa experiência em conhecimento estruturado, e o Context Compiler devolve à próxima sessão *só* o que ela precisa — dentro de um orçamento de tokens.

```text
┌─────────────────────────┐
│   SESSÃO DE CODING       │   Cursor · Claude Code · Codex
│   (experiência bruta)    │
└────────────┬─────────────┘
             │ eventos capturados via hooks / MCP
             ▼
┌─────────────────────────┐
│  DISTILLATION ENGINE     │   classifica · extrai · deduplica · valida
└────────────┬─────────────┘
             ▼
    INTENTION · ADR · FIX · CORRENDA · REVIEW
             │
             ▼
┌─────────────────────────┐
│  ENGENHARIA KNOWLEDGE    │   provenance · authority · freshness
│  STORE (SQLite local)    │
└────────────┬─────────────┘
             ▼
┌─────────────────────────┐
│   CONTEXT COMPILER       │   rank × escopo × autoridade × confiança
└────────────┬─────────────┘
             ▼
    PRÓXIMA SESSÃO já começa sabendo o que o projeto aprendeu
```

O ciclo é **incremental e compressivo**: o histórico bruto pode crescer para sempre, mas o contexto injetado na próxima sessão não — ele é compilado, ranqueado e limitado por um budget de tokens (padrão: 2.000).

### O que ele guarda — conhecimento de engenharia estruturado

Memória genérica guarda "o que aconteceu". Cortex guarda 5 coisas diferentes, porque engenharia de software não é uma coisa só:

| Artefato | Responde | Exemplo |
|---|---|---|
| **Intention** | Por que esta estrutura existe | *"Isolar auth via middleware para trocar provider sem tocar nos handlers"* |
| **ADR** | Que decisão foi tomada, e o que foi rejeitado | *"PostgreSQL. Rejeitado: MongoDB (flexibilidade desnecessária), DynamoDB (lock-in)"* |
| **Fix** | Sintoma → causa-raiz → resolução | *"TypeError em payload nulo → validação ausente → guard clause + Pydantic"* |
| **Correnda** | Uma regra aprendida, com evidência, nunca "verdade absoluta" | *"Validar payload externo antes de destructuring em handlers"* — nasce sempre `proposed`, só vira regra confiável depois que um humano confirma |
| **Review** | O que a sessão produziu e o que ficou pendente | *"2 intentions, 1 ADR, 2 fixes. Pendente: estratégia de cache"* |
| **Negative knowledge** | O que foi rejeitado ou não deve ser repetido | *"Não usar MongoDB neste domínio: schema relacional e ACID são requisitos"* |

Cada artefato carrega **proveniência** (sessão, eventos, arquivos, commits de origem), **confidence** (quão provável é que esteja certo) e **authority** (quão autorizado o Cortex está a tratá-lo como regra — que não é a mesma coisa que confidence). Uma regra com 95% de confiança inferida pelo agente **não** tem a mesma prioridade que uma regra confirmada por humano com 70% — e essa distinção é aplicada de verdade no ranking, não é só um campo decorativo.

Conhecimento superado (`superseded`) nunca é apagado — só sai do contexto padrão. História nunca é destruída, só deixa de ser a verdade atual.

---

## 🚫 Não é / ✅ É

<table>
<tr>
<td valign="top" width="50%">

**Não é:**
- chatbot ou observability logger
- vector database genérico
- RAG genérico
- knowledge graph genérico
- memória de usuário
- substituto de Git, Jira/Linear ou ADR humano
- framework de agentes
- telemetria SaaS

</td>
<td valign="top" width="50%">

**É:**
- um compilador de conhecimento de engenharia
- local-first — zero telemetria, zero cloud por padrão
- provenance-first — toda memória aponta pra evidência
- governado por humano — nada de alto impacto vira lei sozinho
- feito de heurísticas honestas com fallback gracioso em cada camada

</td>
</tr>
</table>

---

## ⚡ Instalação em 2 minutos

```bash
git clone <seu-fork-ou-repo> cortex && cd cortex
pip install -e .
cd seu-projeto
cortex init
```

Para ativar as integrações aprimoradas opcionais, instale o extra:

```bash
pip install -e ".[enhanced]"
```

Os extras mantêm os fallbacks locais. Embeddings densos são opt-in com
`CORTEX_ENABLE_DENSE_EMBEDDINGS=1`, pois o primeiro uso pode baixar pesos;
TOMLKit, detect-secrets, o cliente OpenAI-compatível do Ollama, tree-sitter e
pyvis são carregados sob demanda quando disponíveis.

### Capacidades enterprise opcionais

O núcleo continua instalável sem serviços externos. O extra `enhanced` adiciona
integrações maduras sem alterar o contrato local-first:

| Capacidade | Padrão | Fallback | Efeito prático |
|---|---|---|---|
| Contagem de tokens | `tiktoken` obrigatório | estimativa por palavras | budget de contexto reproduzível |
| Similaridade densa | `model2vec` + `sqlite-vec`, opt-in | n-gram/token local | ranking e contradições sem exigir modelo por padrão |
| Segredos | `detect-secrets` | redaction regex | proteção adicional antes da persistência |
| TOML | `tomlkit` | editor seguro + `tomllib` | preserva comentários e valida atomicamente |
| Ollama | OpenAI SDK compatível | `urllib` | cliente moderno com degradação local |
| Verificação | tree-sitter + grammars | AST Python/text scan | símbolos em múltiplas linguagens |
| Grafo | pyvis | HTML standalone | exploração interativa opcional |

Nenhuma dessas integrações habilita rede silenciosamente: embeddings exigem a
flag explícita, Ollama respeita `privacy.network_calls`, e o fallback continua
disponível quando um pacote ou grammar não está instalado.

Saída esperada:

```text
✓ workspace detected
✓ git root identified
✓ host adapter detected
✓ MCP configured
✓ local store created
✓ context compiler ready
✓ privacy mode: local-only

Cortex is ready.
```

Isso cria `.cortex/cortex.db` (SQLite, WAL) dentro do seu repositório. Na
instalação mínima, nada sai da sua máquina; o único download potencial é o
peso de embeddings quando `CORTEX_ENABLE_DENSE_EMBEDDINGS=1` é habilitado
explicitamente.

---

## 🛤️ Golden Path

```text
1. cortex init                        → workspace + store local criados
2. Trabalhe normalmente               → hooks capturam eventos automaticamente
3. cortex distill                     → eventos viram Intention / ADR / Fix / Correnda
4. cortex correnda confirm cor-0001   → você decide o que vira regra de verdade
5. Próxima sessão                     → cortex_init (MCP) devolve o contexto compilado
```

### Exemplo real, passo a passo

```bash
cortex capture user_instruction "Vamos usar PostgreSQL porque precisamos de ACID" --files src/db
cortex capture agent_response "Decidimos PostgreSQL em vez de MongoDB, schema é previsível" --files src/db

cortex distill
# distillation complete
#   events=2 intentions=0 adrs=2 fixes=0 correndas_proposed=0
#   new artifacts: adr-0001, adr-0002

cortex why adr-0002
# Statement: Decidimos PostgreSQL em vez de MongoDB...
# Evidence: sess-cli-xxxx
# Confidence: 0.85 | Authority: agent_inferred | Status: active
```

Duas sessões depois, se o mesmo tipo de bug aparecer de novo com a mesma causa-raiz, o Cortex propõe uma **Correnda**. Você confirma com um comando:

```bash
cortex correnda confirm cor-0031
```

A partir daí, toda sessão futura cujo escopo bater com essa regra recebe ela automaticamente no contexto — o agente aplica sem você precisar explicar de novo.

### Ligando a um coding agent de verdade

```bash
cortex hook --install claude-code   # escreve .claude/settings.json
cortex hook --install cursor        # escreve .cursor/hooks.json
```

Isso conecta `SessionStart`, `UserPromptSubmit`, `PostToolUse` e `Stop` a eventos do Cortex. No início de cada sessão, o agente já recebe o bloco `CORTEX CONTEXT` compilado. **Falha de captura nunca bloqueia o agente** — é uma garantia de design, não um detalhe.

---

## 🖥️ Referência da CLI

| Categoria | Comandos |
|---|---|
| **Projeto** | `cortex init` · `cortex status [--verbose]` · `cortex doctor` · `cortex config [--set chave valor]` |
| **Conhecimento** | `cortex recall "query" [--provenance]` · `cortex intentions` · `cortex adrs` · `cortex fixes` · `cortex correndas` · `cortex reviews` |
| **Destilação** | `cortex distill [--session id] [--dry-run]` · `cortex review [--session id] [--phase]` |
| **Governança** | `cortex correnda confirm\|reject <id>` · `cortex adrs accept\|reject <id>` · `cortex verify <id>` · `cortex supersede <old> --with <new>` · `cortex contradictions` |
| **Debug / confiança** | `cortex why <id>` · `cortex trace <session>` · `cortex diff --sessions N` · `cortex retrieval-debug "query"` · `cortex graph --output arquivo.html` |
| **Compilação** | `cortex context --task "..." --files src/handlers` |
| **Correnda Commons** | `cortex commons export <id> --output pattern.json` · `cortex commons import pattern.json` |
| **Qualidade** | `cortex benchmark` · `cortex benchmark --dogfood` |
| **Integração** | `cortex hook --install claude-code\|cursor` · `cortex phase` |

---

## 🔌 Referência MCP

```bash
python -m cortex.server.mcp_server   # stdio
```

```json
{
  "mcpServers": {
    "cortex": {
      "command": "python",
      "args": ["-m", "cortex.server.mcp_server"],
      "env": { "CORTEX_ROOT": "/caminho/do/projeto" }
    }
  }
}
```

16 ferramentas expostas:

`cortex_init` · `cortex_recall` · `cortex_remember` · `cortex_emit` · `cortex_capture` · `cortex_distill` · `cortex_review` · `cortex_status` · `cortex_verify` · `cortex_phase` · `cortex_intention` · `cortex_adr` · `cortex_fix` · `cortex_correnda` · `cortex_diff` · `cortex_why`

Destaque: **`cortex_emit`** deixa o próprio agente registrar uma decisão, correção ou regra estruturada no momento em que ela acontece — em vez do Cortex tentar adivinhar isso depois, lendo texto livre com heurísticas.

---

## 🧭 Por que Cortex em vez de memória genérica

Memória persistente para coding agents já é uma categoria validada — Cognee, Mem0 e Basic Memory provam isso, e desde fevereiro de 2026 o próprio Claude Code inclui memória nativa (Auto Memory + Auto Dream). **Cortex não afirma ser o primeiro a ter memória — nem afirma que a memória nativa do host é ruim.** A diferenciação é outra:

| Dimensão | Cortex | Memória genérica / nativa do host |
|---|---|---|
| Ontologia de engenharia explícita (Intention/ADR/Fix/Correnda) | ✅ nativo | ❌ genérico ou indireto |
| Authority ≠ Confidence | ✅ core do ranking | 🟡 raramente separado |
| Proveniência obrigatória por artefato | ✅ toda entidade rastreável até a evidência | 🟡 variável |
| Regra aprendida nasce `proposed`, nunca vira lei sozinha | ✅ garantia de design | ❌ geralmente não |
| Contradição / supersessão preserva histórico | ✅ nunca apaga, só desativa | 🟡 variável — a limpeza nativa do Claude Code (Auto Dream) *deleta* fatos contradichos em vez de superseder |
| Negative knowledge ("já tentamos isso e falhou") | ✅ tipo de primeira classe | ❌ raro |
| Seleção de contexto | ✅ ranqueada por relevância × autoridade × confiança dentro de um budget de tokens | 🟡 memória nativa carrega os primeiros ~200 linhas/25KB do arquivo, relevante ou não, sem busca semântica sobre o resto |
| Verificação contra o código real (AST) | ✅ Tier 0 promove autoridade só com evidência estrutural | 🟡 tratada como "dica", não verificada estruturalmente |
| Local-first, zero telemetria por padrão | ✅ | 🟡 depende do produto |

### E a memória nativa do Claude Code (Auto Memory / Dreams)?

Essa é a pergunta que qualquer pessoa rodando Claude Code em 2026 vai fazer primeiro, e seria desonesto não responder aqui. Auto Memory grava notas próprias em `MEMORY.md` durante a sessão; Auto Dream roda em background e faz uma consolidação real — mescla duplicatas, normaliza datas relativas e **remove fatos contradichos**. É uma barra de qualidade mais alta do que "nenhuma memória", e o Cortex não compete em ter "mais memória" contra isso.

A diferença é o que acontece **depois** que dois fatos conflitam. O Auto Dream decide qual fato é o certo e apaga o outro — não existe grau de confiança, não existe uma pessoa confirmando antes de virar verdade, e o fato descartado não é mais consultável. O Cortex modela isso como `SUPERSEDES`/`CONTRADICTS`: nada é apagado, a Correnda nova não vira `active` sozinha (nasce sempre `proposed`), e `cortex why` deixa rastrear a decisão anterior mesmo depois de superada. Para decisões de arquitetura — o tipo de coisa que se paga caro por errar — isso importa mais do que para "qual porta o servidor local usa".

Se seu caso de uso é "não quero re-explicar o projeto", a memória nativa provavelmente já resolve, sem instalar nada. O Cortex existe para quem quer auditar *por que* uma regra aprendida está sendo aplicada, quem/o que a confirmou, e manter esse histórico mesmo quando ela é superada.

> A tese: *"Coding agents precisam de continuidade; memória persistente já é uma categoria válida; o espaço menos comoditizado está em modelar, verificar e compilar conhecimento específico de engenharia."*

---

## 🔒 Privacidade

- zero telemetria, zero cloud, zero chamada externa por padrão;
- redação automática de tokens, chaves de API, senhas e credenciais **antes** de qualquer persistência;
- tudo vive em `.cortex/` dentro do seu próprio repositório;
- qualquer provider externo (LLM, embeddings) é uma decisão explícita de configuração, nunca o padrão.

---

## 🏗️ Arquitetura

```text
cortex/
├── cli/            Typer CLI — init, recall, distill, why, governança
├── server/         MCP server (stdio) — cortex_init/recall/remember/emit/...
├── adapters/       Claude Code + Cursor hooks, detecção de workspace
├── capture/        eventos brutos de sessão (com redação de segredos)
├── distillation/   extratores heurísticos + LLM opcional, Correndas, reviews
├── knowledge/      modelo Pydantic (Entity, provenance, authority, freshness)
├── compiler/       Context Compiler — ranking × escopo × autoridade × budget
├── storage/        SQLite WAL + FTS5 (bm25)
├── git/            contexto de branch/commits como evidência
├── privacy/        redação antes da persistência
├── verification.py verificação Tier 0 via AST/tree-sitter — evidencia o código real
├── commons.py      Correnda Commons — generalização opt-in de padrões
└── visualizer.py   grafo de proveniência exportável como HTML standalone
```

Guardrails que **não são cosméticos** — são testados:
- Correnda nunca nasce `active` automaticamente.
- Falha de destilação/captura nunca bloqueia o agente (fallback silencioso, JSON de erro sem traceback).
- Contexto compilado sempre respeita o budget de tokens; se falhar, cai num "minimal safe context".
- Conhecimento `stale`/`superseded` some do contexto padrão, mas continua consultável no histórico.

---

## ✅ Testes

```bash
python -m pytest tests/ -q
# 142+ passed

# mesmos checks principais do CI
python -m pytest tests/ -q --cov=cortex --cov-report=term-missing
ruff check .
mypy
pip-audit . --skip-editable
```

A suíte cobre os 8 critérios de aceitação do MVP (§58 do PRD) e contratos dos
fallbacks/integrações opcionais — por exemplo: uma decisão da sessão 1 tem que
ser recuperável na sessão 3 sem reexplicação manual; uma decisão rejeitada não
pode reaparecer como sugestão nova; dois fixes com causa-raiz parecida têm que
gerar uma Correnda candidata; falha do Cortex nunca pode travar o workflow.

---

## 🗺️ Roadmap — estado real

Este projeto documenta o próprio estado com honestidade, de propósito — inclusive o que ainda é fraco. É assim que se constrói confiança em um sistema que decide o que um agente de IA "lembra".

| Onda | O quê | Status |
|---|---|---|
| v0.1 — Evidence Loop | captura + recall + init de contexto | ✅ |
| v0.2 — Distillation Loop | extração automática, confidence, provenance, ranking | ✅ |
| Onda 6 — Agente emissor nativo | ferramenta `cortex_emit` para o agente estruturar conhecimento no ato | ✅ implementado · 🟡 authority/status ainda precisa de ajuste fino antes de produção |
| Onda 7 — Verificação Tier 0 (AST) | promove authority com evidência estrutural real, não grep | ✅ |
| Onda 8 — Benchmark CCB | harness com as 8 tarefas de continuidade do PRD | ✅ fixture · 🟡 dogfood contra repositório real ainda em validação |
| Onda 9 — Grafo de proveniência | exportação HTML standalone, sem servidor | ✅ v1 (lista navegável) |
| Onda 10 — Correnda Commons | generalização opt-in de padrões pra compartilhar entre projetos | ✅ v1 (redação de segredos) · 🟡 generalização semântica ainda é próximo passo |
| Onda 11 — Federação read-only | múltiplas lojas de conhecimento da mesma organização | ✅ |
| Onda 12 — Auto-calibração | hook de pesos configuráveis no Context Compiler | ✅ |
| Onda 13 — Busca Híbrida + Densidade | esparso (BM25) + denso (n-gram/TF-IDF) + densidade de nó no Grafo e sinal técnico | ✅ |
| Onda 14 — Contradição Semântica Robusta | matriz multi-vetorial (Decisão vs Decisão, Decisão vs Rejeitada, Correnda vs Regra, Negações Polares) | ✅ |
| Enterprise integrations | tiktoken, model2vec/sqlite-vec, detect-secrets, TOMLKit, OpenAI/Ollama, tree-sitter e pyvis, todos com fallback | ✅ implementado · paths enriquecidos são opt-in |
| v0.3 — Verification & Hybrid Loop | busca híbrida com densidade, revalidação e matriz de contradição | ✅ concluído (142+ testes passing) |
| v0.5 — Team Memory | multi-agente com permissões e CRDT | ⬜ não iniciado (por escolha, não por atraso) |

**O que isso significa na prática:** este é um MVP funcional, com ciclo fechado e testado ponta a ponta, não um produto de produção acabado. Se você é o tipo de engenheiro que confia mais em quem admite o que ainda não está pronto, esse é o projeto certo pra acompanhar.

---

## 📄 Licença

MIT.

---

<div align="center">

**Cortex não tenta lembrar tudo que aconteceu.**
**Ele tenta lembrar o que o seu projeto aprendeu — e por quê.**

</div>
