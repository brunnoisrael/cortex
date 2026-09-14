# Plano de melhoria e diferenciação do Cortex

**Data:** 2026-09-10  
**Base:** estado do repositório após o ciclo de endurecimento e revisão comparativa do ecossistema.

## Objetivo

Capacitar o Cortex para ser um sistema confiável de **linhagem e governança de conhecimento
de engenharia para coding agents**, sem competir apenas como mais uma memória persistente,
mais um RAG ou mais um servidor MCP.

O plano parte de uma constatação importante: memória cross-session, MCP, SQLite/FTS,
embeddings, hooks e destilação já são padrões conhecidos. O investimento deve concentrar-se
no que pode ser difícil de copiar e fácil de demonstrar:

1. evidência verificável;
2. decisões com validade e escopo explícitos;
3. contradições e supersessões auditáveis;
4. compilação de contexto justificável;
5. avaliação comparativa reproduzível.

## Princípios

- **Evidência antes de autoridade:** uma inferência pode ser recuperável sem virar regra.
- **Nada de verdade silenciosa:** promoção, supersessão e arquivamento precisam ser
  explicáveis e, quando tiverem impacto alto, revisáveis.
- **Falhar com sinal:** o agente não deve ser bloqueado, mas degradações devem aparecer em
  diagnóstico, logs e métricas.
- **Histórico preservado:** preferir relações de supersessão e invalidação a sobrescrita
  destrutiva.
- **Local-first por padrão:** dependências e modelos externos são opt-in.
- **Benchmark contra alternativas:** nenhum diferencial deve ser declarado sem comparação.
- **Não ampliar escopo cedo:** memória de equipe, sincronização e CRDT só entram depois de
  o núcleo individual estar demonstravelmente confiável.

## Estado atual resumido

| Capacidade | Estado | Próximo endurecimento |
|---|---|---|
| Captura de eventos | implementada | medir cobertura e perda por host |
| Destilação heurística | implementada, limitada | extratores avaliados por corpus real |
| Artefatos de engenharia | implementados | schema de evidência mais rigoroso |
| Autoridade/confiança | implementadas | ablação e calibração do ranking |
| Contradição | implementada | validade temporal e revisão operacional |
| Proveniência | implementada | evidência citável e verificável por linha/commit |
| Context compiler | implementado | explicação de seleção e qualidade do contexto |
| Verificação AST/tree-sitter | parcial | cobertura multi-linguagem e testes de falsos positivos |
| MCP/hooks | implementados | contratos de compatibilidade e telemetria local de falhas |
| Benchmark | sintético/adversarial | corpus externo e comparação com concorrentes |
| Memória de equipe | não iniciada | só após as fases anteriores |

## Fase 0 — Baseline e posicionamento

**Prioridade:** P0  
**Objetivo:** saber se o Cortex realmente supera alternativas no problema específico que
pretende resolver.

### Entregas

- Fixar um corpus versionado com sessões de engenharia contendo:
  - decisões explícitas e implícitas;
  - alternativas rejeitadas;
  - bugs e correções;
  - mudanças de decisão ao longo do tempo;
  - regras contraditórias;
  - pendências de sessão;
  - linguagem natural não moldada aos regexes dos extratores.
- Criar adaptadores de avaliação para Cortex, Agent Memory Engine, Agent Memory Bridge,
  Basic Memory e uma memória nativa de host quando disponível.
- Medir:
  - recall@k e precision@k;
  - MRR/nDCG;
  - falsos positivos;
  - contradições recuperadas indevidamente;
  - tokens injetados;
  - tempo de ingestão e consulta;
  - taxa de decisões que sobrevivem à sessão seguinte;
  - explicabilidade da origem recuperada.
- Separar claramente três métricas:
  - qualidade da extração;
  - qualidade do ranking;
  - qualidade do contexto final.

### Critério de aceite

Nenhuma frase de diferenciação no README deve depender apenas de uma hipótese. Cada claim
importante deve apontar para um teste, uma métrica ou uma limitação explícita.

## Fase 1 — Evidence Ledger

**Prioridade:** P0  
**Objetivo:** fazer cada artefato responder “por que o sistema acredita nisso?” com evidência
concreta.

### Melhorias

- Introduzir um modelo explícito de `Evidence` com:
  - tipo: evento, arquivo, símbolo, linha, commit, teste, review;
  - localização;
  - hash ou fingerprint do conteúdo;
  - data de observação;
  - status de resolução;
  - método de verificação.
- Separar `source` de `evidence`: um arquivo citado não é automaticamente uma prova.
- Fazer `cortex why` mostrar a cadeia:

  ```text
  entidade → extração → evento → arquivo/commit/teste → última verificação
  ```

- Adicionar estado explícito `unverifiable` para referências que não podem ser resolvidas.
- Permitir exportar um pacote de evidência reproduzível para auditoria.

### Critério de aceite

Uma entidade não pode receber `repository_verified` se os símbolos/arquivos/commits citados
não forem encontrados e fingerprintados. O relatório deve distinguir “referência resolvida”
de “afirmação comprovada”.

## Fase 2 — Governança de decisões e regras

**Prioridade:** P0  
**Objetivo:** tornar a promoção de conhecimento previsível, reversível e adequada ao risco.

### Melhorias

- Definir uma máquina de estados documentada para cada tipo de artefato.
- Adicionar `risk_level` e `review_policy`:
  - baixo: pode entrar em contexto como observação;
  - médio: exige evidência múltipla;
  - alto: exige confirmação humana ou review associado.
- Diferenciar explicitamente:
  - `observed`;
  - `agent_inferred`;
  - `repository_verified`;
  - `human_confirmed`.
- Registrar recibo de promoção/rejeição com ator, data, razão e evidências usadas.
- Impedir que importações do Commons ultrapassem `proposed` automaticamente.
- Criar comandos para inspeção de fila:
  - `cortex review-queue`;
  - `cortex promote`;
  - `cortex reject`;
  - `cortex quarantine`.

### Critério de aceite

Dado o mesmo store e a mesma ação, a transição de estado deve ser determinística,
idempotente e auditável. Uma regra de alto risco não pode aparecer como instrução ativa sem
o recibo exigido pela política.

## Fase 3 — Contradição, validade e supersessão

**Prioridade:** P0  
**Objetivo:** transformar contradição de sinal heurístico em ciclo operacional.

### Melhorias

- Modelar validade temporal:
  - `valid_from`;
  - `valid_until`;
  - `observed_at`;
  - `superseded_at`.
- Distinguir:
  - contradição direta;
  - mudança de premissa;
  - escopos diferentes;
  - versões diferentes do branch;
  - simples duplicata.
- Criar uma caixa de revisão para conflitos não resolvidos.
- Fazer o compilador mostrar quando uma entidade foi penalizada por contradição.
- Adicionar testes de regressão com três ou mais versões da mesma decisão.
- Evitar que uma regra antiga seja recuperada sem mostrar a decisão que a supersedeu.

### Critério de aceite

Uma consulta deve retornar a decisão atualmente válida para o escopo solicitado, mas permitir
inspecionar as decisões anteriores, suas evidências e a razão da mudança.

## Fase 4 — Context Compiler explicável

**Prioridade:** P1  
**Objetivo:** transformar o compilador em uma superfície de decisão observável, não apenas
um ranking opaco.

### Melhorias

- Expor no CLI/MCP um `retrieval trace` estável:
  - sinais usados;
  - pesos;
  - filtros aplicados;
  - penalidade de contradição;
  - motivo de exclusão;
  - custo estimado em tokens.
- Separar claramente:
  - candidatos recuperados;
  - candidatos elegíveis;
  - candidatos selecionados;
  - itens descartados por budget.
- Adicionar avaliação de budget:
  - utilidade por token;
  - estabilidade do resultado quando o budget muda;
  - presença de itens de alto risco;
  - duplicação dentro do contexto final.
- Criar perfis de compilação para `bug_fix`, `architecture_review`, `onboarding` e
  `session_resume`.
- Fazer o contexto incluir links de proveniência quando isso couber no budget.

### Critério de aceite

Para uma consulta fixa, o Cortex deve explicar por que cada item entrou e por que os itens
mais relevantes que ficaram fora foram excluídos.

## Fase 5 — Verificação de mudança real

**Prioridade:** P1  
**Objetivo:** conectar o conhecimento ao estado efetivo do repositório.

### Melhorias

- Associar entidades a commits e diffs concretos.
- Invalidar ou marcar como stale conhecimento quando:
  - o arquivo citado muda estruturalmente;
  - o símbolo desaparece;
  - o teste associado deixa de existir;
  - a decisão é alterada em outro branch;
  - uma dependência crítica muda.
- Integrar resultados de testes como evidência, sem afirmar que um teste isolado prova a
  decisão inteira.
- Gerar uma revisão de impacto:
  - “quais ADRs e Correndas podem ter ficado obsoletos por este diff?”
- Criar um modo somente leitura para uso em CI.

### Critério de aceite

Uma mudança estrutural relevante deve gerar pelo menos uma das três saídas: nenhuma entidade
afetada, entidades ainda válidas com evidência atualizada, ou fila de revisão stale.

## Fase 6 — Integração com review e fluxo de engenharia

**Prioridade:** P1  
**Objetivo:** inserir o Cortex no lugar onde decisões realmente são confirmadas.

### Melhorias

- Criar comandos para anexar conhecimento a diff, commit ou pull request.
- Gerar um resumo de review com:
  - decisões impactadas;
  - regras aplicáveis;
  - conhecimento negativo relacionado;
  - conflitos pendentes;
  - evidências ausentes.
- Permitir que um humano confirme uma decisão a partir de um review, mantendo o recibo no
  store.
- Implementar exportação Markdown/JSON estável para repositórios que não querem depender do
  SQLite.
- Integrar com `AGENTS.md`, `CLAUDE.md` ou regras do Cursor somente como saída derivada,
  nunca como fonte silenciosa de verdade.

### Critério de aceite

Um desenvolvedor deve conseguir revisar e confirmar uma decisão sem abrir a base SQLite e sem
precisar confiar em texto gerado sem referências.

## Fase 7 — Qualidade da extração

**Prioridade:** P1  
**Objetivo:** reduzir dependência de frases moldadas aos extratores.

### Melhorias

- Manter heurísticas como fallback determinístico.
- Criar conjunto de avaliação anotado com paráfrases, omissões, negações e diálogos longos.
- Adicionar extração estruturada via `cortex_emit` como caminho preferencial quando o agente
  consegue declarar a decisão no momento certo.
- Usar LLM local opcional apenas para sugerir candidatos, nunca para promover autoridade.
- Registrar por que uma extração aconteceu:
  - regex;
  - evento explícito;
  - modelo local;
  - evidência de código.
- Medir precision/recall por artefato, não apenas o score agregado.

### Critério de aceite

O benchmark adversarial deve melhorar sem aumentar de forma desproporcional falsos positivos
ou o volume de memória proposta.

## Fase 8 — Interoperabilidade e migração

**Prioridade:** P2  
**Objetivo:** tornar o conhecimento portátil e reduzir lock-in.

### Melhorias

- Definir um schema versionado de exportação para ADRs, fixes, decisões, evidências e relações.
- Criar importadores controlados para Markdown/JSON de ferramentas próximas.
- Permitir escolher SQLite como índice derivado e Markdown/JSON como fonte de verdade, caso
  o usuário prefira auditabilidade por Git.
- Documentar limites de compatibilidade entre versões do schema.
- Publicar fixtures de migração e round-trip tests.

### Critério de aceite

Uma exportação completa deve poder ser importada em uma instalação limpa sem transformar
conhecimento externo em `active` automaticamente e sem perder proveniência.

## Fase 9 — Memória de equipe, somente depois

**Prioridade:** P2, condicionada às fases anteriores  
**Objetivo:** suportar colaboração sem transformar o Cortex em uma plataforma distribuída
prematura.

Só iniciar esta fase se os benchmarks demonstrarem valor no modo individual.

### Possíveis extensões

- permissões por projeto, branch e tipo de artefato;
- memória compartilhada versus privada;
- merge de entidades com recibos;
- resolução de conflito entre máquinas;
- sincronização opcional via Git ou serviço escolhido pelo usuário;
- retenção e exclusão explícitas por política.

### Implementação concluída nesta revisão

A fase 9 agora possui uma primeira superfície operacional, deliberadamente local e
transport-agnostic, em `cortex/team.py`:

- membros por projeto com papéis `owner`, `member` e `reviewer`;
- ACL explícita por entidade, projeto, principal, permissão e branch;
- leitura compartilhada opt-in: o compilador individual não passa a enxergar memória
  de equipe silenciosamente;
- merge não destrutivo com relação `VARIANT_OF`, razão obrigatória e recibo idempotente;
- bundle `cortex_team_bundle/v1` com checksum, exportação e importação que mantém
  conhecimento externo em `proposed`;
- retenção de metadados revogados com política explícita; entidades do ledger não são
  apagadas automaticamente.

As tabelas são uma migração SQLite aditiva (`schema_version=6`) e os testes cobrem
isolamento por branch, idempotência, checksum, downgrade de autoridade e retenção.
Git, serviço remoto e resolução distribuída continuam sendo transportes opcionais; esta
entrega não inventa sincronização ou CRDT antes de existir um caso real.

**Critério de aceite desta implementação:** dois membros só compartilham uma entidade
quando existe ACL ativa; um merge repetido produz um único recibo; um bundle adulterado
falha por checksum; importação externa não promove autoridade; e retenção não destrói
o ledger local.

### Não fazer ainda

- CRDT sem caso real demonstrado;
- daemon distribuído;
- cloud obrigatória;
- telemetria por padrão;
- mais ferramentas MCP sem necessidade comprovada.

## Backlog imediato recomendado

1. Corrigir e manter o README alinhado ao código.
2. Congelar um schema de evidência antes de aumentar a ontologia.
3. Criar o corpus comparativo externo.
4. Adicionar `retrieval trace` com motivos de inclusão/exclusão.
5. Implementar validade temporal e fila de contradições.
6. Criar verificação de stale por diff/commit.
7. Publicar um benchmark reproduzível, sem claims de superioridade antes dos resultados.
8. Decidir sobre o nome “Cortex” antes de distribuir o projeto.

## Critério de sucesso do plano

O Cortex estará mais capacitado quando conseguir demonstrar, em um repositório real:

- quais decisões foram registradas;
- de onde cada uma veio;
- quais foram verificadas;
- quais ficaram stale ou foram supersedidas;
- por que uma decisão entrou no contexto;
- quanto custou em tokens;
- e quando o sistema corretamente decidiu não sugerir nada.

Esse é um diferencial mais defensável do que simplesmente “ter memória persistente”.
