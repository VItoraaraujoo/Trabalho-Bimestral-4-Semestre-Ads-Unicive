from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import JWT_EXPIRE_MINUTES, JWT_SECRET_KEY


def criar_hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def conferir_senha(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))
    except ValueError:
        return False


def criar_token(usuario_id: int) -> str:
    validade = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    dados = {"sub": str(usuario_id), "exp": validade}
    return jwt.encode(dados, JWT_SECRET_KEY, algorithm="HS256")
