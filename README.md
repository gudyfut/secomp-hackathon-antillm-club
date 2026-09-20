# Campus Sentinel

**Detecção inteligente de ocorrências de segurança em ambientes universitários**

MVP desenvolvido para o Hackathon de Visão Computacional da **SECOMP 2026**.

O Campus Sentinel analisa uma câmera ou um vídeo em ritmo real, acompanha pessoas com pose e
tracking, transforma o movimento observado em evidências temporais e usa o **Jev, da TypeSafe**, para
decidir contextualmente se a cena aparenta ser normal, suspeita ou compatível com violência.

> Este é um protótipo de apoio a operadores humanos. Ele não substitui avaliação humana e não deve
> executar ações de segurança automaticamente.

## O problema

Câmeras convencionais registram o que aconteceu, mas normalmente dependem de alguém observando
todas as telas o tempo todo. Em ambientes universitários, isso dificulta perceber rapidamente uma
agressão em andamento.

O projeto investiga uma arquitetura em que:

1. a visão computacional produz somente observações objetivas;
2. cálculos determinísticos acumulam contexto ao longo do tempo;
3. o Jev interpreta esse conjunto de evidências;
4. a interface apresenta a decisão e seus sinais para revisão humana.

Essa separação é importante: o YOLO não declara que existe uma briga, e o Jev não recebe imagens
brutas. Cada camada tem uma responsabilidade verificável.

## Demonstração disponível

A interface web local permite:

- usar a câmera do notebook em tempo real;
- anexar um vídeo e reproduzi-lo em 1×, como se a ocorrência estivesse acontecendo ao vivo;
- visualizar esqueletos, bounding boxes e IDs persistentes do ByteTrack;
- acompanhar FPS, latência, quantidade de pessoas e cobertura dos sinais;
- inspecionar o `WorldState`, a entrada enviada ao Jev e a resposta recebida;
- receber alertas visuais e, opcionalmente, sonoros.

O painel **Estado da ocorrência** apresenta:

| Cor | Resultado visível | Eventos internos |
| --- | --- | --- |
| Verde | Nenhuma ocorrência detectada | `NORMAL` |
| Amarelo | Interação suspeita — monitorar | `SUSPICIOUS_INTERACTION`, `UNKNOWN_ANOMALY` |
| Vermelho | Possível violência detectada | `FIGHT`, `ASSAULT` |
| Cinza | Evidência insuficiente | Estado incompleto ou ambíguo |

## Arquitetura

```text
câmera ou vídeo no navegador
  -> frames JPEG por WebSocket local
  -> YOLO26n-pose + ByteTrack
  -> PerceptionFrame
  -> histórico e FeaturePipeline
  -> WorldState
  -> Jev / TypeSafe
  -> DecisionResult
  -> painel e alerta na interface
```

### Percepção

O YOLO26n-pose localiza pessoas e keypoints corporais. O ByteTrack mantém IDs entre frames. Objetos
do Ultralytics são convertidos imediatamente para o contrato próprio `PerceptionFrame`; eles não
vazam para as outras camadas.

### Evidências temporais

A `FeaturePipeline` mantém um histórico curto e calcula sinais normalizados pela escala corporal,
entre eles:

- velocidade corporal;
- pico recente de movimento e aceleração dos braços;
- intensidade de movimento;
- possível pessoa caída;
- distância entre pessoas e aproximação rápida;
- menor distância recente entre punho e cabeça/torso, nos dois sentidos;
- sobreposição das bounding boxes;
- contato provável;
- duração da proximidade;
- movimentos rápidos e próximos repetidos.

Picos e menores distâncias são preservados por uma janela recente. Assim, um gesto rápido não
desaparece antes da próxima avaliação.

### Decisão contextual com Jev

O backend envia ao Jev somente um JSON compacto derivado do `WorldState`. Cinco perguntas tipadas
são avaliadas sobre o mesmo estado:

- qualidade da evidência;
- tipo de evento;
- severidade;
- urgência;
- ação recomendada.

O resultado do SDK é convertido para o contrato próprio `DecisionResult`. A interface nunca recebe
objetos internos do SDK nem a chave da API.

#### Fluxo da API

1. O servidor lê `TYPESAFE_API_KEY` do `.env` durante a inicialização da sessão.
2. O `DecisionCoordinator` verifica se existem pelo menos duas pessoas e uma interação.
3. `build_jev_state` valida e serializa as evidências, com unidades e significado de valores nulos.
4. O cliente Python oficial faz uma chamada `system_one` contendo o estado e as cinco perguntas
   `Choice`. As perguntas são avaliadas de forma independente dentro da mesma requisição.
5. A resposta tipada é desacoplada do SDK e mapeada para `DecisionResult`.
6. Falha de rede/API, evidência insuficiente e evento normal permanecem estados diferentes.

Somente o servidor conversa com a TypeSafe. O navegador não conhece a chave e não chama a API
diretamente. Nenhuma imagem é incluída na requisição: saem apenas contagens, distâncias
normalizadas, velocidades, flags e outros sinais estruturados.

## Início rápido

### Requisitos

- Python 3.11 ou superior;
- Git;
- navegador moderno, preferencialmente Chrome ou Edge;
- acesso à internet durante a instalação e para chamadas reais ao Jev;
- conta/chave da TypeSafe para a decisão contextual;
- opcional: GPU NVIDIA com driver recente para aceleração CUDA.

### 1. Preparar o projeto

No diretório do repositório, execute:

```powershell
python scripts/setup.py
```

O instalador:

1. cria o ambiente virtual `.venv`;
2. instala interface, percepção, decisão e ferramentas de teste;
3. tenta ativar PyTorch com CUDA em máquinas NVIDIA compatíveis;
4. mantém fallback para CPU quando CUDA não está disponível;
5. baixa e verifica o `yolo26n-pose.pt`;
6. cria o `.env` local a partir de `.env.example`;
7. executa os testes offline.

Pesos, vídeos, credenciais e o `.env` real não devem ser versionados.

### 2. Configurar a API da TypeSafe

Abra o arquivo `.env` criado na raiz e preencha:

```env
TYPESAFE_API_KEY=sua_chave_aqui
JEV_INTERVAL_SECONDS=0.75
CAMPUS_SENTINEL_MODEL=models/yolo26n-pose.pt
```

Regras importantes:

- obtenha a chave seguindo a documentação/conta oficial da [TypeSafe](https://docs.typesafe.ai/);
- não inclua aspas em volta da chave;
- nunca envie ou versione o `.env`;
- reinicie o servidor depois de alterar o arquivo;
- sem `TYPESAFE_API_KEY`, pose, tracking e features continuam funcionando, mas a interface mostrará
  **Jev desativado** e não produzirá a decisão contextual.

`JEV_INTERVAL_SECONDS` controla o intervalo mínimo entre avaliações. O padrão de `0.75` segundo
favorece a demonstração de gestos rápidos. Valores menores aumentam a quantidade de chamadas, a
latência concorrente e o possível consumo da API.

O backend só solicita uma decisão quando há pelo menos duas pessoas e uma interação calculada. Uma
pessoa sozinha não gera chamada ao Jev.

### 3. Executar a interface

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m interface
```

Linux/macOS:

```bash
./.venv/bin/python -m interface
```

Abra no navegador:

```text
http://127.0.0.1:8000
```

Para usar outra porta:

```powershell
.\.venv\Scripts\python.exe -m interface --port 8001
```

Para encerrar, pressione `Ctrl+C` no terminal.

## Como testar

### Câmera em tempo real

1. Abra a interface e selecione **Equilibrado · 640 px** em uma máquina com GPU.
2. Clique em **Usar câmera**.
3. Autorize o acesso à câmera no navegador.
4. Verifique se caixas, esqueletos e IDs aparecem sobre as pessoas.
5. Coloque duas pessoas inteiras no enquadramento, com cabeça, ombros, cotovelos e punhos visíveis.
6. Faça somente movimentos encenados e seguros, sem contato real.
7. Acompanhe `Jev analisando…` e o painel **Estado da ocorrência**.

Para uma demonstração reprodutível, simule dois ou três movimentos rápidos de uma mão em direção à
cabeça ou ao torso, mantendo as pessoas visíveis por alguns segundos antes e depois. Iluminação,
oclusão e enquadramento afetam diretamente os keypoints.

### Vídeo gravado

1. Clique em **Anexar vídeo**.
2. Escolha um arquivo suportado pelo navegador.
3. Aguarde o aquecimento do modelo.
4. O vídeo começará em 1× somente quando YOLO e ByteTrack estiverem prontos.

Se a IA estiver ocupada, o navegador envia o frame mais recente disponível sem desacelerar o vídeo.
Os timestamps usados nas features continuam sendo os timestamps reais da reprodução.

### Como confirmar cada camada

| Sinal na interface | O que confirma |
| --- | --- |
| Esqueleto e bounding box | YOLO Pose funcionando |
| ID estável sobre a pessoa | ByteTrack funcionando |
| FPS e inferência atualizados | Fluxo navegador → backend funcionando |
| Aba `WorldState` atualizada | Features temporais funcionando |
| `Jev analisando…` | Requisição ao Jev iniciada |
| Abas `Entrada Jev` e `Saída Jev` | Integração TypeSafe concluída |
| Painel verde/amarelo/vermelho | `DecisionResult` aplicado à interface |

Na aba **Entrada Jev**, um caso com contato rápido pode conter sinais como:

```json
{
  "summary": {
    "people_count": 2,
    "interaction_count": 1
  },
  "interactions": [
    {
      "rapid_approach": false,
      "possible_contact": true,
      "repeated_aggressive_motion": true
    }
  ]
}
```

Esses campos são evidências, não um veredito determinístico. O Jev considera o conjunto completo.

## Verificar CUDA

```powershell
.\.venv\Scripts\python.exe -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

Exemplo esperado em uma máquina NVIDIA:

```text
2.x.x+cu...
True
NVIDIA ...
```

A interface também informa `CUDA · nome da GPU` ou `CPU` ao iniciar uma fonte. O sistema funciona em
CPU, mas com resolução e FPS menores.

## Testes

Todos os testes são offline: não usam webcam, pesos do modelo nem créditos do Jev.

Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests
```

Linux/macOS:

```bash
./.venv/bin/python -m pytest
./.venv/bin/python -m ruff check src tests
```

Os testes cobrem contratos, adaptação do Ultralytics, cálculos geométricos e temporais, cenários de
movimento normal e agressivo, serialização do `WorldState`, integração Jev com cliente injetado e
orquestração da interface.

## Ferramentas de diagnóstico

Executar apenas percepção + features em uma janela OpenCV:

```powershell
python scripts/run.py --source 0
python scripts/run.py --source caminho\video.mp4
```

Nesse modo, pressione `q` ou Escape para encerrar. Ele não substitui a interface web e não executa o
fluxo completo de decisão.

Simular a integração Jev sem rede ou créditos:

```powershell
.\.venv\Scripts\python.exe -m decision.examples.simulated
```

Executar uma avaliação real isolada com a chave do `.env`:

```powershell
.\.venv\Scripts\python.exe -m decision.examples.live
```

## Configuração

| Variável | Obrigatória | Padrão | Finalidade |
| --- | --- | --- | --- |
| `TYPESAFE_API_KEY` | Para decisões Jev | — | Credencial lida somente pelo servidor |
| `JEV_INTERVAL_SECONDS` | Não | `0.75` | Intervalo mínimo entre avaliações do Jev |
| `CAMPUS_SENTINEL_MODEL` | Não | `models/yolo26n-pose.pt` | Caminho dos pesos de pose |

## Privacidade e segurança

- câmera e vídeos são processados pelo servidor local iniciado pelo usuário;
- imagens não são enviadas ao Jev: somente métricas estruturadas do `WorldState` saem pela API;
- a chave da TypeSafe permanece no `.env` do backend;
- o MVP não possui banco de dados nem armazenamento de gravações;
- não há reconhecimento facial ou tentativa de identificar pessoas;
- logs evitam credenciais e imagens identificáveis;
- decisões são recomendações para revisão humana.

## Solução de problemas

### `No module named torch`

A instalação do PyTorch foi interrompida ou o ambiente incorreto está sendo usado. Feche outros
processos de instalação e execute novamente:

```powershell
python scripts/setup.py
```

### Câmera indisponível

- permita câmera para `127.0.0.1` no navegador;
- feche aplicativos que estejam usando a webcam;
- prefira Chrome ou Edge;
- recarregue a página depois de alterar a permissão.

### Modelo não encontrado

```powershell
.\.venv\Scripts\python.exe scripts\download_models.py
```

### `Jev desativado`

Confirme `TYPESAFE_API_KEY` no `.env`, sem aspas ou espaços adicionais, e reinicie o servidor.

### Esqueleto aparece, mas não há decisão

- confirme que duas pessoas estão detectadas simultaneamente;
- verifique se `interaction_count` é pelo menos `1` na aba `WorldState`;
- confira se a interface mostra `Jev analisando…`;
- inspecione **Entrada Jev** e **Saída Jev** para separar evidência insuficiente de falha da API.

### Execução lenta

- selecione **Velocidade · 320/416 px**;
- confirme se CUDA aparece na mensagem de inicialização;
- reduza a resolução da câmera ou vídeo;
- evite executar outros programas pesados na GPU.

## Limitações conhecidas

- pose 2D é sensível a oclusão, iluminação, perspectiva e baixa resolução;
- IDs podem trocar quando pessoas se cruzam ou deixam o quadro;
- distâncias são normalizadas em espaço de imagem, não medidas físicas;
- limiares temporais e geométricos ainda precisam de calibração com mais vídeos representativos;
- movimentos esportivos, brincadeiras ou abraços podem produzir falsos positivos;
- agressões muito ocultas ou fora do enquadramento podem produzir falsos negativos;
- disponibilidade, latência e limites da API TypeSafe afetam a decisão contextual;
- o sistema é um MVP de demonstração, não um produto certificado de segurança.

## Estrutura do repositório

```text
src/contracts/    contratos estáveis entre módulos
src/perception/   YOLO, ByteTrack e adaptação para PerceptionFrame
src/features/     histórico, geometria e evidências temporais
src/decision/     integração e mapeamento Jev
src/interface/    FastAPI, WebSocket e painel web
tests/            testes offline e fixtures sintéticas
scripts/          instalação, download do modelo e diagnóstico
models/           pesos locais ignorados pelo Git
data/             espaço local para vídeos/dados não versionados
```

## Tecnologias

### Linguagem, runtime e empacotamento

| Tecnologia | Versão/restrição | Uso no projeto |
| --- | --- | --- |
| Python | 3.11+ | Linguagem de contratos, percepção, features, decisão e backend |
| Setuptools | 68+ no build | Build e descoberta dos pacotes em `src/` |
| `venv` e pip | Inclusos no Python | Ambiente isolado e instalação reproduzível |
| `python-dotenv` | `>=1,<2` | Carregamento de credenciais e configuração do `.env` |

### Visão computacional e cálculo

| Tecnologia | Versão/restrição | Uso no projeto |
| --- | --- | --- |
| [Ultralytics](https://docs.ultralytics.com/) | `8.4.157` | API de inferência, pose e tracking |
| YOLO26n-pose | peso verificado por SHA-256 | Detecção de pessoas e 17 keypoints COCO |
| ByteTrack | integrado ao Ultralytics | Associação temporal e IDs persistentes |
| PyTorch | CUDA `2.14.0` no instalador NVIDIA | Execução do modelo em GPU ou CPU |
| Torchvision | CUDA `0.29.0` no instalador NVIDIA | Operações complementares do ecossistema PyTorch |
| CUDA | rodas `cu130` ou `cu126`, quando compatíveis | Aceleração em GPU NVIDIA; CPU continua disponível |
| OpenCV (`opencv-python`) | `5.0.0.93` | Decodificação JPEG e diagnóstico de câmera/vídeo |
| NumPy | `>=2,<3` | Matrizes de imagem e preparação de frames |
| LAP | `0.5.13` | Backend de atribuição utilizado no ecossistema de tracking |
| Supervision | `0.30.4` no extra `perception` | Utilitário opcional para experimentação em visão |

As features geométricas e temporais são código Python próprio. Elas usam `dataclasses`, históricos
limitados com `deque` e cálculos normalizados, sem um segundo modelo de classificação ou treinamento
adicional.

### Decisão com IA

| Tecnologia | Versão/restrição | Uso no projeto |
| --- | --- | --- |
| [TypeSafe / Jev](https://docs.typesafe.ai/) | `typesafe-sdk >=0.7,<0.8` | Julgamentos contextuais tipados sobre o `WorldState` |
| System One `Choice` | API do SDK | Evidência, evento, severidade, urgência e ação |
| `httpx2` | Dependência do SDK; `2.13.0` verificada | Transporte HTTP assíncrono da integração TypeSafe |
| Pydantic / pydantic-core | Dependências do SDK/FastAPI | Validação dos objetos tipados nas fronteiras externas |

Jev é o único componente responsável pelo veredito contextual. Não há LLM/VLM adicional, árvore de
decisão disfarçada ou envio de pixels à API.

### Backend e comunicação

| Tecnologia | Versão/restrição | Uso no projeto |
| --- | --- | --- |
| FastAPI | `>=0.116,<1` | Aplicação web local e endpoint WebSocket |
| Starlette | Dependência do FastAPI | Transporte ASGI e sessão WebSocket |
| Uvicorn Standard | `>=0.35,<1` | Servidor ASGI local |
| WebSocket | API web padrão | Frames binários e eventos JSON bidirecionais |
| JPEG | codec do navegador/OpenCV | Compressão dos frames enviados ao backend local |
| `asyncio` | biblioteca padrão | Concorrência entre vídeo, inferência e chamada ao Jev |

### Interface

| Tecnologia | Uso no projeto |
| --- | --- |
| HTML5 | Estrutura da interface de demonstração |
| CSS3 responsivo | Painéis, estados e alertas visuais |
| JavaScript sem framework | Captura, reprodução, WebSocket e atualização da interface |
| MediaDevices / `getUserMedia` | Acesso autorizado à câmera do navegador |
| Canvas 2D | Captura JPEG e desenho de esqueletos/bounding boxes |
| Web Audio API | Alerta sonoro opcional |
| Notifications API | Notificação local opcional com permissão do usuário |

A ausência de framework frontend é intencional: reduz instalação, build e pontos de falha durante a
demonstração. O servidor entrega um único arquivo estático e toda a inferência permanece em Python.

### Qualidade e colaboração

| Tecnologia | Versão/restrição | Uso no projeto |
| --- | --- | --- |
| pytest | `>=9,<10` | Testes unitários e de integração offline |
| Ruff | `>=0.16,<0.17` | Lint e consistência do código Python |
| Git e GitHub | Controle de versão e colaboração |
| Fixtures sintéticas | Código próprio | Testes sem webcam, pesos ou consumo da API |

O ambiente usado na validação final continha Python 3.14, NumPy 2.5.3, PyTorch 2.14.0+cu130,
Torchvision 0.29.0+cu130, TypeSafe SDK 0.7.0, FastAPI 0.141.1 e Uvicorn 0.53.0. As restrições de
instalação declaradas em `pyproject.toml` continuam sendo a referência para novas máquinas.

## Licença

O código do projeto está sob a [licença MIT](LICENSE). Modelos, datasets, vídeos e serviços externos
possuem termos próprios e devem ser usados de acordo com suas respectivas licenças e políticas.
