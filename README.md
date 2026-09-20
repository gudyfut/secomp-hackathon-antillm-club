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

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,decision]"
Copy-Item .env.example .env
python -m pytest
```

Developer A instala tambem as dependencias de visao:

```powershell
python -m pip install -e ".[dev,perception]"
```

Pesos como `yolo26n-pose.pt` sao obtidos localmente pela ferramenta de visao e nao devem ser
versionados. A chave do Jev deve existir somente no `.env` local.

## Execucao da camada Jev

O fluxo completo da aplicacao ainda nao possui um entrypoint. A camada decisoria ja oferece uma
simulacao offline e um exemplo real isolado:

```powershell
python -m decision.examples.simulated
python -m decision.examples.live
```

O exemplo real le `TYPESAFE_API_KEY` do `.env`; os headers nunca sao impressos.

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
