from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import Equipamento


def obter_por_id(db: Session, equipamento_id: int) -> Equipamento | None:
    return db.get(Equipamento, equipamento_id)


def obter_por_patrimonio(
    db: Session, patrimonio: str, ignorar_id: int | None = None
) -> Equipamento | None:
    query = select(Equipamento).where(Equipamento.patrimonio == patrimonio)
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
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(equipamento)
    return equipamento


def atualizar(db: Session, equipamento: Equipamento) -> Equipamento:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(equipamento)
    return equipamento


def excluir(db: Session, equipamento: Equipamento) -> None:
    db.delete(equipamento)
    db.commit()
