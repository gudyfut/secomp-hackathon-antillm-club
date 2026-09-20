# Percepção

Este módulo recebe frames de câmera ou vídeo, executa YOLO26n-pose com ByteTrack e emite
`contracts.PerceptionFrame`. Ele relata somente observações — pessoas, caixas, keypoints,
confianças e IDs — e nunca classifica uma interação como briga ou agressão.

`adapters/ultralytics.py` converte um resultado do Ultralytics para os contratos do projeto.
`live.py` contém o fluxo diagnóstico OpenCV e entrega os frames a uma `FeaturePipeline` injetada;
ele não calcula features nem chama o Jev.

O uso principal ocorre pela interface web:

```powershell
python scripts/setup.py
.\.venv\Scripts\python.exe -m interface
```

Para testar somente percepção e features:

```powershell
python scripts/run.py --source 0
python scripts/run.py --source caminho\video.mp4
```

Na janela OpenCV, pressione `q` ou Escape. O overlay mostra FPS, estado do ByteTrack, pessoas
detectadas e emissão de `WorldState`. Esse diagnóstico não executa a decisão contextual.
