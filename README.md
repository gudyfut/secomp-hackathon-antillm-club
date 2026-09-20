# Campus Sentinel

**Detecção inteligente de ocorrências de segurança em ambientes universitários**

MVP desenvolvido para o Hackathon de Visão Computacional da **SECOMP 2026**. O sistema analisa uma
câmera ou um vídeo em ritmo real, acompanha pessoas por pose e tracking, agrega evidências de
movimento ao longo do tempo e usa o **Jev, da TypeSafe**, para classificar a cena como normal,
suspeita ou compatível com violência.

> Protótipo de apoio à decisão. Não substitui avaliação humana e não executa ações de segurança
> automaticamente.

## Navegação

- [Problema e solução](#problema-e-solução)
- [Demonstração](#demonstração)
- [Arquitetura](#arquitetura)
- [Instalação e execução](#instalação-e-execução)
- [Como testar](#como-testar)
- [Stack](#stack)
- [Privacidade e limitações](#privacidade-e-limitações)
- [Uso de IA e créditos](#uso-de-ia-e-créditos)
- [Melhorias futuras](#melhorias-futuras)

## Problema e solução

Em campi com corredores, salas e áreas de convivência, câmeras convencionais dependem de alguém
observando várias telas. Isso pode atrasar a percepção e a revisão de uma agressão em andamento.
Além disso, uma imagem isolada não distingue com segurança violência de abraços, esportes ou
brincadeiras: aproximação, contato, movimento dos braços e quedas precisam ser avaliados como uma
sequência temporal.

O Campus Sentinel atua como uma camada de triagem:

1. detecta pessoas, poses e trajetórias localmente;
2. calcula movimento, proximidade e contato provável em uma janela temporal;
3. envia ao Jev somente evidências estruturadas, nunca imagens;
4. recebe evento, severidade, urgência e ação recomendada;
5. mostra a decisão e os sinais para revisão humana.

O escopo do MVP é agressão e briga. Ele não faz reconhecimento facial, não identifica pessoas, não
detecta roubo ou vandalismo, não armazena gravações e não aciona a segurança automaticamente.

## Demonstração

A interface web local permite:

- usar a câmera do notebook;
- anexar um vídeo e reproduzi-lo em 1×, preservando o comportamento de tempo real;
- ver esqueletos, bounding boxes e IDs do ByteTrack;
- acompanhar FPS, latência, pessoas e evidências do `WorldState`;
- inspecionar a entrada e a saída do Jev;
- receber alertas visuais e sonoros opcionais.

| Painel | Eventos internos |
| --- | --- |
| Verde — normal | `NORMAL` |
| Amarelo — suspeito | `SUSPICIOUS_INTERACTION`, `UNKNOWN_ANOMALY` |
| Vermelho — possível violência | `FIGHT`, `ASSAULT` |
| Cinza — evidência insuficiente | Estado incompleto ou ambíguo |

## Arquitetura

```text
câmera/vídeo no navegador
  -> JPEG por WebSocket
  -> YOLO26n-pose + ByteTrack
  -> PerceptionFrame
  -> FeaturePipeline + histórico
  -> WorldState
  -> Jev / TypeSafe
  -> DecisionResult
  -> painel e alerta
```

- **Percepção:** YOLO26n-pose encontra pessoas e 17 keypoints COCO; ByteTrack mantém os IDs.
- **Features:** cálculos próprios medem velocidade, movimento dos braços, aproximação, distâncias
  punho-cabeça/torso, sobreposição, contato provável, repetição e possível queda.
- **Decisão:** cinco perguntas `Choice` avaliam evidência, evento, severidade, urgência e ação em
  uma única chamada `system_one`.
- **Interface:** FastAPI e WebSocket coordenam o fluxo; o navegador recebe apenas JSON dos
  contratos do projeto.

Picos rápidos e menores distâncias são mantidos em uma janela recente para que um gesto breve não
desapareça antes da próxima avaliação. Falha da API, evidência insuficiente e evento normal são
estados distintos.

## Instalação e execução

### Requisitos

- Python 3.11+ e Git;
- Chrome ou Edge;
- internet para instalação e chamadas ao Jev;
- pelo menos 5 GB livres; dependências CUDA podem exigir espaço adicional;
- GPU NVIDIA com driver recente é opcional; há fallback para CPU.

### 1. Clonar e preparar o ambiente

```bash
git clone https://github.com/gudyfut/secomp-hackathon-antillm-club.git
cd secomp-hackathon-antillm-club
```

Execute o instalador na raiz do repositório.

Windows PowerShell:

```powershell
python scripts/setup.py
```

Linux/macOS:

```bash
python3 scripts/setup.py
```

O script cria `.venv`, instala todas as dependências, tenta habilitar CUDA, baixa e verifica o peso
`yolo26n-pose.pt`, cria `.env` e executa os testes offline. A primeira instalação requer internet e
pode demorar por causa do PyTorch e do modelo.

### 2. Configurar TypeSafe/Jev

Edite o `.env` criado na raiz:

```env
TYPESAFE_API_KEY=sua_chave_aqui
JEV_INTERVAL_SECONDS=0.75
CAMPUS_SENTINEL_MODEL=models/yolo26n-pose.pt
```

> **Acesso à API para avaliação:** no momento da entrega, o site da
> [TypeSafe](https://typesafe.ai/) direciona novos usuários para uma **waitlist**, portanto uma API
> key pode não ficar disponível imediatamente e a obtenção de uma nova chave pode levar tempo.
> Para testar o fluxo completo, entre em contato com
> **Murilo, integrante da equipe**. Ele se dispõe a orientar o acesso e, quando apropriado,
> disponibilizar uma chave temporária exclusivamente para a avaliação.

Por segurança, solicite e receba a chave somente por canal privado. Nunca publique credenciais em
issues, commits, capturas de tela ou chats públicos. A chave deve ficar apenas no `.env`, ser usada
somente no teste autorizado e ser removida/revogada ao final. Sem a chave, pose, tracking e features
continuam funcionando; somente a decisão contextual fica desativada.

### 3. Iniciar

Windows:

```powershell
.\.venv\Scripts\python.exe -m interface
```

Linux/macOS:

```bash
./.venv/bin/python -m interface
```

Abra `http://127.0.0.1:8000`. Para outra porta, acrescente `--port 8001`. Encerre com `Ctrl+C`.

## Como testar

### Câmera

1. Abra a interface e clique em **Usar câmera**.
2. Autorize a webcam e confirme caixas, esqueletos e IDs.
3. Mantenha duas pessoas inteiras no quadro, com braços e cabeça visíveis.
4. Faça apenas movimentos encenados e seguros, sem contato real.
5. Observe `Jev analisando…` e o painel de ocorrência.

Para uma demonstração reprodutível, mantenha as pessoas visíveis por alguns segundos e simule dois
ou três movimentos rápidos da mão em direção à cabeça ou ao torso. Iluminação, oclusão e distância
da câmera afetam os keypoints.

### Vídeo

Clique em **Anexar vídeo** e selecione um arquivo suportado pelo navegador. A reprodução em 1× só
começa após o aquecimento do modelo. Se a inferência estiver ocupada, o navegador envia o frame mais
recente sem desacelerar o vídeo; as features continuam usando o timestamp real da reprodução.

### Diagnóstico por camada

| Evidência na interface | Componente confirmado |
| --- | --- |
| Esqueleto e caixa | YOLO Pose |
| ID persistente | ByteTrack |
| FPS/latência | navegador → backend |
| Aba `WorldState` | features temporais |
| `Jev analisando…` | chamada TypeSafe iniciada |
| Entrada/saída Jev | integração concluída |
| Painel colorido | `DecisionResult` aplicado |

### Testes e ferramentas

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests

# Percepção + features em janela OpenCV, sem Jev
python scripts/run.py --source 0
python scripts/run.py --source caminho\video.mp4

# Integração Jev simulada, sem rede
.\.venv\Scripts\python.exe -m decision.examples.simulated
```

Os testes automatizados são offline: não abrem webcam, não carregam pesos e não consomem a API.

### Verificar CUDA

```powershell
.\.venv\Scripts\python.exe -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

A interface também informa `CUDA · nome da GPU` ou `CPU` ao iniciar.

### Problemas comuns

| Sintoma | Verificação rápida |
| --- | --- |
| `Jev desativado` | Preencha `TYPESAFE_API_KEY` e reinicie o servidor |
| Esqueleto sem decisão | Confirme duas pessoas e `interaction_count >= 1` |
| Modelo ausente | Execute `.\.venv\Scripts\python.exe scripts\download_models.py` |
| Câmera indisponível | Libere a permissão e feche outros aplicativos que usam a webcam |
| Execução lenta | Use o perfil Velocidade e confirme se CUDA foi reconhecido |

## Estrutura

```text
src/contracts/    contratos estáveis
src/perception/   YOLO, ByteTrack e adaptação
src/features/     histórico e evidências temporais
src/decision/     integração e mapeamento Jev
src/interface/    FastAPI, WebSocket e painel web
tests/            testes e fixtures sintéticas
scripts/          instalação, modelo e diagnóstico
models/           pesos locais ignorados pelo Git
data/             vídeos/dados locais não versionados
```

## Stack

| Área | Tecnologias | Uso |
| --- | --- | --- |
| Linguagem | Python 3.11+, Setuptools, venv, pip | Toda a aplicação e empacotamento |
| Visão | Ultralytics 8.4.157, YOLO26n-pose, ByteTrack | Pessoas, pose e tracking |
| Cálculo | PyTorch, Torchvision, CUDA/CPU, NumPy, LAP | Inferência e matrizes |
| Vídeo | OpenCV 5.0.0.93 | Decodificação e diagnóstico |
| Decisão | TypeSafe SDK `>=0.7,<0.8`, Jev, System One `Choice` | Julgamentos tipados |
| Backend | FastAPI, Starlette, Uvicorn, WebSocket, asyncio | Servidor e comunicação |
| Interface | HTML5, CSS3, JavaScript, Canvas, MediaDevices, Web Audio | Painel sem build frontend |
| Qualidade | pytest, Ruff, fixtures sintéticas | Testes e análise estática |
| Colaboração | Git, GitHub e OpenAI Codex | Versionamento e apoio ao desenvolvimento |

Versões e restrições reproduzíveis estão em [`pyproject.toml`](pyproject.toml). Origens, licenças e
finalidades estão detalhadas em [recursos externos](docs/entrega/recursos-externos.md).

## Privacidade e limitações

### Privacidade

- imagens são processadas pelo servidor local e não são enviadas ao Jev;
- a chave TypeSafe permanece no `.env` do backend;
- não há banco, gravação, reconhecimento facial ou identificação de pessoas;
- resultados são recomendações para revisão humana.

### Limitações conhecidas

- pose 2D é sensível a oclusão, iluminação, perspectiva e baixa resolução;
- IDs podem trocar quando pessoas se cruzam ou deixam o quadro;
- distâncias são normalizadas na imagem, não medidas físicas;
- brincadeiras, abraços e esportes podem gerar falsos positivos;
- agressões ocultas ou fora do quadro podem gerar falsos negativos;
- limiares ainda precisam de calibração com vídeos autorizados e representativos;
- disponibilidade e latência da TypeSafe afetam a decisão;
- este é um MVP, não um produto certificado de segurança.

## Uso de IA e créditos

O projeto usa IA em papéis diferentes:

- **YOLO26n-pose:** modelo pré-treinado local para percepção;
- **Jev:** componente da solução que julga o `WorldState` estruturado;
- **[OpenAI Codex](https://developers.openai.com/codex/):** apoio ao desenvolvimento, incluindo
  leitura das orientações, arquitetura, código, testes, diagnóstico, documentação e Git.

Codex não faz parte do runtime nem decide sobre as cenas. Requisitos, aceitação e responsabilidade
permanecem com a equipe. Suas saídas foram verificadas por revisão de código/diffs, testes offline,
Ruff e execuções manuais da interface. O registro completo está em
[uso de IA](docs/entrega/uso-de-ia.md).

O MVP não utilizou dataset externo nem treinou um modelo. Os vídeos de teste são entradas locais,
não são versionados e devem ter origem e autorização adequadas.

## Aderência ao Hackathon

O README cobre problema, proposta, visão computacional, execução, arquitetura, stack, créditos,
limitações e futuro — os itens técnicos solicitados nas orientações. A demonstração ao vivo, o
limite de cinco minutos, os nomes/contribuições e a participação de todos dependem da equipe no
pitch e não podem ser comprovados somente pelo repositório.

## Melhorias futuras

- calibrar limiares com vídeos autorizados e medir precisão, revocação, latência e falsos alarmes;
- melhorar robustez a oclusão, perspectiva, iluminação e troca de IDs;
- acionar o Jev também por mudança material de estado;
- criar perfis de calibração por câmera e melhorar acessibilidade do painel;
- definir auditoria, retenção e controle de acesso antes de qualquer armazenamento;
- integrar alertas institucionais somente com confirmação humana e políticas de segurança.

Esses itens são um roteiro, não funcionalidades entregues. A prioridade segue sendo validar o fluxo
de agressões antes de ampliar o escopo.

## Licença

O código está sob a [licença MIT](LICENSE). Modelos, serviços e demais recursos externos possuem
termos próprios.
