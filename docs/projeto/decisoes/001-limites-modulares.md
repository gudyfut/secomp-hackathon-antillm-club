# ADR 001 - Contratos e limites modulares do MVP

- **Data:** 2026-09-20
- **Estado:** aceita
- **Participantes:** equipe do Campus Sentinel

## Contexto

Dois desenvolvedores e seus agentes precisam trabalhar em paralelo em percepcao e em
features/decisao, sem compartilhar tipos de SDK nem editar os mesmos arquivos com frequencia.

## Decisao

Adotar tres contratos imutaveis e independentes de SDK:

```text
PerceptionFrame -> FeaturePipeline
WorldState -> DecisionEngine
DecisionResult -> Interface
```

Ultralytics e ByteTrack ficam encapsulados em adapters de perception. Jev fica encapsulado em
decision. Features contem somente transformacoes deterministicamente testaveis.

## Consequencias

- Cada fluxo pode usar fixtures sinteticas e evoluir sem esperar a implementacao do outro.
- Mudancas em `src/contracts/` exigem coordenacao e testes de todos os consumidores.
- Um eventual limite entre runtimes para Jev deve serializar estes mesmos conceitos sem expor o
  SDK; a estrategia exata foi adiada ate a implementacao.
- A estrutura evita microservicos e abstracoes adicionais no MVP.

## Verificacao

`tests/contracts/`, `tests/features/` e `tests/decision/` exercitam as fronteiras sem YOLO ou Jev
reais.
