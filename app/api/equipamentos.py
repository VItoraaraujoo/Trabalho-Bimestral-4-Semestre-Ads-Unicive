from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models import Equipamento, Usuario
from ..schemas.equipamento import (
    EquipamentoCreate,
    EquipamentoRead,
    EquipamentoUpdate,
    StatusEquipamento,
)
from ..services import equipamento_service
from ..services.equipamento_service import (
    EquipamentoNaoBaixadoError,
    EquipamentoNaoEncontradoError,
    NumeroSerieDuplicadoError,
    StatusGerenciadoError,
)
from .dependencias import administrador, usuario_atual


router = APIRouter(prefix="/equipamentos", tags=["Equipamentos"])
DatabaseSession = Annotated[Session, Depends(get_db)]
UsuarioAtual = Annotated[Usuario, Depends(usuario_atual)]
AdministradorAtual = Annotated[Usuario, Depends(administrador)]

RESPOSTA_ERRO_BANCO = {
    "description": "Banco de dados indisponível. Verifique a conexão e tente novamente.",
    "content": {
        "application/json": {
            "example": {
                "detail": "Banco de dados indisponível. Verifique a conexão e tente novamente."
            }
        }
    },
}
RESPOSTA_NAO_ENCONTRADO = {
    "description": "Equipamento não encontrado.",
    "content": {
        "application/json": {
            "example": {"detail": "Equipamento não encontrado."}
        }
    },
}
RESPOSTA_NUMERO_SERIE_DUPLICADO = {
    "description": "Já existe um equipamento com esse número de série.",
    "content": {
        "application/json": {
            "example": {
                "detail": "Já existe um equipamento com esse número de série."
            }
        }
    },
}
RESPOSTA_EQUIPAMENTO_NAO_BAIXADO = {
    "description": "O equipamento precisa receber baixa antes de ser excluído.",
    "content": {
        "application/json": {
            "example": {
                "detail": "O equipamento precisa receber baixa antes de ser excluído."
            }
        }
    },
}


def _traduzir_erro_de_consulta(exc: EquipamentoNaoEncontradoError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Equipamento não encontrado.",
    )


def _traduzir_erro_de_numero_serie(exc: NumeroSerieDuplicadoError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Já existe um equipamento com esse número de série.",
    )


@router.post(
    "",
    response_model=EquipamentoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar equipamento",
    responses={
        status.HTTP_409_CONFLICT: RESPOSTA_NUMERO_SERIE_DUPLICADO,
        status.HTTP_503_SERVICE_UNAVAILABLE: RESPOSTA_ERRO_BANCO,
    },
)
def criar_equipamento(
    dados: EquipamentoCreate, db: DatabaseSession, _admin: AdministradorAtual
) -> Equipamento:
    try:
        return equipamento_service.criar(db, dados)
    except NumeroSerieDuplicadoError as exc:
        raise _traduzir_erro_de_numero_serie(exc) from exc
    except StatusGerenciadoError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get(
    "",
    response_model=list[EquipamentoRead],
    summary="Listar equipamentos",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: RESPOSTA_ERRO_BANCO},
)
def listar_equipamentos(
    db: DatabaseSession,
    _usuario: UsuarioAtual,
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
    responses={
        status.HTTP_404_NOT_FOUND: RESPOSTA_NAO_ENCONTRADO,
        status.HTTP_503_SERVICE_UNAVAILABLE: RESPOSTA_ERRO_BANCO,
    },
)
def consultar_equipamento(
    equipamento_id: int, db: DatabaseSession, _usuario: UsuarioAtual
) -> Equipamento:
    try:
        return equipamento_service.consultar(db, equipamento_id)
    except EquipamentoNaoEncontradoError as exc:
        raise _traduzir_erro_de_consulta(exc) from exc


@router.put(
    "/{equipamento_id}",
    response_model=EquipamentoRead,
    summary="Atualizar equipamento",
    responses={
        status.HTTP_404_NOT_FOUND: RESPOSTA_NAO_ENCONTRADO,
        status.HTTP_409_CONFLICT: RESPOSTA_NUMERO_SERIE_DUPLICADO,
        status.HTTP_503_SERVICE_UNAVAILABLE: RESPOSTA_ERRO_BANCO,
    },
)
def atualizar_equipamento(
    equipamento_id: int,
    dados: EquipamentoUpdate,
    db: DatabaseSession,
    _admin: AdministradorAtual,
) -> Equipamento:
    try:
        return equipamento_service.atualizar(db, equipamento_id, dados)
    except EquipamentoNaoEncontradoError as exc:
        raise _traduzir_erro_de_consulta(exc) from exc
    except NumeroSerieDuplicadoError as exc:
        raise _traduzir_erro_de_numero_serie(exc) from exc
    except StatusGerenciadoError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete(
    "/{equipamento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir equipamento",
    responses={
        status.HTTP_404_NOT_FOUND: RESPOSTA_NAO_ENCONTRADO,
        status.HTTP_409_CONFLICT: RESPOSTA_EQUIPAMENTO_NAO_BAIXADO,
        status.HTTP_503_SERVICE_UNAVAILABLE: RESPOSTA_ERRO_BANCO,
    },
)
def excluir_equipamento(
    equipamento_id: int, db: DatabaseSession, _admin: AdministradorAtual
) -> Response:
    try:
        equipamento_service.excluir(db, equipamento_id)
    except EquipamentoNaoEncontradoError as exc:
        raise _traduzir_erro_de_consulta(exc) from exc
    except EquipamentoNaoBaixadoError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O equipamento precisa receber baixa antes de ser excluído.",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
