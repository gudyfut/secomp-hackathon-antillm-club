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
- Node.js 20 ou superior apenas quando a integracao oficial com Jev for implementada;
- Git.

Um unico comando cria `.venv`, instala as dependencias, baixa e verifica o modelo oficial e roda
os testes offline:

```powershell
python scripts/setup.py
```

Pesos como `models/yolo26n-pose.pt` sao recursos externos baixados localmente e nao devem ser
versionados. A chave do Jev deve existir somente no `.env` local.

## Execucao

Valide fronteira real de perception para features com webcam ou arquivo de video:

```powershell
python scripts/run.py --source 0
```

Janela mostra pose YOLO, ByteTrack, FPS e emissao de `WorldState`. Terminal mostra somente estados
emitidos pela `FeaturePipeline`. Pressione `q` ou Escape para encerrar.

Para usar um arquivo de video:

```powershell
python scripts/run.py --source caminho\video.mp4
```

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
