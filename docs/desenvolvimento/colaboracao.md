# Colaboracao em paralelo

## Fluxos de trabalho

### Developer A - Perception

1. Criar branch `feature/perception-<objetivo>`.
2. Trabalhar em `src/perception/` e `tests/perception/`.
3. Converter dependencias externas para `PerceptionFrame` dentro de `perception/adapters`.
4. Validar a saida contra fixtures/contratos, sem adicionar julgamento de agressao.
5. Entregar um commit focado e avisar se algum contrato compartilhado precisar mudar.

### Developer B - Features e Decision

1. Criar branch `feature/features-<objetivo>` ou `feature/decision-<objetivo>`.
2. Trabalhar em `src/features/`, `src/decision/` e testes correspondentes.
3. Usar `tests/fixtures/synthetic.py` enquanto a percepcao real nao estiver pronta.
4. Manter calculos deterministicos em features e julgamentos contextuais no Jev.
5. Simular o cliente Jev em testes locais; inferencia real deve ser um teste separado e explicito.

## Handoff por contrato

```text
A entrega PerceptionFrame
             |
             v
B atualiza TrackHistory/FeaturePipeline e entrega WorldState
             |
             v
B integra Jev e entrega DecisionResult
             |
             v
A + B integram a interface
```

Cada branch deve evitar arquivos do outro fluxo. Contratos, interface, README e configuracoes
globais sao compartilhados: coordenar antes de editar e manter mudancas pequenas.

## Mudanca de contrato

1. Explicar a necessidade e exemplos de antes/depois.
2. Preferir campo opcional/aditivo quando semanticamente correto.
3. Atualizar contrato, fixture e todos os testes consumidores no mesmo commit.
4. Evitar renomear/remover campos durante trabalho paralelo.
5. Nao refatorar implementacoes de outro dono como parte da mudanca.

## Integracao

- Integrar primeiro contratos acordados, se houver mudanca compartilhada.
- Integrar depois as branches de cada modulo.
- Rodar `python -m pytest` apos cada merge.
- Fazer o primeiro teste ponta a ponta com fixture antes de usar video real e inferencia Jev real.
