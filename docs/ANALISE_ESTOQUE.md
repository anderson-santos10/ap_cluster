# Análise da fonte de estoque

Análise da leitura de 23 de outubro de 2026. As decisões de escopo foram aprovadas naquele planejamento. A integração inicial autorizada foi executada em 24 de outubro de 2026; o estado de código, banco e telas após a execução está registrado no adendo ao final deste documento e em `docs/INTEGRACAO_ABAS_COMPLEMENTARES.md`.

A planilha lida foi `C:\Users\Anderson\Documents\PROJETOS\CZC\Criticos Ap Cluster.xlsx`, em modo somente leitura, sem gravação. O SHA-256 permaneceu `777ede653828560abec0640dcd409a6bed051ebe39614dd29e0bce7ddcff5d06` (679.994 bytes). `LRR BR 22.10.xlsx` não foi aberto.

O cruzamento usa os 96 itens já gravados no PostgreSQL local. Antes e depois da consulta, as contagens eram 96 itens, 62 entregas e 0 históricos.

Há três tipos de afirmação neste texto. **Fato** é o que esta leitura mediu. **Hipótese** é uma leitura possível, sem confirmação. **Pendente** é decisão que continua com a equipe.

## 1. Resumo executivo

A aba `Est. Parq.` tem 327 posições, não 96 itens. A chave do item continua sendo material + centro. Depósito e lote distinguem a posição. Várias linhas do mesmo material e centro não são, por si, duplicidade.

Dos 96 itens, 74 encontram posição com o código exato do material e o mesmo centro. 39 desses têm uma linha. 35 têm mais de uma. 22 não encontram par exato: 12 materiais não estão no extrato, 9 estão só em outro centro, e 1 (`GP069610 ` com espaço final, centro `B865`) só coincidiria se o espaço fosse removido. Esse espaço não foi removido e o item não foi ligado ao estoque.

Há 43 grupos repetidos na chave material + centro + depósito + lote: 18 pares iguais e 25 pares com quantidade diferente. Nenhum texto diverge dentro do par. A regra já confirmada bloqueia o cálculo desses grupos. Esta leitura não soma nem apaga.

Utilização livre, trânsito, qualidade e bloqueado são colunas separadas. Bloqueado está zero nas 327 linhas. Qualidade é positiva em duas células. Não há quantidade negativa nem célula de quantidade vazia. Ausência de posição continua diferente de zero.

## 2. Estrutura e qualidade da aba

A grade tem 328 linhas e 13 colunas. A linha 1 é o cabeçalho. As linhas 2 a 328 têm dados. Não há linha vazia no meio nem valor além da coluna 13.

| Coluna | Cabeçalho na planilha | Leitura desta etapa |
| --- | --- | --- |
| A | sem título | Fórmula `CONCAT` do material com o centro. O resultado coincide com material + centro nas 327 linhas |
| B | Centro | Código SAP do centro |
| C | Nome 1 | Nome SAP do centro. Não é o apelido da planta usado na `Base` |
| D | Depósito | Código do depósito. Vazio em 38 linhas e, pela regra já registrada, faz parte da chave |
| E | Descrição do depósito | Nome do depósito. Não diverge para o mesmo centro e depósito |
| F | Material | Código do material, sem normalizar |
| G | Texto breve material | Descrição da posição. Não escolhe o texto da `Base` |
| H | UM básica | `PC` ou `L` |
| I | Lote | Preenchido em 246 linhas e vazio em 81. Os valores são `N_IMP`, `N_NAC`, `B_IMP`, `B_NAC`, `D_IMP`, `D_NAC` e vazio |
| J | Utilização livre | Quantidade própria. É a única coluna que a fórmula da `Base` consulta |
| K | Estoque em trânsito | Quantidade própria |
| L | Em contr.qualidade | Quantidade própria |
| M | Bloqueado | Quantidade própria |

**Fato.** A coluna A tem fórmula nas 327 linhas de dados (`=_xlfn.CONCAT(F2,B2)` e equivalentes). As outras doze colunas não têm fórmula. O resultado gravado da coluna A é igual a material + centro, sem separador, nas 327 linhas.

**Fato.** A fórmula da `Base`, nas 96 linhas, é `=IFERROR(VLOOKUP(A2,'Est. Parq.'!A:J,10,0),0)`. Ela devolve a primeira utilização livre da chave concatenada, ou zero se a busca falha. Esse zero não é saldo. Em 30 itens o cache é a primeira utilização livre e difere da soma das linhas. Em 22 itens o cache é zero porque não há linha com a chave exata. O cache não foi usado como estoque.

**Fato.** Não há material, centro, depósito, lote, unidade, descrição ou nome com espaço no início ou no fim dentro de `Est. Parq.`. Não há material com diferença só de maiúsculas. Não há par material + centro que passe a colidir depois de remover espaços ou ignorar maiúsculas. Oito textos breves têm espaço duplo no meio; o exemplo `LEVEL SWITCH HINE LM1FA500NASP  ALARM` é o mesmo texto já gravado nos dois itens `GP069610`. O espaço interno não cria outro código.

**Fato.** Sete células de material estão como número no Excel, todas `109534`, nas linhas 4 a 10. O número não tem zero à esquerda. No banco, `109534` está em texto e coincide com essas linhas nos centros em que o item existe.

## 3. Estatísticas e exemplos

**Fato.** 327 linhas, 39 materiais distintos, 9 centros e 10 valores de depósito.

Centros e nomes SAP, com a quantidade de linhas:

| Centro | Nome 1 | Linhas |
| --- | --- | --- |
| B825 | SGRE Mto Bloco Norte Sul | 45 |
| B832 | SGRE Mto Uniao dos Ventos | 44 |
| B833 | SGRE Mto Uniao dos Ventos Exp | 22 |
| B838 | SGRE Mto Vila Acre | 31 |
| B856 | SGRE Mto Ventos Serra do Mel I | 40 |
| B857 | SGRE Mto Ventos Serra do Mel I | 32 |
| B864 | SGRE MTO Maral | 32 |
| B865 | SGRE MTO Terra Santa | 42 |
| B867 | SGRE Mto Ventos Serra do Mel I | 39 |

`B856`, `B857` e `B867` repetem o mesmo nome SAP. O código do centro continua sendo o que separa as posições. `B833` não está entre os 96 itens.

Depósitos: `SBN1` 39, vazio 38, `SUV1` 37, `SVM3` 35, `STS1` 33, `SAV1` 32, `SVS1` 31, `SVS2` 31, `SVA1` 29, `SUV2` 22.

Unidades: `PC` em 305 linhas e `L` em 22. Nenhum par material + centro mistura as duas unidades.

Quantidades, sem somar categorias:

| Coluna | Positivo | Zero | Vazio | Negativo |
| --- | --- | --- | --- | --- |
| Utilização livre | 253 | 74 | 0 | 0 |
| Estoque em trânsito | 36 | 291 | 0 | 0 |
| Em contr.qualidade | 2 | 325 | 0 | 0 |
| Bloqueado | 0 | 327 | 0 | 0 |

**Fato.** 38 linhas têm as quatro quantidades em zero. 36 têm utilização livre zero e outra categoria positiva. Só 2 têm utilização livre positiva e outra categoria também positiva. Uma casa decimal aparece em 19 utilizações livres, todas de `GP131157` em `PC`, e em um trânsito: linha 311, `GP486978-004`, `B825`, depósito vazio, unidade `L`, trânsito `1457.4`. Esse material não está nos 96 itens.

Qualidade positiva:

- linha 2, `GP127960`, `B838`, `SVA1`, `N_IMP`, qualidade 2;
- linha 3, `GP127960`, `B832`, `SUV1`, `N_IMP`, qualidade 1.

A linha 2 forma par com a linha 134, em que a qualidade é 0 e o restante é igual. A linha 3 não está num par repetido.

**Fato.** A chave material + centro + depósito + lote forma 284 grupos: 241 com uma linha, 18 com duas linhas iguais e 25 com duas linhas diferentes. Nenhum grupo tem mais de duas linhas. Nos 25 conflitos, o texto não muda. A divergência é utilização livre em 21, trânsito em 3 e qualidade em 1.

O maior conflito de utilização livre é `GP131157` / `B825` / `SBN1` / lote vazio: linha 25 com `1946.9` e linha 143 com `1117.9`, unidade `PC`.

Pares idênticos, se fossem somados, acrescentariam 35 na utilização livre e 26 no trânsito. Essa soma não foi feita. Dois pares idênticos são zero nas quatro colunas: linhas 35 e 153 (`GP131157`, `B865`, `STS1`, lote vazio) e linhas 42 e 186 (`GP249817`, `B825`, `SBN1`, `N_IMP`).

**Fato.** Há 220 pares material + centro no extrato. 72 têm mais de uma linha. Desses, 30 têm mais de um depósito e 31 têm o mesmo depósito com lotes diferentes. Um par pode estar nos dois casos. 38 dos 39 materiais aparecem em mais de um centro. Material igual em outro centro não liga o item.

## 4. Cruzamento com os 96 itens

A comparação exigiu o mesmo material e o mesmo centro, caractere por caractere.

| Situação | Itens |
| --- | --- |
| Correspondência exata | 74 |
| Uma linha de estoque | 39 |
| Várias linhas de estoque | 35 |
| Sem correspondência exata | 22 |
| Só coincidiria depois de remover espaço | 1 |
| Material ausente do extrato | 12 |
| Material só em outro centro | 9 |

74 + 22 = 96. O caso do espaço está dentro dos 22 e não foi contado nos 74.

**Fato.** Dos 74, 55 só têm grupos de uma linha. 19 incluem ao menos um grupo repetido, então um total do item misturaria posição válida com par ainda bloqueado. 64 dos 74 têm alguma utilização livre positiva. 10 têm posição e utilização livre zero em todas as linhas encontradas. Esse zero é dado presente. Não é o desconhecido dos 22 sem par exato.

Exemplos de livre zero com posição exata:

- `109534` / `B865`, linha 9: livre 0 e trânsito 2;
- `GP023882` / `B825`, linha 80: as quatro quantidades são 0;
- `GP131157` / `B865`, linhas 34, 35, 152 e 153: livre 0 em todas, mas o trânsito das linhas 34 e 152 é 400 e 150. O grupo continua bloqueado.

**Fato.** `GP069610` sem espaço, centro `B864`, encontra a linha 87: depósito `SAV1`, lote `N_IMP`, livre 2. A descrição do banco e a do estoque são iguais, inclusive o espaço duplo antes de `ALARM`.

**Fato.** `GP069610 ` com espaço final, centro `B865`, não encontra linha. O extrato tem o código sem espaço nesse centro, em duas posições que não são o mesmo grupo: linha 88, depósito vazio, lote vazio, livre 0 e trânsito 1; linha 89, `STS1`, `N_IMP`, quatro zeros. Há também linhas desse código em `B825`, `B832`, `B838`, `B857` e `B867`. Nenhuma foi ligada ao item de `B865`.

Materiais ausentes do extrato, nos centros do item: `565784` em `B864` e `B865`; `AMB0155` em `B864` e `B865`; `GP004263` em `B825`, `B832`, `B856`, `B857` e `B867`; `GP004892` em `B825`; `GP004897` em `B864` e `B865`.

Material presente só em outro centro: `GP004975` / `B825`; `GP091145` / `B832`; `GP224705` / `B864`; `GP254146` / `B864`; `GP351497` / `B838`; `GP410281` em `B857` e `B867`; `GP459925` em `B857` e `B867`. O estoque desses códigos fica nos outros centros e não atende o item.

**Fato.** Cinco descrições do item diferem do texto breve da posição exata. Nenhuma foi escolhida:

- `GP124403` / `B856`: no item, `AMB_EBM_K2E225RA9209`; no estoque, `CENTRIFUGAL FAN 230V\1260m3\h UL-LOW NOI`;
- `GP335709` / `B825`: no item, `B/Y ANTISLIP ADHESIVE TAPE 50MM X 300MM`; no estoque, `FITA ANTIDERRAPANTE PR/AM 50X300MM`;
- `GP411469` em `B856`, `B857` e `B867`: no item, `3.53KW` e `35HZ`; no estoque, `3.54KW` e `50/60HZ`.

No próprio extrato, nenhum par material + centro tem dois textos breves diferentes. A divergência é entre a `Base` e o estoque, ou entre centros do mesmo material na `Base`, como já ocorre com `GP124403`.

**Fato.** 146 pares material + centro do extrato, em 200 linhas, não pertencem aos 96 itens. `B833` responde por 18 desses pares. Essas linhas não viram item crítico por esta análise.

## 5. Chave, duplicidade e normalização

**Fato.** Material + centro identifica o item, não a posição. Depósito e lote são necessários para a posição: há pares com mais de um depósito e pares com o mesmo depósito e lotes diferentes.

**Fato.** A duplicidade que bloqueia cálculo é a repetição da chave completa. São 43 grupos, todos com exatamente duas linhas. Cópia idêntica e conflito ficam bloqueados do mesmo modo, porque a regra confirmada não autoriza somar nem descartar.

**Fato.** A única correspondência que depende de normalização é `GP069610 ` / `B865`. Remover o espaço ligaria duas posições de `GP069610` / `B865` e mudaria o saldo. Isso não foi feito. Não houve diferença só de maiúsculas.

**Fato.** `109534` numérico no Excel e `109534` texto no banco coincidem onde o centro também coincide. Não apareceu zero à esquerda para preservar.

**Hipótese, não revalidada nesta leitura.** O campo Lote pode ser tipo de avaliação, porque os códigos se repetem no vocabulário já anotado do `SQVI`. Esta etapa não reabriu o `SQVI` para conferir essa hipótese. Na tela futura o valor deve aparecer como está na coluna `Lote`, sem ser renomeado.

## 6. Decisões aprovadas para a primeira integração

Estas decisões foram recebidas na retomada do planejamento. Orientam a etapa futura. Não autorizam, por si, escrever código nem carregar a aba.

- O escopo é o dos 96 itens críticos já importados da `Base`.
- A correspondência é só material + centro exatos, caractere por caractere.
- Espaço não é removido e o código do material não é normalizado.
- Lote, depósito e posições repetidas permanecem separados. Depósito ou lote vazio continua na chave.
- Os 43 grupos repetidos desta análise são sinalizados. As quantidades deles não são somadas automaticamente.
- Quantidade e unidade originais permanecem, inclusive casa decimal em `PC`. Esse caso é sinalizado para revisão.
- A descrição do item crítico permanece. A descrição diferente do estoque é sinalizada.
- Utilização livre, trânsito, controle de qualidade e bloqueado aparecem em separado.
- Sem correspondência exata, o estoque fica desconhecido, não zero.
- Posição que não corresponda a um dos 96 itens fica fora desta versão.
- Esta versão não calcula saldo projetado e não cria importação automática recorrente.

Continua valendo o que já estava confirmado: o disponível usa só utilização livre; grupo repetido bloqueia o cálculo daquele grupo; o nome SAP não substitui o código do centro.

## 7. O que continua pendente

Nenhuma pendência abaixo impede listar as posições no detalhe, sinalizar os 43 grupos, sinalizar `PC` decimal e manter o item sem correspondência como desconhecido.

Impedem só o número ou a ação que ainda não foi aprovada:

1. O critério para liberar cada um dos 18 pares idênticos e dos 25 conflitos. Sem ele, os 19 itens com grupo repetido não ganham total. A listagem desses pares já está aprovada.
2. Se a primeira tela mostra a soma da utilização livre dos 55 itens cujos grupos são todos únicos. A regra antiga permite somar posição válida. Esta retomada não aprovou exibir esse total. A proposta mínima não o exibe.
3. A palavra usada quando depósito ou lote está vazio. O vazio já faz parte da chave. A palavra “vazio” ainda não foi aprovada como regra. A tela implementada mostra “em branco”, como fato do campo sem texto, e não como código de negócio.
4. Qual descrição substitui a outra nos cinco desencontros e nas duas descrições de `GP124403` na `Base`. A primeira tela não escolhe: conserva a do item e sinaliza a do estoque.
5. O significado de lote e o significado da casa decimal em `PC`. A coluna continua se chamando `Lote`. O número decimal permanece e fica sinalizado. A hipótese de tipo de avaliação não foi confirmada.
6. Se uma carga posterior pode atualizar quantidade já gravada. A primeira carga, se for autorizada, não atualiza posição existente nem altera o item.

Fora desta versão, sem serem pendências da listagem: extrato geral das 200 linhas e de `B833`; Ok/Nok; alerta de falta; saldo projetado; importação automática recorrente. O aviso de que `GP069610 ` teria par só sem o espaço também não foi aprovado. A tela não mostra a quantidade desse outro código.

## 8. Critérios de aceite

Os testes automáticos usam dados sintéticos na base isolada. Não gravam os 96 itens reais. Quando uma carga real for autorizada, a pré-validação precisa reproduzir os fatos já medidos: 74 pares exatos, 22 sem par, o espaço de `GP069610 ` / `B865`, as cinco divergências de descrição e os 43 grupos.

| Critério | Resultado verificável |
| --- | --- |
| Correspondência exata | O mesmo material e o mesmo centro ligam a posição ao item. Outra combinação não liga |
| Código com espaço | `GP069610 ` e `GP069610` continuam itens diferentes. O espaço final em `B865` não recebe as posições do código sem espaço |
| Material ausente | Item cujo material não está no extrato no mesmo centro fica desconhecido. Não aparece quantidade zero no lugar da ausência |
| Divergência de centro | Material igual em outro centro não liga. Exemplo medido: `GP004975` do item em `B825` não usa o estoque de `B832`, `B833` ou `B838` |
| Lotes diferentes | Duas posições com o mesmo material, centro e depósito, e lotes diferentes, aparecem as duas. Não são o grupo repetido |
| Depósitos diferentes | Duas posições com o mesmo material, centro e lote, e depósitos diferentes, aparecem as duas. Não são o grupo repetido |
| Posições repetidas | Duas linhas com a mesma chave material + centro + depósito + lote aparecem as duas, sinalizadas, sem total. Vale para par idêntico e para conflito |
| Divergência de descrição | A descrição do item não muda. O texto diferente do estoque aparece como divergência. Exemplo medido: `GP124403` / `B856` |
| `PC` com decimal | Quantidade não inteira em `PC` permanece com a casa decimal e fica sinalizada para revisão. Exemplo medido: `GP131157` / `B825` / `SBN1` / lote vazio, `1946.9` e `1117.9`, que também é grupo repetido |
| Quatro quantidades | Livre, trânsito, qualidade e bloqueado ficam em colunas próprias. Bloqueado zero continua zero, não “sem informação” |
| Zero confirmado | Linha presente com utilização livre zero mostra zero. Item sem linha mostra desconhecido |
| Fora dos 96 | Posição sem item correspondente não é gravada e não vira item. `B833` e `GP486978-004` ficam de fora |
| Carga | Itens, entregas e histórico já gravados não mudam. Não há saldo projetado. O comando sem autorização explícita não abre a planilha. Repetir a mesma linha de origem não cria outra posição |
| Telas atuais | Lista, filtros, paginação, busca e `/painel/` não passam a calcular estoque nesta versão |

## 9. Implementação mínima

O aplicativo `inventory` do plano técnico não existe, e o catálogo de centros continua pendente. A fatia mínima foi implementada em `criticals`, sem aplicativo novo e sem permissão nova concedida aos três perfis. Consultar a posição usa a mesma permissão de consultar o item. Não há ação de liberar grupo, editar quantidade ou trocar descrição.

Arquivos prováveis, só na etapa autorizada:

- `criticals/models.py`: posição com material, centro, depósito, lote, unidade, quatro quantidades, texto breve do estoque e linha original da aba. Vínculo com o item só depois da chave exata. Unicidade da linha de origem para a mesma carga não gravar duas vezes.
- `criticals/migrations/0004_stock_position.py`: criação da tabela, aplicada em `apcluster` em 24 out 2026. A migração seguinte e as contagens atuais estão registradas na seção 14.
- `criticals/stock.py`: leitura e comparação. Não remove espaço e não soma grupo repetido.
- `criticals/management/commands/integrar_abas_complementares.py`: comando em simulação por padrão, com confirmação explícita para gravar, recusa conflito e não atualiza linhas existentes.
- `criticals/views.py` e `criticals/source_views.py`: detalhe e painel consultam as posições; as linhas SQVI/LRR têm páginas próprias somente de leitura.
- `templates/criticals/item_detail.html`: tabela no lugar da frase única de saldo. Sem posição exata, o texto passa a dizer que o saldo é desconhecido porque não há par material + centro, e que isso é diferente de zero. Com posição, uma linha por depósito e lote, com as quatro quantidades. Grupo repetido e `PC` decimal usam sinalização visível, sem total. Descrição do item intacta e, se diferir, o texto do estoque ao lado como divergência.
- `static/css/app.css`: só se a sinalização precisar de classe além da já usada para revisão.
- `criticals/tests/test_stock.py`: os critérios da seção 8, com registros sintéticos.

A apresentação não tem coluna somando as quatro quantidades, não tem saldo projetado e não avisa falta. Depósito ou lote sem texto aparece como “em branco”. A lista principal, o painel executivo e a busca não incorporam métricas de estoque; a página `/painel/estoque/` e o detalhe exibem as posições integradas. No `apcluster`, 74 itens têm ao menos uma posição exata e os outros 22 permanecem com estoque desconhecido.

## 10. Riscos se a etapa futura furar estas regras

- Tratar o zero do `VLOOKUP` como saldo esconde os 22 itens sem chave exata e o espaço de `GP069610 `.
- Somar as duas linhas de um conflito publica, por exemplo, `1946.9` com `1117.9` como se fossem um estoque só.
- Somar trânsito ou qualidade na utilização livre muda o disponível.
- Ligar material de outro centro, ou o código sem espaço, atribui saldo ao item errado.
- Escolher uma das cinco descrições apaga a divergência.
- Criar item para `B833` amplia a base crítica sem decisão.
- Importação recorrente gravaria por cima de uma revisão ainda não definida.

## 11. Arquivos examinados

Documentação: `docs/PLANO_TECNICO.md`, `docs/ANALISE_PLANILHA.md`, `docs/REGRAS_DE_NEGOCIO.md`, `docs/DECISOES_PENDENTES.md`, `docs/PREPARACAO_IMPORTACAO.md`, `docs/PLANO_PAINEL.md`.

Código, só para localizar a frase atual de saldo e o comando que recusa carga sem autorização: `templates/criticals/item_detail.html`, `criticals/management/commands/importar_base.py`. A leitura anterior deste arquivo já tinha visto modelos, rotas, telas e a ausência de posição gravada. A busca global existente não entra nesta fatia.

## 12. O que mudou na retomada de planejamento

Foram atualizados este arquivo, `docs/REGRAS_DE_NEGOCIO.md` e `docs/DECISOES_PENDENTES.md`. Essa retomada não gravou posição.

## 13. Estado da tela de estoque antes da carga complementar

O detalhe do item lista as posições ligadas a ele. Na data desta nota de planejamento, a tabela ainda estava vazia. O estado posterior está registrado abaixo.

## 14. Estado verificado após integração em 24 out 2026

O comando `integrar_abas_complementares` foi executado após prévia, confirmação do PostgreSQL local `apcluster` em loopback e conferência do SHA-256 aprovado. Gravou, em transação, 127 linhas de estoque de `Est. Parq.`, 40 linhas SQVI e 72 linhas LRR. Nenhuma linha fora das correspondências exatas foi gravada. O comando reconhece origens idênticas em reexecuções e recusa conflitos; não atualiza registros conhecidos.

As contagens verificadas após a carga são: 96 itens, 62 entregas, 0 históricos de status, 127 posições de estoque, 40 linhas SQVI, 72 linhas LRR, 1 usuário e 3 grupos. A planilha não foi salva nem modificada. `SQVI` e `LRR` são exibidos em `/fontes/sqvi/` e `/fontes/lrr/`, com filtros de itens, paginação e consulta somente leitura. `/painel/estoque/` mostra cada posição, sem total por grupo repetido; a ausência de linha continua significando estoque desconhecido. Não houve mudança de usuários, grupos ou permissões.

Das 127 posições vinculadas, 24 grupos repetem material + centro + depósito + lote: 12 pares iguais e 12 conflitantes; o dashboard os sinaliza sem somar. Os 43 grupos registrados na análise da aba inteira incluem 19 grupos com linhas fora do recorte e não equivalem ao número de grupos mostrados pelo dashboard. Não há quantidade decimal em `PC` entre as posições integradas. As 19 linhas decimais de `GP131157` em `B825` ficam fora do recorte porque os itens críticos desse material estão nos centros `B864` e `B865`.

O resultado de estoque mantém utilização livre, trânsito, qualidade e bloqueado separados. O dashboard não calcula saldo projetado; não interpreta recebimentos ou saldos pendentes; não substitui o LRR operacional do item pelos parâmetros MRP. As linhas não correspondentes foram excluídas da integração. A planilha permaneceu no mesmo SHA-256 `777ede653828560abec0640dcd409a6bed051ebe39614dd29e0bce7ddcff5d06`.
