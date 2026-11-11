import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FuncionarioDados(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    cpf: str = Field(min_length=11, max_length=14, description="CPF com ou sem pontuação")
    matricula: str = Field(min_length=1, max_length=50)
    setor: str = Field(min_length=1, max_length=100)

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, valor: str) -> str:
        cpf = re.sub(r"\D", "", valor)
        if len(cpf) != 11:
            raise ValueError("O CPF deve ter 11 números.")
        return cpf

    @field_validator("nome", "matricula", "setor")
    @classmethod
    def limpar_texto(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("O campo não pode ficar vazio.")
        return valor


class FuncionarioCriar(FuncionarioDados):
    pass


class FuncionarioAtualizar(FuncionarioDados):
    pass


class FuncionarioResposta(FuncionarioDados):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool
