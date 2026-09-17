# Autoridade de trabalho do Cortex

Este arquivo é uma instrução normativa para qualquer agente, humano ou modelo
que implemente mudanças neste repositório. Em caso de conflito, preserva-se a
hipótese científica e as regras de evidência deste documento; conveniência de
implementação, cópia de padrões externos ou preferência de um agente não
substituem essas regras.

O documento de execução e prioridades é
[`docs/RESEARCH_ROADMAP.md`](docs/RESEARCH_ROADMAP.md).

## Tese que não pode ser diluída

O Cortex não é apenas um RAG, um banco vetorial ou um gerenciador de notas.
A hipótese testada é que agentes de engenharia se tornam mais confiáveis
quando a memória preserva, de forma consultável:

- a evidência original de cada afirmação;
- autoridade separada de confiança inferida;
- escopo e aplicabilidade;
- validade temporal, supersessão e contradição;
- linhagem até evento, arquivo, símbolo, commit, teste ou revisão;
- abstenção quando a evidência não sustenta uma resposta.

Uma mudança que remova esses sinais, trate memória como texto sem proveniência,
ou transforme uma inferência do agente em verdade confirmada é uma regressão
conceitual, mesmo que melhore uma métrica isolada.

## Regra obrigatória de dogfooding via MCP

Durante toda implementação não trivial, o agente deve chamar o servidor MCP do
Cortex deste repositório para consultar e registrar o próprio trabalho. O
servidor local é iniciado com:

```bash
python -m cortex.server.mcp_server
```

Quando o host MCP estiver configurado, o agente deve executar este ciclo:

1. Antes de editar: `cortex_init`, `cortex_status`, `cortex_phase` e
   `cortex_recall` para recuperar decisões, pendências, restrições e evidências
   relacionadas ao trabalho.
2. Durante a implementação: `cortex_capture` para eventos de trabalho e
   `cortex_emit` para decisões, correções, riscos ou conhecimento negativo.
   Use `cortex_remember` somente dentro da política de autoridade do servidor;
   um agente não pode fabricar confirmação humana.
3. Depois de editar: `cortex_distill`, `cortex_review`,
   `cortex_retrieval_trace` e `cortex_verify` quando aplicável. Registre o
   resultado dos testes, o commit e qualquer limitação com proveniência.
4. Antes de concluir: consulte `cortex_why` ou `cortex_evidence_export` para a
   evidência principal e rode o benchmark relevante. Para avaliação semântica,
   siga `.agents/skills/cortex-judge/SKILL.md` e só use `answer_supported=true`
   quando o fato estiver explicitamente nas evidências recuperadas.

Se o MCP não estiver disponível, o agente deve declarar essa limitação no
resultado, executar a melhor validação local possível e não afirmar que houve
dogfooding MCP. Não se deve simular uma chamada MCP escrevendo JSON manual ou
inventando uma memória equivalente.

## Regras contra generalização e regressão

- Não trocar o vocabulário científico do projeto por uma abstração genérica
  sem atualizar a hipótese, as métricas e o protocolo de validação.
- Não copiar Mem0, Graphiti, A-MEM, Agent Zero Memory ou outro sistema como
  “novidade”. Recursos inspirados em trabalhos externos devem registrar a fonte,
  a diferença funcional e a razão experimental no roadmap ou em um ADR.
- Não publicar uma média sem informar corpus, split, tamanho, qualidade de
  anotação, baseline, orçamento de tokens, latência, modelo e hash do código.
- Resultados do corpus sintético interno são confirmatórios apenas para as
  invariantes desse corpus. Dogfooding de uma sessão, CCB e LongMemEval sem
  anotação independente são exploratórios.
- Não esconder falhas com `skip`, média agregada, fallback silencioso ou
  documentação desatualizada. Falhas de extração, ranking, abstenção,
  proveniência e supersessão devem aparecer por caso.
- Uma alteração só está concluída quando há teste determinístico, teste de
  regressão da tese, evidência MCP e documentação atualizada.

## Portão de conclusão

Antes de marcar uma tarefa como concluída, o agente deve reportar:

```text
MCP dogfooding: realizado | indisponível (motivo)
Evidência consultada/registrada: <ferramentas ou IDs>
Testes: <comando e resultado>
Benchmark: <manifesto, adapters, decisão>
Regressões da tese: <nenhuma ou lista>
Limitações: <lista explícita>
Commit: <hash ou não commitado>
```

O objetivo deste contrato é manter o Cortex como um experimento cumulativo,
auditável e específico — não permitir que sucessivas implementações reduzam a
ideia a mais uma cópia de RAG com memória.
