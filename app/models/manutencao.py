from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, false
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class Manutencao(Base):
    __tablename__ = "manutencoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("equipamentos.id", ondelete="SET NULL"), nullable=True
    )
    patrimonio: Mapped[str] = mapped_column(String(60), nullable=False)
    nome_equipamento: Mapped[str] = mapped_column(String(150), nullable=False)
    data: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    laudo: Mapped[str] = mapped_column(String(2000), nullable=False)
    sem_conserto: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
