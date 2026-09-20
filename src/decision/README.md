# Jev decision layer

Ownership: Developer B.

Este modulo recebe `contracts.WorldState`, envia apenas evidencias estruturadas ao Jev e converte
a resposta do SDK em tipos proprios. O restante do projeto nunca deve receber objetos internos do
SDK. A integracao usa Python e o pacote oficial `typesafe-sdk`.

## Estado atual

`jev/JevWorldStateEvaluator` implementa a fronteira testavel:

```text
WorldState
  -> JSON com worldState
  -> pergunta Choice provisoria
  -> SDK Python do Jev
  -> JevAssessment independente do SDK
```

A pergunta atual distingue `no_clear_concern`, `concerning_interaction` e
`insufficient_evidence`. Ela valida a integracao, mas ainda nao e um classificador calibrado de
briga. Por isso o adapter ainda nao inventa um mapeamento definitivo para `DecisionResult`. Evento,
severidade, urgencia, acao, politica de confianca e cadencia serao definidos com exemplos reais do
MVP.

Falha da API, evidencia insuficiente e ausencia de preocupacao permanecem estados diferentes.
Calculos deterministicos continuam em `features`; a decisao contextual pertence ao Jev.

## Instalacao

Na raiz do repositorio:

```powershell
python -m pip install -e ".[dev,decision]"
```

O cliente le `TYPESAFE_API_KEY` do ambiente. O exemplo real carrega essa variavel do `.env` da
raiz. Nunca versione nem imprima a chave.

## Comandos

```powershell
# Testes offline: nao usam chave nem rede
python -m pytest tests/decision

# Demonstra exatamente a entrada, perguntas e saida usando uma resposta simulada
python -m decision.examples.simulated

# Faz uma chamada real e mostra o JSON HTTP enviado e recebido sem mostrar headers
python -m decision.examples.live
```

O campo `usage.output_tokens` e telemetria retornada pela API. Sua presenca nao implica, sozinha,
cobranca de tokens de saida.

## Onde alterar depois

- `jev/serialization.py`: formato JSON derivado de `WorldState`;
- `jev/questions.py`: perguntas e criterios enviados ao modelo;
- `jev/evaluator.py`: chamada do SDK e mapeamento da resposta;
- `examples/`: demonstracoes offline e real;
- `tests/decision/test_jev.py`: contrato e falhas do adapter.
