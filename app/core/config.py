import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL, make_url


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def normalizar_database_url(database_url: str) -> URL:
    """Prepara URLs do Supabase para o driver psycopg 3 do SQLAlchemy."""
    url = make_url(database_url.strip())

    # A URL copiada do painel normalmente começa com postgresql://. O driver
    # psycopg 3 precisa estar explícito para o SQLAlchemy selecionar o pacote.
    if url.drivername in {"postgres", "postgresql", "postgresql+psycopg2"}:
        url = url.set(drivername="postgresql+psycopg")

    if url.drivername.startswith("postgresql+"):
        host = (url.host or "").lower()
        if host.endswith((".supabase.co", ".supabase.com")):
            query = dict(url.query)
            query.setdefault("sslmode", "require")
            url = url.set(query=query)

    return url


_database_url = os.getenv("DATABASE_URL")
if not _database_url:
    raise RuntimeError(
        "DATABASE_URL não configurada. Copie .env.example para .env e informe "
        "a URI do banco Supabase."
    )

DATABASE_URL = normalizar_database_url(_database_url)
_diretorio_relatorios = Path(os.getenv("RELATORIOS_DIR", "relatorios"))
RELATORIOS_DIR = (
    _diretorio_relatorios
    if _diretorio_relatorios.is_absolute()
    else PROJECT_ROOT / _diretorio_relatorios
)
RELATORIO_TIMEZONE = os.getenv("RELATORIO_TIMEZONE", "America/Sao_Paulo")
CORS_ORIGINS = [
    origem.strip()
    for origem in os.getenv("CORS_ORIGINS", "").split(",")
    if origem.strip()
]

APP_TITLE = "Gestão de Equipamentos de TI"
APP_DESCRIPTION = "API para cadastrar e administrar equipamentos de TI."
APP_VERSION = "0.1.0"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "chave-local-ativoti-trocar-no-servidor")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
