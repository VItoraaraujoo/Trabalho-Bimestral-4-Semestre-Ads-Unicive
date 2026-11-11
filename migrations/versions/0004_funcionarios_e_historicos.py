"""Adiciona funcionários, alocações, manutenções e sistemas usados.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "funcionarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("cpf", sa.String(length=11), nullable=False),
        sa.Column("matricula", sa.String(length=50), nullable=False),
        sa.Column("setor", sa.String(length=100), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cpf"),
        sa.UniqueConstraint("matricula"),
    )
    op.create_table(
        "alocacoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("equipamento_id", sa.Integer(), nullable=True),
        sa.Column("funcionario_id", sa.Integer(), nullable=False),
        sa.Column("patrimonio", sa.String(length=60), nullable=False),
        sa.Column("nome_equipamento", sa.String(length=150), nullable=False),
        sa.Column("nome_funcionario", sa.String(length=150), nullable=False),
        sa.Column("cpf_funcionario", sa.String(length=11), nullable=False),
        sa.Column("matricula_funcionario", sa.String(length=50), nullable=False),
        sa.Column("setor_funcionario", sa.String(length=100), nullable=False),
        sa.Column("situacao", sa.String(length=20), nullable=False),
        sa.Column("data_alocacao", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_devolucao", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observacao", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["equipamento_id"], ["equipamentos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["funcionario_id"], ["funcionarios.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_alocacoes_equipamento_aberto",
        "alocacoes",
        ["equipamento_id"],
        unique=True,
        sqlite_where=sa.text("data_devolucao IS NULL"),
        postgresql_where=sa.text("data_devolucao IS NULL"),
    )
    op.create_table(
        "manutencoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("equipamento_id", sa.Integer(), nullable=True),
        sa.Column("patrimonio", sa.String(length=60), nullable=False),
        sa.Column("nome_equipamento", sa.String(length=150), nullable=False),
        sa.Column("data", sa.DateTime(timezone=True), nullable=False),
        sa.Column("laudo", sa.String(length=2000), nullable=False),
        sa.Column("sem_conserto", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.ForeignKeyConstraint(["equipamento_id"], ["equipamentos.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sistemas_funcionarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("funcionario_id", sa.Integer(), nullable=False),
        sa.Column("nome_funcionario", sa.String(length=150), nullable=False),
        sa.Column("matricula_funcionario", sa.String(length=50), nullable=False),
        sa.Column("nome_sistema", sa.String(length=150), nullable=False),
        sa.Column("data_inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_fim", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["funcionario_id"], ["funcionarios.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("sistemas_funcionarios")
    op.drop_table("manutencoes")
    op.drop_index("uq_alocacoes_equipamento_aberto", table_name="alocacoes")
    op.drop_table("alocacoes")
    op.drop_table("funcionarios")
