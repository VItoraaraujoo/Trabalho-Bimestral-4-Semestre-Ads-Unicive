import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "equipamentos.db"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}",
)

APP_TITLE = "Gestão de Equipamentos de TI"
APP_DESCRIPTION = "API para cadastrar e administrar equipamentos de TI."
APP_VERSION = "0.1.0"
