---
name: cortex-judge
description: "Protocolo e rubrica de avaliação para o Code Agent atuar como LLM Judge sem depender de APIs externas, avaliando suporte semântico, ranking e abstenção no benchmark do Cortex."
---

# Cortex LLM Judge Skill

Esta skill habilita o agente de código a atuar diretamente como **LLM Judge** no benchmark de memória de engenharia do Cortex, eliminando a dependência de APIs externas pagas ou tokens externos.

## Workflow

1. **Localizar o lote de entrada**: O benchmark exporta os casos em `artifacts/judge_inbox.json`.
2. **Avaliar cada caso**:
   - `case_id`: Identificador da instância do benchmark.
   - `answer_supported`: `true` se as evidências recuperadas (`retrieved_evidence_texts`) contêm fatos factuais suficientes para responder à pergunta com base na `gold_answer`. `false` caso contrário.
   - `relevance_ranking`: Lista com os IDs de evidência ordenados do mais informativo para o menos informativo.
   - `abstention_appropriate`: `true` se a decisão de se abster (`abstained=true`) coincidiu com a ausência de evidência (`expected_abstention=true`), OU se a decisão de responder coincidiu com a presença de evidência real.
   - `fidelity_score`: `1.0` se totalmente fiel e sem alucinação, `0.5` se parcialmente suportado, `0.0` se sem suporte.
   - `reasoning`: Explicação técnica concisa (1-2 frases).
3. **Gravar a saída**: Salvar em `artifacts/judge_verdicts.json`.
4. **Calcular métricas**: Executar `python -m cortex.benchmarks.llm_judge --eval` para gerar `artifacts/judge_report.json`.

## Rubrica de Julgamento

| Critério | Regra |
|---|---|
| **Ausência / Abstention** | Se a pergunta for sobre tópico inexistente (Redis, Docker, etc.) e o sistema não recuperou evidência, `abstention_appropriate: true` e `answer_supported: false`. |
| **Suporte Factual** | Informações como contagem de testes ("243"), commit hash ("c5f1bd1") ou nomes de arquivos devem estar explicitamente presentes nas evidências para marcar `answer_supported: true`. |
| **Ranking MRR** | O ID do evento que contém a resposta mais direta deve estar na primeira posição de `relevance_ranking`. |
