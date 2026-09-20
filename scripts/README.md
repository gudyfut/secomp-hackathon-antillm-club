# Scripts reproduziveis

## Preparar um clone novo

```powershell
python scripts/setup.py
```

O script:

1. exige Python 3.11 ou superior;
2. cria `.venv` sem alterar o Python global;
3. instala o projeto com os extras `dev`, `perception` e `decision`;
4. baixa `models/yolo26n-pose.pt` da origem oficial do Ultralytics;
5. valida tarefa e SHA-256 do peso;
6. cria `.env` a partir de `.env.example` quando ele ainda nao existe;
7. executa todos os testes offline.

Internet e necessaria apenas na primeira preparacao. O modelo e as dependencias ficam locais e
nao sao enviados ao Git.

## Executar

```powershell
python scripts/run.py --source 0
```

O wrapper sempre usa o ambiente criado pelo setup, sem exigir ativacao manual. Tambem aceita um
arquivo de video em `--source` e os demais argumentos de `main.py`.

## Exemplos do Jev

No Windows, sem ativar o ambiente:

```powershell
.\.venv\Scripts\python.exe -m decision.examples.simulated
.\.venv\Scripts\python.exe -m decision.examples.live
```

O exemplo simulado e offline. O exemplo real exige `TYPESAFE_API_KEY` preenchida no `.env`.

## Baixar ou revalidar somente os pesos

Com o ambiente ativado:

```powershell
python scripts/download_models.py
```
