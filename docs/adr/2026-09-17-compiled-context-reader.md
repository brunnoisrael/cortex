# ADR: leitor fixo de contexto compilado

## Contexto

A Fase B precisa medir a fronteira entre recuperação e resposta. Um leitor que
consulte o `KnowledgeStore`, o histórico bruto ou o gold mistura as etapas e
pode transformar evidência ausente em certeza do agente.

## Decisão

Adicionar `cortex.reader.read_compiled_context()` como leitor determinístico.
Ele recebe apenas a pergunta e o bloco textual compilado. Linhas de evidência
são reconhecidas somente quando carregam um ID entre colchetes; respostas
apoiadas citam apenas esses IDs. Evidência parcial, ausente, superseded, stale
ou deleted produz `abstention`, com `missing_evidence` e trace do conjunto de
IDs recebido.

O `CortexAdapter` mantém métricas de recuperação separadas das métricas do
leitor: suporte factual, fidelidade, decisão de abstenção, acurácia da resposta
final e validade das citações. Isso não é um claim de qualidade geral: o leitor
é uma política fixa de medição e os resultados do corpus interno continuam
confirmatórios somente para aquele corpus.

## Transporte MCP

O SDK MCP instalado (`mcp` 1.29.1) foi testado por stdio. O servidor termina o
handler de `cortex_init` e envia uma resposta JSON-RPC válida, mas o cliente
pode deixar o `stdout_reader` bloqueado na primeira chamada após
`initialize`. Uma chamada concorrente de `list_tools()` do próprio SDK libera
a fila; o harness de integração usa essa sequência e deixa `stdio_client`
encerrar o processo filho. Isso é uma limitação do cliente/harness observado,
não uma mudança de autoridade ou uma confirmação de que o Desktop já está
registrado.

## Consequências

- Nenhuma afirmação do leitor pode citar um ID que não esteja no contexto.
- A resposta final pode abster-se mesmo quando a recuperação encontrou itens;
  essas dimensões permanecem observáveis separadamente.
- O leitor não promove autoridade: `authority`, validade e proveniência são
  propriedades do contexto compilado e da memória governada.
