# Visao do produto

## Identificacao

- **Nome provisorio:** Campus Sentinel
- **Titulo:** Deteccao Inteligente de Ocorrencias de Seguranca em Ambientes Universitarios
- **Evento:** Hackathon de Visao Computacional - SECOMP 2026
- **Equipe:** [PREENCHER: nomes dos tres integrantes]

## Problema

Equipes responsaveis pela seguranca do campus podem ter dificuldade para acompanhar fluxos de
video e distinguir eventos relevantes de deteccoes isoladas. O problema deve ser delimitado com
um local, publico-alvo e tipos de ocorrencia que possam ser demonstrados durante o evento.

### Delimitacao a confirmar

- Local/cenario universitario: [VALIDAR]
- Usuario principal: [VALIDAR]
- Tipo de ocorrencia coberto no prototipo: agressao/briga.
- Tipos explicitamente fora do escopo: [VALIDAR]
- Acao esperada do usuario apos uma decisao: [VALIDAR]

## Hipotese de solucao

Uma cadeia de processamento transforma sinais extraidos do video em eventos estruturados. Uma
camada de decisao interpreta esses eventos e produz uma ocorrencia compreensivel, com contexto
suficiente para apresentacao ou alerta.

Esta hipotese nao implica que toda deteccao seja uma ocorrencia real. O prototipo deve comunicar
incerteza e manter revisao humana quando apropriado.

## Beneficio esperado

[PREENCHER: uma frase mensuravel sobre o valor para o usuario]

## Cenario principal

1. A aplicacao recebe uma fonte de video permitida.
2. A camada de percepcao extrai observacoes relevantes.
3. A camada de features agrega historico e produz um `WorldState`.
4. O Jev avalia o contexto disponivel e produz um `DecisionResult`.
5. A interface apresenta o resultado e suas informacoes de apoio.
6. O usuario compreende o que ocorreu e qual acao pode tomar.

## Requisitos do prototipo

- [ ] Demonstrar ao menos um cenario completo, do video ate a apresentacao da decisao.
- [ ] Tornar visivel a contribuicao da Visao Computacional.
- [ ] Explicar o caminho captura -> processamento -> saida.
- [ ] Funcionar em uma demonstracao ao vivo ou possuir contingencia honesta e previamente testada.
- [ ] Expor limitacoes e condicoes de falha relevantes.

## Fora do escopo inicial

- Operacao autonoma sem supervisao humana.
- Implantacao em producao no campus.
- Identificacao de pessoas, salvo decisao explicita, justificada e autorizada pela equipe/evento.
- Garantia de prevencao ou confirmacao de crimes.
- Vandalismo, assalto e outras categorias antes de validar o MVP de agressao/briga.

## Criterios de sucesso

| Criterio | Meta | Como medir | Evidencia |
|---|---|---|---|
| Fluxo ponta a ponta | [PREENCHER] | [PREENCHER] | [PREENCHER] |
| Qualidade da percepcao | [PREENCHER] | [PREENCHER] | [PREENCHER] |
| Qualidade da decisao | [PREENCHER] | [PREENCHER] | [PREENCHER] |
| Clareza da interface | [PREENCHER] | [PREENCHER] | [PREENCHER] |
| Tempo/responsividade | [PREENCHER] | [PREENCHER] | [PREENCHER] |
