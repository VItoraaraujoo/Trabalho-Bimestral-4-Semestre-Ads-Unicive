from getpass import getpass

from ..repositories.usuario_repository import obter_por_email
from .database import SessionLocal
from .seguranca import criar_hash_senha
from .validacao import normalizar_email


def main() -> None:
    try:
        email = normalizar_email(input("E-mail do administrador: ").strip())
    except ValueError:
        print("Informe o e-mail usado no cadastro do administrador.")
        return

    senha = getpass("Nova senha (mínimo 8 caracteres): ")
    confirmacao = getpass("Confirme a nova senha: ")

    if senha != confirmacao:
        print("As senhas não conferem.")
        return
    if len(senha) < 8:
        print("A senha deve ter pelo menos 8 caracteres.")
        return
    if len(senha.encode("utf-8")) > 72:
        print("A senha deve ter no máximo 72 bytes.")
        return

    with SessionLocal() as db:
        administrador = obter_por_email(db, email)
        if (
            administrador is None
            or administrador.perfil != "admin"
            or not administrador.ativo
        ):
            print("Não foi encontrado um administrador ativo com esse e-mail.")
            return

        administrador.senha_hash = criar_hash_senha(senha)
        db.commit()

    print("Senha do administrador redefinida. Você já pode entrar no site.")


if __name__ == "__main__":
    main()
