# Integração das abas complementares — AP Cluster

## Escopo executado

Em 24 out 2026 foram integradas somente as abas `Est. Parq.`, `SQVI` e `LRR` da fonte oficial `C:\Users\Anderson\Documents\PROJETOS\CZC\Criticos Ap Cluster.xlsx`. O arquivo tinha SHA-256 `777ede653828560abec0640dcd409a6bed051ebe39614dd29e0bce7ddcff5d06`; foi lido sem salvamento.

O escopo de vínculo é limitado aos 96 itens críticos já existentes e exige material + centro exatamente iguais, incluindo espaços. Não cria itens, não normaliza códigos e não associa registros por descrição.

| Aba | Linhas de origem | Correspondências exatas gravadas | Itens vinculados | Fora do recorte |
|---|---:|---:|---:|---:|
| `Est. Parq.` | 327 | 127 posições | 74 | 200 |
| `SQVI` | 546 | 40 linhas | 28 | 506 |
| `LRR` | 1.849 | 72 linhas | 72 | 1.777 |

## Persistência e páginas

- `StockPosition` representa cada posição de estoque separadamente. Guarda material, centro, nome original do centro, depósito, descrição do depósito, lote, unidade, descrição do estoque, as quatro quantidades independentes, linha de origem e hashes. A restrição de unicidade da origem evita uma segunda posição para a mesma linha da aba.
- `LinkedSheetRow` mantém cada linha de `SQVI` ou `LRR` como valores originais em JSON, junto ao número da linha, material, centro, vínculo ao item e hashes. A restrição única é por aba + linha de origem. Fórmula e valor em cache ficam identificados como conteúdo da fonte; não são recalculados nem usados como indicador.
- `/painel/estoque/` apresenta posições por item, centro, depósito e lote; separa livre, trânsito, qualidade e bloqueado; sinaliza repetição, diferença de descrição e quantidade decimal em `PC`. Não soma posições nem calcula estoque projetado.
- `/fontes/sqvi/` e `/fontes/lrr/` apresentam as linhas vinculadas com filtros existentes por material, descrição, centro e status, paginação e detalhes dos campos originais. As páginas são somente leitura e exigem autenticação e a permissão já existente `criticals.view_criticalitem`.

Linhas SQVI/LRR sem par no recorte são contadas como fora do extrato vinculado. Isso não significa inexistência de pedido ou ausência de parâmetro. As páginas não alteram o item crítico, não definem recebimento, não calculam saldo pendente e não substituem LRR vazio por parâmetros da aba `LRR`.

## Reimportação e integridade

`integrar_abas_complementares` executa simulação por padrão. A escrita exige `--confirmar-integracao`, valida banco local, caminho e hash aprovados, cabeçalhos, contagens esperadas e conflitos de origem. Origem e linha iguais com conteúdo igual são reconhecidas; conteúdo diferente ou linha conhecida que desapareceu da fonte gera conflito. A rotina não atualiza nem exclui registros existentes. As novas linhas são gravadas em transação.

Após a execução, consultas somente leitura confirmaram 96 itens, 62 entregas, 0 históricos, 127 posições de estoque, 40 linhas SQVI, 72 linhas LRR, 1 usuário e 3 grupos. As quatro relações de material/centro armazenado versus item vinculado tiveram zero divergências. As restrições de origem não apresentaram duplicidades. Nenhum usuário, grupo ou permissão foi alterado.

Entre as 127 posições integradas há 24 grupos repetidos por material + centro + depósito + lote: 12 pares com quantidades iguais e 12 com divergência. O extrato inteiro tem 43 grupos; os demais 19 incluem linhas fora do escopo e não foram gravados. Nenhum dos 127 registros integrados tem quantidade decimal em `PC`. As 19 utilizações livres decimais de `GP131157` em `PC` pertencem a `B825`, centro sem item crítico `GP131157`; foram corretamente excluídas pela correspondência exata. O relatório sinaliza decimais quando houver posição elegível desse tipo.

## Migração

Foi criada e aplicada `criticals.0005_stockposition_center_name_and_more`, dependente de `0004_stock_position`. A migração é aditiva: acrescenta `center_name`, `deposit_description`, `source_file_sha256` e `content_sha256` a `StockPosition` e cria `LinkedSheetRow`; não remove nem reescreve registros preexistentes.

## Limites e pendências mantidas

- As 24 repetições dentro do recorte integrado permanecem linhas distintas e sinalizadas (12 iguais, 12 conflitantes); nenhuma quantidade foi consolidada. Critérios de revisão/liberação continuam pendentes. Os 43 grupos do extrato completo são mantidos como estatística da fonte, incluindo os que estão fora do recorte.
- Quantidades, valores vazios, espaços e descrições das linhas integradas são preservados. O texto do item crítico não é substituído. O recorte integrado não contém casas decimais em `PC`; o código e testes preservam e sinalizam o caso caso uma linha elegível venha a conter esse valor.
- Recebimento, saldo pendente, demanda, saldo projetado e alerta de falta não são calculados.
- O conteúdo MRP da aba `LRR` é mostrado como registro de fonte e não atualiza `CriticalItem.lrr`.
- Não foi criada carga recorrente. Mudanças na ordenação/estrutura da planilha podem alterar a identidade por número da linha; uma alteração de conteúdo conhecida é reportada como conflito.
- O arquivo `LRR BR 22.10.xlsx` não foi utilizado.

## Validação executada

- `manage.py check`: sem problemas.
- `criticals.tests.test_source_integration`: 8 testes aprovados.
- `criticals.tests`: 99 testes aprovados.
- `accounts.tests.test_authentication`: 10 aprovados, 1 ignorado.
- As páginas SQVI/LRR usam banco sintético nos testes; o painel de estoque passou pelos testes existentes. A execução real da prévia e da carga foi restrita ao PostgreSQL local confirmado.
