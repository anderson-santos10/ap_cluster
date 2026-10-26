# Plano técnico — AP Cluster

Etapa atual: a aba `Base` foi importada em 23 out 2026. Em 24 out 2026 foram integradas as correspondências exatas das abas `Est. Parq.`, `SQVI` e `LRR`: 127 posições de estoque, 40 linhas SQVI e 72 linhas LRR. O PostgreSQL local `apcluster` contém 96 itens, 62 entregas e 0 históricos. As páginas são `/painel/estoque/`, `/fontes/sqvi/` e `/fontes/lrr/`. Detalhes em `docs/INTEGRACAO_ABAS_COMPLEMENTARES.md` e `docs/MAPA_RELACOES_EXCEL.md`.

## Estado do projeto

| Item | Situação |
|---|---|
| Raiz | `C:\Users\Anderson\Documents\PROJETOS\CZC` |
| Git | A pasta não é um repositório |
| Código | Projeto Django em `config`, com `accounts` e `criticals` |
| Ambiente | Windows, neste computador, servidor de desenvolvimento local |
| Banco | PostgreSQL 18.6 local em loopback:5432; `apcluster`; 96 itens, 62 entregas, 0 históricos, 127 posições, 40 linhas SQVI e 72 linhas LRR |
| Usuário | `auth.User`; matriz restrita nos três grupos; alteração de status sem concessão; conta superusuária fora dos grupos |
| Hospedagem | Não definida; nuvem fica para depois da validação local |
| Fonte da primeira versão | `C:\Users\Anderson\Documents\PROJETOS\CZC\Criticos Ap Cluster.xlsx` |
| Fora desta versão | `LRR BR 22.10.xlsx`, na raiz do projeto |
| Documentação | Esta pasta `docs` |

O AP Cluster permanece independente de SGS-Gelosar. A planilha aprovada está na raiz do projeto, no caminho oficial confirmado em 24 out 2026. O conteúdo identificado pelo SHA-256 anterior não foi alterado.

## Ambiente e acesso

O desenvolvimento e os testes ocorrem no Windows, neste computador. A aplicação será aberta no navegador local, pelo servidor de desenvolvimento do Django. Rodar localmente não publica o sistema na internet nem o torna disponível para outros computadores. Acesso compartilhado em rede, se for necessário, será avaliado à parte.

Não há hospedagem em nuvem nesta etapa. Não serão criados serviços no Railway, no Render nem em outra plataforma. A hospedagem definitiva fica para uma etapa futura, depois que a aplicação local estiver validada.

O PostgreSQL 18.6 local está em uso somente em `localhost:5432`, no banco `apcluster`. Não há conexão com Railway, Render ou outro servidor.

A equipe usará contas individuais, cada pessoa com o próprio usuário e senha. As páginas internas exigem autenticação, e a sessão pode ser encerrada. A permissão é verificada no servidor; ocultar um botão não substitui essa verificação.

Os perfis previstos separam Administração, Compras e Estoque/Operação.

| Perfil | Responsabilidade prevista |
|---|---|
| Administração | Consulta operacional e administração de usuários, sem exclusão nem alteração de grupos |
| Compras | Consulta de itens, entregas e histórico |
| Estoque/Operação | Consulta e registro de entrega manual |

A alteração de status permanece bloqueada para os três perfis. O acesso por centro SAP continua pendente. A conta real existente não teve senha nem grupos alterados.

Alteração de status, revisão de estoque e registro de entrega guardam quem realizou a operação. Esse histórico distingue o autor; não depende de a aplicação estar publicada fora da máquina local.

## Escopo inicial

A primeira versão parte exclusivamente de `Criticos Ap Cluster.xlsx`. A arquitetura atende primeiro ao que essa planilha efetivamente traz:

- item crítico da `Base`;
- centro SAP, na coluna Parque, com o apelido da coluna Planta;
- estoque associado ao item, a partir das posições de `Est. Parq.`;
- pedidos e transferências do `SQVI`, tipos UB e NB;
- previsão, status operacional e observação;
- histórico de entregas, com quantidade e data por evento.

A `Base` hoje tem uma quantidade e uma data por item. O modelo precisa permitir várias entregas, como a regra confirmada determina. Isso é estrutura do sistema, não uma segunda fonte de dados.

Nem todo campo pode ser calculado ou importado sem validar a coluna. Estoque Parque, Ok/Nok e Quant. PO são fórmulas, e a de Quant. PO está desalinhada. Recebimento e saldo pendente continuam fora de cálculo. LRR vazio, quantidade negativa, descrição divergente e grupo de estoque duplicado seguem as regras confirmadas, sem correção silenciosa.

`Din` e `Grafico` são apresentação da `Base`, não fontes adicionais integradas. Os quatro gráficos da aba `Grafico` são apresentados pelo painel Django, com cálculos sobre dados do banco; o cache e as tabelas dinâmicas do Excel não são usados como dados de produção. O inventário e o mapa das relações estão em `docs/PLANO_PAINEL.md` e `docs/MAPA_RELACOES_EXCEL.md`.

`LRR BR 22.10.xlsx` não é lido, cruzado nem importado nesta fase. O parâmetro MRP usado no desenho inicial é o da aba `LRR` da planilha aprovada, não o do arquivo excluído.

## Arquitetura recomendada

Seis aplicativos, criados só quando o desenvolvimento for autorizado.

| Aplicativo | Responsabilidade na primeira versão | Por que existe |
|---|---|---|
| `accounts` | Login, encerramento de sessão, proteção das páginas internas e permissões de servidor | Administração, Compras e Estoque/Operação usam contas individuais |
| `catalog` | Material e centro SAP, com apelido | Parque e GP são a chave do item crítico |
| `criticals` | Item crítico, LRR informado, previsão, status, observação e entregas | É o conteúdo operacional da `Base` |
| `inventory` | Posições de utilização livre ligadas ao item e consolidação com bloqueio | `Est. Parq.` tem depósito, lote e quatro quantidades |
| `procurement` | Documento UB ou NB e item, sem saldo pendente | `SQVI` é a fonte documental |
| `imports` | Leitura, validação, prévia, confirmação e rastreabilidade | A carga precisa ser revisada antes de gravar |

### Dependências

```text
accounts
catalog
    <- inventory
    <- procurement
    <- criticals
imports -> accounts, catalog, inventory, procurement, criticals
```

- `catalog` identifica o centro pelo código SAP.
- `inventory` e `procurement` referenciam material e centro.
- `criticals` guarda os campos operacionais e pode ler estoque e documentos. Não grava recebimento nem saldo pendente. Status e entrega registram o usuário que alterou.
- `inventory` registra o usuário da revisão de estoque. Grupo bloqueado por duplicidade continua sem liberação automática.
- `imports` lê a planilha aprovada sem alterar o arquivo. Só grava depois da confirmação e preserva status, previsão, observação, entregas e o fato de o LRR original estar em branco.

Painel e auditoria ficam como telas nesta fase. Não há aplicativo só para eles.

### Fora até nova decisão

- Recebimento e saldo pendente.
- Liberação de grupo de estoque bloqueado por duplicidade.
- Escolha automática de descrição.
- Permissão restrita por centro SAP.
- Hospedagem definitiva e acesso da aplicação a partir de outros computadores.
- Lista fechada de status além do que for confirmado, com preservação de `Roteiro setembro` quando existir.
- Qualquer dado de `LRR BR 22.10.xlsx`, inclusive `STATUS SCM`.

## Telas operacionais

Login em `/contas/entrar/`, encerramento de sessão por POST e página inicial autenticada. A lista de itens fica em `/itens/`, com filtro por material, descrição, centro e status, paginação, estado vazio e indicação visual de status. O detalhe separa mês esperado, data real de entrega, valor literal, LRR ausente e saldo desconhecido. A entrega manual e a alteração de status têm formulários próprios; a segunda responde 403 enquanto a permissão não for concedida. `/itens/inconsistencias/` lista espaço preservado, colisão normalizada, previsão literal, quantidade negativa e data ausente.

O dashboard de estoque consulta posições da aba `Est. Parq.` sem somar posições repetidas. `/fontes/sqvi/` e `/fontes/lrr/` exibem as linhas de origem ligadas por material + centro exatos, em leitura somente, com filtros e paginação. SQVI não é tratado como recebimento e LRR não substitui o LRR operacional do item.

## Validação e carga futura

```text
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py showmigrations
.\.venv\Scripts\python.exe manage.py migrate --check
.\.venv\Scripts\python.exe manage.py prevalidar_base
.\.venv\Scripts\python.exe manage.py importar_base
.\.venv\Scripts\python.exe manage.py test criticals.tests accounts.tests.test_authentication --settings=config.settings.testing
```

`prevalidar_base` lê só a aba `Base`, confirma o PostgreSQL local e não grava. `importar_base` continua recusando a execução sem autorização explícita. A carga de 23 out 2026 usou essa autorização depois da pré-validação. Uma nova leitura reconhece as 96 linhas e as 62 entregas e não as atualiza.

## Fluxo futuro de importação

1. Ler `Criticos Ap Cluster.xlsx` sem alterar a origem.
2. Validar abas, cabeçalhos e tipos, reconhecendo cabeçalho com espaço e coluna repetida pela posição.
3. Mostrar a prévia.
4. Separar erro, alerta e duplicidade. Quantidade negativa, LRR vazio, material sem posição e descrição divergente aparecem como alerta.
5. Esperar confirmação explícita.
6. Gravar com usuário, instante, nome e hash.
7. Manter a origem do registro e não sobrescrever campo operacional.

A prévia mostra o cache de Quant. PO e a soma refeita de UB e NB. Gravar a soma como quantidade documental depende da validação dessa coluna. O cache desalinhado não é a fonte.

## Etapas

| Etapa | Conteúdo | Situação |
|---|---|---|
| 1 | Inspecionar `Criticos Ap Cluster.xlsx` | Leitura concluída; localização reconfirmada |
| 2 | Inspecionar `LRR BR 22.10.xlsx` | Concluída e depois excluída da primeira versão |
| 3 | Registrar a fonte aprovada, as regras e as pendências | Concluída |
| 3b | Registrar ambiente local, contas individuais e perfis | Concluída nesta atualização |
| 4 | Criar o projeto Django e a migração de autenticação | Aplicada em `apcluster` |
| 5 | Modelar item crítico, posições e linhas de fonte vinculadas | Implementado em `criticals`; sem catálogo mestre e sem cálculos de compra |
| 6 | Prévia da planilha aprovada | Repetida imediatamente antes da carga; 96 linhas e 62 entregas |
| 7 | Telas e permissões | Painéis, fontes SQVI/LRR, autenticação e permissões de leitura existentes; alteração de status continua sem concessão |
| 8 | Carga da aba `Base` | Executada em 23 out 2026; 96 itens, 62 entregas, 0 atualizações |
| 9 | Integração de `Est. Parq.`, `SQVI` e `LRR` | Executada em 24 out 2026; somente correspondências exatas: 127, 40 e 72 linhas |

A etapa 4 não inclui `migrate`, criação de tabelas, importação, configuração de PostgreSQL, hospedagem, criação de usuários, cópia da planilha, repositório Git nem commit.

## Stack prevista

Python e Django no Windows, com HTML, CSS e JavaScript separados. PEP 8. O banco em uso é o PostgreSQL local `apcluster`. O acesso desta fase é o navegador do próprio computador, pelo servidor de desenvolvimento.

## Segurança desta atualização

As migrações aditivas de `criticals` e `accounts` foram aplicadas no `apcluster` local. A aba `Base` foi importada em 23 out 2026. Não houve hospedagem, alteração de senha, associação da conta existente a um grupo, alteração da planilha, commit ou push.
