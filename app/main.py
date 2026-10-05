from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from . import models  # Registra os models antes da criação das tabelas.
from .api.equipamentos import router as equipamentos_router
from .core.config import APP_DESCRIPTION, APP_TITLE, APP_VERSION
from .core.database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
)

app.include_router(equipamentos_router)


@app.get("/", tags=["Saúde"], summary="Verificar se a API está ativa")
def verificar_api() -> dict[str, str]:
    return {"mensagem": "API de equipamentos ativa.", "documentacao": "/docs"}
