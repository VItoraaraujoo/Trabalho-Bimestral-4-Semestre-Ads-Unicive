from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models import Usuario
from ..schemas.relatorio import RelatorioEquipamentos
from ..services.relatorio_service import montar_relatorio
from .dependencias import usuario_atual


router = APIRouter(prefix="/relatorios", tags=["Relatórios"])
DatabaseSession = Annotated[Session, Depends(get_db)]
UsuarioAtual = Annotated[Usuario, Depends(usuario_atual)]


@router.get(
    "/equipamentos",
    response_model=RelatorioEquipamentos,
    summary="Resumo dos equipamentos para consulta e relatório",
)
def relatorio_equipamentos(
    db: DatabaseSession, _usuario: UsuarioAtual
) -> RelatorioEquipamentos:
    return montar_relatorio(db)
