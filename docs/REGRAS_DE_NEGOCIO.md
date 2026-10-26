# Regras de negócio — AP Cluster

Há três níveis neste documento.

- **Confirmada:** decisão recebida para o produto. Orienta o desenho. Vira código só quando a etapa correspondente for autorizada.
- **Observada:** fato lido na fonte aprovada, `Criticos Ap Cluster.xlsx`. Não fecha uma regra por si só.
- **Hipótese:** leitura possível, ainda sem confirmação.

A escolha dessa planilha como fonte única da primeira versão não responde às dúvidas ainda abertas. Elas continuam em `docs/DECISOES_PENDENTES.md`.

A investigação de `LRR BR 22.10.xlsx` não fornece regra para esta versão. O registro dela está no final de `docs/ANALISE_PLANILHA.md`.

## Confirmadas

### Estoque e materiais

- O código SAP do centro é o identificador principal do centro.
- O estoque disponível considera somente posições de utilização livre.
- O estoque consolidado soma posições válidas por material e centro.
- Duplicidade ou conflito em um grupo bloqueia o cálculo daquele grupo até a revisão.
- Registros duplicados não são excluídos nem somados às cegas.
- Material ausente do extrato de estoque fica com saldo desconhecido. A ausência não vira zero.
- LRR vazio entra como zero no cálculo, e o sistema conserva a informação de que o valor original estava em branco.
- Divergência de descrição é registrada para investigação. Nenhuma das descrições é escolhida em silêncio como a correta.
- A primeira integração de estoque, quando o código for autorizado, limita-se aos 96 itens críticos já importados da `Base`.
- A posição só se liga ao item pelo material e pelo centro exatos. Espaço não é removido e o código não é normalizado.
- Lote, depósito e posições repetidas permanecem separados. Depósito ou lote vazio continua fazendo parte da chave.
- Os 43 grupos repetidos na chave material + centro + depósito + lote são sinalizados. As quantidades desses grupos não são somadas automaticamente.
- Quantidade e unidade originais permanecem, inclusive casa decimal em `PC`. Casa decimal em `PC` é sinalizada para revisão, sem conversão.
- A descrição gravada no item crítico permanece. A descrição diferente do estoque é sinalizada, não substitui o item.
- Utilização livre, trânsito, controle de qualidade e bloqueado aparecem em separado.
- Posição sem correspondência exata é estoque desconhecido, não zero.
- Posição que não corresponda a um dos 96 itens fica fora dessa integração.
- Essa versão não calcula saldo projetado e não cria importação automática recorrente.

### Pedidos e recebimentos

- A quantidade documental de pedidos considera documentos UB e NB.
- O modo confiável de identificar recebimento continua pendente.
- Saldo pendente não é calculado nem apresentado como confiável antes de validar o vínculo entre pedido, item e recebimento.
- Quantidade entregue negativa é preservada e sinalizada para revisão, sem correção automática. No modelo, a sinalização é `Delivery.requires_review`.

### Previsão, status e entrega

- Previsão no primeiro dia do mês representa o mês esperado de chegada, não uma data exata.
- Um item crítico pode ter várias entregas, cada uma com quantidade e data próprias.
- O status legado `Roteiro setembro` permanece no histórico. Não é convertido nem excluído automaticamente.
- A alteração de status se divide entre Compras e Estoque/Operação.
- Reimportar dados de origem não sobrescreve informação operacional mantida manualmente.

### Fonte da primeira versão

- A primeira versão utiliza somente `C:\Users\Anderson\Documents\PROJETOS\CZC\Criticos Ap Cluster.xlsx`.
- A primeira carga utiliza somente a aba `Base`. Estoque, `SQVI` e a aba `LRR` ficam fora dessa carga.
- A entrega importada é reconhecida pela fonte e pela linha original da `Base`. Material e centro continuam sendo a chave do item. Reordenar a planilha desloca essa identidade.
- `LRR BR 22.10.xlsx` fica fora da carga, do cruzamento e da importação desta fase.

### Ambiente e acesso

- O desenvolvimento e os testes são locais, no Windows, pelo servidor de desenvolvimento do Django e pelo navegador deste computador.
- A hospedagem definitiva fica para depois da validação local. Nesta etapa não há serviço em nuvem.
- O PostgreSQL 18.6 está instalado neste computador, escuta só em localhost, e a primeira migração do banco `apcluster` já foi aplicada.
- Cada integrante terá usuário e senha próprios, no modelo padrão do Django. As páginas internas exigem sessão autenticada, e a sessão pode ser encerrada.
- A permissão é verificada no servidor. Ocultar uma ação na tela não substitui essa verificação.
- Administração consulta itens, entregas e histórico, e pode consultar, criar e editar usuários. Não exclui usuários nem altera grupos.
- Compras consulta itens, entregas e histórico. Não registra entrega nem altera status.
- Estoque/Operação consulta os mesmos registros e registra entrega manual, inclusive quantidade negativa e data ausente. Não altera status.
- A alteração de status existe na aplicação, exige `change_critical_status` e não está concedida a nenhum grupo. A lista de status de cada perfil continua pendente.
- A reimportação da aba `Base` só relata diferença. Ela não atualiza campos descritivos ou operacionais, não apaga histórico e não altera entrega manual.
- O código do material é guardado como veio. Espaço no início ou no fim não une registros. A comparação sem espaços serve apenas para alerta.
- O valor literal `*` permanece fora da data de previsão. Seu significado comercial continua pendente.
- Estoque desconhecido, zero confirmado e divergência permanecem distintos. O estoque da planilha não entra nesta carga.
- Alteração de status, revisão de estoque e registro de entrega identificam quem executou a operação.
- O acesso por centro SAP permanece pendente.
- Nenhuma conta real é criada sem a lista de integrantes, logins e perfis. Não há cadastro público.
- O uso local não abre a aplicação para a internet nem para outros computadores. Acesso em rede, se necessário, será decidido à parte.

## Observadas na fonte aprovada

- Na `Base`, material + parque é único. Parque é o código do centro, como `B856`. Planta é o apelido, como VSMI.
- A fórmula de Estoque Parque usa a primeira utilização livre e devolve 0 quando não encontra o par. Isso convive com a regra confirmada, que trata a ausência como desconhecido e soma só posições válidas.
- A fórmula de Ok/Nok subtrai o LRR e trata vazio como zero, sem guardar que o original estava em branco. A regra confirmada pede as duas coisas: usar zero na conta e preservar o branco.
- Nas 72 linhas com LRR preenchido, o número é igual ao ponto de reabastecimento da aba `LRR` deste mesmo arquivo. Vinte e quatro linhas estão vazias.
- A quantidade documental pretendida pela planilha soma `Qtd.pedido` de UB e NB. As 96 fórmulas apontam para outra linha. Quando a soma certa difere da soma da linha apontada, o cache segue a linha apontada. Nos outros 48 itens, as duas somas são zero.
- Há 26 quantidades entregues negativas. Os 7 itens Entregue parcial são negativos. Em rota é quase todo positivo. O significado do sinal não está escrito na planilha.
- A `Base` guarda uma quantidade e uma data de entrega por item. A regra confirmada permite várias entregas.
- O status está digitado. Os valores atuais são Pendente, Em rota, Entregue, Entregue parcial, Criar RC, Sem necessidade parque e Obsoleto. `Roteiro setembro` aparece só no cache antigo dos gráficos.
- Há descrições diferentes entre a `Base` e o texto breve do estoque, e duas descrições para `GP124403` na própria `Base`.
- `Fornecimento` e quantidade de remessa misturam valor e o texto `#N/A`. Isso não identifica, sozinho, um recebimento.
- Datas do `SQVI` aparecem como data ou como número serial. `DataConf.` inclui 31 dez 9999. `OrgTransp.` e `SaídaMerc` contêm datas.

## Hipóteses ainda sem validação

- A quantidade entregue negativa representaria falta ou saldo em aberto.
- Em rota representaria quantidade a caminho, e a data seria a previsão de chegada daquela movimentação.
- `B8D1`, citado como origem na maior parte das transferências UB, seria um centro fornecedor do cluster.
- O campo Lote da posição de estoque seria tipo de avaliação, porque os códigos se repetem em `Tp.aval.` do `SQVI`.
- Os códigos de uma letra do `SQVI` e os flags `X` e `D` da aba `LRR` deste arquivo teriam um significado operacional estável.

Nenhuma dessas hipóteses autoriza cálculo, correção ou descarte de dado.
