from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..core.config import JWT_SECRET_KEY
from ..core.database import get_db
from ..models import Usuario
from ..repositories import usuario_repository


DatabaseSession = Annotated[Session, Depends(get_db)]
esquema_token = HTTPBearer(auto_error=False)


def usuario_atual(
    credenciais: Annotated[
        HTTPAuthorizationCredentials | None, Depends(esquema_token)
    ],
    db: DatabaseSession,
) -> Usuario:
    if credenciais is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Entre no sistema para continuar.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        dados = jwt.decode(
            credenciais.credentials, JWT_SECRET_KEY, algorithms=["HS256"]
        )
        usuario_id = int(dados["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A sessão expirou ou é inválida. Entre novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    usuario = usuario_repository.obter_por_id(db, usuario_id)
    if usuario is None or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A sessão expirou ou é inválida. Entre novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


def administrador(usuario: Annotated[Usuario, Depends(usuario_atual)]) -> Usuario:
    if usuario.perfil != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil permite apenas consultar os dados e gerar relatórios.",
        )
    return usuario
