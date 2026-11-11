from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class Alocacao(Base):
    __tablename__ = "alocacoes"
    __table_args__ = (
        Index(
            "uq_alocacoes_equipamento_aberto",
            "equipamento_id",
            unique=True,
            sqlite_where=text("data_devolucao IS NULL"),
            postgresql_where=text("data_devolucao IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("equipamentos.id", ondelete="SET NULL"), nullable=True
    )
    funcionario_id: Mapped[int] = mapped_column(
        ForeignKey("funcionarios.id", ondelete="RESTRICT"), nullable=False
    )
    patrimonio: Mapped[str] = mapped_column(String(60), nullable=False)
    nome_equipamento: Mapped[str] = mapped_column(String(150), nullable=False)
    nome_funcionario: Mapped[str] = mapped_column(String(150), nullable=False)
    cpf_funcionario: Mapped[str] = mapped_column(String(11), nullable=False)
    matricula_funcionario: Mapped[str] = mapped_column(String(50), nullable=False)
    setor_funcionario: Mapped[str] = mapped_column(String(100), nullable=False)
    situacao: Mapped[str] = mapped_column(String(20), nullable=False, default="Em uso")
    data_alocacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_devolucao: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True)
