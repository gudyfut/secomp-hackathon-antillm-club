# Adaptador do Ultralytics

`ultralytics.py` mantém a fronteira entre a biblioteca externa e os contratos internos:

```text
Ultralytics Result -> adapter -> PerceptionFrame
```

O adaptador copia somente escalares necessários: bounding boxes, confiança, `track_id`, 17
keypoints COCO com confiança e metadados de frame/timestamp. Tensores, objetos `Results`, objetos do
ByteTrack e frames OpenCV nunca fazem parte de `PerceptionFrame`.

As features e a interface dependem do contrato do projeto, não da estrutura interna do
Ultralytics. Alterações no SDK devem ser absorvidas e testadas neste adaptador.
