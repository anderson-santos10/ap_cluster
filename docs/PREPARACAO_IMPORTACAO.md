# Preparação da importação — AP Cluster

Leitura de 23 out 2026. Nenhum registro de negócio foi gravado no PostgreSQL. A planilha não foi salva.

O destino conferido antes da leitura continua sendo o PostgreSQL local `apcluster`, em `localhost:5432`, com o usuário `apcluster_app`. As tabelas `criticals_criticalitem`, `criticals_delivery` e `criticals_statuschange` estavam vazias. Esta etapa não abriu o banco para gravar.

## Arquivo lido

| Item | Valor |
|---|---|
| Caminho | `C:\Users\Anderson\Documents\PROJETOS\CZC\Criticos Ap Cluster.xlsx` |
| SHA-256 | `777ede653828560abec0640dcd409a6bed051ebe39614dd29e0bce7ddcff5d06` |
| Tamanho | 679.994 bytes |
| Modo | leitura, sem gravação |
| Fora desta leitura | `LRR BR 22.10.xlsx` |

O hash depois da leitura permaneceu o mesmo.

Abas e intervalos com dados:

| Aba | Intervalo lido | Linhas de dados | Papel nesta preparação |
|---|---|---|---|
| `Base` | colunas A a Q, linhas 2 a 97 | 96 | origem possível de `CriticalItem` e de uma entrega |
| `Est. Parq.` | 13 colunas, linhas 2 a 328 | 327 | posições de estoque; sem modelo de destino |
| `SQVI` | 61 colunas, linhas 2 a 547 | 546 | movimentações UB e NB; sem modelo de destino |
| `LRR` | 48 colunas, linhas 2 a 1850 | 1.849 | parâmetro MRP usado só na comparação do LRR |
| `Din` | 28 linhas por 5 colunas | apresentação | tabela dinâmica; não é cadastro |
| `Grafico` | quatro gráficos no pacote | sem tabela operacional | o texto `Roteiro setembro` aparece só no cache da dinâmica |

Três cabeçalhos da `Base` trazem espaço no final: `Quant. PO `, `Previsão no Parque ` e `Data entrega `. A coluna B do `SQVI` também se chama `conc ` com espaço. A leitura precisa usar o texto exato.

## Resumo

A chave material + centro é única nas 96 linhas da `Base`. Dá para representar o item crítico e, quando houver quantidade, uma entrega. A planilha inteira não cabe nos modelos atuais: falta o apelido da planta, faltam as posições de estoque e faltam os documentos UB e NB.

A primeira carga ficou limitada à aba `Base` e foi executada em 23 out 2026. Estoque, `SQVI` e a aba `LRR` continuam fora.

O cache de quantidade pedida segue a linha errada da fórmula. Recebimento e saldo pendente continuam sem regra comprovada. Os 43 grupos repetidos de estoque continuam bloqueados. O modelo de entrega guarda fonte e linha de origem. As migrações locais incluem `criticals.0002_delivery_origin`, `criticals.0003_critical_status_permission` e `accounts.0002_permissoes_iniciais`. A carga da aba `Base` foi executada em 23 out 2026: 96 itens e 62 entregas. Estoque, `SQVI` e a aba `LRR` continuam de fora.

## Três chaves que não se misturam

| Objeto | Chave observada | O que ela não é |
|---|---|---|
| Item crítico | material + centro, na `Base` colunas GP e Parque | não identifica uma movimentação nem uma posição |
| Posição de estoque | material + centro + depósito + lote | não é o item crítico; depósito ou lote vazios fazem parte da chave |
| Movimentação | `Doc.compra` + item ao lado desse número | não é material + centro |

No `SQVI`, as duas colunas chamadas `Item` diferem em 402 linhas. A primeira acompanha a requisição. A usada aqui é a que fica ao lado de `Doc.compra`. Neste arquivo há 546 documentos e 546 pares documento + item. A unicidade do número, neste extrato, não substitui o item: um arquivo futuro pode trazer várias linhas do mesmo documento.

A coluna B do `SQVI` é a fórmula `CONCAT` de material e centro. A coluna A é outra fórmula, data e número do documento juntos. A soma da `Base` usa a coluna B.

Vinte e oito itens da `Base` têm ao menos uma movimentação. São 40 linhas do `SQVI`. Nove desses itens têm mais de uma linha, no máximo três. Quinhentas e seis linhas do `SQVI` não encontram a chave da `Base`. Compartilhar material e centro não torna essas linhas o mesmo evento.

## Mapeamento proposto

| Origem | Destino | Transformação | Vazio ou inválido | Validação | Situação |
|---|---|---|---|---|---|
| `Base` GP | `CriticalItem.material` | número vira texto; texto permanece, inclusive espaço | vazio impede a linha | obrigatório; até 40 caracteres; único com o centro | segura para o item; o espaço de `GP069610 ` fica em revisão |
| `Base` Parque | `CriticalItem.center` | texto do código SAP | vazio impede a linha | obrigatório; até 10 caracteres | segura |
| `Base` Descrição | `CriticalItem.description` | texto da própria linha | não ocorreu vazio | não escolher outro texto no lugar | segura no item; divergência com o estoque fica registrada |
| `Base` LRR | `CriticalItem.lrr` | número em `Decimal`; vazio fica nulo | não converter vazio em zero nem copiar o ponto da aba `LRR` | 72 preenchidos coincidem com o ponto; 24 vazios | segura |
| `Base` Previsão, quando é data | `CriticalItem.forecast_on` | guardar o dia, inclusive dia 1; texto original fica vazio | — | 95 datas, todas no dia 1, de ago/2026 a mar/2027 | segura |
| `Base` Previsão `*` | `CriticalItem.forecast_original` | guardar `*`; data fica nula | não interpretar o token | uma linha, status Obsoleto | segura para armazenar; o significado continua pendente |
| `Base` Status | `CriticalItem.status` | texto livre | não ocorreu vazio | não criar `StatusChange` nesta carga | segura como texto atual |
| `Base` Obs | `CriticalItem.observation` | texto; vazio fica vazio | 80 linhas vazias | — | segura |
| `Base` Quant. Entregue | `Delivery.quantity` | `Decimal`, inclusive negativo e zero | sem quantidade, não criar entrega | 62 linhas; 26 negativas; nenhum zero | segura; a origem da linha impede repetir a mesma entrega |
| `Base` Data entrega | `Delivery.delivered_on` | data da célula | sem data, gravar nulo; serial não vira data | 57 datas, de 15 jun 2026 a 30 out 2026; 5 quantidades sem data | segura |
| `Base` Planta | sem campo | — | — | um `B838` está como VSMII e os outros como VACI | pendente, decisão 15 |
| `Base` Conc, Mes/Ano, Coluna4, Coluna3 | não gravar | são fórmulas | — | Conc é material + centro | incompatível com gravação; pode ser recalculado |
| `Base` Estoque Parque e Estoque Ok/Nok | não gravar | cache da fórmula | ausência na fórmula vira 0 e não pode ser importada assim | o cache acompanha a primeira utilização livre, não a soma | incompatível com o modelo atual |
| `Base` Quant. PO | não gravar | cache da fórmula deslocada | — | ver a seção do pedido | incompatível com o modelo atual |
| `Est. Parq.` | sem modelo | depósito, lote e quatro quantidades | grupo repetido não é somado nem apagado | 43 grupos em revisão | incompatível até existir `inventory` e a decisão 2 |
| `SQVI` | sem modelo | uma linha por documento + item | `#N/A` não vira zero | UB e NB entram na quantidade documental quando ela for gravada no modelo certo | incompatível até existir `procurement` e a decisão 1 |
| Aba `LRR` | sem modelo | 1.849 parâmetros | — | só o ponto foi comparado ao LRR da `Base` | incompatível, fora do item crítico |
| Cache `Roteiro setembro` | `StatusChange` | não gerar | o texto não está nas 96 linhas | preservar se um dia aparecer numa linha | incompatível com esta carga |
| Autor e instante | campos de usuário | ficam vazios | a planilha não informa | — | segura como vazio |

Os códigos numéricos da `Base` são `109534` e `565784`, cada um em `B864` e `B865`. A célula está como número. O destino guarda texto.

O LRR preenchido e a quantidade entregue da `Base` são inteiros. Utilização livre e quantidade pedida chegam a uma casa decimal. O teto técnico de 14 dígitos e 3 casas comporta esses valores. O limite de negócio continua na decisão 14.

## Duplicidades de estoque

A chave material + centro + depósito + lote forma 284 grupos: 241 com uma linha, 18 com duas linhas iguais e 25 com duas linhas divergentes. Nenhum grupo tem mais de duas linhas. Nenhum campo de texto diverge dentro do grupo. Não há quantidade negativa. Somar ou apagar continua fora de questão. O saldo desses 43 grupos permanece sem resolução.

Se as 18 cópias idênticas fossem somadas, a utilização livre desses grupos aumentaria 35 e o trânsito aumentaria 26. Qualidade e bloqueado não aumentariam. Isso é o efeito da soma, não uma liberação.

Duas cópias são zeradas nas quatro quantidades: `GP131157` / `B865` / `STS1` e `GP249817` / `B825` / `SBN1` / `N_IMP`. A soma não muda o número, e o grupo continua repetido.

| Situação | Material | Centro | Depósito | Lote | Linhas | O que cada linha mostra | Soma se as duas fossem juntadas |
|---|---|---|---|---|---|---|---|
| cópia | GP127960 | B825 | SBN1 | B_IMP | 11, 128 | livre 2 | livre 4 |
| cópia | GP127960 | B825 | SBN1 | N_IMP | 12, 129 | livre 8 | livre 16 |
| cópia | GP127960 | B832 | SUV1 | B_IMP | 13, 131 | livre 1 | livre 2 |
| cópia | GP127960 | B833 | SUV2 | N_IMP | 14, 132 | livre 2 | livre 4 |
| cópia | GP127960 | B838 | SVA1 | B_IMP | 15, 133 | livre 1 | livre 2 |
| cópia | GP127960 | B856 | SVS1 | N_IMP | 16, 135 | livre 2 | livre 4 |
| cópia | GP127960 | B857 | SVS2 | N_IMP | 17, 136 | livre 3 | livre 6 |
| cópia | GP127960 | B864 | SAV1 | N_IMP | 19, 138 | livre 2 | livre 4 |
| cópia | GP127960 | B865 | vazio | vazio | 20, 139 | trânsito 1 | trânsito 2 |
| cópia | GP127960 | B865 | STS1 | N_IMP | 21, 140 | livre 4 | livre 8 |
| cópia | GP127960 | B867 | SVM3 | B_IMP | 22, 141 | livre 1 | livre 2 |
| cópia | GP127960 | B867 | SVM3 | N_IMP | 23, 142 | livre 2 | livre 4 |
| cópia | GP131157 | B832 | vazio | vazio | 26, 144 | trânsito 25 | trânsito 50 |
| cópia | GP131157 | B865 | STS1 | vazio | 35, 153 | quatro quantidades 0 | 0 |
| cópia | GP241858 | B832 | SUV1 | N_IMP | 40, 184 | livre 2 | livre 4 |
| cópia | GP241858 | B833 | SUV2 | N_IMP | 41, 185 | livre 2 | livre 4 |
| cópia | GP249817 | B825 | SBN1 | N_IMP | 42, 186 | quatro quantidades 0 | 0 |
| cópia | GP249817 | B838 | SVA1 | N_IMP | 44, 188 | livre 3 | livre 6 |
| conflito | GP127960 | B838 | SVA1 | N_IMP | 2, 134 | qualidade 0 e 2 | qualidade 2 |
| conflito | GP127960 | B864 | SAV1 | B_IMP | 18, 137 | livre 0 e 1 | livre 1 |
| conflito | GP131157 | B825 | SBN1 | vazio | 25, 143 | livre 1117,9 e 1946,9 | livre 3064,8 |
| conflito | GP131157 | B832 | SUV1 | vazio | 27, 145 | livre 82 e 257 | livre 339 |
| conflito | GP131157 | B833 | SUV2 | vazio | 28, 146 | livre 0,5 e 8,5 | livre 9 |
| conflito | GP131157 | B838 | SVA1 | vazio | 29, 147 | livre 0,8 e 14,8 | livre 15,6 |
| conflito | GP131157 | B856 | SVS1 | vazio | 30, 149 | livre 10,7 e 402,7 | livre 413,4 |
| conflito | GP131157 | B857 | SVS2 | vazio | 32, 150 | livre 11,8 e 381,8 | livre 393,6 |
| conflito | GP131157 | B864 | SAV1 | vazio | 33, 151 | livre 194 e 304 | livre 498 |
| conflito | GP131157 | B865 | vazio | vazio | 34, 152 | trânsito 150 e 400 | trânsito 550 |
| conflito | GP131157 | B867 | vazio | vazio | 36, 154 | trânsito 500 e 1225 | trânsito 1725 |
| conflito | GP131157 | B867 | SVM3 | vazio | 37, 155 | livre 0,1 e 83,1 | livre 83,2 |
| conflito | GP241858 | B825 | vazio | vazio | 38, 182 | trânsito 11 e 14 | trânsito 25 |
| conflito | GP241858 | B825 | SBN1 | N_IMP | 39, 183 | livre 7 e 8 | livre 15 |
| conflito | GP249817 | B832 | SUV1 | N_IMP | 43, 187 | livre 13 e 16 | livre 29 |
| conflito | GP249817 | B856 | SVS1 | N_IMP | 45, 190 | livre 5 e 12 | livre 17 |
| conflito | GP249817 | B857 | SVS2 | N_IMP | 46, 191 | livre 0 e 3 | livre 3 |
| conflito | GP249817 | B864 | SAV1 | N_IMP | 47, 192 | livre 20 e 24 | livre 44 |
| conflito | GP249817 | B865 | STS1 | N_IMP | 49, 193 | livre 3 e 4 | livre 7 |
| conflito | GP249817 | B867 | SVM3 | N_IMP | 50, 195 | livre 14 e 17 | livre 31 |
| conflito | GP525859 | B856 | SVS1 | N_IMP | 51, 324 | livre 0 e 2 | livre 2 |
| conflito | GP525859 | B857 | SVS2 | N_IMP | 52, 325 | livre 15 e 18 | livre 33 |
| conflito | GP525859 | B864 | SAV1 | N_IMP | 53, 326 | livre 13 e 15 | livre 28 |
| conflito | GP525859 | B865 | STS1 | N_IMP | 54, 327 | livre 6 e 8 | livre 14 |
| conflito | GP525859 | B867 | SVM3 | N_IMP | 55, 328 | livre 0 e 2 | livre 2 |

Os 25 conflitos se dividem em 21 de utilização livre, 3 de trânsito e 1 de qualidade. Todos exigem conferência humana. O maior efeito de uma soma indevida está em `GP131157` / `B825`: 1117,9 junto com 1946,9 viraria 3064,8.

`GP131157` está em unidade `PC` e mesmo assim tem casa decimal. A casa decimal não fica restrita à unidade `L`. O extrato tem 305 linhas `PC` e 22 linhas `L`.

## Estoque fora dos grupos repetidos

Setenta e cinco itens da `Base` têm posição quando a busca usa material e centro nas colunas próprias. Em 30 deles, o cache de Estoque Parque é igual à primeira utilização livre e diferente da soma das posições. A fórmula é `VLOOKUP` da primeira linha, ou 0 se não achar. Esse cache não é o estoque consolidado da regra confirmada.

Vinte e um itens não têm posição no próprio centro. O saldo deles é desconhecido, não zero.

Doze materiais não aparecem no extrato: `565784` em `B864` e `B865`, `AMB0155` em `B864` e `B865`, `GP004263` em `B825`, `B832`, `B856`, `B857` e `B867`, `GP004892` em `B825`, `GP004897` em `B864` e `B865`.

Nove existem em outro centro: `GP004975` / `B825`, `GP091145` / `B832`, `GP224705` / `B864`, `GP254146` / `B864`, `GP351497` / `B838`, `GP410281` em `B857` e `B867`, `GP459925` em `B857` e `B867`.

O centro `B833` está no estoque e no `SQVI`, e não está na `Base`.

A linha 29 da `Base` guarda o material `GP069610 ` com espaço final, no centro `B865`. A chave concatenada fica `GP069610 B865`, com espaço no meio. O estoque tem duas posições em `GP069610B865`, sem esse espaço. O `VLOOKUP` não as encontra e o cache de estoque fica 0. O LRR dessa linha está vazio, enquanto o ponto de reabastecimento da aba `LRR` é 1. O vazio permanece vazio. O zero do cache não entra como saldo.

## Pedido, recebimento e pendência

As 96 fórmulas de Quant. PO apontam para outra linha da `Base`. O deslocamento não é único: há fórmulas três, quatro, seis ou sete linhas acima, e também referências mais distantes.

Em 48 itens, a soma da própria chave e a soma da linha apontada são as duas zero. O cache também é zero. Em outros 48, as somas diferem, e o cache acompanha a linha apontada. Em nenhum item o cache acompanha só a soma certa quando ela difere da soma errada.

Exemplo: a linha 4, `GP241858` / `B832`, tem cache 750 e soma própria 0. A fórmula aponta para a linha 44, cuja soma é 750. A linha 44, `GP131157` / `B864`, tem cache 0 e soma própria 750.

A quantidade documental, se um dia for gravada, é a soma refeita de `Qtd.pedido` na chave material + centro, para UB e NB. O cache não é essa quantidade. Não há campo para ela em `CriticalItem`.

O `SQVI` tem 524 linhas `UB`, documento começando em `430`, e 22 linhas `NB`, documento começando em `450`. Não há quantidade pedida negativa nem zero. Há quantidade com uma casa decimal.

Quantidade confirmada: 383 zeros, 143 iguais ao pedido e 20 menores. Confirmação não foi tratada como recebimento.

`Fornecimento` é `#N/A` em 390 linhas e um número, no padrão `800…`, em 156. Nessas 156, `Qtd.remessa` também é numérica. Nas 390, a remessa é `#N/A`. O par parece um número de fornecimento com uma quantidade, e não uma entrada de mercadoria identificada. `Data fim da EM` é outra coluna: 494 valores estão como serial. `DataConf.` do documento `4300011896` é o serial `2958465`, que no calendário do Excel corresponde a 31 dez 9999. Esse valor não será gravado como data operacional.

Só 3 das 62 quantidades entregues coincidem com a soma documental da própria chave. A entrega da `Base` não foi usada como recebimento do pedido.

Nenhuma dessas colunas sustenta saldo pendente. Pedido menos entrega, pedido menos confirmação e pedido menos remessa ficam sem adoção.

## Descrições e apelidos

`GP124403` tem duas descrições na `Base`: `AMB_EBM_K2E225RA9209` em `B856` e o texto do ventilador em `B857` e `B867`. O modelo guarda a descrição no item, então as duas permanecem, cada uma no seu centro. O estoque de `B856` traz só o texto do ventilador.

Também divergem da `Base`, no mesmo centro:

- `GP335709` / `B825`: a `Base` traz o texto em inglês e o estoque traz `FITA ANTIDERRAPANTE PR/AM 50X300MM`;
- `GP411469` em `B856`, `B857` e `B867`: a `Base` traz `3.53KW` e `35HZ`; o estoque traz `3.54KW` e `50/60HZ`.

Nenhum texto foi escolhido como oficial.

Apelidos lidos na `Base`: `B825` BLOCO NORTE SUL (BNS), `B832` UNIÃO DOS VENTOS (UDV), `B838` VACI, `B856` VSMI, `B857` VSMII, `B864` MARAL, `B865` TERRA SANTA, `B867` VSMIII. `GP296945` / `B838` está com VSMII.

## Quantidade entregue

| Status | Quantidade positiva | Quantidade negativa | Sem quantidade |
|---|---|---|---|
| Em rota | 30 | 1 | 0 |
| Pendente | 0 | 2 | 25 |
| Entregue | 6 | 14 | 1 |
| Entregue parcial | 0 | 7 | 0 |
| Criar RC | 0 | 1 | 5 |
| Sem necessidade parque | 0 | 1 | 2 |
| Obsoleto | 0 | 0 | 1 |

As cinco quantidades sem data estão em Entregue: `109534` / `B865`, `565784` / `B865`, `GP254146` / `B865`, `GP307720` / `B825` e `GP371842` / `B857`. A data permanece nula.

O sinal negativo aparece em mais de um status. A planilha não explica o sinal. O valor fica preservado e `requires_review` fica verdadeiro.

## Identificação da entrega

A `Base` não traz documento SAP nem outro identificador do evento. Quantidade e data podem se repetir, e material + centro identificam o item, não a entrega. A origem adotada é o par:

- fonte `criticos-ap-cluster:Base`;
- número original da linha na aba, começando em 2.

Esse par é único enquanto a linha de origem estiver preenchida. Duas linhas do mesmo item geram duas entregas. A mesma linha, lida de novo, aponta para a mesma entrega. Entrega lançada no sistema deixa fonte e linha vazias e fica fora dessa unicidade. Fonte sem linha, ou linha sem fonte, não satisfaz a restrição.

A limitação é a reordenação. Se a planilha mudar a ordem das linhas, o número deixa de apontar para o mesmo evento: a linha antiga parece ausente e a nova parece outra entrega. Inserir ou excluir uma linha no meio desloca as seguintes. O número da linha não sobrevive a essa mudança. Não há, na `Base`, chave melhor comprovada para substituí-lo.

## Reimportação

A política da primeira versão é `somente_relatar`. A rotina classifica cada linha e não grava atualização:

| Situação | Reconhecimento | Efeito preparado |
|---|---|---|
| Novo item | material + centro ainda não existe | criar, quando a carga for autorizada |
| Item existente | a chave já existe | reconhecer |
| Nova entrega | a origem ainda não existe | criar a entrega daquela linha |
| Entrega já importada | a mesma fonte e a mesma linha | não criar outra |
| Divergência | a origem ou a chave já existe com conteúdo diferente | reportar e não sobrescrever |
| Dado inválido | material vazio, centro vazio ou valor acima do teto técnico | rejeitar a linha e revisar |

Campos comparados no item: descrição, LRR, previsão, texto original da previsão, status e observação. Na entrega: quantidade e data. Quantidade negativa, zero, data ausente e data válida permanecem distintos.

A reimportação preserva histórico de status, autor da entrega e entregas sem fonte. A divergência não gera atualização. Repetir a pré-validação não duplica registros. A identidade pelo número da linha vale enquanto a ordem e a estrutura da aba `Base` permanecerem estáveis.

Uma atualização automática futura exigiria outra decisão humana. Ela não está implementada. A carga não cria `StatusChange`.

## O que os modelos atuais cobrem

`CriticalItem` e `Delivery` cobrem a parte operacional da `Base`, com a ressalva do apelido. Não cobrem posição, documento, parâmetro MRP, cache calculado nem o status que existe só na dinâmica.

O modelo `Delivery` tem `source` e `source_row`, a unicidade `delivery_source_row_uniq` e a checagem `delivery_source_pair`. A migração `criticals.0002_delivery_origin` aplicou isso no PostgreSQL local:

- `source`, texto de até 80 caracteres;
- `source_row`, inteiro positivo, nulo quando a entrega não vem da importação;
- unicidade de fonte + linha quando a linha está preenchida;
- checagem de que os dois vêm juntos ou ficam ambos vazios.

Em 23 out 2026 o `apcluster` local passou a ter 96 itens e 62 entregas. Nenhuma alteração de status foi criada pela carga. O código `GP069610 ` permanece com o espaço, separado de `GP069610`. A previsão `*` ficou em `forecast_original`, com data nula. Há 26 quantidades negativas e 24 LRR ausentes.

Continuam sem modelo nesta carga: apelido da planta, `inventory` e `procurement`.

## Regras confirmadas e o que continua hipótese

Continuam valendo as regras já confirmadas: chave material + centro, LRR vazio diferente de zero, previsão no dia 1 como mês, `*` sem significado atribuído, histórico separado do status atual, várias entregas por item, negativo preservado, data ausente sem invenção, conta removida sem apagar o histórico, estoque ausente desconhecido, grupo duplicado bloqueado, UB e NB na quantidade documental, recebimento e pendência sem cálculo.

Nesta leitura, continuam hipótese: negativo como falta, `Em rota` como quantidade a caminho, `B8D1` como centro fornecedor, lote como tipo de avaliação, e legenda dos códigos de uma letra. `Fornecimento` numérico também não ficou comprovado como recebimento.

## Riscos se a carga fosse feita agora

- Gravar o cache de Quant. PO trocaria a quantidade de 48 itens pela soma de outra linha.
- Gravar o cache de Estoque Parque lançaria 0 para ausência e para a chave com espaço, e ignoraria a soma e os grupos bloqueados.
- Somar os 25 conflitos misturaria dois valores incompatíveis. O caso de 1117,9 e 1946,9 mostra o tamanho do desvio.
- Somar as 18 cópias aumentaria 35 na utilização livre e 26 no trânsito.
- Repetir a mesma linha de origem não cria outra entrega. Reordenar a planilha ainda pode trocar a identidade.
- Preencher o LRR vazio de `GP069610 ` / `B865` com 1 apagaria o branco original.
- Escolher uma descrição apagaria a outra.
- Tratar duas linhas do `SQVI` com o mesmo material e centro como a mesma entrega juntaria documentos diferentes.
- Salvar a planilha com a biblioteca de leitura removeria os segmentadores. O script de pré-validação abre em leitura e não salva.

## Decisões antes de autorizar a importação

1. A primeira carga gravou só a `Base` em 23 out 2026. Estoque, `SQVI` e a aba `LRR` ficaram de fora. Uma nova execução da pré-validação reconheceu as 96 linhas e as 62 entregas, sem atualizar nada.
2. Confirmar o tratamento do espaço em `GP069610 `. A preparação preserva o espaço, registra a diferença e não liga essa linha às posições sem espaço.
3. Confirmar se o apelido fica de fora até o catálogo, ou se entra no item. Decisão 15, incluindo VSMII em `B838`.
4. A primeira versão só relata divergência. Isso já foi adotado e testado. Uma atualização automática futura continua pendente de decisão humana.
5. Confirmar que o status atual não gera `StatusChange` e que `Roteiro setembro` não entra enquanto estiver só no cache da dinâmica.
6. Confirmar que o cache de Quant. PO e o cache de Estoque Parque não serão gravados.
7. Escolher, quando for a hora do estoque, o critério que libera cada um dos 43 grupos. Até lá o saldo do grupo não é calculado.
8. Identificar recebimento antes de qualquer saldo pendente. Decisão 1.
9. Dizer quais centros entram no cadastro. Além dos oito da `Base`, o estoque e o destino do `SQVI` citam `B833`. A origem cita `B8D1` em 480 linhas, `B817` em 5, e também `B855`, `B830` e `B837`, além de centros que já estão na `Base`. A origem vazia nas 22 linhas `NB` não é um centro. Decisão 3.

## Procedimento sugerido para uma carga futura

1. Conferir o SHA-256 do arquivo. Se mudar, repetir esta preparação antes de gravar.
2. Executar `python manage.py prevalidar_base`. Ele lê só a aba `Base`, confirma o banco local e não grava. Cabeçalho inesperado ou linha inválida entra no relatório.
3. Revisar a lista de conferência humana: espaço no material, cinco datas ausentes, 26 quantidades negativas, cinco descrições divergentes, 21 itens sem posição, 43 grupos de estoque e o cache deslocado.
4. Esperar as confirmações da seção anterior.
5. Confirmar que o comando aponta para o PostgreSQL local `apcluster`, em localhost, porta 5432, com o usuário `apcluster_app`. Se a conexão não puder ser confirmada, a rotina falha e não grava.
6. Numa transação, e só depois de autorização explícita em uma solicitação futura, criar o item que ainda não existe e a entrega cuja origem ainda não existe. Não atualizar item ou entrega já registrados. Manter LRR nulo quando a célula estiver vazia. Guardar `*` fora da data. Não inventar data. Não corrigir negativo. Não apagar entregas sem fonte nem histórico.
7. Não criar alteração de status, posição, documento nem parâmetro MRP nessa carga.
8. Conferir as contagens do arquivo: 96 itens, 24 LRR nulos, 95 previsões em data, um texto `*`, 62 entregas, 26 em revisão, 5 sem data.
9. Se a conferência falhar, desfazer a transação. A planilha permanece como estava. Não há `flush`, `reset` nem recriação do banco nesse procedimento.

## Como repetir a pré-validação

No ambiente do projeto:

```text
.\.venv\Scripts\python.exe manage.py prevalidar_base
.\.venv\Scripts\python.exe manage.py importar_base
.\.venv\Scripts\python.exe manage.py test criticals.tests.test_preparation criticals.tests.test_base_load --settings=config.settings.testing
.\.venv\Scripts\python.exe manage.py check
```

`prevalidar_base` lê somente a aba `Base`, compara com o banco e não grava. `importar_base` recusa a carga antes de abrir a planilha. Os testes usam valores sintéticos. O script antigo `scripts/prevalidar_criticos.py` continua sendo análise das outras abas e não é a rotina de importação.
