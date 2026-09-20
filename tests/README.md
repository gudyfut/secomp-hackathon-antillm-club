# Testes

- `contracts/`: estabilidade e construcao dos tipos compartilhados.
- `perception/`: adaptadores, video e tracking isolados.
- `features/`: calculos com `PerceptionFrame` sintetico, sem YOLO.
- `decision/`: politica/mapeamento com `WorldState` sintetico e cliente Jev simulado.
- `fixtures/`: construtores sinteticos compartilhados pelos testes.

Execute:

```powershell
python -m pytest
```

Mocks validam a integracao do codigo, nao a qualidade do modelo Jev nem a precisao do detector.
