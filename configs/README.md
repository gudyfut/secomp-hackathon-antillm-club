# Configurações

Este diretório é reservado a configurações versionáveis e exemplos seguros. A configuração local
usada pelo MVP fica no arquivo `.env` da raiz, criado a partir de `.env.example`. O `.env` real é
ignorado pelo Git e nunca deve conter dados para commit.

## Variáveis atuais

| Variável | Obrigatória | Padrão | Uso |
| --- | --- | --- | --- |
| `TYPESAFE_API_KEY` | Para decisões do Jev | — | Credencial usada somente pelo backend |
| `JEV_INTERVAL_SECONDS` | Não | `0.75` | Intervalo mínimo entre avaliações contextuais |
| `CAMPUS_SENTINEL_MODEL` | Não | `models/yolo26n-pose.pt` | Caminho local dos pesos de pose |

Sem a chave da TypeSafe, percepção, tracking e extração de features continuam funcionando, mas o
painel informa que o Jev está desativado. Reinicie o servidor depois de alterar o `.env`.

Não crie uma variável nova sem definir um padrão seguro, validar seu valor no módulo responsável e
documentá-la também no README principal e em `.env.example`.
