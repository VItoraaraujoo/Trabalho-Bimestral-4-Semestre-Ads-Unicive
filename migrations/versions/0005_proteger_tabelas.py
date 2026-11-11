"""Ativa proteção por linha nas tabelas do sistema no Supabase.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-20
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABELAS = (
    "equipamentos",
    "usuarios",
    "funcionarios",
    "alocacoes",
    "manutencoes",
    "sistemas_funcionarios",
)


def upgrade() -> None:
    # A API usa o banco diretamente pelo servidor. Sem políticas públicas,
    # os clientes precisam passar pela autenticação do FastAPI.
    if op.get_bind().dialect.name == "postgresql":
        for tabela in TABELAS:
            op.execute(f"ALTER TABLE public.{tabela} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        for tabela in reversed(TABELAS):
            op.execute(f"ALTER TABLE public.{tabela} DISABLE ROW LEVEL SECURITY")
