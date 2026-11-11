from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models import (
    Alocacao,
    Funcionario,
    Manutencao,
    SistemaFuncionario,
    Usuario,
)
from ..schemas.funcionario import (
    FuncionarioAtualizar,
    FuncionarioCriar,
    FuncionarioResposta,
)
from ..schemas.historico import (
    AlocacaoCriar,
    AlocacaoResposta,
    ManutencaoCriar,
    ManutencaoResposta,
    SistemaCriar,
    SistemaResposta,
)
from ..services import gestao_service
from ..services.gestao_service import (
    DadoDuplicadoError,
    RegistroNaoEncontradoError,
    RegraDeGestaoError,
)
from .dependencias import administrador, usuario_atual


router = APIRouter(tags=["Funcionários e históricos"])
DatabaseSession = Annotated[Session, Depends(get_db)]
UsuarioAtual = Annotated[Usuario, Depends(usuario_atual)]
AdministradorAtual = Annotated[Usuario, Depends(administrador)]


def _erro_regra(exc: RegraDeGestaoError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/funcionarios", response_model=list[FuncionarioResposta])
def listar_funcionarios(
    db: DatabaseSession,
    _usuario: UsuarioAtual,
    incluir_inativos: bool = Query(default=False),
) -> list[Funcionario]:
    return gestao_service.listar_funcionarios(db, incluir_inativos)


@router.get("/funcionarios/{funcionario_id}", response_model=FuncionarioResposta)
def consultar_funcionario(
    funcionario_id: int, db: DatabaseSession, _usuario: UsuarioAtual
) -> Funcionario:
    try:
        return gestao_service.obter_funcionario(db, funcionario_id)
    except RegistroNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/funcionarios",
    response_model=FuncionarioResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_funcionario(
    dados: FuncionarioCriar, db: DatabaseSession, _admin: AdministradorAtual
) -> Funcionario:
    try:
        return gestao_service.criar_funcionario(db, dados)
    except DadoDuplicadoError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um funcionário com esse CPF ou matrícula.",
        ) from exc


@router.put("/funcionarios/{funcionario_id}", response_model=FuncionarioResposta)
def atualizar_funcionario(
    funcionario_id: int,
    dados: FuncionarioAtualizar,
    db: DatabaseSession,
    _admin: AdministradorAtual,
) -> Funcionario:
    try:
        return gestao_service.atualizar_funcionario(db, funcionario_id, dados)
    except RegistroNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DadoDuplicadoError as exc:
        raise HTTPException(
            status_code=409,
            detail="Já existe um funcionário com esse CPF ou matrícula.",
        ) from exc


@router.delete("/funcionarios/{funcionario_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_funcionario(
    funcionario_id: int, db: DatabaseSession, _admin: AdministradorAtual
) -> Response:
    try:
        gestao_service.excluir_funcionario(db, funcionario_id)
    except RegistroNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RegraDeGestaoError as exc:
        raise _erro_regra(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/alocacoes", response_model=list[AlocacaoResposta])
def listar_alocacoes(
    db: DatabaseSession,
    _usuario: UsuarioAtual,
    funcionario_id: int | None = None,
    abertas: bool | None = None,
) -> list[Alocacao]:
    return gestao_service.listar_alocacoes(db, funcionario_id, abertas)


@router.post(
    "/alocacoes",
    response_model=AlocacaoResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_alocacao(
    dados: AlocacaoCriar, db: DatabaseSession, _admin: AdministradorAtual
) -> Alocacao:
    try:
        return gestao_service.criar_alocacao(db, dados)
    except (RegistroNaoEncontradoError, RegraDeGestaoError) as exc:
        codigo = 404 if isinstance(exc, RegistroNaoEncontradoError) else 409
        raise HTTPException(status_code=codigo, detail=str(exc)) from exc


@router.post("/alocacoes/{alocacao_id}/devolver", response_model=AlocacaoResposta)
def devolver_equipamento(
    alocacao_id: int, db: DatabaseSession, _admin: AdministradorAtual
) -> Alocacao:
    try:
        return gestao_service.devolver_equipamento(db, alocacao_id)
    except RegistroNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RegraDeGestaoError as exc:
        raise _erro_regra(exc) from exc


@router.get("/manutencoes", response_model=list[ManutencaoResposta])
def listar_manutencoes(
    db: DatabaseSession,
    _usuario: UsuarioAtual,
    equipamento_id: int | None = None,
) -> list[Manutencao]:
    return gestao_service.listar_manutencoes(db, equipamento_id)


@router.post(
    "/manutencoes",
    response_model=ManutencaoResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_manutencao(
    dados: ManutencaoCriar, db: DatabaseSession, _admin: AdministradorAtual
) -> Manutencao:
    try:
        return gestao_service.criar_manutencao(db, dados)
    except RegistroNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RegraDeGestaoError as exc:
        raise _erro_regra(exc) from exc


@router.get("/sistemas", response_model=list[SistemaResposta])
def listar_sistemas(
    db: DatabaseSession,
    _usuario: UsuarioAtual,
    funcionario_id: int | None = None,
) -> list[SistemaFuncionario]:
    return gestao_service.listar_sistemas(db, funcionario_id)


@router.post(
    "/sistemas",
    response_model=SistemaResposta,
    status_code=status.HTTP_201_CREATED,
)
def adicionar_sistema(
    dados: SistemaCriar, db: DatabaseSession, _admin: AdministradorAtual
) -> SistemaFuncionario:
    try:
        return gestao_service.adicionar_sistema(db, dados)
    except RegistroNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RegraDeGestaoError as exc:
        raise _erro_regra(exc) from exc


@router.patch("/sistemas/{sistema_id}/finalizar", response_model=SistemaResposta)
def finalizar_sistema(
    sistema_id: int, db: DatabaseSession, _admin: AdministradorAtual
) -> SistemaFuncionario:
    try:
        return gestao_service.finalizar_sistema(db, sistema_id)
    except RegistroNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RegraDeGestaoError as exc:
        raise _erro_regra(exc) from exc
