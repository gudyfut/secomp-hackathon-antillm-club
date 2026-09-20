# Registro de uso de Inteligência Artificial

As orientações do Hackathon permitem ferramentas de IA, mas exigem transparência, domínio técnico
e responsabilidade da equipe. Neste projeto, IA foi usada tanto na solução quanto como apoio ao
desenvolvimento.

## IA presente na solução

| Ferramenta/modelo | Papel | Entrada | Saída | Limites e revisão |
| --- | --- | --- | --- | --- |
| YOLO26n-pose via Ultralytics | Percepção local pré-treinada | Frames da câmera ou vídeo | Pessoas, caixas e 17 keypoints COCO | Sensível a oclusão, iluminação, perspectiva e resolução |
| Jev / TypeSafe | Decisão contextual tipada | `WorldState` com evidências numéricas e booleanas | Evento, severidade, urgência e ação recomendada | Não recebe imagens; resultado é consultivo e requer revisão humana |

Não houve treinamento de modelo novo, reconhecimento facial ou uso de dataset externo pelo MVP.
Vídeos usados na demonstração são entradas locais, não são incorporados ao repositório e devem ter
origem e autorização adequadas.

## IA usada no desenvolvimento

| Data | Ferramenta | Onde foi usada | Como e por que foi usada | Verificação humana/técnica |
| --- | --- | --- | --- | --- |
| 2026-09-20 | OpenAI Codex | Repositório e documentação inicial | Leitura das orientações, estrutura do repositório e documentos de entrega | Revisão dos arquivos e histórico Git |
| 2026-09-20 | OpenAI Codex | Arquitetura e implementação | Discussão de contratos, módulos, features temporais, integração Jev e interface para acelerar o MVP | Revisão de código, testes sintéticos e execução manual |
| 2026-09-20 | OpenAI Codex | Qualidade e diagnóstico | Criação/ajuste de testes, investigação de falhas e conferência de configuração | `pytest`, Ruff e inspeção dos diffs |
| 2026-09-20 | OpenAI Codex | Documentação e Git | Atualização dos READMEs, comparação com as orientações e operações Git solicitadas | Links verificados, conteúdo comparado ao código e aprovação da equipe |

O Codex atuou como agente de programação e não integra o runtime do Campus Sentinel. Ele não analisa
as cenas e não produz o resultado normal/suspeito/violência. Requisitos, decisões de produto,
aceitação das mudanças e responsabilidade pela entrega permaneceram com a equipe.

## Explicação curta para o pitch

- **Onde a IA aparece na solução:** YOLO26n-pose extrai pose localmente; Jev interpreta o estado
  temporal estruturado e devolve decisões tipadas.
- **Onde a IA apoiou o desenvolvimento:** Codex ajudou a estruturar, implementar, testar, revisar e
  documentar o projeto.
- **Por que foi usada:** para acelerar o trabalho dentro do tempo do hackathon e manter consistência
  entre arquitetura, código, testes e documentação.
- **Como as saídas foram verificadas:** revisão dos arquivos e diffs, 46 testes offline, Ruff e
  testes manuais da câmera/interface feitos pela equipe.
- **Riscos identificados:** sugestões incorretas, documentação divergente do código, dependência de
  validação humana e limitações dos modelos externos.

Os detalhes das dependências, modelos, origens e licenças estão em
[recursos externos](recursos-externos.md).
