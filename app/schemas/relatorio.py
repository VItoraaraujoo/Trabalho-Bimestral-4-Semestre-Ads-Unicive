from pydantic import BaseModel


class GrupoRelatorio(BaseModel):
    nome: str
    quantidade: int


class EquipamentoRelatorio(BaseModel):
    id: int
    patrimonio: str | None
    nome: str
    tipo: str
    numero_serie: str | None
    marca: str | None
    modelo: str | None
    condicao: str
    status: str
    setor: str | None
    funcionario_id: int | None = None
    nome_funcionario: str | None = None
    cpf_funcionario: str | None = None
    matricula_funcionario: str | None = None


class RelatorioEquipamentos(BaseModel):
    total_equipamentos: int
    por_status: list[GrupoRelatorio]
    por_tipo: list[GrupoRelatorio]
    por_setor: list[GrupoRelatorio]
    equipamentos: list[EquipamentoRelatorio]
