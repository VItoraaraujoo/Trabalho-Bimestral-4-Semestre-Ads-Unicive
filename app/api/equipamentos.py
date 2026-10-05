from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models import Equipamento
from ..schemas.equipamento import (
    EquipamentoCreate,
    EquipamentoRead,
    EquipamentoUpdate,
    StatusEquipamento,
)
from ..services import equipamento_service
from ..services.equipamento_service import (
    EquipamentoNaoEncontradoError,
    PatrimonioDuplicadoError,
)


router = APIRouter(prefix="/equipamentos", tags=["Equipamentos"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def _traduzir_erro_de_consulta(exc: EquipamentoNaoEncontradoError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Equipamento não encontrado.",
    )


def _traduzir_erro_de_patrimonio(exc: PatrimonioDuplicadoError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Já existe um equipamento com esse patrimônio.",
    )


@router.post(
    "",
    response_model=EquipamentoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar equipamento",
)
def criar_equipamento(dados: EquipamentoCreate, db: DatabaseSession) -> Equipamento:
    try:
        return equipamento_service.criar(db, dados)
    except PatrimonioDuplicadoError as exc:
        raise _traduzir_erro_de_patrimonio(exc) from exc


@router.get("", response_model=list[EquipamentoRead], summary="Listar equipamentos")
def listar_equipamentos(
    db: DatabaseSession,
    status_filtro: Annotated[
        StatusEquipamento | None,
        Query(alias="status", description="Filtra pelo status do equipamento"),
    ] = None,
    tipo: Annotated[str | None, Query(description="Busca por tipo")] = None,
    setor: Annotated[str | None, Query(description="Busca por setor")] = None,
) -> list[Equipamento]:
    return equipamento_service.listar(db, status=status_filtro, tipo=tipo, setor=setor)


@router.get(
    "/{equipamento_id}",
    response_model=EquipamentoRead,
    summary="Consultar equipamento por ID",
)
def consultar_equipamento(
    equipamento_id: int, db: DatabaseSession
) -> Equipamento:
    try:
        return equipamento_service.consultar(db, equipamento_id)
    except EquipamentoNaoEncontradoError as exc:
        raise _traduzir_erro_de_consulta(exc) from exc


@router.put(
    "/{equipamento_id}",
    response_model=EquipamentoRead,
    summary="Atualizar equipamento",
)
def atualizar_equipamento(
    equipamento_id: int, dados: EquipamentoUpdate, db: DatabaseSession
) -> Equipamento:
    try:
        return equipamento_service.atualizar(db, equipamento_id, dados)
    except EquipamentoNaoEncontradoError as exc:
        raise _traduzir_erro_de_consulta(exc) from exc
    except PatrimonioDuplicadoError as exc:
        raise _traduzir_erro_de_patrimonio(exc) from exc


@router.delete(
    "/{equipamento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir equipamento",
)
def excluir_equipamento(equipamento_id: int, db: DatabaseSession) -> Response:
    try:
        equipamento_service.excluir(db, equipamento_id)
    except EquipamentoNaoEncontradoError as exc:
        raise _traduzir_erro_de_consulta(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
