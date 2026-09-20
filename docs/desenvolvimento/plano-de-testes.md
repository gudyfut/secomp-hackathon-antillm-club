# Plano de testes

## Objetivo

Demonstrar que os componentes e o fluxo integrado funcionam nos cenarios escolhidos, incluindo
falhas previsiveis. Resultados devem ser reais e reproduziveis.

## Matriz

| ID | Nivel | Cenario | Entrada | Resultado esperado | Resultado observado | Evidencia | Estado |
|---|---|---|---|---|---|---|---|
| T-001 | Contrato | Construcao de `PerceptionFrame` sintetico | Fixture local | Tipo criado sem SDK externo | `python -m pytest` | `tests/contracts/` | Automatizado |
| T-002 | Contrato | Construcao de `WorldState` sintetico | Fixture local | Tipo criado sem YOLO | `python -m pytest` | `tests/contracts/` | Automatizado |
| T-003 | Integracao | Perception para features | `PerceptionFrame` sintetico | Pipeline substituivel pelo contrato | `python -m pytest` | `tests/features/` | Automatizado |
| T-004 | Integracao | WorldState para decision | `WorldState` sintetico | Engine substituivel pelo contrato | `python -m pytest` | `tests/decision/` | Automatizado |
| T-005 | Ponta a ponta | Cenario principal da demo | [PREENCHER] | Ocorrencia exibida | [PREENCHER] | [PREENCHER] | Planejado |
| T-006 | Resiliencia | Video/servico indisponivel | [PREENCHER] | Mensagem e fallback seguros | [PREENCHER] | [PREENCHER] | Planejado |
| T-007 | Qualidade | Baixa iluminacao/angulo adverso | [PREENCHER] | Limitacao observavel | [PREENCHER] | [PREENCHER] | Planejado |

## Ensaio da demonstracao

- Ambiente e hardware: [PREENCHER]
- Comando executado: [PREENCHER]
- Duracao: [PREENCHER]
- Data/hora do ultimo ensaio: [PREENCHER]
- Plano de contingencia testado: [PREENCHER]
