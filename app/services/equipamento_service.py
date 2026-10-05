from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import Equipamento
from ..repositories import equipamento_repository as repository
from ..schemas.equipamento import (
    EquipamentoCreate,
    EquipamentoUpdate,
    StatusEquipamento,
)


class EquipamentoNaoEncontradoError(Exception):
    pass


class PatrimonioDuplicadoError(Exception):
    pass


def _dados_para_modelo(dados: EquipamentoCreate | EquipamentoUpdate) -> dict:
    valores = dados.model_dump()
    valores["status"] = dados.status.value
    return valores


def criar(db: Session, dados: EquipamentoCreate) -> Equipamento:
    if dados.patrimonio and repository.obter_por_patrimonio(db, dados.patrimonio):
        raise PatrimonioDuplicadoError

    equipamento = Equipamento(**_dados_para_modelo(dados))
    try:
        return repository.criar(db, equipamento)
    except IntegrityError as exc:
        raise PatrimonioDuplicadoError from exc


def listar(
    db: Session,
    status: StatusEquipamento | None = None,
    tipo: str | None = None,
    setor: str | None = None,
) -> list[Equipamento]:
    return repository.listar(
        db,
        status=status.value if status is not None else None,
        tipo=tipo,
        setor=setor,
    )


def consultar(db: Session, equipamento_id: int) -> Equipamento:
    equipamento = repository.obter_por_id(db, equipamento_id)
    if equipamento is None:
        raise EquipamentoNaoEncontradoError
    return equipamento


def atualizar(
    db: Session, equipamento_id: int, dados: EquipamentoUpdate
) -> Equipamento:
    equipamento = consultar(db, equipamento_id)
    if dados.patrimonio and repository.obter_por_patrimonio(
        db, dados.patrimonio, ignorar_id=equipamento_id
    ):
        raise PatrimonioDuplicadoError

    for campo, valor in _dados_para_modelo(dados).items():
        setattr(equipamento, campo, valor)

    try:
        return repository.atualizar(db, equipamento)
    except IntegrityError as exc:
        raise PatrimonioDuplicadoError from exc


def excluir(db: Session, equipamento_id: int) -> None:
    equipamento = consultar(db, equipamento_id)
    repository.excluir(db, equipamento)
