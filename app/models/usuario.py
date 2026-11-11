from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    cpf: Mapped[str | None] = mapped_column(String(14), nullable=True, unique=True)
    matricula: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    setor: Mapped[str] = mapped_column(String(100), nullable=False)
    perfil: Mapped[str] = mapped_column(String(20), nullable=False, default="comum")
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
