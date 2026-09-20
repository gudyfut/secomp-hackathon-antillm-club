# Interface web

A interface atual é parte do MVP. Ela serve o painel local com FastAPI, recebe frames JPEG por
WebSocket, coordena a inferência e mostra as evidências e decisões sem expor a chave da TypeSafe ao
navegador.

## Componentes

- `app.py`: aplicação FastAPI, rota `/`, WebSocket `/ws/analyze`, carregamento do modelo e seleção
  de CPU/CUDA;
- `runtime.py`: ligação entre adaptador de percepção, `TemporalFeaturePipeline` e
  `JevDecisionEngine`;
- `static/index.html`: captura da câmera, reprodução de vídeo em 1×, overlays e painel de estado;
- `__main__.py`: entrada executável e opções de host/porta.

O navegador envia uma mensagem `start`, metadados do frame e o JPEG binário. O servidor responde
com eventos de estado, frames processados, início de avaliação, decisão ou erro. O painel representa
`NORMAL` em verde, interações suspeitas em amarelo e `FIGHT`/`ASSAULT` em vermelho.

## Executar

```powershell
.\.venv\Scripts\python.exe -m interface
```

Abra `http://127.0.0.1:8000`. A chave `TYPESAFE_API_KEY` permanece no `.env` do servidor. Sem ela,
os overlays e o `WorldState` continuam ativos, mas não há decisão contextual.

A camada de composição instancia o modelo Ultralytics e o cliente TypeSafe e os injeta nos módulos
responsáveis. Resultados externos são convertidos pelos adaptadores; o painel recebe somente JSON
derivado de `PerceptionFrame`, `WorldState` e `DecisionResult`.
