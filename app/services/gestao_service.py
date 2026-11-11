from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    Alocacao,
    Equipamento,
    Funcionario,
    Manutencao,
    SistemaFuncionario,
)
from ..schemas.funcionario import FuncionarioAtualizar, FuncionarioCriar
from ..schemas.historico import AlocacaoCriar, ManutencaoCriar, SistemaCriar


class RegistroNaoEncontradoError(Exception):
    pass


class DadoDuplicadoError(Exception):
    pass


class RegraDeGestaoError(Exception):
    pass


def agora() -> datetime:
    return datetime.now(timezone.utc)


def listar_funcionarios(db: Session, incluir_inativos: bool = False) -> list[Funcionario]:
    consulta = select(Funcionario).order_by(Funcionario.nome)
    if not incluir_inativos:
        consulta = consulta.where(Funcionario.ativo.is_(True))
    return list(db.scalars(consulta))


def obter_funcionario(db: Session, funcionario_id: int) -> Funcionario:
    funcionario = db.get(Funcionario, funcionario_id)
    if funcionario is None:
        raise RegistroNaoEncontradoError("Funcionário não encontrado.")
    return funcionario


def criar_funcionario(db: Session, dados: FuncionarioCriar) -> Funcionario:
    funcionario = Funcionario(**dados.model_dump())
    db.add(funcionario)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DadoDuplicadoError from exc
    db.refresh(funcionario)
    return funcionario


def atualizar_funcionario(
    db: Session, funcionario_id: int, dados: FuncionarioAtualizar
) -> Funcionario:
    funcionario = obter_funcionario(db, funcionario_id)
    for campo, valor in dados.model_dump().items():
        setattr(funcionario, campo, valor)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DadoDuplicadoError from exc
    db.refresh(funcionario)
    return funcionario


def excluir_funcionario(db: Session, funcionario_id: int) -> None:
    """Desativa o cadastro e encerra vínculos abertos sem apagar o histórico."""
    funcionario = obter_funcionario(db, funcionario_id)
    if not funcionario.ativo:
        raise RegraDeGestaoError("Este funcionário já foi removido da empresa.")

    alocacoes = db.scalars(
        select(Alocacao).where(
            Alocacao.funcionario_id == funcionario.id,
            Alocacao.data_devolucao.is_(None),
        )
    ).all()
    for alocacao in alocacoes:
        if alocacao.equipamento_id is not None:
            equipamento = db.get(Equipamento, alocacao.equipamento_id)
            if equipamento is not None:
                equipamento.status = "Em estoque"
        alocacao.data_devolucao = agora()

    sistemas = db.scalars(
        select(SistemaFuncionario).where(
            SistemaFuncionario.funcionario_id == funcionario.id,
            SistemaFuncionario.data_fim.is_(None),
        )
    ).all()
    for sistema in sistemas:
        sistema.data_fim = agora()

    funcionario.ativo = False
    db.commit()


def listar_alocacoes(
    db: Session, funcionario_id: int | None = None, abertas: bool | None = None
) -> list[Alocacao]:
    consulta = select(Alocacao).order_by(Alocacao.data_alocacao.desc())
    if funcionario_id is not None:
        consulta = consulta.where(Alocacao.funcionario_id == funcionario_id)
    if abertas is True:
        consulta = consulta.where(Alocacao.data_devolucao.is_(None))
    elif abertas is False:
        consulta = consulta.where(Alocacao.data_devolucao.is_not(None))
    return list(db.scalars(consulta))


def criar_alocacao(db: Session, dados: AlocacaoCriar) -> Alocacao:
    funcionario = obter_funcionario(db, dados.funcionario_id)
    if not funcionario.ativo:
        raise RegraDeGestaoError("Não é possível entregar equipamento a funcionário inativo.")
    equipamento = db.get(Equipamento, dados.equipamento_id)
    if equipamento is None:
        raise RegistroNaoEncontradoError("Equipamento não encontrado.")
    if equipamento.status != "Em estoque":
        raise RegraDeGestaoError("Somente equipamentos em estoque podem ser alocados.")
    alocacao_aberta = db.scalar(
        select(Alocacao.id).where(
            Alocacao.equipamento_id == equipamento.id,
            Alocacao.data_devolucao.is_(None),
        )
    )
    if alocacao_aberta is not None:
        raise RegraDeGestaoError("Este equipamento já tem uma alocação ativa.")

    alocacao = Alocacao(
        equipamento_id=equipamento.id,
        funcionario_id=funcionario.id,
        patrimonio=equipamento.patrimonio,
        nome_equipamento=equipamento.nome,
        nome_funcionario=funcionario.nome,
        cpf_funcionario=funcionario.cpf,
        matricula_funcionario=funcionario.matricula,
        setor_funcionario=funcionario.setor,
        situacao=dados.situacao.value,
        data_alocacao=agora(),
        observacao=dados.observacao,
    )
    equipamento.status = dados.situacao.value
    db.add(alocacao)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise RegraDeGestaoError("Este equipamento já tem uma alocação ativa.") from exc
    db.refresh(alocacao)
    return alocacao


def devolver_equipamento(db: Session, alocacao_id: int) -> Alocacao:
    alocacao = db.get(Alocacao, alocacao_id)
    if alocacao is None:
        raise RegistroNaoEncontradoError("Alocação não encontrada.")
    if alocacao.data_devolucao is not None:
        raise RegraDeGestaoError("Este equipamento já foi devolvido.")
    alocacao.data_devolucao = agora()
    if alocacao.equipamento_id is not None:
        equipamento = db.get(Equipamento, alocacao.equipamento_id)
        if equipamento is not None:
            equipamento.status = "Em estoque"
    db.commit()
    db.refresh(alocacao)
    return alocacao


def listar_manutencoes(
    db: Session, equipamento_id: int | None = None
) -> list[Manutencao]:
    consulta = select(Manutencao).order_by(Manutencao.data.desc())
    if equipamento_id is not None:
        consulta = consulta.where(Manutencao.equipamento_id == equipamento_id)
    return list(db.scalars(consulta))


def criar_manutencao(db: Session, dados: ManutencaoCriar) -> Manutencao:
    equipamento = db.get(Equipamento, dados.equipamento_id)
    if equipamento is None:
        raise RegistroNaoEncontradoError("Equipamento não encontrado.")
    if equipamento.status not in {"Em estoque", "Em manutenção"}:
        raise RegraDeGestaoError(
            "Devolva o equipamento antes de registrar uma manutenção."
        )
    alocacao_aberta = db.scalar(
        select(Alocacao.id).where(
            Alocacao.equipamento_id == equipamento.id,
            Alocacao.data_devolucao.is_(None),
        )
    )
    if alocacao_aberta is not None:
        raise RegraDeGestaoError("Devolva o equipamento antes de iniciar a manutenção.")

    manutencao = Manutencao(
        equipamento_id=equipamento.id,
        patrimonio=equipamento.patrimonio,
        nome_equipamento=equipamento.nome,
        data=agora(),
        laudo=dados.laudo,
        sem_conserto=dados.sem_conserto,
    )
    equipamento.status = "Baixado" if dados.sem_conserto else "Em estoque"
    db.add(manutencao)
    db.commit()
    db.refresh(manutencao)
    return manutencao


def listar_sistemas(
    db: Session, funcionario_id: int | None = None
) -> list[SistemaFuncionario]:
    consulta = select(SistemaFuncionario).order_by(SistemaFuncionario.data_inicio.desc())
    if funcionario_id is not None:
        consulta = consulta.where(SistemaFuncionario.funcionario_id == funcionario_id)
    return list(db.scalars(consulta))


def adicionar_sistema(db: Session, dados: SistemaCriar) -> SistemaFuncionario:
    funcionario = obter_funcionario(db, dados.funcionario_id)
    if not funcionario.ativo:
        raise RegraDeGestaoError("Não é possível cadastrar sistemas para funcionário inativo.")
    sistema_aberto = db.scalar(
        select(SistemaFuncionario.id).where(
            SistemaFuncionario.funcionario_id == funcionario.id,
            func.lower(SistemaFuncionario.nome_sistema) == dados.nome_sistema.lower(),
            SistemaFuncionario.data_fim.is_(None),
        )
    )
    if sistema_aberto is not None:
        raise RegraDeGestaoError("Este sistema já está registrado para o funcionário.")
    registro = SistemaFuncionario(
        funcionario_id=funcionario.id,
        nome_funcionario=funcionario.nome,
        matricula_funcionario=funcionario.matricula,
        nome_sistema=dados.nome_sistema,
        data_inicio=agora(),
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


def finalizar_sistema(db: Session, sistema_id: int) -> SistemaFuncionario:
    registro = db.get(SistemaFuncionario, sistema_id)
    if registro is None:
        raise RegistroNaoEncontradoError("Registro de sistema não encontrado.")
    if registro.data_fim is not None:
        raise RegraDeGestaoError("Este acesso ao sistema já foi encerrado.")
    registro.data_fim = agora()
    db.commit()
    db.refresh(registro)
    return registro
