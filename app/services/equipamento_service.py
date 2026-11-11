from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import Alocacao, Equipamento
from ..repositories import equipamento_repository as repository
from ..schemas.equipamento import (
    EquipamentoCreate,
    EquipamentoUpdate,
    StatusEquipamento,
)


class EquipamentoNaoEncontradoError(Exception):
    pass


class NumeroSerieDuplicadoError(Exception):
    pass


class EquipamentoNaoBaixadoError(Exception):
    pass


class StatusGerenciadoError(Exception):
    pass


def _dados_para_modelo(dados: EquipamentoCreate | EquipamentoUpdate) -> dict:
    valores = dados.model_dump()
    valores["status"] = dados.status.value
    valores["condicao"] = dados.condicao.value
    return valores


def criar(db: Session, dados: EquipamentoCreate) -> Equipamento:
    if dados.status.value != StatusEquipamento.EM_ESTOQUE.value:
        raise StatusGerenciadoError(
            "Novos equipamentos começam em estoque. Use alocação ou manutenção para mudar o status."
        )
    if dados.numero_serie and repository.obter_por_numero_serie(
        db, dados.numero_serie
    ):
        raise NumeroSerieDuplicadoError

    equipamento = Equipamento(**_dados_para_modelo(dados))
    try:
        return repository.criar(db, equipamento)
    except IntegrityError as exc:
        raise NumeroSerieDuplicadoError from exc


def listar(
    db: Session,
    status: StatusEquipamento | None = None,
    tipo: str | None = None,
    setor: str | None = None,
) -> list[Equipamento]:
    return repository.listar(
        db,
        status=status.value if status is not None else None,
        tipo=tipo,
        setor=setor,
    )


def consultar(db: Session, equipamento_id: int) -> Equipamento:
    equipamento = repository.obter_por_id(db, equipamento_id)
    if equipamento is None:
        raise EquipamentoNaoEncontradoError
    return equipamento


def atualizar(
    db: Session, equipamento_id: int, dados: EquipamentoUpdate
) -> Equipamento:
    equipamento = consultar(db, equipamento_id)
    status_atual = equipamento.status
    status_novo = dados.status.value
    status_de_alocacao = {
        StatusEquipamento.EM_USO.value,
        StatusEquipamento.EMPRESTADO.value,
    }
    if status_novo in status_de_alocacao and status_novo != status_atual:
        raise StatusGerenciadoError(
            "Use a tela de alocação para entregar um equipamento a um funcionário."
        )
    if (
        status_novo == StatusEquipamento.BAIXADO.value
        and status_atual != StatusEquipamento.BAIXADO.value
    ):
        raise StatusGerenciadoError(
            "Registre um laudo de manutenção e marque que não há conserto para dar baixa."
        )
    if (
        status_atual == StatusEquipamento.EM_MANUTENCAO.value
        and status_novo != StatusEquipamento.EM_MANUTENCAO.value
    ):
        raise StatusGerenciadoError(
            "Registre o laudo escrito para encerrar a manutenção e atualizar o status."
        )
    if status_atual in status_de_alocacao and status_novo != status_atual:
        raise StatusGerenciadoError(
            "Devolva o equipamento pela alocação antes de alterar seu status."
        )
    if status_novo in {
        StatusEquipamento.EM_MANUTENCAO.value,
        StatusEquipamento.BAIXADO.value,
    }:
        alocacao_aberta = db.scalar(
            select(Alocacao.id).where(
                Alocacao.equipamento_id == equipamento_id,
                Alocacao.data_devolucao.is_(None),
            )
        )
        if alocacao_aberta is not None:
            raise StatusGerenciadoError(
                "Devolva o equipamento antes de enviá-lo para manutenção ou dar baixa."
            )
    if dados.numero_serie and repository.obter_por_numero_serie(
        db, dados.numero_serie, ignorar_id=equipamento_id
    ):
        raise NumeroSerieDuplicadoError

    for campo, valor in _dados_para_modelo(dados).items():
        setattr(equipamento, campo, valor)

    try:
        return repository.atualizar(db, equipamento)
    except IntegrityError as exc:
        raise NumeroSerieDuplicadoError from exc


def excluir(db: Session, equipamento_id: int) -> None:
    equipamento = consultar(db, equipamento_id)
    if equipamento.status != StatusEquipamento.BAIXADO.value:
        raise EquipamentoNaoBaixadoError
    repository.excluir(db, equipamento)
