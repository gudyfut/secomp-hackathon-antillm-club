# Testes

- `contracts/`: estabilidade e construção dos contratos compartilhados;
- `perception/`: adaptação de resultados e comportamento isolado de tracking;
- `features/`: geometria e cenários temporais com `PerceptionFrame` sintético;
- `decision/`: serialização, perguntas e mapeamento com cliente Jev injetado;
- `interface/`: coordenação da cadência e integração entre os contratos;
- `fixtures/`: construtores sintéticos reutilizados pela suíte.

Execute no Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests
```

Os testes são offline: não abrem a webcam, não carregam pesos e não fazem chamadas reais ao Jev.
Mocks validam o contrato da integração, não a precisão do detector nem a qualidade do modelo.
