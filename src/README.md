# Módulos da aplicação

```text
câmera/vídeo
  -> perception -> PerceptionFrame
  -> features   -> WorldState
  -> decision   -> DecisionResult
  -> interface
```

- `contracts/`: contratos e portas estáveis, sem lógica de negócio;
- `perception/`: YOLO26n-pose, ByteTrack e adaptação para `PerceptionFrame`;
- `features/`: histórico, geometria, movimento e construção de `WorldState`;
- `decision/`: serialização, perguntas tipadas, chamada ao Jev e `DecisionResult`;
- `interface/`: FastAPI, WebSocket, coordenação do fluxo e painel web;
- `shared/`: reservado somente a utilitários realmente neutros.

Os adaptadores convertem resultados externos antes das fronteiras estáveis: resultados do
Ultralytics viram `PerceptionFrame` e respostas do SDK TypeSafe viram `DecisionResult`. A camada de
composição da interface instancia essas dependências, mas o painel do navegador recebe apenas JSON
derivado dos contratos do projeto. O detalhamento está no [README principal](../README.md).
