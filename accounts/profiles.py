"""Perfis iniciais da equipe.

Administração consulta os itens e administra contas, sem apagar usuários.
Compras consulta os itens. Estoque/Operação consulta e registra entregas.
A alteração de status permanece sem concessão até a lista de cada perfil
ser confirmada. O recorte por centro continua pendente.
"""

PROFILE_ADMINISTRATION = "Administração"
PROFILE_PURCHASING = "Compras"
PROFILE_STOCK = "Estoque/Operação"

PROFILES = (
    PROFILE_ADMINISTRATION,
    PROFILE_PURCHASING,
    PROFILE_STOCK,
)
