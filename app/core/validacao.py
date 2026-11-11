def normalizar_email(valor: str) -> str:
    """Deixa o e-mail padronizado e verifica se o domínio tem um ponto."""
    email = valor.strip().lower()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise ValueError("Informe um e-mail válido, como nome@empresa.com.")
    return email
