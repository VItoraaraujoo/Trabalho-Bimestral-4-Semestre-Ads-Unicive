from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models import Usuario
from ..schemas.usuario import (
    UsuarioAtualizar,
    UsuarioCredenciaisAtualizar,
    UsuarioCriar,
    UsuarioResposta,
)
from ..services import usuario_service
from ..services.usuario_service import (
    EmailJaCadastradoError,
    UltimoAdministradorError,
    UsuarioAtualNaoPodeSerExcluidoError,
    UsuarioNaoEncontradoError,
)
from .dependencias import administrador, usuario_atual


router = APIRouter(prefix="/usuarios", tags=["Usuários"])
DatabaseSession = Annotated[Session, Depends(get_db)]
AdministradorAtual = Annotated[Usuario, Depends(administrador)]
UsuarioAutenticado = Annotated[Usuario, Depends(usuario_atual)]


def erro_email_duplicado(exc: EmailJaCadastradoError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Já existe um usuário com esse e-mail, CPF ou matrícula.",
    )


@router.post("", response_model=UsuarioResposta, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    dados: UsuarioCriar, db: DatabaseSession, _admin: AdministradorAtual
) -> Usuario:
    try:
        return usuario_service.criar(db, dados)
    except EmailJaCadastradoError as exc:
        raise erro_email_duplicado(exc) from exc


@router.get("", response_model=list[UsuarioResposta])
def listar_usuarios(db: DatabaseSession, _admin: AdministradorAtual) -> list[Usuario]:
    return usuario_service.listar(db)


@router.put("/{usuario_id}", response_model=UsuarioResposta)
def atualizar_usuario(
    usuario_id: int,
    dados: UsuarioAtualizar,
    db: DatabaseSession,
    _admin: AdministradorAtual,
) -> Usuario:
    try:
        return usuario_service.atualizar(db, usuario_id, dados)
    except UsuarioNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.") from exc
    except EmailJaCadastradoError as exc:
        raise erro_email_duplicado(exc) from exc


@router.patch("/{usuario_id}/credenciais", response_model=UsuarioResposta)
def atualizar_credenciais(
    usuario_id: int,
    dados: UsuarioCredenciaisAtualizar,
    db: DatabaseSession,
    usuario: UsuarioAutenticado,
) -> Usuario:
    if usuario.perfil != "admin" and usuario.id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode alterar as credenciais da própria conta.",
        )
    try:
        return usuario_service.atualizar_credenciais(db, usuario_id, dados)
    except UsuarioNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.") from exc
    except EmailJaCadastradoError as exc:
        raise erro_email_duplicado(exc) from exc


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_usuario(
    usuario_id: int,
    db: DatabaseSession,
    administrador_atual: AdministradorAtual,
) -> Response:
    try:
        usuario_service.excluir(db, administrador_atual, usuario_id)
    except UsuarioNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.") from exc
    except UltimoAdministradorError as exc:
        raise HTTPException(
            status_code=409,
            detail="Cadastre outro administrador antes de excluir este usuário.",
        ) from exc
    except UsuarioAtualNaoPodeSerExcluidoError as exc:
        raise HTTPException(
            status_code=409,
            detail="Não é possível excluir o próprio acesso.",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
