# Roadmap geral — AP Cluster

Auditoria de 23 de outubro de 2026. Só leitura. Nenhum código, dado, permissão ou planilha foi modificado.

A planilha lida foi `C:\Users\Anderson\Documents\PROJETOS\CZC\Criticos Ap Cluster.xlsx`, sem gravação. O SHA-256 permaneceu `777ede653828560abec0640dcd409a6bed051ebe39614dd29e0bce7ddcff5d06` (679.994 bytes). `LRR BR 22.10.xlsx` não foi aberto.

## 1. Resumo executivo

A primeira versão operacional da `Base` está no ar no PostgreSQL local: 96 itens, 62 entregas e nenhum histórico de status. Login, lista, detalhe, filtros, entrega manual, painel, busca e a matriz de permissão existem. A alteração de status continua sem concessão.

Em 24 out 2026 o detalhe passou a listar posições de estoque. A tabela existe e está vazia. Os quatro gráficos da planilha continuam sendo o `/painel/`, sem segunda cópia. `SQVI`, `LRR` e `Din` não viraram tela. A carga real de `Est. Parq.` continua sem autorização.

`GP069610 ` / `B865` não corresponde ao código sem espaço. A aba `LRR` tem o código sem espaço nesse centro; essa linha não preenche o LRR vazio da `Base`.

## 2. Escopo da primeira versão

Entra:

- contas individuais, três perfis e a matriz já concedida;
- itens críticos da aba `Base`, com material e centro exatos;
- entregas, inclusive quantidade negativa e data ausente;
- histórico de status, quando uma alteração for permitida;
- lista, filtros, paginação, detalhe e inconsistências;
- painel somente leitura;
- busca global de itens e entregas;
- posições de `Est. Parq.` ligadas aos 96 itens, na forma aprovada em `docs/ANALISE_ESTOQUE.md`.

Não entra, enquanto a decisão correspondente não mudar:

- recebimento, saldo pendente e documentos do `SQVI`;
- Ok/Nok, alerta de falta e saldo projetado;
- soma ou liberação dos 43 grupos repetidos;
- troca da descrição do item pela do estoque;
- permissão por centro, catálogo de apelidos e novas contas reais;
- abas `LRR`, `Din` e `Grafico` como tabelas importadas;
- qualquer dado de `LRR BR 22.10.xlsx`;
- hospedagem e acesso fora deste computador.

## 3. Estado atual comprovado

Leitura somente do `apcluster`, em transação marcada como somente leitura e desfeita:

| Medida | Valor |
| --- | --- |
| Itens | 96, sem par material + centro repetido |
| Entregas | 62, das quais 26 negativas e 5 sem data |
| Histórico de status | 0 |
| Contas | 1, ativa, equipe e superusuária, em nenhum grupo |
| Grupos | Administração, Compras, Estoque/Operação |
| `change_critical_status` | a permissão existe e nenhum usuário ou grupo a possui |
| Itens com espaço na borda do material | 1 |
| Previsão original preenchida | 1 |
| Migrações de `accounts` e `criticals` | as cinco existentes estão aplicadas |

A planilha, na mesma auditoria: abas `Base`, `Grafico`, `SQVI`, `LRR`, `Est. Parq.` e `Din`. `Base` tem 96 pares únicos, os mesmos sete status já documentados, 62 quantidades entregues, 26 negativas, um `*` e uma fórmula na coluna A das 96 linhas. `Est. Parq.` tem 327 linhas, fórmula na coluna A das 327, 74 itens com par exato e 43 grupos repetidos na chave material + centro + depósito + lote.

`manage.py check` não apontou problema.

## 4. Inventário

| Funcionalidade | Estado | Onde está | Testes nesta auditoria |
| --- | --- | --- | --- |
| Autenticação e sessão | Concluída e validada | `/contas/entrar/`, `/contas/sair/`, `/` | Cliente HTTP isolado aprovado. A asserção do motor PostgreSQL não foi reexecutada |
| Matriz de permissão | Concluída e validada | `accounts/migrations/0002_permissoes_iniciais.py` | Conferida no banco: os três grupos têm só os códigos previstos |
| Itens, filtros e paginação | Concluída e validada | `/itens/`, `CriticalItem` | `criticals.tests.test_views` incluído na suíte aprovada |
| Detalhe do item | Concluída e validada | `/itens/<id>/` | Coberto pela suíte. O saldo continua a frase de desconhecido |
| Entrega manual | Concluída e validada | `/itens/<id>/entregas/nova/`, permissão `add_delivery` | Suíte isolada. Não foi criada entrega no `apcluster` |
| Histórico e troca de status | Bloqueada | `/itens/<id>/status/`, `StatusChange` | A tela responde 403 sem a permissão. A lista de status por perfil não existe |
| Inconsistências | Concluída e validada | `/itens/inconsistencias/` | Suíte isolada |
| Painel | Concluída e validada | `/painel/`, `criticals/panel.py` | `test_panel` aprovado. O navegador não foi reaberto nesta auditoria |
| Busca global | Concluída e validada | `/busca/`, `criticals/search.py` | `test_search` aprovado. O navegador não foi reaberto nesta auditoria |
| Carga da `Base` | Concluída e validada | `importar_base`, `prevalidar_base` | Contagens do banco iguais às da planilha. O comando continua recusando sem autorização |
| Estoque | Pendente | Não há modelo nem rota | Planejado em `docs/ANALISE_ESTOQUE.md`. Nada foi codificado |
| Administração de usuários | Parcial | admin do Django e `criar_conta` | Não há tela própria. Contas reais dependem da lista de integrantes |
| Layout responsivo | Parcial | `static/css/app.css` | O painel já foi medido antes. Esta auditoria não repetiu o navegador nem a tabela de estoque, que ainda não existe |
| `SQVI`, `LRR`, `Din`, `Grafico` | Fora do escopo da primeira versão | Só na planilha | Caches e fórmulas não são fonte de saldo, recebimento ou Ok/Nok |

A busca consulta itens e entregas dentro de `view_criticalitem` e, para entregas, também `view_delivery`. Não consulta estoque, histórico nem contas. O painel agrega os itens já gravados e não lê `Est. Parq.`.

## 5. Planilha, documentação e código

Fatos reconfirmados no arquivo nesta auditoria: 6 abas, 96 linhas na `Base`, 62 quantidades, 26 negativas, um asterisco, um material com espaço na borda, 327 posições, 74 pares exatos e 43 grupos repetidos. O hash não mudou.

Fatos já registrados e compatíveis com o banco: status, entregas sem data, previsão literal, espaço preservado e ausência de histórico.

Hipóteses que continuam sem confirmação: lote como tipo de avaliação; significado de `*` e da quantidade negativa; significado da casa decimal em `PC`. Nenhuma delas autoriza conversão.

A documentação atrasada em dois pontos, sem efeito no código atual:

- `docs/ANALISE_PLANILHA.md` foi corrigido para 74 correspondências exatas. O espaço final de `GP069610 ` / `B865` permanece sem ligação.
- `docs/PLANO_TECNICO.md` descreve as telas sem citar `/painel/` e `/busca/`, que já existem.

`docs/ANALISE_ESTOQUE.md`, `docs/REGRAS_DE_NEGOCIO.md` e `docs/DECISOES_PENDENTES.md` já registram a regra exata e o planejamento da primeira integração. Eles prevalecem sobre o número 75.

## 6. Problemas concretos

Não há correção de código obrigatória. Não há divergência entre as 96 linhas da `Base` e o banco.

A frase dos 75 itens foi corrigida em `docs/ANALISE_PLANILHA.md`. Uma carga que ainda removesse o espaço ligaria `GP069610 ` / `B865` ao código errado.

## 7. Pendências

- Posições de estoque no detalhe, com as quatro quantidades separadas, grupo repetido sinalizado e sem total.
- Pré-validação e comando de carga de `Est. Parq.`, recusando sem autorização explícita.
- Carga real dessa aba, só depois de nova autorização.
- Troca de status, depois da lista de textos por perfil.
- Contas reais, depois da lista de integrantes.
- Atualizar o plano técnico para as telas que já existem, quando o estoque também estiver fechado.

## 8. Roadmap

Não há fase de correção de código. Deploy e nuvem ficam de fora.

### Fase 0 — Documentação que muda a carga

| ID | Tarefa | Prioridade | Estimativa |
| --- | --- | --- | --- |
| AP-001 | Trocar, em `docs/ANALISE_PLANILHA.md`, a frase de 75 itens com posição pela contagem exata de 74, explicando o espaço de `GP069610 ` | Alta | Concluída em 24 out 2026 |

Objetivo: impedir que a carga futura trate ausência de par exato como estoque. Estado: concluída. O documento registra 74 correspondências exatas e mantém `GP069610 ` / `B865` sem herdar o código sem espaço. Não tocou banco nem planilha.

### Fase 1 — Estabilidade

Nenhuma tarefa. A suíte isolada passou e as contagens fecham com a `Base`.

### Fase 2 — Funções principais

Nenhuma tarefa de construção. Lista, detalhe, entrega, painel e busca já atendem as regras confirmadas. A troca de status permanece bloqueada de propósito.

### Fase 3 — Estoque

A regra de implementação é a da seção 6 de `docs/ANALISE_ESTOQUE.md`. Dados sintéticos nos testes. A planilha real só entra na AP-021.

| ID | Tarefa | Prioridade | Estimativa | Depende de |
| --- | --- | --- | --- | --- |
| AP-010 | Modelo da posição em `criticals`. Concluída em 24 out 2026: tabela criada, zero posições, nenhuma permissão concedida aos grupos | Alta | concluída | AP-001 |
| AP-011 | Pré-validação somente leitura de `Est. Parq.`: 74 pares, 22 sem par, 43 grupos, cinco divergências de descrição, sem abrir carga | Alta | 0,5 a 1 dia | AP-001 |
| AP-012 | Comando de carga que recusa sem autorização explícita, não atualiza o item e não duplica a mesma linha de origem | Alta | 0,5 a 1 dia | AP-010, AP-011 |
| AP-013 | Tabela no detalhe. Concluída em 24 out 2026, com estado desconhecido enquanto não houver carga | Alta | concluída | AP-010 |
| AP-014 | Testes sintéticos da listagem. Concluída em 24 out 2026 no banco isolado | Alta | concluída | AP-010, AP-013 |

Arquivos prováveis: `criticals/models.py`, uma migração nova só nessa etapa, `criticals/stock.py`, `criticals/management/commands/importar_estoque.py`, `criticals/views.py`, `templates/criticals/item_detail.html`, `criticals/tests/test_stock.py` e, se precisar, `static/css/app.css`. Lista, filtros, painel e busca não mudam.

Aceite de AP-010 a AP-014: os critérios de `docs/ANALISE_ESTOQUE.md` passam em banco isolado; o `apcluster` ainda não recebeu posição, a menos que a AP-021 tenha sido autorizada à parte.

Risco: migrar o modelo no `apcluster` é alteração de esquema. Só acontece dentro da tarefa autorizada, depois de revisar o SQL, e não nesta auditoria.

### Fase 4 — Validação

| ID | Tarefa | Prioridade | Estimativa | Depende de |
| --- | --- | --- | --- | --- |
| AP-020 | Repetir a suíte isolada e percorrer no navegador, com sessão sintética, lista, detalhe, painel, busca e a tabela de estoque | Alta | 0,5 dia | AP-013, AP-014 |
| AP-021 | Carga real de `Est. Parq.`, somente com autorização explícita, depois da pré-validação mostrar 74, 22 e 43 | Alta | 0,5 dia | AP-012 e autorização |

AP-021 não começa junto com o código. Sem a autorização, o comando tem de recusar antes de abrir o arquivo.

### Fase 5 — Uso da tabela nova

| ID | Tarefa | Prioridade | Estimativa | Depende de |
| --- | --- | --- | --- | --- |
| AP-030 | Conferir a tabela de estoque em largura de mesa e em 390 px, sem sobrepor quantidade e rótulo | Média | 0,5 dia | AP-013 |

### Fase 6 — Fechamento

| ID | Tarefa | Prioridade | Estimativa | Depende de |
| --- | --- | --- | --- | --- |
| AP-040 | Atualizar `docs/PLANO_TECNICO.md` com painel, busca e o comportamento real do estoque, e marcar a checklist da seção 11 | Média | 0,5 dia | AP-020 |

Prioridades em aberto: 4 altas (AP-011, AP-012, AP-020, AP-021) e 2 médias (AP-030, AP-040). AP-001, AP-010, AP-013 e AP-014 estão concluídas. Nenhuma crítica e nenhuma baixa. As faixas de esforço são estimativa, não prazo.

## 9. Dependências e bloqueios

AP-010, AP-013 e AP-014 já foram feitas. AP-011 ainda pode anteceder o comando. AP-012 espera a pré-validação. AP-020 percorre a suíte e o navegador. AP-021 espera autorização humana além do código.

Bloqueios que não geram tarefa agora:

- liberar os 43 grupos e mostrar soma dos 55 itens de grupos únicos;
- a palavra “vazio” para depósito ou lote vazio;
- qual descrição substitui a outra;
- significado de lote, de `*` e da casa decimal em `PC`;
- se uma segunda carga de estoque pode atualizar quantidade;
- quais textos de status pertencem a Compras e a Estoque/Operação;
- recebimento no `SQVI` e saldo pendente;
- permissão por centro e lista de integrantes.

## 10. Critérios de aceite da primeira versão

- Os 96 itens e as 62 entregas continuam consultáveis, com o espaço do material preservado.
- Filtro de status exato, paginação, painel e busca seguem como estão.
- Entrega manual continua só para quem tem `add_delivery`. Quantidade negativa não é corrigida.
- Troca de status continua 403 até a decisão do perfil e a concessão da permissão.
- Estoque só liga material e centro exatos. Os 22 sem par ficam desconhecidos, não zero.
- Os 43 grupos aparecem sinalizados e sem total. `PC` decimal permanece sinalizado.
- A descrição do item não é substituída. As quatro quantidades não são somadas entre si.
- Posição fora dos 96 não vira item.
- Não há saldo projetado nem importação recorrente.
- A suíte isolada passa. A conta real, os grupos e as permissões não são alterados para fazer o teste passar.

## 11. Checklist de conclusão

Obrigatório:

- [x] Login, logout e páginas internas protegidas.
- [x] Três perfis com a matriz restrita, conferida no banco.
- [x] 96 itens e 62 entregas iguais à `Base`.
- [x] Lista, detalhe, filtros, paginação e inconsistências.
- [x] Painel e busca global cobertos por teste.
- [x] Estoque no detalhe, com as regras exatas. A tabela local está vazia até a AP-021.
- [ ] Pré-validação e comando de estoque que recusa sozinho.
- [ ] Carga real de `Est. Parq.` somente se for autorizada, sem mudar item, entrega ou histórico.
- [ ] Suíte isolada e passagem no navegador depois do estoque.
- [x] `docs/ANALISE_PLANILHA.md` sem a contagem que remove espaço.
- [ ] `docs/PLANO_TECNICO.md` alinhado às telas existentes.
- [x] Limitações de recebimento, Ok/Nok, status por perfil e hospedagem registradas.

Melhoria futura, fora deste fechamento: catálogo de centros, `SQVI`, soma dos grupos únicos, liberação dos 43 grupos e contas da equipe. Os quatro gráficos já estão no painel.

## 12. Riscos e fora do escopo

- Somar o par `1946.9` e `1117.9`, ou ligar o código sem espaço, publica saldo do item errado.
- Tratar o zero do `VLOOKUP` como saldo esconde os 22 itens sem par.
- Rodar teste de `accounts.tests.test_access` com o ajuste de banco isolado falha de propósito. Rodá-lo no ajuste local compara a senha do ambiente; por isso não foi executado aqui.
- Fora do escopo: nuvem, rede, `LRR BR 22.10.xlsx`, recebimento e saldo pendente.

## 13. Comandos executados

```text
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py showmigrations accounts criticals
.\.venv\Scripts\python.exe manage.py test criticals accounts.tests.test_authentication --settings=config.settings.testing
```

`check`: nenhum problema. Migrações de `accounts` e `criticals`: todas aplicadas. Testes: 82 aprovados, 1 ignorado, 0 falhos. O ignorado é o teste que só avisa para usar o banco isolado. O banco de teste foi o SQLite em memória de `config.settings.testing`. O `apcluster` não foi usado como banco de teste.

A planilha e o `apcluster` foram lidos por um script temporário, em transação somente leitura, apagado ao fim. Não houve `migrate`, `importar_base` nem `importar_estoque` nessa auditoria. Em 24 out 2026, numa etapa posterior, `criticals.0004_stock_position` foi aplicada. O SQL só criou a tabela de posições. Nenhuma posição foi importada.

## 14. Limitações da auditoria

- O navegador não foi aberto. Painel, busca e layout não foram revistos visualmente nesta tarefa.
- `accounts.tests.test_access` não rodou, para não comparar nem exibir a senha do PostgreSQL.
- `SQVI`, `LRR`, `Din` e `Grafico` não foram reprocessados linha a linha. A estrutura e os riscos usados aqui vêm da leitura já documentada, mais a conferência das abas, da `Base` e de `Est. Parq.`.
- Não foi conferido o hash de cada uma das 327 posições além das contagens e da chave repetida.

## 15. Próxima tarefa

AP-011 e AP-012. A listagem já existe e o banco local continua sem posição. A carga real continua sem autorização.
