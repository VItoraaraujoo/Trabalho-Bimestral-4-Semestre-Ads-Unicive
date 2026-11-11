from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class SistemaFuncionario(Base):
    __tablename__ = "sistemas_funcionarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    funcionario_id: Mapped[int] = mapped_column(
        ForeignKey("funcionarios.id", ondelete="RESTRICT"), nullable=False
    )
    nome_funcionario: Mapped[str] = mapped_column(String(150), nullable=False)
    matricula_funcionario: Mapped[str] = mapped_column(String(50), nullable=False)
    nome_sistema: Mapped[str] = mapped_column(String(150), nullable=False)
    data_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_fim: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
