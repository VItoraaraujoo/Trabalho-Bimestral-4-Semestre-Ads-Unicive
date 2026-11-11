from typing import Annotated


from fastapi import APIRouter, Depends, HTTPException, status

from ..core.seguranca import criar_token
from ..models import Usuario
from ..schemas.usuario import LoginResposta, UsuarioLogin, UsuarioResposta
from ..services import usuario_service
from ..services.usuario_service import LoginInvalidoError
from .dependencias import DatabaseSession, usuario_atual


router = APIRouter(prefix="/auth", tags=["Acesso"])
UsuarioAtual = Annotated[Usuario, Depends(usuario_atual)]


@router.post("/login", response_model=LoginResposta, summary="Entrar com e-mail e senha")
def login(dados: UsuarioLogin, db: DatabaseSession) -> LoginResposta:
    try:
        usuario = usuario_service.entrar(db, dados)
    except LoginInvalidoError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return LoginResposta(
        access_token=criar_token(usuario.id),
        usuario=UsuarioResposta.model_validate(usuario),
    )


@router.get("/me", response_model=UsuarioResposta, summary="Consultar usuário conectado")
def meu_usuario(usuario: UsuarioAtual) -> Usuario:
    return usuario
