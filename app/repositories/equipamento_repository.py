from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models import Equipamento


def obter_por_id(db: Session, equipamento_id: int) -> Equipamento | None:
    return db.get(Equipamento, equipamento_id)


def obter_por_numero_serie(
    db: Session, numero_serie: str, ignorar_id: int | None = None
) -> Equipamento | None:
    query = select(Equipamento).where(Equipamento.numero_serie == numero_serie)
    if ignorar_id is not None:
        query = query.where(Equipamento.id != ignorar_id)
    return db.scalar(query)


def listar(
    db: Session,
    status: str | None = None,
    tipo: str | None = None,
    setor: str | None = None,
) -> list[Equipamento]:
    query = select(Equipamento).order_by(Equipamento.nome)
    if status is not None:
        query = query.where(Equipamento.status == status)
    if tipo:
        query = query.where(Equipamento.tipo.ilike(f"%{tipo.strip()}%"))
    if setor:
        query = query.where(Equipamento.setor.ilike(f"%{setor.strip()}%"))
    return list(db.scalars(query).all())


def criar(db: Session, equipamento: Equipamento) -> Equipamento:
    db.add(equipamento)
    try:
        db.flush()
        equipamento.patrimonio = f"ATI-{equipamento.id:06d}"
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(equipamento)
    return equipamento


def atualizar(db: Session, equipamento: Equipamento) -> Equipamento:
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(equipamento)
    return equipamento


def excluir(db: Session, equipamento: Equipamento) -> None:
    db.delete(equipamento)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
