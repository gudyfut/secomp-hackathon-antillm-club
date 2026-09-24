# Extração de features e WorldState

Este módulo consome somente `contracts.PerceptionFrame`, mantém históricos limitados por
`track_id`, calcula evidências determinísticas e emite `contracts.WorldState`. Ele não decide se há
uma briga e não depende de YOLO, vídeos ou pesos para ser testado.

## Pipeline atual

`TemporalFeaturePipeline.update(frame)` usa os timestamps da fonte, não o relógio de execução. O
histórico padrão retém até 5 segundos e pode emitir um `WorldState` a cada 0,25 segundo. Amostras e
interações antigas são descartadas para limitar o uso de memória.

As medidas usam a altura corporal/bounding box como escala sempre que possível:

- velocidade corporal e pico recente de velocidade;
- velocidade, aceleração e picos de movimento dos braços;
- intensidade de articulação corporal relativa ao torso;
- heurística de possível pessoa caída;
- distância entre pessoas e aproximação rápida;
- menor distância recente de punhos à cabeça ou ao torso, nos dois sentidos;
- sobreposição das bounding boxes, proximidade e contato provável;
- duração da proximidade e movimento agressivo repetido.

Os sinais booleanos `rapid_approach`, `possible_contact` e `repeated_aggressive_motion` são
calculados com os limiares iniciais de `FeatureConfig`. `possible_contact` só fica verdadeiro
quando uma distância de punho à cabeça/torso está abaixo do limiar **e** há movimento rápido do
braço na mesma amostra; proximidade ou sobreposição de boxes sem movimento não é contato provável.
Todos esses sinais são evidências objetivas para o Jev, não um veredito de violência.

## Unidades e dados ausentes

- velocidades: alturas corporais por segundo;
- aceleração: alturas corporais por segundo ao quadrado;
- distâncias: alturas corporais em espaço de imagem;
- `bbox_overlap`: IoU visual no intervalo `[0, 1]`;
- duração: segundos.

Histórico insuficiente, timing inválido, caixa degenerada ou keypoint com baixa confiança produz
`None`; movimento observado igual a zero produz `0.0`. Os valores padrão — incluindo confiança
mínima `0.35`, contato `0.32`, movimento de braço `0.80` e dois picos para repetição — são limiares
de engenharia e ainda precisam ser calibrados com vídeos representativos.

## Limitações

Normalização 2D não mede distância física nem remove totalmente a perspectiva. Oclusões degradam a
pose, IDs podem trocar, ruído do detector afeta movimentos locais e a comparação entre pares cresce
quadraticamente com o número de pessoas visíveis.
