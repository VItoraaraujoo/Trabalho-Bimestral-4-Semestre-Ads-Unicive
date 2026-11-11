from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..core.validacao import normalizar_email


class PerfilUsuario(str, Enum):
    ADMIN = "admin"
    COMUM = "comum"


class UsuarioDados(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=5, max_length=150)
    cpf: str = Field(min_length=11, max_length=14)
    matricula: str = Field(min_length=1, max_length=50)
    setor: str = Field(min_length=1, max_length=100)
    perfil: PerfilUsuario = PerfilUsuario.COMUM

    @field_validator("nome", "setor")
    @classmethod
    def limpar_obrigatorios(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("O campo não pode ficar vazio.")
        return valor

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:
        return normalizar_email(valor)

    @field_validator("cpf")
    @classmethod
    def normalizar_cpf(cls, valor: str) -> str:
        cpf = valor.replace(".", "").replace("-", "").strip()
        if not cpf.isdigit() or len(cpf) != 11:
            raise ValueError("O CPF deve ter 11 números.")
        return cpf

    @field_validator("matricula")
    @classmethod
    def limpar_matricula(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("A matrícula não pode ficar vazia.")
        return valor


class UsuarioCriar(UsuarioDados):
    senha: str = Field(min_length=8, max_length=72)


class UsuarioAtualizar(UsuarioDados):
    senha: str | None = Field(default=None, min_length=8, max_length=72)


class UsuarioCredenciaisAtualizar(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=5, max_length=150)
    nova_senha: str | None = Field(default=None, min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:
        return normalizar_email(valor)

    @field_validator("nova_senha", mode="before")
    @classmethod
    def senha_em_branco_mantem_atual(cls, valor: str | None) -> str | None:
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            return None
        return valor

    @field_validator("nova_senha")
    @classmethod
    def limitar_bytes_bcrypt(cls, valor: str | None) -> str | None:
        if valor is not None and len(valor.encode("utf-8")) > 72:
            raise ValueError("A nova senha deve ter no máximo 72 bytes.")
        return valor


class UsuarioLogin(BaseModel):
    email: str
    senha: str


class UsuarioResposta(UsuarioDados):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool


class LoginResposta(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResposta
