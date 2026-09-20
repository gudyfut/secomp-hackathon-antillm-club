# Guia de contribuicao

## Fluxo sugerido

1. Escolha uma tarefa pequena e confirme o responsavel e o ownership no `AGENTS.md`.
2. Crie uma branch curta: `feature/perception-*`, `feature/features-*` ou `feature/decision-*`.
3. Implemente uma mudanca coesa, com teste ou evidencia correspondente.
4. Atualize o diario e a documentacao afetada.
5. Revise os creditos de recursos externos e o registro de uso de IA.
6. Faca commits pequenos com mensagens que expliquem o resultado.

## Convencoes

- Nao registre segredos, dados pessoais, videos reais nao autorizados ou artefatos grandes.
- Explique como reproduzir resultados; nao use apenas capturas de tela como comprovacao.
- Marque conteudo incompleto com `[PREENCHER]` e duvidas com `[VALIDAR]`.
- Antes de integrar, rode os comandos de formatacao, testes e verificacao definidos no README.
- Nao misture mudancas de contratos compartilhados com refactors de modulos de outro dono.

## Pull request ou revisao entre pares

Mesmo durante o evento, uma revisao curta deve confirmar:

- aderencia ao escopo;
- separacao entre as camadas;
- tratamento de erros e cenarios sem deteccao;
- testes ou demonstracao manual reproduzivel;
- atualizacao de documentacao, creditos e limitacoes.
