# Modelos e pesos

Pesos não são versionados neste repositório. O instalador baixa o recurso configurado e verifica
seu tipo e checksum:

```powershell
python scripts/setup.py
```

| Arquivo local | Uso | SHA-256 esperado |
| --- | --- | --- |
| `models/yolo26n-pose.pt` | Pose humana via Ultralytics `8.4.157` | `eb3bb8268828aeaf515cec23a4bfafd793944a86fe9af94ba7823609c14522a9` |

O arquivo tem aproximadamente 7,5 MB. Para baixar ou revalidar apenas o peso:

```powershell
.\.venv\Scripts\python.exe scripts\download_models.py
```

Modelos e serviços externos possuem termos próprios. Consulte
[`docs/entrega/recursos-externos.md`](../docs/entrega/recursos-externos.md) antes da entrega.
