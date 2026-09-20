# Campus Sentinel

**Deteccao Inteligente de Ocorrencias de Seguranca em Ambientes Universitarios**

MVP do Hackathon de Visao Computacional da SECOMP 2026. O foco atual e detectar evidencias
visuais e temporais relacionadas a **agressoes/brigas em video** e usar Jev para a decisao
contextual. O projeto ainda esta em preparacao arquitetural; a solucao completa nao foi
implementada.

## Arquitetura

```text
video/camera -> YOLO26n-pose + ByteTrack -> PerceptionFrame
             -> FeaturePipeline -> WorldState
             -> Jev -> DecisionResult -> interface
```

- `perception`: observacoes objetivas de video, pose e tracking.
- `features`: historico e calculos deterministas que produzem `WorldState`.
- `decision`: julgamento contextual com Jev e saida `DecisionResult`.
- `contracts`: fronteiras estaveis entre os modulos.
- `interface`: sera priorizada depois da integracao do MVP.

Detalhes: [arquitetura](docs/projeto/arquitetura.md) e [regras para agentes](AGENTS.md).

## Preparacao do ambiente

Requisitos atuais:

- Python 3.11 ou superior;
- Git.

Um unico comando cria `.venv`, instala perception, features, Jev e ferramentas de desenvolvimento,
baixa e verifica o modelo oficial, prepara o `.env` local e roda os testes offline:

```powershell
python scripts/setup.py
```

Pesos como `models/yolo26n-pose.pt` sao recursos externos baixados localmente e nao devem ser
versionados. A chave do Jev deve existir somente no `.env` local.

## Execucao

### Webcam ou video

```powershell
python scripts/run.py --source 0
python scripts/run.py --source caminho\video.mp4
```

A janela mostra pose, bounding boxes, tracking ByteTrack, FPS e emissao de `WorldState`. O terminal
mostra os estados emitidos pela `FeaturePipeline`. Pressione `q` ou Escape para encerrar.

### Jev

```powershell
# Offline: nao usa chave, rede ou creditos
.\.venv\Scripts\python.exe -m decision.examples.simulated

# Real: le TYPESAFE_API_KEY do .env
.\.venv\Scripts\python.exe -m decision.examples.live
```

O exemplo real mostra o JSON enviado e recebido, mas nunca imprime headers ou a chave. A pergunta
atual e provisoria e valida a fronteira `WorldState -> JevAssessment`; ela ainda nao representa um
classificador calibrado de briga nem produz o `DecisionResult` final do MVP.

## Onde trabalhar

- Developer A: `src/perception/` e `tests/perception/`.
- Developer B: `src/features/`, `src/decision/`, `tests/features/` e `tests/decision/`.
- Compartilhado: `src/contracts/`, `src/interface/` e arquivos globais.

A estrategia de branches e handoff esta em
[docs/desenvolvimento/colaboracao.md](docs/desenvolvimento/colaboracao.md).

## Documentacao e entrega

Consulte o [indice de documentacao](docs/README.md). Recursos externos, uso de IA, experimentos,
limitacoes e evidencias devem ser registrados durante o evento.

## Licenca

Codigo sob [licenca MIT](LICENSE). Modelos, datasets e outros recursos externos possuem termos
proprios que devem ser verificados e creditados.
