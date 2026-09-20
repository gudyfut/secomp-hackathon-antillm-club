# Scripts reproduzíveis

## Preparar um clone novo

Na raiz do repositório:

```powershell
python scripts/setup.py
```

O instalador exige Python 3.11+, cria `.venv`, instala os extras `dev`, `perception`, `decision` e
`interface`, tenta habilitar PyTorch CUDA em uma GPU NVIDIA compatível, baixa e verifica
`models/yolo26n-pose.pt`, cria o `.env` local quando necessário e executa os testes offline. Se CUDA
não estiver disponível, o sistema permanece utilizável em CPU.

## Executar a interface completa

```powershell
.\.venv\Scripts\python.exe -m interface
```

Depois, abra `http://127.0.0.1:8000`. Este é o fluxo principal: câmera ou vídeo, YOLO Pose,
ByteTrack, features temporais, Jev e painel web.

## Diagnóstico local de percepção

```powershell
python scripts/run.py --source 0
python scripts/run.py --source caminho\video.mp4
```

`run.py` usa automaticamente o Python da `.venv` e encaminha os argumentos a `main.py`. Esse modo
abre uma janela OpenCV com percepção e features; não executa a interface web nem a decisão Jev.
Pressione `q` ou Escape para encerrar.

## Exemplos do Jev

```powershell
.\.venv\Scripts\python.exe -m decision.examples.simulated
.\.venv\Scripts\python.exe -m decision.examples.live
```

O primeiro usa uma resposta simulada e não consome rede ou créditos. O segundo faz uma avaliação
real e exige `TYPESAFE_API_KEY` no `.env`.

## Baixar ou revalidar somente os pesos

```powershell
.\.venv\Scripts\python.exe scripts\download_models.py
```
