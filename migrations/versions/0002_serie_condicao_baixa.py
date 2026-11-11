"""Adiciona série, condição e novos estados do equipamento.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("equipamentos") as tabela:
        tabela.add_column(sa.Column("numero_serie", sa.String(length=100)))
        tabela.add_column(
            sa.Column("condicao", sa.String(length=20), nullable=True)
        )

    conexao = op.get_bind()
    equipamentos_sem_patrimonio = conexao.execute(
        sa.text(
            "SELECT id FROM equipamentos "
            "WHERE patrimonio IS NULL OR trim(patrimonio) = ''"
        )
    ).fetchall()
    for equipamento in equipamentos_sem_patrimonio:
        conexao.execute(
            sa.text(
                "UPDATE equipamentos SET patrimonio = :patrimonio WHERE id = :id"
            ),
            {
                "patrimonio": f"ATI-{equipamento.id:06d}",
                "id": equipamento.id,
            },
        )

    conexao.execute(
        sa.text(
            "UPDATE equipamentos SET condicao = 'Usado' WHERE condicao IS NULL"
        )
    )
    conexao.execute(
        sa.text(
            "UPDATE equipamentos "
            "SET status = CASE "
            "WHEN status = 'Disponível' THEN 'Em estoque' "
            "WHEN status = 'Descartado' THEN 'Baixado' "
            "ELSE status END"
        )
    )

    with op.batch_alter_table("equipamentos") as tabela:
        tabela.alter_column(
            "condicao",
            existing_type=sa.String(length=20),
            nullable=False,
            server_default="Usado",
        )
        tabela.alter_column(
            "status",
            existing_type=sa.String(length=40),
            server_default="Em estoque",
            existing_nullable=False,
        )
        tabela.create_index(
            "ix_equipamentos_numero_serie", ["numero_serie"], unique=True
        )


def downgrade() -> None:
    conexao = op.get_bind()
    conexao.execute(
        sa.text(
            "UPDATE equipamentos "
            "SET status = CASE "
            "WHEN status = 'Em estoque' THEN 'Disponível' "
            "WHEN status = 'Baixado' THEN 'Descartado' "
            "ELSE status END"
        )
    )

    with op.batch_alter_table("equipamentos") as tabela:
        tabela.drop_index("ix_equipamentos_numero_serie")
        tabela.alter_column(
            "status",
            existing_type=sa.String(length=40),
            server_default="Disponível",
            existing_nullable=False,
        )
        tabela.drop_column("condicao")
        tabela.drop_column("numero_serie")
