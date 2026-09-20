# Configuracoes

Armazene somente configuracoes versionaveis e exemplos seguros. Segredos e valores locais devem
ser fornecidos por ambiente e nunca enviados ao repositorio.

Quando o formato for definido, inclua validacao, valores padrao seguros e uma configuracao minima
para a demonstracao.

As variaveis reservadas atualmente estao em `.env.example`: `TYPESAFE_API_KEY`,
`CAMPUS_SENTINEL_MODEL` e `CAMPUS_SENTINEL_VIDEO_SOURCE`. Nenhum modulo deve depender de uma
variavel nova sem documenta-la primeiro.
