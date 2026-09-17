# Roadmap de pesquisa e prova de conceito do Cortex

**Status:** plano normativo pós-auditoria

Este documento transforma o estado atual do projeto em um programa de pesquisa.
Ele deve ser lido junto com [`AGENTS.md`](../AGENTS.md),
[`docs/benchmark.md`](benchmark.md) e a rubrica
`.agents/skills/cortex-judge/SKILL.md`.

## 1. Diagnóstico honesto

O Cortex já possui uma base de engenharia incomum: captura via MCP, memória
tipada, autoridade distinta de confiança, proveniência, Evidence Ledger,
validade temporal, supersessão, compilação com orçamento, runner determinístico,
abstenção e ablações.

Os resultados atuais, entretanto, não provam ainda uma contribuição científica
fora da curva:

| Evidência | Observação atual | Interpretação correta |
|---|---|---|
| Corpus interno, 250 casos | `stale_leak_rate` Cortex 0,0% vs BM25 49,6%; `set_f1` 0,89 vs 0,72 | Resultado forte, mas o corpus é autoral e favorece os invariantes projetados |
| Dogfooding, 20 casos | Cortex comprime para ~15 tokens, mas recall ~0,27 vs BM25 ~0,43 e raw-context ~0,48 | Boa eficiência/safety signal; qualidade de recuperação ainda insuficiente |
| Judge semântico, 20 casos | `abstention_accuracy=0,85`, `answer_support_recall=0,25`, fidelidade `0,625` | Não inventar está melhor demonstrado que responder corretamente |
| Adversarial, 4 casos | Cortex ainda tem stale leak de 25% | O problema de atualização/supersessão não está resolvido em geral |
| CCB | Fixture moldado passa 8/8; versão natural só pontua 3 tarefas aplicáveis | O resultado mede parcialmente o formato do fixture e a cobertura do extrator |
| LongMemEval/SWE-bench | Loaders e gates existem, mas não há avaliação externa completa reproduzida | Infraestrutura de validação, não evidência científica ainda |

Antes de qualquer claim, corrigir a divergência entre os números do README,
`DOGFOODING_EVALUATION.md` e os artefatos gerados. Resultados devem ser gerados
automaticamente e identificados por commit, manifesto, dataset hash, modelo,
hardware e orçamento.

## 2. Formulação científica alvo

### Claim principal

Em tarefas de manutenção de software com histórico temporal, uma memória
governada por evidência reduz seleção de conhecimento obsoleto e afirmações sem
suporte, mantendo desempenho downstream comparável ou superior a RAG e
full-context sob o mesmo orçamento de contexto.

### Contribuições que podem ser defendidas

1. Uma representação de memória de engenharia que separa conteúdo, autoridade,
   confiança, validade, escopo e linhagem.
2. Uma política de compilação que trata supersessão, contradição e abstenção
   como restrições verificáveis, não apenas como sinais de ranking.
3. Um benchmark temporal de software que avalia simultaneamente suporte factual,
   stale leakage, custo, abstenção e sucesso da tarefa do agente.
4. Uma análise de fronteira segurança–utilidade–custo, incluindo ablações que
   mostrem qual mecanismo produz cada ganho.

O claim não deve ser “a primeira memória com grafo/proveniência” nem “SOTA em
memória de agentes” sem comparação externa. A contribuição mais defensável é
“memória governada para engenharia de software com garantias de evidência e
avaliação temporal downstream”.

## 3. Próximas implementações, em ordem

### Fase A — congelar a medição

**Estado em 2026-09-16:** o registro de execução foi implementado no runner
com `--experiment-registry`; ele mantém hora/host fora do payload determinístico
e associa cada linha a commit, manifesto, corpus congelado, adapters, modelos,
orçamento, classificação e hashes dos artefatos. Os itens abaixo continuam
abertos até que os documentos publicados sejam derivados desses registros.

- [Concluído] Criar um registro de experimentos versionado com uma linha por execução:
  commit, manifesto, hash do corpus, adapter, modelo, budget, hardware e
  classificação `confirmatory`/`exploratory`.
- Gerar README e `DOGFOODING_EVALUATION.md` a partir dos artefatos, evitando
  números copiados manualmente.
- Corrigir o badge de testes, a contagem de task types e a divergência entre
  os relatórios atuais.
- Fazer o `vector_rag` usar um encoder local fixado e identificável quando
  comparado como baseline; o fallback n-grama deve ser nomeado como tal.

**Aceitação:** duas execuções reproduzem `summary.json` e a documentação não
contém nenhum número que não possa ser rastreado a um artefato.

### Fase B — fechar o ciclo evidência → resposta

- Implementar um leitor fixo que receba apenas o contexto compilado.
- Exigir citações de IDs de evidência para afirmações verificáveis.
- Fazer a resposta abster-se quando não há suporte suficiente.
- Avaliar separadamente: recuperação, suporte factual, fidelidade, decisão de
  abstenção e resposta final.
- Rodar a rubrica `cortex-judge` com anotação cega e, para uma amostra,
  verificação humana independente.

**Aceitação:** nenhuma resposta pode citar evento que não foi recuperado; toda
afirmação apoiada, parcialmente apoiada ou não apoiada é mensurável por caso.

### Fase C — tornar a teoria testável

Formalizar e testar estas propriedades:

- **Proveniência:** todo item compilado possui uma cadeia até pelo menos uma
  fonte observável.
- **Não-ressurreição:** item supersedido não é selecionado para consulta de
  estado atual, salvo quando a consulta pede histórico.
- **Autoridade:** inferência do agente não pode se promover a confirmação
  humana sem uma transição explícita e autorizada.
- **Abstenção:** abaixo do limiar de evidência, a saída segura é abstention,
  não uma resposta com falsa certeza.
- **Reprodutibilidade:** o mesmo histórico, cutoff e configuração produzem o
  mesmo conjunto de evidências e trace.

Usar testes property-based ou geração de histórias com inserção de updates,
negações, duplicatas, eventos fora de ordem e consultas históricas.

**Aceitação:** cada propriedade tem especificação, teste positivo, teste
adversarial e contraexemplo documentado quando falha.

### Fase D — benchmark externo de engenharia

Construir um corpus temporal a partir de repositórios reais:

- episódios em ordem cronológica, compostos por issues, commits, testes,
  reviews e trajetórias de agente;
- cutoff estrito: patches futuros e respostas gold nunca entram na memória;
- perguntas sobre decisão, causa-raiz, correção rejeitada, estado atual,
  dependências e trabalho interrompido;
- dois anotadores cegos, κ reportado e split por repositório/tempo;
- teste final fechado, não usado para calibração.

SWE-bench deve ser usado como resultado downstream, não como simples corpus de
retrieval: medir se uma memória construída em episódios anteriores melhora a
resolução de uma issue posterior sob o mesmo agente, modelo, ferramentas,
tempo e orçamento. LongMemEval-S e LongMemEval-V2 entram como controles externos;
resultados sem anotação comparável continuam exploratórios.

Comparar pelo menos:

```text
sem memória
full-context controlado
BM25
vector-RAG com encoder fixado
memória estruturada/graph baseline reproduzível
Cortex completo
Cortex sem autoridade, sem supersessão, sem ledger e sem grafo
```

### Fase E — experimento decisivo

Pré-registrar como métricas primárias:

- sucesso da tarefa downstream;
- taxa de resposta com suporte factual;
- stale-leak rate;
- false-certainty rate;
- tokens e latência por consulta.

Usar comparações pareadas, intervalos de confiança e correção para múltiplas
hipóteses. O resultado esperado não precisa ser a maior acurácia bruta: a tese
é uma fronteira melhor entre confiabilidade, utilidade e custo.

**Critério de sucesso:** Cortex deve ser não inferior em sucesso downstream,
reduzir significativamente stale leakage/false certainty e usar menos contexto
que o baseline forte. Se perder utilidade sem compensação de segurança, a tese
deve ser reduzida, não reinterpretada.

## 4. Checklist obrigatório por implementação

Antes de começar:

- chamar o MCP do Cortex e executar `cortex_recall`, `cortex_status` e
  `cortex_phase`;
- registrar a hipótese, o risco e a métrica que a mudança pretende afetar.

Durante:

- registrar decisões e descobertas com `cortex_capture`/`cortex_emit`;
- não transformar intenção do agente em autoridade humana;
- preservar IDs, cutoff, proveniência e status de revisão.

Depois:

- executar `cortex_distill`, `cortex_review`, `cortex_retrieval_trace` e
  `cortex_verify` quando aplicável;
- executar testes unitários, regressão adversarial e benchmark correspondente;
- atualizar este roadmap ou um ADR quando a decisão mudar;
- registrar limitações e evidências no resumo final.

## 5. O que não fazer

- Não otimizar somente `set_f1` ignorando stale leakage e suporte factual.
- Não adicionar um novo componente apenas porque aparece em um paper concorrente.
- Não declarar inovação por combinação intuitiva sem definição formal e ablação.
- Não usar um corpus autoral como prova de generalização.
- Não apagar, suavizar ou esconder o caso adversarial que falhar.
- Não concluir uma implementação sem dogfooding MCP, salvo indisponibilidade
  explicitamente registrada.
