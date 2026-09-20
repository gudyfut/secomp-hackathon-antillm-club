# Recursos externos e creditos

Registre qualquer biblioteca, framework, API, servico, modelo, dataset, trecho adaptado ou
material de referencia. Verifique a licenca antes do uso.

| Recurso/versao | Tipo | Origem/URL | Licenca/termos | Finalidade | Alteracoes | Onde usado | Verificado por |
|---|---|---|---|---|---|---|---|
| Ultralytics 8.4.157 | Framework | https://github.com/ultralytics/ultralytics | AGPL-3.0 ou licenca comercial aplicavel | Pose e tracking | Integracao por adapter proprio | `src/perception/` | Equipe |
| YOLO26n-pose, asset v8.4.0 | Modelo pre-treinado | https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n-pose.pt | AGPL-3.0 por padrao segundo Ultralytics | Deteccao de pessoas e 17 keypoints COCO | Nenhuma; inferencia local | `models/` via `scripts/download_models.py` | Equipe |
| ByteTrack via Ultralytics | Algoritmo de tracking | https://docs.ultralytics.com/modes/track/ | Termos do pacote Ultralytics | IDs persistentes entre frames | Configuracao oficial `bytetrack.yaml` | `src/perception/live.py` e `src/interface/runtime.py` | Equipe |
| lap 0.5.13 | Biblioteca numerica | https://pypi.org/project/lap/ | BSD-2-Clause | Associacao linear exigida pelo ByteTrack | Nenhuma | dependencia `perception` | Equipe |
| OpenCV 5.0.0.93 | Biblioteca | https://opencv.org/ | Apache-2.0 | Captura e preview da webcam | Nenhuma | `src/perception/live.py` | Equipe |
| Supervision 0.30.4 | Biblioteca planejada | https://github.com/roboflow/supervision | MIT | Utilitarios visuais quando necessario | Ainda nao utilizada no caminho atual | extra `perception` | Equipe |
| PyTorch / Torchvision | Framework de calculo | https://pytorch.org/ | BSD-3-Clause | Inferencia YOLO em CPU ou CUDA | Selecao automatica de dispositivo | instalacao e `src/interface/` | Equipe |
| NumPy | Biblioteca numerica | https://numpy.org/ | BSD-3-Clause | Matrizes e decodificacao de frames | Nenhuma | contratos, percepcao e interface | Equipe |
| TypeSafe SDK / Jev | API e SDK de IA | https://docs.typesafe.ai/ | Termos do servico e do pacote | Julgamentos tipados sobre o `WorldState` | Adapter e serializacao proprios | `src/decision/jev/` | Equipe |
| FastAPI / Starlette | Framework web | https://fastapi.tiangolo.com/ | MIT | Aplicacao local e WebSocket | Integracao propria | `src/interface/app.py` | Equipe |
| Uvicorn | Servidor ASGI | https://www.uvicorn.org/ | BSD-3-Clause | Servir a interface local | Configuracao propria | `src/interface/__main__.py` | Equipe |
| python-dotenv | Biblioteca | https://github.com/theskumar/python-dotenv | BSD-3-Clause | Carregar `.env` no backend | Nenhuma | interface e exemplos Jev | Equipe |
| pytest | Ferramenta de testes | https://pytest.org/ | MIT | Suite offline | Fixtures e testes proprios | `tests/` | Equipe |
| Ruff | Linter | https://docs.astral.sh/ruff/ | MIT | Verificacao estatica | Configuracao no `pyproject.toml` | desenvolvimento | Equipe |
| OpenAI Codex | IA generativa de desenvolvimento | https://developers.openai.com/codex/ | Termos do servico OpenAI | Apoio a arquitetura, codigo, testes, diagnostico, documentacao e Git | Saidas revisadas pela equipe | desenvolvimento; nao integra o runtime | Equipe |

O MVP nao utilizou dataset externo nem treinou um novo modelo. Videos de teste sao fornecidos
localmente, nao sao versionados e devem ser usados somente com origem e autorizacao adequadas.

## Observacao de licenca

O site oficial do Ultralytics informa que codigo e modelos YOLO sao oferecidos sob AGPL-3.0 por
padrao, com alternativa comercial para uso proprietario. Este repositorio atualmente possui uma
licenca MIT propria; antes de distribuicao publica ou uso alem do hackathon academico, a equipe
deve confirmar a compatibilidade da licenca do projeto completo. Esta anotacao nao e parecer
juridico.

## Checklist por recurso

- [ ] A origem e a versao sao reproduziveis.
- [ ] A licenca permite o uso pretendido.
- [ ] A atribuicao exigida esta presente.
- [ ] O recurso nao corresponde a reproducao integral de um projeto pronto.
- [ ] A equipe entende e consegue explicar como ele e usado.
