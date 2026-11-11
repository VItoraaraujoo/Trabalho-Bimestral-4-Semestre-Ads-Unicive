from collections.abc import Generator
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Mantém os testes isolados e impede acesso ao Supabase configurado no computador.
os.environ["DATABASE_URL"] = "sqlite://"

from app.core.database import Base, get_db
from app.core.seguranca import criar_hash_senha
from app.main import create_app
from app.models import Usuario


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    database_path = tmp_path / "teste.db"
    test_engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    test_session = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )
    Base.metadata.create_all(bind=test_engine)
    with test_session() as db:
        db.add(
            Usuario(
                nome="Admin de teste",
                email="admin@teste.com",
                senha_hash=criar_hash_senha("senha-admin-123"),
                cpf="00000000001",
                matricula="ADM-TESTE",
                setor="TI",
                perfil="admin",
                ativo=True,
            )
        )
        db.commit()

    def substituir_sessao() -> Generator[Session, None, None]:
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = substituir_sessao
    try:
        with TestClient(app) as test_client:
            login = test_client.post(
                "/api/v1/auth/login",
                json={"email": "admin@teste.com", "senha": "senha-admin-123"},
            )
            test_client.headers.update(
                {"Authorization": f"Bearer {login.json()['access_token']}"}
            )
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()
