from getpass import getpass

from sqlalchemy.exc import IntegrityError

from ..models import Usuario
from ..repositories.usuario_repository import obter_por_email
from .database import SessionLocal
from .seguranca import criar_hash_senha
from .validacao import normalizar_email


def main() -> None:
    email = input("E-mail do administrador: ").strip()
    nome = input("Nome completo: ").strip()
    cpf = input("CPF (11 números): ").strip().replace(".", "").replace("-", "")
    matricula = input("Matrícula: ").strip()
    setor = input("Setor: ").strip()
    senha = getpass("Senha (mínimo 8 caracteres): ")
    try:
        email = normalizar_email(email)
    except ValueError:
        print("Informe um e-mail válido, como nome@empresa.com.")
        return

    if (
        not nome
        or not matricula
        or not setor
        or len(senha) < 8
        or len(cpf) != 11
        or not cpf.isdigit()
    ):
        print("Confira nome, e-mail, matrícula, setor, senha e CPF antes de tentar novamente.")
        return

    with SessionLocal() as db:
        if obter_por_email(db, email):
            print("Já existe um usuário com esse e-mail.")
            return
        administrador = Usuario(
            nome=nome,
            email=email,
            senha_hash=criar_hash_senha(senha),
            cpf=cpf,
            matricula=matricula,
            setor=setor,
            perfil="admin",
            ativo=True,
        )
        db.add(administrador)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            print("Não foi possível criar o administrador. Verifique os dados.")
            return
    print("Administrador criado. Use o e-mail e a senha na tela de acesso.")


if __name__ == "__main__":
    main()
