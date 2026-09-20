O repositório foi reorganizado para dois fluxos paralelos, com contratos mínimos compartilhados e sem implementar os algoritmos de detecção de agressão.

  ## Estrutura relevante

  src/
  ├── contracts/
  │   ├── perception.py
  │   ├── world_state.py
  │   ├── decision.py
  │   └── ports.py
  ├── perception/
  │   └── adapters/
  ├── features/
  ├── decision/
  ├── interface/
  └── shared/

  tests/
  ├── contracts/
  ├── perception/
  ├── features/
  ├── decision/
  └── fixtures/
      └── synthetic.py

  Diretórios antigos e vazios como src/pipeline/ e tests/unit/ foram removidos. Não criei toda a árvore especulativa de geometry/, motion/, jev/ etc.; esses
  diretórios deverão surgir quando tiverem implementação real.

  ## Principais arquivos

  - AGENTS.md: arquitetura, ownership, limites de edição, contratos, tecnologias, Git, testes e proibições.
  - README.md: instalação curta, arquitetura e indicação de onde cada pessoa trabalha.
  - pyproject.toml: Python 3.11+, dependências básicas, extras de percepção e ferramentas de desenvolvimento.
  - .env.example: modelo, fonte de vídeo e TYPESAFE_API_KEY, sem credenciais.
  - docs/projeto/arquitetura.md: fluxo streaming, cadências, features planejadas e limites externos.
  - docs/desenvolvimento/colaboracao.md: branches, handoff e procedimento para alterações de contrato.
  - ADR 001 (docs/projeto/decisoes/001-limites-modulares.md): registra formalmente a divisão modular.

  ## Contratos estabelecidos

  Em src/contracts (src/contracts/README.md):

  - Percepção: BoundingBox, PoseKeypoint, PoseKeypoints, TrackedPerson e PerceptionFrame.
  - Features: PersonFeatures, InteractionFeatures e WorldState.
  - Decisão: EventType, Severity, Urgency, Action e DecisionResult.
  - Portas: FeaturePipeline.update() e DecisionEngine.decide().

  As dataclasses são imutáveis e independentes de SDK. Campos opcionais representam evidência ausente — não zero ou resultado negativo.

  ## Fluxos dos desenvolvedores

  Developer A trabalha normalmente apenas em:

  src/perception/**
  tests/perception/**

  Outputs de Ultralytics e ByteTrack devem ser convertidos pelo adapter:

  Ultralytics Result -> Perception Adapter -> PerceptionFrame

  Developer B trabalha normalmente em:

  src/features/**
  src/decision/**
  tests/features/**
  tests/decision/**

  Pode desenvolver sem esperar pelo YOLO usando tests/fixtures/synthetic.py.

  Áreas compartilhadas:

  src/contracts/**
  src/interface/**
  tests/contracts/**
  configurações globais
  documentação transversal

  ## Decisões importantes

  - Perception não emite veredito de agressão.
  - Features não importam Ultralytics.
  - Jev recebe WorldState; a interface recebe apenas DecisionResult.
  - FeaturePipeline.update() pode não produzir um estado em todos os frames.
  - DecisionEngine.decide() é assíncrono, preparando a chamada externa sem introduzir timers ou serviços agora.
  - Não foi criado um SDK Python fictício para Jev. A documentação oficial atual apresenta SDK JavaScript/TypeScript, Node 20+ e TYPESAFE_API_KEY; a escolha do
    menor adapter entre runtimes ficou conscientemente adiada. Documentação TypeSafe

  - A abordagem planejada de YOLO26n-pose com ByteTrack é suportada oficialmente pelo Ultralytics. Documentação de tracking

  ## Validação

  - 5 testes passando.
  - Ruff sem problemas.
  - 35 arquivos Markdown verificados, sem links quebrados.
  - Nenhum diretório vazio em src/ ou tests/.
  - .gitignore cobre credenciais, vídeos, pesos, resultados do YOLO e artefatos locais.
  - Apenas dependências leves de desenvolvimento foram instaladas; o pacote pesado de percepção não foi baixado.
  - Nenhuma branch ou commit foi criado.