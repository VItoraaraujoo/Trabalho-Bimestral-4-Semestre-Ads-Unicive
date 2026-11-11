from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.seguranca import conferir_senha, criar_hash_senha
from ..models import Usuario
from ..repositories import usuario_repository as repository
from ..schemas.usuario import (
    UsuarioAtualizar,
    UsuarioCredenciaisAtualizar,
    UsuarioCriar,
    UsuarioLogin,
)


class EmailJaCadastradoError(Exception):
    pass


class LoginInvalidoError(Exception):
    pass


class UsuarioNaoEncontradoError(Exception):
    pass


class UltimoAdministradorError(Exception):
    pass


class UsuarioAtualNaoPodeSerExcluidoError(Exception):
    pass


def criar(db: Session, dados: UsuarioCriar) -> Usuario:
    if repository.obter_por_email(db, dados.email):
        raise EmailJaCadastradoError
    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=criar_hash_senha(dados.senha),
        cpf=dados.cpf,
        matricula=dados.matricula,
        setor=dados.setor,
        perfil=dados.perfil.value,
    )
    try:
        db.add(usuario)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise EmailJaCadastradoError from exc
    db.refresh(usuario)
    return usuario


def entrar(db: Session, dados: UsuarioLogin) -> Usuario:
    usuario = repository.obter_por_email(db, dados.email.strip().lower())
    if (
        usuario is None
        or not usuario.ativo
        or not conferir_senha(dados.senha, usuario.senha_hash)
    ):
        raise LoginInvalidoError
    return usuario


def listar(db: Session) -> list[Usuario]:
    return repository.listar(db)


def atualizar(
    db: Session, usuario_id: int, dados: UsuarioAtualizar
) -> Usuario:
    usuario = repository.obter_por_id(db, usuario_id)
    if usuario is None:
        raise UsuarioNaoEncontradoError
    outro_email = repository.obter_por_email(db, dados.email)
    if outro_email is not None and outro_email.id != usuario_id:
        raise EmailJaCadastradoError

    usuario.nome = dados.nome
    usuario.email = dados.email
    usuario.cpf = dados.cpf
    usuario.matricula = dados.matricula
    usuario.setor = dados.setor
    usuario.perfil = dados.perfil.value
    if dados.senha:
        usuario.senha_hash = criar_hash_senha(dados.senha)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise EmailJaCadastradoError from exc
    db.refresh(usuario)
    return usuario


def atualizar_credenciais(
    db: Session, usuario_id: int, dados: UsuarioCredenciaisAtualizar
) -> Usuario:
    usuario = repository.obter_por_id(db, usuario_id)
    if usuario is None:
        raise UsuarioNaoEncontradoError
    outro_email = repository.obter_por_email(db, dados.email)
    if outro_email is not None and outro_email.id != usuario_id:
        raise EmailJaCadastradoError

    usuario.email = dados.email
    if dados.nova_senha:
        usuario.senha_hash = criar_hash_senha(dados.nova_senha)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise EmailJaCadastradoError from exc
    db.refresh(usuario)
    return usuario


def excluir(db: Session, usuario: Usuario, usuario_id: int) -> None:
    alvo = repository.obter_por_id(db, usuario_id)
    if alvo is None:
        raise UsuarioNaoEncontradoError
    if usuario.id == alvo.id:
        raise UsuarioAtualNaoPodeSerExcluidoError
    if alvo.perfil == "admin" and alvo.ativo:
        if repository.contar_administradores_ativos(db) <= 1:
            raise UltimoAdministradorError
    db.delete(alvo)
    db.commit()
