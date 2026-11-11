import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from . import models  # Registra os models no SQLAlchemy.
from .api.autenticacao import router as autenticacao_router
from .api.equipamentos import router as equipamentos_router
from .api.gestao import router as gestao_router
from .api.relatorios import router as relatorios_router
from .api.usuarios import router as usuarios_router
from .core.config import APP_DESCRIPTION, APP_TITLE, APP_VERSION, CORS_ORIGINS
from .core.database import get_db
from .services.relatorio_automatico import (
    executar_agendamento_relatorios,
    parar_agendamento_relatorios,
)


logger = logging.getLogger(__name__)
MENSAGEM_BANCO_INDISPONIVEL = (
    "Banco de dados indisponível. Verifique a conexão e tente novamente."
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    tarefa_relatorios = asyncio.create_task(executar_agendamento_relatorios())
    try:
        yield
    finally:
        await parar_agendamento_relatorios(tarefa_relatorios)


def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_TITLE,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(equipamentos_router, prefix="/api/v1")
    app.include_router(gestao_router, prefix="/api/v1")
    app.include_router(autenticacao_router, prefix="/api/v1")
    app.include_router(usuarios_router, prefix="/api/v1")
    app.include_router(relatorios_router, prefix="/api/v1")

    @app.exception_handler(SQLAlchemyError)
    def tratar_falha_no_banco(
        _request: Request, _erro: SQLAlchemyError
    ) -> JSONResponse:
        logger.error(
            "Falha ao acessar o banco de dados.",
            exc_info=(type(_erro), _erro, _erro.__traceback__),
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": MENSAGEM_BANCO_INDISPONIVEL},
        )

    @app.get("/", tags=["Saúde"], summary="Verificar se a API está ativa")
    def verificar_api() -> dict[str, str]:
        return {"mensagem": "API de equipamentos ativa.", "documentacao": "/docs"}

    @app.get("/health", tags=["Saúde"], summary="Verificar API e banco de dados")
    def verificar_banco(db: Session = Depends(get_db)) -> dict[str, str]:
        try:
            db.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            logger.exception("Falha ao verificar a conexão com o banco de dados.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=MENSAGEM_BANCO_INDISPONIVEL,
            ) from exc
        return {"status": "ok", "database": "connected"}

    return app


app = create_app()
