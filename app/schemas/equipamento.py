from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StatusEquipamento(str, Enum):
    EM_USO = "Em uso"
    DISPONIVEL = "Disponível"
    EM_MANUTENCAO = "Em manutenção"
    DESCARTADO = "Descartado"


class EquipamentoBase(BaseModel):
    nome: str = Field(min_length=1, max_length=150, description="Nome de identificação")
    tipo: str = Field(min_length=1, max_length=80, description="Tipo do equipamento")
    patrimonio: str | None = Field(default=None, max_length=60)
    marca: str | None = Field(default=None, max_length=100)
    modelo: str | None = Field(default=None, max_length=100)
    setor: str | None = Field(default=None, max_length=100)
    status: StatusEquipamento = StatusEquipamento.DISPONIVEL
    observacao: str | None = Field(default=None, max_length=500)

    @field_validator("nome", "tipo")
    @classmethod
    def limpar_campos_obrigatorios(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("O campo não pode ficar vazio.")
        return value

    @field_validator("patrimonio", "marca", "modelo", "setor", "observacao")
    @classmethod
    def normalizar_campos_opcionais(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class EquipamentoCreate(EquipamentoBase):
    pass


class EquipamentoUpdate(EquipamentoBase):
    pass


class EquipamentoRead(EquipamentoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
