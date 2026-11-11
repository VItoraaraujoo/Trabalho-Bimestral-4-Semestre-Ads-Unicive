from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SituacaoAlocacao(str, Enum):
    EM_USO = "Em uso"
    EMPRESTADO = "Emprestado"


class AlocacaoCriar(BaseModel):
    equipamento_id: int = Field(gt=0)
    funcionario_id: int = Field(gt=0)
    situacao: SituacaoAlocacao = SituacaoAlocacao.EM_USO
    observacao: str | None = Field(default=None, max_length=500)

    @field_validator("observacao")
    @classmethod
    def limpar_observacao(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        return valor.strip() or None


class AlocacaoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipamento_id: int | None
    funcionario_id: int
    patrimonio: str
    nome_equipamento: str
    nome_funcionario: str
    cpf_funcionario: str
    matricula_funcionario: str
    setor_funcionario: str
    situacao: str
    data_alocacao: datetime
    data_devolucao: datetime | None
    observacao: str | None


class ManutencaoCriar(BaseModel):
    equipamento_id: int = Field(gt=0)
    laudo: str = Field(min_length=1, max_length=2000)
    sem_conserto: bool = False

    @field_validator("laudo")
    @classmethod
    def limpar_laudo(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("Escreva o laudo da manutenção.")
        return valor


class ManutencaoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipamento_id: int | None
    patrimonio: str
    nome_equipamento: str
    data: datetime
    laudo: str
    sem_conserto: bool


class SistemaCriar(BaseModel):
    funcionario_id: int = Field(gt=0)
    nome_sistema: str = Field(min_length=1, max_length=150)

    @field_validator("nome_sistema")
    @classmethod
    def limpar_nome(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("Informe o nome do sistema.")
        return valor


class SistemaResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    funcionario_id: int
    nome_funcionario: str
    matricula_funcionario: str
    nome_sistema: str
    data_inicio: datetime
    data_fim: datetime | None
