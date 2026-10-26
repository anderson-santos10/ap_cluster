# Análise da planilha — AP Cluster

Atualizado em 23 out 2026, depois da escolha da fonte da primeira versão.

A primeira versão usa somente `Criticos Ap Cluster.xlsx`. A leitura de `LRR BR 22.10.xlsx` permanece no final deste arquivo como investigação separada. Os números, parâmetros e o status SCM daquela leitura não entram nesta análise.

Nenhuma das duas planilhas foi alterada.

## Fonte aprovada

| Item | Valor |
|---|---|
| Caminho | `C:\Users\Anderson\Documents\PROJETOS\CZC\Criticos Ap Cluster.xlsx` |
| Situação | Na raiz do projeto. O caminho anterior, fora dessa pasta, não é mais a fonte |
| Tamanho | 679.994 bytes |
| Gravação em disco | 23 out 2026, 15:37 |
| Acesso nesta atualização | Arquivo localizado e não modificado |

A leitura das abas foi feita em 23 out 2026, somente leitura. Uma segunda leitura, no mesmo dia, conferiu a preparação da importação em `docs/PREPARACAO_IMPORTACAO.md`. O arquivo não foi reprocessado junto com `LRR BR 22.10.xlsx` e não foi modificado.

Abas: `Base`, `Grafico`, `SQVI`, `LRR`, `Est. Parq.`, `Din`.

## O que o arquivo contém

`Base` é o registro operacional: 96 itens, um por material e centro. `Est. Parq.` traz posições de estoque. `LRR`, dentro deste mesmo arquivo, traz parâmetros MRP. `SQVI` traz documentos de transferência e de compra. `Din` e `Grafico` apresentam a `Base` em tabelas dinâmicas e gráficos.

Há campos digitados, campos com fórmula e valores em cache. Fórmula e cache não são importação automática. A coluna precisa ser validada antes de qualquer gravação.

## Base — 96 linhas, 17 colunas

Tabela Excel `Tabela1` em `B1:Q97`. A coluna `Conc` fica fora da tabela. Há filtro de tela em Parque = `B825`; as 96 linhas continuam gravadas. Sem lista suspensa de status.

| Coluna | Cabeçalho | Origem | Preenchimento | O que a inspeção mostrou |
|---|---|---|---|---|
| A | Conc | Fórmula | 96/96 | `CONCAT` de material e parque |
| B | GP | Digitado | 96/96 | Código do material. 92 textos e 4 números |
| C | Descrição | Digitado | 96/96 | 43 textos. Um material tem duas descrições |
| D | Parque | Digitado | 96/96 | Código do centro SAP. 8 códigos |
| E | Planta | Digitado | 96/96 | Apelido operacional |
| F | LRR | Valor | 72/96 | 24 vazios. Quando preenchido, coincide com o ponto de reabastecimento da aba `LRR` deste arquivo |
| G | Estoque Parque | Fórmula | 96/96 | Primeira utilização livre; ausência vira 0 na fórmula |
| H | Estoque Ok/Nok | Fórmula | 96/96 | Estoque Parque menos LRR. LRR vazio entra como 0 na conta do Excel |
| I | Quant. PO | Fórmula | 96/96 | Soma pretendida de `Qtd.pedido`; as 96 fórmulas apontam para outra linha |
| J | Previsão no Parque | Digitado | 96/96 | 95 datas no dia 1; o item obsoleto está com o texto `*` |
| K | Mes/Ano | Fórmula | 96/96 | Mês e ano da previsão |
| L | Coluna4 | Fórmula | 96/96 | Nome do mês |
| M | Coluna3 | Fórmula | 96/96 | Ano |
| N | Status | Digitado | 96/96 | Texto livre |
| O | Quant. Entregue | Digitado | 62/96 | 26 negativos, nenhum zero |
| P | Data entrega | Digitado | 57/96 | 15 jun 2026 a 30 out 2026 |
| Q | Obs | Digitado | 16/96 | Texto livre |

Há 43 materiais quando o espaço final é desconsiderado. A linha 29 guarda `GP069610 ` com esse espaço, então o texto bruto tem 44 valores. A chave material + parque continua única nas 96 linhas. O mesmo material aparece em até 7 centros.

Status nas linhas atuais: Em rota 31, Pendente 27, Entregue 21, Entregue parcial 7, Criar RC 6, Sem necessidade parque 3, Obsoleto 1. O cache dos gráficos ainda guarda `Roteiro setembro`, que não está nas 96 linhas.

Centros e apelidos: `B856` VSMI, `B865` Terra Santa, `B864` Maral, `B867` VSMIII, `B857` VSMII, `B825` Bloco Norte Sul, `B832` União dos Ventos, `B838` VACI. Uma linha de `B838` (`GP296945`) está com apelido VSMII. No estoque, `B856`, `B857` e `B867` compartilham o mesmo nome SAP.

Previsão de ago/2026 a mar/2027. Em rota traz quantidade e data em geral positivas. Entregue parcial está todo com quantidade negativa. Entregue mistura sinais. A quantidade entregue não segue, de forma estável, a soma do pedido.

## Est. Parq. — 327 posições

Colunas: chave sem título, Centro, Nome 1, Depósito, Descrição do depósito, Material, Texto breve, UM básica, Lote, Utilização livre, Estoque em trânsito, Em contr.qualidade, Bloqueado.

A fórmula da `Base` lê só a primeira utilização livre. Trânsito, qualidade e bloqueado ficam de fora. Se o material e o centro não aparecem, a fórmula devolve 0.

74 itens da `Base` têm correspondência exata de material e centro. 22 não têm: 12 materiais ausentes do extrato, 9 existentes só em outro centro, e `GP069610 ` com espaço final no centro `B865`. Esse código não corresponde a `GP069610` sem o espaço, e o espaço não é removido. Em 30 itens da `Base`, a primeira utilização livre difere da soma das linhas. Há 43 grupos repetidos de material + centro + depósito + lote: 18 cópias idênticas e 25 com quantidades diferentes. Somar as cópias idênticas acrescentaria 35 unidades livres. Não há quantidade negativa.

O extrato inclui o centro `B833`, que não está na `Base`. A unidade é `PC` em 305 linhas e `L` em 22. O campo `Lote` usa valores como `N_IMP`, `N_NAC` e `B_IMP`, o mesmo vocabulário de tipo de avaliação no `SQVI`. O arquivo não diz se esse campo é lote ou avaliação.

Cinco descrições da `Base` diferem do texto breve do estoque. `GP124403` tem duas descrições dentro da própria `Base`.

## LRR deste arquivo — 1.849 linhas

Parâmetros MRP por material e centro, 883 materiais e 9 centros, incluindo `B833`. A chave material + centro é única nesta aba.

O ponto de reabastecimento coincide com a coluna LRR da `Base` nas 72 linhas em que a chave material + centro é exatamente a mesma e a coluna da `Base` está preenchida. As outras 24 linhas da `Base` têm LRR vazio e não têm par exato nesta aba. `GP069610 ` / `B865`, com o espaço final do material, é uma dessas 24. A aba `LRR` tem `GP069610` sem esse espaço no centro `B865`, com ponto 1. São códigos diferentes. O ponto dessa linha não preenche o LRR vazio da `Base`.

`Marc.p/elimin.` é `X` em todas as linhas. `Status atualização` é `D` em todas. Todas constam modificadas em 10 set 2026. Quinze colunas estão vazias. Estoque de segurança, tipo de MRP e grupo MRP não entram nas fórmulas da `Base`.

## SQVI — 546 linhas, 61 colunas

Cada documento aparece uma vez. 524 linhas são tipo `UB`, número começando em `430`, preço zero e sem fornecedor. 22 são tipo `NB`, número começando em `450`, com preço, moeda `ZBR` e fornecedor. Há três fornecedores nas linhas `NB`.

A coluna B, material + centro, é a chave usada pela soma da `Base`. 28 itens críticos têm ao menos uma linha, em 40 movimentações. 506 linhas não encontram essa chave na `Base`. `CFor` é `B8D1` em 480 transferências. Também aparecem como origem `B817`, `B855`, `B830` e `B837`, além de centros já usados na `Base`. As 22 linhas `NB` estão com essa coluna vazia.

Requisição vazia em 379 linhas. 494 datas de cada coluna de data estão como número serial do Excel. `Dt.criação`, depois da conversão, vai de 17 mai 2026 a 17 set 2026. `DataConf.` inclui 31 dez 9999. `Fornecimento` e quantidade de remessa estão com o texto `#N/A` em 390 linhas e com valor em 156. `OrgTransp.` e `SaídaMerc` contêm datas. Há cabeçalhos repetidos (`Item`, `E`, `UMP`) e cabeçalhos de uma letra sem legenda.

Quantidade confirmada: 383 zeradas, 143 iguais ao pedido e 20 menores. Não há quantidade pedida negativa nem zero.

As 96 fórmulas de Quant. PO apontam para outra linha. Nos 48 itens em que a soma da própria chave difere da soma da linha apontada, o cache segue a linha apontada. Nos outros 48, as duas somas e o cache são zero. O cache não é a quantidade documental. O detalhe está em `docs/PREPARACAO_IMPORTACAO.md`.

`Sugestão BR1` traz, entre outros, Corretiva, LRR, Service Bulletin, GGCC e Preventiva, além de `#N/A`. Nesse arquivo, LRR também é um texto de sugestão, além da coluna numérica da `Base`.

## Din e Grafico

`Din` tem cinco tabelas dinâmicas da `Base`, nomeadas `Tabela dinâmica4` a `Tabela dinâmica8`. `Grafico` não tem série de dados em células: a dimensão lida é `A1:A1`. Em 24 out 2026 a releitura confirmou quatro gráficos: `ITENS CRITICOS POR PARQUE` e `STATUS ENTREGA` são barras 3D; `TOTAL CRITICOS` e `PREVISÃO NO PARQUE` são barras. O gráfico por parque usa a coluna Planta. Há segmentadores de Planta e Status. Os números visíveis em `Din` dependem desses filtros. O cache foi atualizado em 23 out 2026, 08:38. O painel Django recalcula os quatro indicadores a partir dos itens gravados e não copia esse cache.

## O que pode ser lido e o que depende de validação

Podem ser lidos como valores de origem, ainda sujeitos à prévia: código do material, descrição, centro, apelido, LRR com o vazio preservado, previsão, status, quantidade entregue, data de entrega, observação, as quatro quantidades de cada posição de estoque, e as linhas `UB` e `NB` com número, item, quantidade pedida, unidade e preço.

Dependem de validação antes de calcular ou gravar como resultado: Estoque Parque, Estoque Ok/Nok, Quant. PO, mês e ano derivados, qualquer saldo pendente e qualquer recebimento. A `Base` tem uma quantidade e uma data de entrega por linha. O histórico de várias entregas não está modelado na planilha; a regra confirmada pede que o sistema possa registrá-las.

## Limites desta fonte

- Não há vínculo já validado entre pedido, item e recebimento.
- Não há critério, na planilha, para liberar um grupo de estoque duplicado.
- Não há descrição única quando os textos divergem.
- Não há lista fechada de status nem legenda dos códigos de uma letra.
- Centros que aparecem nos extratos e não aparecem na `Base`, como `B833`, `B8D1` e `B817`, não estão decididos para o cadastro inicial.
- Material ausente do estoque vira zero na fórmula do Excel. A regra confirmada trata essa ausência como saldo desconhecido.

## Investigação separada — fora da primeira versão

Em 23 out 2026 também foi lido `C:\Users\Anderson\Documents\PROJETOS\CZC\LRR BR 22.10.xlsx` (2.637.806 bytes, gravação em 23 out 2026, 15:59). Essa leitura não é fonte da primeira versão. Não deve ser cruzada nem importada com `Criticos Ap Cluster.xlsx` nesta fase.

O arquivo tem as abas `Sheet1` (9.904 linhas, 53 colunas, 37 centros) e `Planilha1` (esqueleto de totais por centro, sem números). A chave única é material + área MRP. `STATUS SCM` é a fórmula `IFS` que compara `ESTOQUE SAP PARQUE` ao estoque de segurança e devolve `ZERADO`, `OK` ou `CRÍTICO`. As colunas de estoque desse arquivo não têm fórmula. `B8D1` aparece com depósitos MRP `2N03` e `2N04` e com colunas de estoque nomeadas `2N01` e `2R01`.

Esses fatos ficam registrados para uma eventual fase futura. Eles não corrigem, não completam e não substituem a análise de `Criticos Ap Cluster.xlsx`.
