"""Cria a tabela de equipamentos.

Revision ID: 0001
Revises:
Create Date: 2026-10-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "equipamentos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("tipo", sa.String(length=80), nullable=False),
        sa.Column("patrimonio", sa.String(length=60), nullable=True),
        sa.Column("marca", sa.String(length=100), nullable=True),
        sa.Column("modelo", sa.String(length=100), nullable=True),
        sa.Column("setor", sa.String(length=100), nullable=True),
        sa.Column(
            "status",
            sa.String(length=40),
            server_default="Disponível",
            nullable=False,
        ),
        sa.Column("observacao", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sqlite_autoincrement=True,
    )
    op.create_index("ix_equipamentos_tipo", "equipamentos", ["tipo"])
    op.create_index(
        "ix_equipamentos_patrimonio",
        "equipamentos",
        ["patrimonio"],
        unique=True,
    )
    op.create_index("ix_equipamentos_setor", "equipamentos", ["setor"])
    op.create_index("ix_equipamentos_status", "equipamentos", ["status"])


def downgrade() -> None:
    op.drop_index("ix_equipamentos_status", table_name="equipamentos")
    op.drop_index("ix_equipamentos_setor", table_name="equipamentos")
    op.drop_index("ix_equipamentos_patrimonio", table_name="equipamentos")
    op.drop_index("ix_equipamentos_tipo", table_name="equipamentos")
    op.drop_table("equipamentos")
