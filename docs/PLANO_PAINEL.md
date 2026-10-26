# Plano do painel

Diagnóstico de 23 de outubro de 2026. Este documento planeja a evolução além da aba `Base`. Não autoriza importação, migração, alteração de registros, de usuários ou de permissões.

A planilha lida foi `C:\Users\Anderson\Documents\PROJETOS\CZC\Criticos Ap Cluster.xlsx`. A leitura foi somente do pacote e das células em cache. O arquivo não foi salvo. O SHA-256 permaneceu `777ede653828560abec0640dcd409a6bed051ebe39614dd29e0bce7ddcff5d06`. `LRR BR 22.10.xlsx` não foi aberto.

Os números gravados em `Din` e dentro dos gráficos são cache de tabela dinâmica. Eles dependem dos segmentadores que estavam selecionados e não fecham entre si. O painel recalcula a partir dos itens, sem copiar esse cache.

## Versão 1

Aprovada em 23 de outubro de 2026 e disponível em `/painel/`.

- O eixo “por parque” usa o código do centro. Apelido de planta não foi inventado.
- O percentual da previsão usa somente itens com data válida. Itens sem data, inclusive a previsão literal `*`, aparecem numa contagem separada e fora das barras.
- Centro e status, na lista e no painel, são comparados por igualdade. Assim, `Entregue` não inclui `Entregue parcial`.
- SQVI, LRR e Est. Parq. continuam fora. Estoque, recebimento e saldo não são calculados.

## O que a planilha contém

Seis abas:

| Aba | Papel | Situação no sistema |
| --- | --- | --- |
| `Base` | 96 itens, chave material + centro, até uma entrega por linha | Importada: 96 itens e 62 entregas |
| `Grafico` | Quatro gráficos e dois segmentadores; não tem tabela própria | Tela `/painel/`, recalculada no banco |
| `Din` | Cinco tabelas dinâmicas da `Base`; é a fonte visual dos gráficos | Ausente de propósito |
| `SQVI` | 546 linhas de documentos de compra | Ausente |
| `LRR` | 1849 parâmetros de ponto de reposição | Só o ponto já preenchido na `Base` entrou no item |
| `Est. Parq.` | 327 posições de estoque | Ausente; o saldo na tela continua desconhecido |

`Din` não deve virar tabela. `Grafico` também não. Os dois são consulta sobre os itens.

## Os quatro gráficos

Os gráficos leem células de `Din`. A contagem é sempre a contagem do campo `GP` (o material), não a soma de quantidade. O cache da tabela dinâmica também guarda valores que não estão nas 96 linhas atuais, entre eles o status `Roteiro setembro`, a planta `MARRAL` e códigos de centro dentro do campo `Planta`. Esses valores aparecem no segmentador como sem dados. Não entram no painel.

Os segmentadores `Planta` e `Status` filtram só três dinâmicas: a de planta, a do total e a contagem de status. A dinâmica de percentual por status e a de previsão não estão ligadas a esses segmentadores. A de previsão tem um filtro de página próprio no campo `Status`.

O arquivo estava salvo com `Planta = TERRA SANTA` e `Status = Em rota` nesses segmentadores. Por isso o cache visível não é o universo dos 96 itens.

### 1. Itens críticos por parque

- Arquivo: `xl/charts/chart1.xml`. Título: `ITENS CRITICOS POR PARQUE`. Barras 3D.
- Fonte desenhada: `Din!A4:A5` e `Din!B4:B5`.
- Categoria real da dinâmica: campo `Planta`, não o código do centro. O título diz parque, mas o corte é o apelido da planta.
- Métrica: contagem de itens. A definição da dinâmica pede percentual do total, mas a célula salva mostra a contagem `1` para `TERRA SANTA` e total `1`.
- O intervalo inclui a linha `Total Geral`. Um gráfico fiel não pode plotar o total como se fosse uma planta.
- Fórmula em uso: contar `CriticalItem` agrupado pelo código do centro. O apelido da planta não entra nesta versão.
- O cache `1` não é o indicador. Terra Santa tem 15 itens na carga.

### 2. Status da entrega

- Arquivo: `xl/charts/chart2.xml`. Título: `STATUS ENTREGA`. Barras 3D.
- Fonte desenhada: `Din!A17:A24` e `Din!B17:B24`.
- Categorias do cache: Em rota, Pendente, Entregue, Entregue parcial, Criar RC, Sem necessidade parque, Obsoleto. A última linha do intervalo é `Total Geral`.
- Métrica: contagem do material dividida pelo total da dinâmica, em percentual.
- Este gráfico não recebe os segmentadores. O cache fecha com a carga: 31, 27, 21, 7, 6, 3 e 1, somando 96. Em percentual: 31/96, 27/96, 21/96, 7/96, 6/96, 3/96 e 1/96.
- Fórmula proposta: contar itens por `status` dentro do filtro da tela e dividir pelo total do mesmo filtro. Mostrar a contagem ao lado do percentual. Sem filtro, o denominador é 96 e o resultado deve repetir esses sete grupos. `Roteiro setembro` só aparece se um dia existir num item.

### 3. Total de críticos

- Arquivo: `xl/charts/chart3.xml`. Título: `TOTAL CRITICOS`. Barras simples.
- Fonte desenhada: `Din!A28`, valor em cache `5`.
- Métrica: contagem dos itens que sobram depois dos segmentadores. Não há categoria além do próprio total.
- O `5` é o recorte salvo. Não é o total do sistema. Há outra célula de status, também filtrada, com `Em rota = 5`, enquanto a de planta mostra total `1`. Os caches não são consistentes entre si.
- Fórmula proposta: `CriticalItem` visível depois dos filtros. Sem filtro, o valor é 96.

### 4. Previsão no parque

- Arquivo: `xl/charts/chart4.xml`. Título: `PREVISÃO NO PARQUE`. Barras simples.
- Fonte desenhada: `Din!D4:D10` e `Din!E4:E10`.
- Categorias no cache: MAR/2027, FEV/2027, JAN/2027, DEZ/2026, NOV/2026, OUT/2026. A linha `D10` é `Total Geral`. AGO/2026 e SET/2026 existem no cache do campo e não estão nesse intervalo visível.
- Métrica: contagem percentual do campo `Mes/Ano`. Os percentuais das seis linhas somam 100% do subconjunto que a dinâmica estava mostrando, não 100% dos 96. O campo de origem é a previsão, e o dia 1 representa o mês.
- Fórmula proposta: agrupar por ano e mês de `forecast_on`. O literal `*` fica de fora das barras e aparece como contagem separada, hoje 1. Itens sem previsão, se surgirem, também ficam fora das barras.
- Denominador aprovado: itens com data de previsão. Itens sem data válida, inclusive `*`, ficam numa contagem separada.

## Relação entre as abas

A chave operacional do item é material + centro. O espaço do material faz parte da chave. `GP069610` em `B864` e `GP069610 ` em `B865` continuam registros diferentes.

| Aba | Como encontra o item | O que não fazer |
| --- | --- | --- |
| `LRR` | Material + `Área MRP centro` | Não usar `Área MRP`, que mistura centro e depósito. Não preencher o LRR vazio da `Base` com o ponto da aba. O único desencontro conhecido continua sendo `GP069610 ` / `B865`: vazio na `Base` e ponto 1 na aba |
| `Est. Parq.` | Material + centro, e em seguida depósito e lote | Não somar os 43 grupos duplicados. Não transformar ausência em zero. A fórmula da `Base` pega a primeira utilização livre ou devolve zero; por isso o cache não serve |
| `SQVI` | Coluna `conc`, material + centro de destino | Não herdar a fórmula `Quant. PO` da `Base`: as 96 fórmulas apontam para outra linha. A quantidade de documento, se um dia for calculada, soma as linhas do próprio material + centro. Documento e item do pedido identificam a linha; o item da requisição é outro campo |

Entrega da `Base` e linha da `SQVI` não são o mesmo fato. A carga tem 62 entregas. A `SQVI` tem 40 linhas cujo material + centro existe na `Base`, em 28 itens, e 506 linhas sem par na `Base`. Centro de destino também inclui `B833`, que não está na `Base`. Origem inclui `B8D1` e outros centros ainda não cadastrados.

Datas da `SQVI` em série do Excel, inclusive a série que cai em 9999-12-31, não são data operacional. `Qtd.confir`, `Fornecimento` e `Qtd.saída` não viram recebimento nem saldo pendente.

## Fórmulas que não entram no painel agora

| Indicador da `Base` | Fórmula da planilha | Fonte proposta | Bloqueio |
| --- | --- | --- | --- |
| Estoque Parque | Primeira utilização livre do material + centro, ou zero se a busca falha | Soma das posições válidas, só depois da revisão dos 43 grupos | Saldo ausente é desconhecido. O zero da fórmula some com a busca falha e com o espaço de `GP069610 ` |
| Ok/Nok | Estoque em cache menos LRR, e LRR vazio entra como zero | Posição revisada menos o LRR do item | Não dá para classificar ok ou nok sem saldo conhecido |
| Quant. PO | `SUMIF` na `SQVI` com a chave de outra linha | Soma da quantidade de pedido das linhas do próprio item | O cache não é a soma certa. Recebimento continua indefinido |
| Mês/Ano | Mês e ano da previsão | `forecast_on`; `*` permanece texto | O significado comercial de `*` continua pendente |

## Comparação com o sistema

Implementado:

- lista, detalhe, filtros por material, descrição, centro e status, paginação;
- entregas com origem da linha da `Base`, quantidade negativa preservada e data ausente preservada;
- histórico de status, ainda vazio porque a importação não cria histórico;
- registro manual de entrega e bloqueio da troca de status para os três perfis;
- inconsistências de espaço, colisão, `*`, quantidade negativa e data ausente.

Parcial:

- LRR numérico da `Base`, com vazio diferente de zero. A aba `LRR` inteira não foi importada;
- filtros da lista por material, descrição, centro e status; o painel acrescenta o mês da previsão;
- saldo apenas como texto “desconhecido”, sem posição de estoque.

Ausente:

- apelido da planta, de propósito nesta versão;
- documentos da `SQVI`;
- posições da `Est. Parq.`;
- Ok/Nok e quantidade de pedido recalculada.

A tela `/painel/` cobre o total, o centro, o status e o mês, com link para a lista filtrada.

## Telas propostas

Uma rota nova, `/painel/`, somente leitura, para quem já pode ver itens. Sem modelo novo nesta primeira leva.

Quatro blocos, na mesma ordem da planilha:

1. total de itens do filtro;
2. barras por centro, com a contagem;
3. barras por status, com contagem e percentual do filtro;
4. barras por mês de previsão, com o `*` separado.

Os filtros são centro e status, combinados. Material e descrição continuam na lista, não no desenho da planilha. Clicar numa barra abre `/itens/` com o mesmo filtro. Barras simples, sem o efeito 3D.

A segunda leva, só depois das decisões, acrescenta no detalhe do item: posições de estoque, parâmetros LRR e documentos SQVI. Cada um entra com a própria chave e sem juntar pelo código sem espaço.

## Etapas

Cada etapa para e pode ser conferida sozinha. Nenhuma começa sem aprovação.

1. Agregações em memória, testadas com dados sintéticos: total, centro, status e mês. O `*` não entra no mês. A base isolada de teste não usa os 96 registros reais.
2. A rota `/painel/` com os quatro números e os filtros, ainda sem desenho elaborado. Teste de permissão: quem não vê item não vê o painel.
3. Barras a partir desses mesmos números e o link para a lista filtrada.
4. Conferência manual: sem filtro, 96 itens, os sete status nas contagens 31, 27, 21, 7, 6, 3 e 1, oito centros e o `*` fora dos meses. Essa conferência lê o banco; não reimporta.
5. Planta, estoque, SQVI e Ok/Nok ficam para decisões próprias. Não misturar essas etapas com o painel da `Base`.

## Decisões que continuam com a equipe

- Ok/Nok e quantidade de pedido ficam fora do primeiro painel.
- Os 43 grupos de estoque, o recebimento, o saldo pendente, os centros extras e o significado de `*` continuam como já registrados em `docs/DECISOES_PENDENTES.md`.

## Riscos

- Copiar o cache mostraria total 5, Terra Santa 1 e percentuais de um recorte que nem fecha com o total ao lado.
- Tratar `Total Geral` como categoria infla o gráfico.
- Juntar `GP069610` com `GP069610 ` ligaria o estoque e o LRR errados.
- Somar posições duplicadas ou usar o zero da busca criaria saldo falso.
- Usar a fórmula atual de `Quant. PO` publicaria a quantidade de outro item.
