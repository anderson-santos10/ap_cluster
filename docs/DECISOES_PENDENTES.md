# Decisões pendentes — AP Cluster

## Decisões já tomadas

Em 23 out 2026 ficou definido que a primeira versão usa somente `Criticos Ap Cluster.xlsx`. Em 24 out 2026 o caminho oficial confirmado passou a ser `C:\Users\Anderson\Documents\PROJETOS\CZC\Criticos Ap Cluster.xlsx`. O tamanho e o SHA-256 são os da leitura anterior.

`C:\Users\Anderson\Documents\PROJETOS\CZC\LRR BR 22.10.xlsx` não entra na fonte inicial. As planilhas não serão combinadas, cruzadas nem importadas juntas nesta fase.

No mesmo dia ficou definido o ambiente e o acesso:

- desenvolvimento e teste locais no Windows, pelo navegador deste computador e pelo servidor de desenvolvimento do Django;
- hospedagem definitiva adiada até a validação local, sem Railway, Render ou outro serviço de nuvem nesta etapa;
- PostgreSQL 18.6 local, escutando só em localhost, com a primeira migração aplicada em `apcluster`;
- contas individuais, sessão, páginas internas protegidas e permissão verificada no servidor;
- perfis de Administração, Compras e Estoque/Operação, como grupos do Django, com a matriz restrita descrita abaixo;
- registro de quem altera status, revisa estoque e registra entrega.

Na revisão de 23 out 2026, o modelo de usuário ficou definido como `django.contrib.auth.models.User`, antes de qualquer tabela. Existe uma conta superusuária, fora dos três grupos. A senha e os grupos dessa conta não foram alterados.

Na preparação da primeira carga, ficou confirmado:

- a primeira importação usa somente a aba `Base`;
- quantidade negativa permanece como está e fica sinalizada para revisão;
- cada entrega importada guarda a fonte `criticos-ap-cluster:Base` e a linha original, com unicidade no modelo.

A migração `criticals.0002_delivery_origin` foi aplicada no `apcluster` local. Em seguida, `criticals.0003_critical_status_permission` e `accounts.0002_permissoes_iniciais` também foram aplicadas. Em 23 out 2026 a aba `Base` foi importada: 96 itens, 62 entregas e nenhum histórico. A conta real e as permissões não mudaram.

No planejamento posterior do estoque, ainda em 23 out 2026, ficou aprovado para a primeira integração: escopo dos 96 itens; ligação só por material e centro exatos, sem remover espaço nem normalizar; lotes, depósitos e posições repetidas separados; grupos repetidos sinalizados e não somados; quantidades e unidades originais preservadas, com casa decimal em `PC` sinalizada; descrição do item preservada e divergência do estoque sinalizada; as quatro quantidades em separado; ausência de correspondência como desconhecido, não zero; posições fora dos 96 excluídas; sem saldo projetado e sem importação automática recorrente. Em 24 out 2026, a integração autorizada gravou 127 posições de `Est. Parq.`, 40 linhas SQVI e 72 linhas LRR, vinculadas exclusivamente por chaves exatas. O estado técnico está em `docs/INTEGRACAO_ABAS_COMPLEMENTARES.md` e `docs/ANALISE_ESTOQUE.md`.

## Classificação desta revisão

| Ponto | Classificação | Efeito |
|---|---|---|
| `*` na previsão | Implementada e testada como preservação | O texto fica em `forecast_original` e a data fica nula. O significado comercial continua pendente de decisão humana |
| Espaço no material | Implementada e testada | O código original permanece. A comparação sem espaços só gera alerta e não une registros nem liga estoque |
| Centros fora da `Base` | Fora do escopo atual | A carga inicial reconhece os oito centros da `Base`. `B833`, `B8D1`, `B817`, `B855`, `B830` e `B837` não entram |
| Divergência de estoque | Implementada e testada | Posições da `Est. Parq.` foram integradas às 74 correspondências exatas. A tela mostra posições separadas, destaca grupos repetidos, descrição divergente e, quando existir, `PC` decimal. Entre as 127 posições há 24 grupos repetidos (12 pares iguais, 12 conflitantes) e nenhum `PC` decimal. Não soma posições nem transforma ausência em zero |
| Reimportação | Implementada e testada | Diferença em linha já importada é relatório. Nenhum campo descritivo ou operacional é atualizado automaticamente |
| Status por perfil | Pendente de decisão humana | A permissão `change_critical_status` existe e não foi concedida a nenhum grupo |
| Recebimento, saldo pendente, descrição oficial, apelido, centros do catálogo, permissão por centro, limites de negócio, integrantes, rede e hospedagem | Pendente de decisão humana ou fora do escopo | Nenhuma dessas escolhas foi preenchida por uma solução técnica |

## Ainda sem resposta

A carga inicial aprovada das três abas complementares foi executada em 24 out 2026; isso não resolve as decisões comerciais abaixo. SQVI e LRR são exibidos como linhas originais vinculadas, sem cálculo ou atualização do item.

1. **Recebimento.** Como identificar e conciliar recebimento no `SQVI` da planilha aprovada. A leitura de 23 out 2026 viu `Fornecimento` como `#N/A` ou como número, ao lado de `Qtd.remessa`, e não adotou esse par como recebimento. Quantidade confirmada também não foi adotada. Enquanto isso, saldo pendente não é calculado nem apresentado como confiável.

2. **Duplicidade de estoque.** Como distinguir cópia idêntica de conflito e qual critério libera um grupo bloqueado. A releitura de 23 out 2026 encontrou 43 grupos na aba inteira: 18 pares idênticos e 25 pares conflitantes na chave material + centro + depósito + lote. Somar as cópias idênticas da aba inteira aumentaria 35 na utilização livre e 26 no trânsito; essa soma não foi adotada. No recorte integrado dos 96 itens, há 24 grupos: 12 pares idênticos e 12 conflitantes, todos sinalizados e sem soma. Outros 19 grupos incluem linhas excluídas por não corresponderem exatamente a item crítico. O critério de revisão/liberação continua em aberto. Também não ficou aprovado exibir total de utilização livre, mesmo para itens cujos grupos são todos únicos.

3. **Centros do cadastro inicial.** Quais centros serão cadastrados no início. A `Base` tem oito centros. Os extratos do mesmo arquivo também citam `B833`, `B8D1` e `B817`. A origem do `SQVI` cita ainda `B855`, `B830` e `B837`. A seleção ainda não foi feita.

4. **Permissão por centro.** Quais perfis consultam ou alteram cada centro SAP. Administração, Compras e Estoque/Operação estão previstos. O recorte por centro continua aberto.

5. **Descrição oficial.** Qual texto substitui o outro quando há divergência. A fonte aprovada tem diferença entre a `Base` e o estoque, e duas descrições para o mesmo material na `Base`. A primeira tela de estoque conserva a descrição do item e sinaliza a do estoque. Essa escolha não fecha qual texto é o oficial e não impede a tela.

6. **Reimportação.** A primeira versão ficou na política `somente_relatar`: diferença em linha já importada gera revisão e não altera descrição, LRR, previsão, status, observação, quantidade nem data. Histórico de status, autor e entregas sem fonte permanecem preservados. A identidade pela linha da planilha depende de a ordem e a estrutura da aba `Base` permanecerem estáveis. Uma política futura de atualização ainda exigiria decisão humana; ela não está implementada.

7. **Status e códigos válidos.** Quais status e códigos operacionais serão aceitos. A `Base` tem sete textos atuais, e o cache antigo tem `Roteiro setembro`, que deve ser preservado se aparecer. Os códigos de uma letra do `SQVI` e os flags da aba `LRR` deste arquivo seguem sem legenda confirmada.

8. **Datas e campos sem interpretação fechada.** Como tratar número serial, 31 dez 9999, a previsão gravada como `*`, cabeçalhos cuja célula é uma data, e campos MRP cujo significado não foi confirmado.

9. **Ausências da fonte escolhida.** Como o sistema trata o que `Criticos Ap Cluster.xlsx` não fornece. Exemplos já vistos: várias entregas por item, vínculo validado de recebimento, critério para liberar duplicidade, descrição única e permissão por centro. A ausência não será preenchida com a outra planilha nem com valor inventado.

10. **Uso futuro de `LRR BR 22.10.xlsx`.** Se essa planilha será incorporada, e em que fase. Nesta versão ela permanece fora. A investigação já feita não autoriza uso parcial.

11. **Acesso fora deste computador.** Se a aplicação local precisará ser alcançada por outros computadores da rede. O uso no navegador desta máquina não inclui essa abertura.

12. **Hospedagem.** O PostgreSQL 18.6 local escuta só em localhost, o banco `apcluster` existe e a primeira migração foi aplicada. A hospedagem só entra depois da validação local.

13. **Integrantes, logins e perfis reais.** A criação de contas depende dessa lista. Nenhuma conta foi inventada.

14. **Tamanho de negócio dos campos.** A leitura da `Base`, sem alterar o arquivo, mostrou estes máximos: material 9, centro 4, status 22, descrição 40, observação 54, LRR inteiro e quantidade entregue inteira. A previsão não datada encontrada foi `*`. O modelo usa tetos maiores (40, 10, 80 e 14 dígitos com 3 casas) para não cortar a fonte. O limite de negócio, se houver um diferente desses tetos, continua sem confirmação.

15. **Material, centro e apelido.** O plano coloca o cadastro e o apelido em `catalog`. O item crítico guarda material e centro como texto e não guarda a planta da linha. Falta decidir se isso permanece até o catálogo existir. Uma linha de `B838` traz o apelido VSMII.

16. **Quais textos de status pertencem a cada perfil.** Compras responde por estados e operações de compra. Estoque/Operação responde por rota, recebimento e entrega. A lista fechada de status continua aberta. Por isso `change_critical_status` não foi concedida. A matriz já concedida está abaixo e não inclui edição de item, exclusão nem administração de grupos.

| Operação | Administração | Compras | Estoque/Operação |
|---|---|---|---|
| Consultar item, entrega e histórico | sim | sim | sim |
| Registrar entrega manual | não | não | sim |
| Alterar status | não | não | não |
| Criar ou editar item crítico | não | não | não |
| Consultar, criar e editar usuário | sim | não | não |
| Excluir usuário ou alterar grupo | não | não | não |

A conta superusuária existente continua fora dos grupos. O superusuário do Django não passa por essa matriz.

## Histórico que não volta para a primeira versão

A leitura de `LRR BR 22.10.xlsx` deixou perguntas próprias: limiar do `STATUS SCM`, origem das colunas de estoque sem fórmula, depósitos `2N03`/`2N04` diante das colunas `2N01`/`2R01`, totais vazios de `Planilha1`, recorte dos 37 centros e códigos de material como `094588C`.

Essas perguntas ficam arquivadas com a investigação. Elas só seriam reabertas se a decisão 10 autorizar essa planilha numa fase futura.

## Efeito prático

A preparação da carga inicial da aba `Base` está em `docs/PREPARACAO_IMPORTACAO.md`; ela não gravou estoque ou linhas SQVI/LRR. A integração complementar está registrada em `docs/INTEGRACAO_ABAS_COMPLEMENTARES.md`. Ainda não dá para calcular recebimento, saldo pendente, estoque consolidado de grupos bloqueados, nem completar lacuna com `LRR BR 22.10.xlsx`.
