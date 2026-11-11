from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Alocacao, Equipamento
from ..schemas.relatorio import (
    EquipamentoRelatorio,
    GrupoRelatorio,
    RelatorioEquipamentos,
)


def contar_por_campo(db: Session, campo) -> list[GrupoRelatorio]:
    consulta = (
        select(campo.label("nome"), func.count(Equipamento.id).label("quantidade"))
        .group_by(campo)
        .order_by(campo)
    )
    resultados = db.execute(consulta).all()
    return [
        GrupoRelatorio(nome=nome or "Não informado", quantidade=quantidade)
        for nome, quantidade in resultados
    ]


def montar_relatorio(db: Session) -> RelatorioEquipamentos:
    total = db.scalar(select(func.count()).select_from(Equipamento)) or 0
    consulta_equipamentos = (
        select(Equipamento, Alocacao)
        .outerjoin(
            Alocacao,
            (Alocacao.equipamento_id == Equipamento.id)
            & Alocacao.data_devolucao.is_(None),
        )
        .order_by(Equipamento.patrimonio)
    )
    lista_equipamentos = []
    for equipamento, alocacao in db.execute(consulta_equipamentos):
        lista_equipamentos.append(
            EquipamentoRelatorio(
                id=equipamento.id,
                patrimonio=equipamento.patrimonio,
                nome=equipamento.nome,
                tipo=equipamento.tipo,
                numero_serie=equipamento.numero_serie,
                marca=equipamento.marca,
                modelo=equipamento.modelo,
                condicao=equipamento.condicao,
                status=equipamento.status,
                setor=equipamento.setor,
                funcionario_id=alocacao.funcionario_id if alocacao else None,
                nome_funcionario=alocacao.nome_funcionario if alocacao else None,
                cpf_funcionario=alocacao.cpf_funcionario if alocacao else None,
                matricula_funcionario=(
                    alocacao.matricula_funcionario if alocacao else None
                ),
            )
        )
    return RelatorioEquipamentos(
        total_equipamentos=total,
        por_status=contar_por_campo(db, Equipamento.status),
        por_tipo=contar_por_campo(db, Equipamento.tipo),
        por_setor=contar_por_campo(db, Equipamento.setor),
        equipamentos=lista_equipamentos,
    )
