# Modulos da aplicacao

```text
perception -> PerceptionFrame -> features -> WorldState -> decision -> DecisionResult
```

- `contracts/`: tipos e portas compartilhados, sem logica de negocio.
- `perception/`: video, YOLO26n-pose, ByteTrack e adaptacao para os contratos internos.
- `features/`: historico temporal, geometria, movimento e estado do mundo.
- `decision/`: integracao Jev, politica de chamada e mapeamento da decisao.
- `interface/`: futura visualizacao; consome apenas contratos internos.
- `shared/`: utilitarios realmente neutros; nao use como pasta de codigo sem dono.

Subdiretorios devem nascer quando houver codigo correspondente. O detalhamento arquitetural esta
em `docs/projeto/arquitetura.md`.
