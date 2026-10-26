# Mapa de relações — Criticos Ap Cluster

Leitura de 24 out 2026, sem gravar a planilha. Arquivo `C:\Users\Anderson\Documents\PROJETOS\CZC\Criticos Ap Cluster.xlsx`. SHA-256 depois da leitura: `777ede653828560abec0640dcd409a6bed051ebe39614dd29e0bce7ddcff5d06` (679.994 bytes). `LRR BR 22.10.xlsx` não foi aberto. As descrições de estado nas seções de análise refletem a situação antes da integração; o estado atual está registrado na seção 7.

A chave aprovada é material + centro, com o texto exato. Espaço nas pontas permanece. Descrição parecida não liga registro.

## 1. O que cada aba é

| Aba | Linhas com conteúdo | Papel |
| --- | --- | --- |
| `Base` | 96, 17 colunas | Itens críticos. Uma linha por material e centro. Já importada |
| `Grafico` | sem série em células (`A1:A1`) | Quatro gráficos da `Base` |
| `SQVI` | 546, 61 colunas | Documentos `UB` e `NB`; 40 linhas exatas vinculadas |
| `LRR` | 1.849, 48 colunas | Parâmetros MRP; 72 linhas exatas vinculadas |
| `Est. Parq.` | 327, 13 colunas | Posições de estoque; 127 linhas exatas vinculadas |
| `Din` | 19 linhas visíveis no cache, 5 colunas na primeira linha | Cinco tabelas dinâmicas da `Base` |

`Base` e `Est. Parq.` têm fórmula na coluna A. `Estoque Parque`, `Estoque Ok/Nok` e `Quant. PO` da `Base` são fórmulas. O zero do `VLOOKUP` de estoque não é saldo.

## 2. Gráficos

| Título na planilha | Tipo | Fonte | No Django |
| --- | --- | --- | --- |
| `ITENS CRITICOS POR PARQUE` | barra 3D | `Base`, agrupado pela coluna Planta | `/painel/`, título “Itens por centro”. Usa o código do centro, não o apelido |
| `STATUS ENTREGA` | barra 3D | `Base`, coluna Status | `/painel/`, “Status da entrega”, contagem e percentual dos itens filtrados |
| `TOTAL CRITICOS` | barra | cache filtrado; o valor visível antigo não é os 96 | `/painel/`, “Total de críticos”, contagem dos itens filtrados |
| `PREVISÃO NO PARQUE` | barra | `Base`, previsão | `/painel/`. O percentual usa só itens com data válida. Em branco e `*` ficam fora das barras |

Não há quinto gráfico. `Din` não é fonte: são as tabelas `Tabela dinâmica4` a `Tabela dinâmica8`. Segmentadores de Planta e Status deixam o cache diferente do universo de 96 itens. O painel recalcula. Não foi criada outra página de gráfico.

Sem itens no filtro, o painel já mostra o estado vazio da consulta. Isso não usa número fixo.

## 3. Relações

### Confirmadas

| Origem | Destino | Chave | Evidência | Uso |
| --- | --- | --- | --- | --- |
| `Base` `GP` + `Parque` | o próprio item | material + centro exatos | 96 pares, nenhum repetido | Já é `CriticalItem` |
| `Base` quantidade, data e observação | entregas do item | linha da `Base` | 62 quantidades na carga já feita | Já é `Delivery` |
| `Est. Parq.` `Material` + `Centro` | `Base` `GP` + `Parque` | material + centro exatos | 127 posições em 74 itens. 22 itens sem par. `GP069610 ` / `B865` sem posição. `GP069610` / `B864` com posição | Integradas e exibidas no detalhe e em `/painel/estoque/`; as posições permanecem separadas |
| `LRR` `Material` + `Área MRP centro` + `Ponto reabastec.` | `Base` `GP` + `Parque` + `LRR` | material + centro exatos | 72 linhas vinculadas. Nos 72 pares antes da carga, o ponto coincide com o LRR não vazio da `Base` | Linhas originais exibidas em `/fontes/lrr/`. Não atualizam nem completam `CriticalItem.lrr` |
| `Grafico` e `Din` | `Base` | tabelas dinâmicas e gráficos | quatro gráficos e cinco dinâmicas, sem coluna nova | Já coberto pelo painel, com as diferenças da seção 2 |
| `SQVI` `Material` + `Cen.` | `Base` `GP` + `Parque` | material + centro exatos | 40 linhas em 28 itens. 506 linhas sem par. 524 `UB` e 22 `NB` | Linhas originais exibidas em `/fontes/sqvi/`; não são calculados recebimento nem saldo pendente |

Na `Est. Parq.`, 43 grupos repetem material + centro + depósito + lote. Cinco itens têm texto breve diferente da descrição da `Base`. Depósito e lote em branco entram na chave. Essas posições continuam fora do banco.

### Relações sem interpretação operacional confirmada

As páginas SQVI e LRR exibem os campos originais das linhas vinculadas. A falta de uma regra operacional não impede a consulta, mas bloqueia cálculos e atualizações com base nesses campos.

| Hipótese | Por que não fecha |
| --- | --- |
| `LRR` `GP069610` / `B865`, ponto 1, preenche o item `GP069610 ` / `B865` | O material da `Base` tem espaço final. O da aba `LRR` não tem. A chave exata não existe. O LRR da `Base` continua vazio |
| `SQVI` `Fornecimento` ou `Qtd.remessa` é recebimento | 390 linhas estão com `#N/A` e 156 com outro valor. A coluna não foi adotada |
| Saldo pendente a partir de pedido, confirmação e remessa | Não há regra aprovada. Quantidade confirmada não substitui essa conta |
| `SQVI` `Tp.aval.` e `Est. Parq.` `Lote` são o mesmo conceito | O vocabulário se parece (`N_IMP`, `N_NAC`, `B_IMP`). A planilha não declara a igualdade. A coluna na tela continua “Lote” |
| `Sugestão BR1` com o texto LRR é o ponto de reabastecimento | São campos diferentes. Um é texto de sugestão; o outro é número na `Base` |
| `Din` pode ser importada como tabela | É cache de dinâmica, filtrado por segmentador |
| Descrições iguais ligam abas | Há divergência registrada. A descrição não é chave |
| Centro de outra linha, ou código sem espaço, vale como estoque do item | Regra aprovada em sentido contrário |

## 4. Páginas

| Página | Situação | Quem acessa | Dados |
| --- | --- | --- | --- |
| `/painel/` | Dashboard executivo. Quatro indicadores da seção 2, mais a lista de revisão | quem tem `view_criticalitem` | itens e entregas já gravados |
| `/painel/estoque/` | Contagem e listagem das posições gravadas. Sem posição, o saldo fica desconhecido. Não soma grupo repetido | a mesma permissão | 127 posições ligadas a 74 itens |
| `/painel/entregas/` | Contagem, mês da data existente, status do item e tabela. Data ausente fica fora da linha | a mesma permissão | entregas dos itens já gravados |
| `/itens/` e detalhe | Reutilizados. O detalhe ganhou a lista de posições | a mesma permissão | item, entregas e posições ligadas |
| `/busca/` | Reutilizada. Não pesquisa estoque, `SQVI` nem `LRR` | item: `view_criticalitem`; entrega: essa e `view_delivery` | itens e entregas |
| Entrega manual | Reutilizada | `add_delivery` | formulário já existente |
| Troca de status | Continua 403 | `change_critical_status`, sem concessão | histórico |
| `/fontes/sqvi/` | Consulta paginada e somente leitura das linhas ligadas | `view_criticalitem` | 40 linhas preservadas |
| `/fontes/lrr/` | Consulta paginada e somente leitura dos parâmetros ligados | `view_criticalitem` | 72 linhas preservadas |
| Relatórios de recebimento, saldo pendente e planejamento calculado | Não criados | — | dependem de regras ainda abertas |

No detalhe, zero posições mostra saldo desconhecido, diferente de zero. Posição presente com quantidade zero mostra zero. Grupo repetido não gera soma. `PC` com casa decimal fica sinalizado. As quatro quantidades ficam em colunas próprias.

Para item sem posição exata, o saldo permanece desconhecido, não zero. Posição presente com quantidade zero mostra zero confirmado.

## 5. O que a migração fez

`criticals.0004_stock_position` criou `criticals_stockposition`, a chave para o item, o índice e as restrições de origem. Não houve `UPDATE` nem `DELETE` em item, entrega ou histórico. Depois dela: 96 itens, 62 entregas, 0 históricos e 0 posições.

O Django criou `add_stockposition`, `change_stockposition`, `delete_stockposition` e `view_stockposition`. Nenhum dos três grupos recebeu essas permissões. A consulta usa `view_criticalitem`. O modelo não está no admin.

`criticals.0005_stockposition_center_name_and_more` acrescentou os campos de proveniência das posições e criou `LinkedSheetRow`. Foi aplicada em 24 out 2026. A alteração é aditiva; não reescreve itens, entregas, históricos, usuários ou grupos.

## 6. Decisões operacionais que continuam bloqueadas

- reimportar a `Base`;
- somar os 43 grupos ou os 55 itens de grupos únicos;
- escolher a descrição oficial;
- tratar recebimento e saldo pendente;
- substituir o LRR vazio pelo ponto da aba `LRR`;
- calcular recebimentos, saldos pendentes, projeções ou indicadores MRP sem regra confirmada.

## 7. Estado verificado após integração

Em 24 out 2026, a prévia confirmou o hash aprovado e classificou 127 posições da `Est. Parq.`, 40 linhas SQVI e 72 linhas LRR como novas, sem conflitos. A carga foi executada em transação no PostgreSQL local `apcluster`. As contagens posteriores foram 96 itens, 62 entregas, 0 históricos, 127 posições, 40 linhas SQVI e 72 linhas LRR. Repetir a prévia classificou todas as linhas como iguais e nenhuma como nova. Não houve duplicidades por identificador de origem nem divergência entre as chaves armazenadas e o item relacionado. Usuários e grupos permaneceram em 1 e 3.

As 127 posições ligadas contêm 24 grupos repetidos (12 pares iguais e 12 conflitantes), sinalizados sem soma. A estatística de 43 grupos se refere às 327 linhas do extrato inteiro; 19 grupos incluem posições não ligadas e excluídas. Nenhuma posição integrada tem quantidade fracionária em `PC`. As ocorrências fracionárias de `GP131157` pertencem a `B825`, sem item crítico desse material nesse centro, por isso não são associadas.

O detalhamento de implementação, reimportação e limites está em `docs/INTEGRACAO_ABAS_COMPLEMENTARES.md`.
