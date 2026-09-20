# Camada de decisão Jev

Este módulo recebe `contracts.WorldState`, envia somente evidências estruturadas ao Jev e converte
a resposta do SDK oficial para tipos próprios. Nenhum pixel, objeto do Ultralytics ou chave de API
é incluído no estado enviado.

## Fluxo atual

```text
WorldState
  -> build_jev_state
  -> cinco perguntas Choice em uma chamada system_one
  -> JevDecisionAssessment
  -> DecisionResult
```

As perguntas independentes avaliam qualidade da evidência, evento, severidade, urgência e ação. O
vocabulário de evento é `NORMAL`, `SUSPICIOUS_INTERACTION`, `FIGHT`, `ASSAULT` ou
`UNKNOWN_ANOMALY`. A ação é consultiva: `IGNORE`, `MONITOR`, `ALERT` ou `DISPATCH_SECURITY`.

`JevDecisionAssessment` preserva cada escolha, confiança e distribuição de probabilidades sem
calcular uma média artificial. Quando o Jev indica evidência insuficiente, não é criado um
`DecisionResult`. Falha de API, evidência insuficiente e evento normal permanecem estados distintos.

## Configuração e segurança

```powershell
python -m pip install -e ".[dev,decision]"
```

O cliente lê `TYPESAFE_API_KEY` do ambiente; os exemplos carregam o `.env` da raiz. Nunca versione,
imprima ou envie essa chave ao cliente web. `JEV_INTERVAL_SECONDS` é aplicado pelo coordenador da
interface e não pelo adaptador de decisão.

## Verificação

```powershell
.\.venv\Scripts\python.exe -m pytest tests\decision
.\.venv\Scripts\python.exe -m decision.examples.simulated
.\.venv\Scripts\python.exe -m decision.examples.live
```

Os testes e o exemplo simulado não usam a rede. O exemplo real consome a API. O campo
`usage.output_tokens` é telemetria retornada pelo serviço e, isoladamente, não comprova cobrança.

Arquivos principais:

- `jev/serialization.py`: JSON compacto derivado do `WorldState`;
- `jev/questions.py`: perguntas `Choice` e critérios;
- `jev/evaluator.py`: chamada `system_one`, validação e mapeamento;
- `jev/types.py`: tipos internos desacoplados do SDK.
