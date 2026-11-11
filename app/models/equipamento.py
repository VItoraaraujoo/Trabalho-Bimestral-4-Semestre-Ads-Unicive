from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class Equipamento(Base):
    __tablename__ = "equipamentos"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    patrimonio: Mapped[str | None] = mapped_column(
        String(60), unique=True, nullable=True, index=True
    )
    numero_serie: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )
    marca: Mapped[str | None] = mapped_column(String(100), nullable=True)
    modelo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    setor: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    condicao: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Usado", server_default="Usado"
    )
    status: Mapped[str] = mapped_column(
        String(40), nullable=False, default="Em estoque", server_default="Em estoque", index=True
    )
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True)
