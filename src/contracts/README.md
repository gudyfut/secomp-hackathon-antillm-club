# Contratos compartilhados

Esta pasta e a fronteira estavel entre os modulos. Ela contem somente estruturas de dados e
protocolos pequenos, sem calculos de features, chamadas externas ou regras de decisao.

## Fluxo

```text
perception -> PerceptionFrame
features   -> WorldState
decision   -> DecisionResult
```

As dataclasses usam tuplas e `frozen=True` para reduzir mutacao acidental entre componentes.
Campos opcionais representam informacao ausente; ausencia nunca deve ser convertida
silenciosamente em zero ou `False`.

Mudancas exigem coordenacao entre os desenvolvedores, atualizacao das fixtures sinteticas e teste
de todos os consumidores. Dependencias externas nao podem aparecer nestes tipos.
