# Arquitetura do Campus Sentinel

## Objetivo do MVP

Detectar evidencias observaveis e temporais relacionadas a agressao/briga em video e entregar um
estado estruturado para o julgamento contextual do Jev. Vandalismo, assalto e outras ocorrencias
sao extensoes futuras, nao prioridades atuais.

## Fluxo

```mermaid
flowchart LR
    A[Video ou camera] --> B[YOLO26n-pose]
    B --> C[ByteTrack]
    C --> D[Perception adapter]
    D -->|PerceptionFrame| E[TrackHistory e FeaturePipeline]
    E -->|WorldState| F[Jev DecisionEngine]
    F -->|DecisionResult| G[Interface]
```

## Responsabilidades e dependencias

| Modulo | Entrada | Saida | Responsabilidade | Dependencias externas permitidas |
|---|---|---|---|---|
| Perception | frame/video | `PerceptionFrame` | Pose, deteccao, tracking e metadados objetivos | Ultralytics, ByteTrack, OpenCV, NumPy, Supervision |
| Features | `PerceptionFrame` | `WorldState` | Historico, geometria, movimento e interacoes deterministicas | NumPy; nunca Ultralytics |
| Decision | `WorldState` | `DecisionResult` | Julgamentos tipados e politica contextual | Jev/TypeSafe encapsulado |
| Interface | contratos internos | visualizacao | Mostrar evidencias, estado e decisao | Nunca objetos Ultralytics/Jev |

## Contratos estabelecidos

Os tipos canonicos estao em `src/contracts/`:

- `BoundingBox`, `PoseKeypoint`, `PoseKeypoints`, `TrackedPerson`, `PerceptionFrame`;
- `PersonFeatures`, `InteractionFeatures`, `WorldState`;
- `EventType`, `Severity`, `Urgency`, `Action`, `DecisionResult`;
- portas `FeaturePipeline.update()` e `DecisionEngine.decide()`.

Campos opcionais significam evidencia ausente/insuficiente. Nao converter ausencia em zero. Os
contratos nao importam SDKs externos nem incluem logica de negocio.

## Arquitetura temporal

```text
frame (20-30 FPS, quando o hardware permitir)
  -> atualizacao de perception
  -> atualizacao continua de historico/features
  -> WorldState quando a janela estiver pronta
  -> Jev algumas vezes por segundo ou por mudanca relevante
```

A cadencia exata deve ser calibrada. O contrato permite que `FeaturePipeline.update()` retorne
`None` quando ainda nao ha um novo estado. `DecisionEngine.decide()` e assincrono porque envolve
uma dependencia externa; isso nao exige timers complexos ou microservicos.

## Features planejadas

### Por pessoa

- `body_speed`, `wrist_speed`, `wrist_acceleration`;
- `motion_intensity`, `person_fallen`.

### Por interacao

- `distance_between_people`, `rapid_approach`;
- `wrist_to_head_distance`, `wrist_to_torso_distance`;
- `bbox_overlap`, `possible_contact`;
- `interaction_duration_ms`, `repeated_aggressive_motion`.

Distancias devem ser normalizadas por escala corporal/bounding box quando possivel. Cada
implementacao precisa documentar unidade, faixa e comportamento com keypoints ausentes.

## Limites externos

```text
Ultralytics Result -> src/perception/adapters -> PerceptionFrame
Jev SDK response   -> src/decision/jev       -> DecisionResult
```

Esses adapters sao os unicos locais autorizados a conhecer detalhes dos SDKs. Features podem ser
testadas com `PerceptionFrame` sintetico e decision com `WorldState` sintetico.

## Decisoes adiadas intencionalmente

- politica/cadencia exata de chamada ao Jev;
- formato de serializacao caso o adapter Jev use runtime diferente do pipeline Python;
- framework e persistencia da interface;
- thresholds e janelas temporais, que exigem experimentos;
- qualquer treinamento de modelo.
