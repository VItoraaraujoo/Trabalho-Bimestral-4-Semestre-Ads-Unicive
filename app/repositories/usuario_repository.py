from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Usuario


def obter_por_id(db: Session, usuario_id: int) -> Usuario | None:
    return db.get(Usuario, usuario_id)


def obter_por_email(db: Session, email: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(func.lower(Usuario.email) == email.lower()))


def listar(db: Session) -> list[Usuario]:
    consulta = select(Usuario).order_by(Usuario.nome)
    return list(db.scalars(consulta).all())


def contar_administradores_ativos(db: Session) -> int:
    consulta = select(func.count()).select_from(Usuario).where(
        Usuario.perfil == "admin", Usuario.ativo.is_(True)
    )
    return int(db.scalar(consulta) or 0)
