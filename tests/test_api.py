import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import normalizar_database_url


def payload(numero_serie: str | None = "SN-001") -> dict[str, str | None]:
    return {
        "nome": "Notebook de teste",
        "tipo": "Notebook",
        "numero_serie": numero_serie,
        "marca": "Exemplo",
        "modelo": "Modelo A",
        "setor": "Laboratório",
        "condicao": "Usado",
        "status": "Em estoque",
        "observacao": "Cadastro de teste",
    }


def test_crud_completo_e_filtros(client: TestClient) -> None:
    assert client.get("/api/v1/equipamentos").json() == []

    criacao = client.post("/api/v1/equipamentos", json=payload())
    assert criacao.status_code == 201
    equipamento = criacao.json()
    equipamento_id = equipamento["id"]
    assert equipamento["nome"] == "Notebook de teste"
    assert equipamento["patrimonio"] == "ATI-000001"
    assert equipamento["numero_serie"] == "SN-001"

    lista = client.get(
        "/api/v1/equipamentos", params={"tipo": "note", "setor": "labor"}
    )
    assert lista.status_code == 200
    assert [item["id"] for item in lista.json()] == [equipamento_id]
    lista_status = client.get(
        "/api/v1/equipamentos", params={"status": "Em estoque"}
    )
    assert [item["id"] for item in lista_status.json()] == [equipamento_id]

    consulta = client.get(f"/api/v1/equipamentos/{equipamento_id}")
    assert consulta.status_code == 200
    assert consulta.json()["patrimonio"] == "ATI-000001"

    atualizacao = payload()
    atualizacao["setor"] = "Financeiro"
    resposta_atualizacao = client.put(
        f"/api/v1/equipamentos/{equipamento_id}", json=atualizacao
    )
    assert resposta_atualizacao.status_code == 200
    assert resposta_atualizacao.json()["id"] == equipamento_id
    assert resposta_atualizacao.json()["status"] == "Em estoque"

    exclusao_bloqueada = client.delete(f"/api/v1/equipamentos/{equipamento_id}")
    assert exclusao_bloqueada.status_code == 409
    assert "receber baixa" in exclusao_bloqueada.json()["detail"]

    em_manutencao = payload()
    em_manutencao["status"] = "Em manutenção"
    assert client.put(
        f"/api/v1/equipamentos/{equipamento_id}", json=em_manutencao
    ).status_code == 200
    assert client.put(
        f"/api/v1/equipamentos/{equipamento_id}", json=payload()
    ).status_code == 409
    laudo = client.post(
        "/api/v1/manutencoes",
        json={"equipamento_id": equipamento_id, "laudo": "Falha na placa principal."},
    )
    assert laudo.status_code == 201
    assert laudo.json()["sem_conserto"] is False
    atualizado_para_baixa = payload()
    atualizado_para_baixa["status"] = "Baixado"
    assert client.put(
        f"/api/v1/equipamentos/{equipamento_id}", json=atualizado_para_baixa
    ).status_code == 409
    em_manutencao["status"] = "Em manutenção"
    assert client.put(
        f"/api/v1/equipamentos/{equipamento_id}", json=em_manutencao
    ).status_code == 200
    laudo_sem_conserto = client.post(
        "/api/v1/manutencoes",
        json={
            "equipamento_id": equipamento_id,
            "laudo": "Equipamento sem reparo possível.",
            "sem_conserto": True,
        },
    )
    assert laudo_sem_conserto.status_code == 201

    exclusao = client.delete(f"/api/v1/equipamentos/{equipamento_id}")
    assert exclusao.status_code == 204
    assert client.get(f"/api/v1/equipamentos/{equipamento_id}").status_code == 404


def test_numero_serie_duplicado_retorna_409(client: TestClient) -> None:
    assert client.post("/api/v1/equipamentos", json=payload()).status_code == 201
    resposta = client.post("/api/v1/equipamentos", json=payload())
    assert resposta.status_code == 409
    assert "número de série" in resposta.json()["detail"]


def test_numero_serie_pode_ficar_vazio_e_patrimonio_segue_sequencial(
    client: TestClient,
) -> None:
    primeiro = client.post("/api/v1/equipamentos", json=payload(numero_serie=None))
    segundo = client.post(
        "/api/v1/equipamentos",
        json={**payload(numero_serie=None), "nome": "Teclado de teste", "tipo": "Teclado"},
    )

    assert primeiro.status_code == 201
    assert segundo.status_code == 201
    assert primeiro.json()["patrimonio"] == "ATI-000001"
    assert segundo.json()["patrimonio"] == "ATI-000002"
    assert primeiro.json()["numero_serie"] is None


def test_health_confirma_conexao_com_banco(client: TestClient) -> None:
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "database": "connected"}


def test_relatorio_resume_equipamentos(client: TestClient) -> None:
    client.post("/api/v1/equipamentos", json=payload())
    equipamento = client.post(
        "/api/v1/equipamentos",
        json={**payload(None), "nome": "Monitor de teste", "tipo": "Monitor"},
    ).json()
    funcionario = client.post(
        "/api/v1/funcionarios",
        json={
            "nome": "Pessoa de teste",
            "cpf": "00000000011",
            "matricula": "MAT-RELATORIO",
            "setor": "TI",
        },
    ).json()
    client.post(
        "/api/v1/alocacoes",
        json={
            "equipamento_id": equipamento["id"],
            "funcionario_id": funcionario["id"],
            "situacao": "Em uso",
        },
    )

    resposta = client.get("/api/v1/relatorios/equipamentos")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["total_equipamentos"] == 2
    assert {item["nome"] for item in dados["por_status"]} == {"Em estoque", "Em uso"}
    assert {item["nome"] for item in dados["por_tipo"]} == {"Monitor", "Notebook"}
    inventario = {item["tipo"]: item for item in dados["equipamentos"]}
    assert inventario["Monitor"]["nome_funcionario"] == "Pessoa de teste"
    assert inventario["Monitor"]["matricula_funcionario"] == "MAT-RELATORIO"


def test_dados_invalidos_retorna_422(client: TestClient) -> None:
    resposta = client.post(
        "/api/v1/equipamentos",
        json={"nome": "", "tipo": "Notebook"},
    )
    assert resposta.status_code == 422


def test_usuario_exige_email_com_dominio_valido(client: TestClient) -> None:
    resposta = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Pessoa de teste",
            "email": "admin@admin",
            "senha": "senha-teste-123",
            "cpf": "00000000013",
            "matricula": "USR-EMAIL-TESTE",
            "setor": "TI",
            "perfil": "comum",
        },
    )

    assert resposta.status_code == 422


def test_id_inexistente_retorna_404(client: TestClient) -> None:
    assert client.get("/api/v1/equipamentos/999").status_code == 404
    assert client.put("/api/v1/equipamentos/999", json=payload()).status_code == 404
    assert client.delete("/api/v1/equipamentos/999").status_code == 404


def test_documentacao_openapi_tem_rotas_de_equipamento(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    openapi = client.get("/openapi.json").json()
    rotas = openapi["paths"]
    assert "/api/v1/equipamentos" in rotas
    assert "/api/v1/equipamentos/{equipamento_id}" in rotas
    assert "/api/v1/funcionarios" in rotas
    assert "/api/v1/funcionarios/{funcionario_id}" in rotas
    assert "/api/v1/alocacoes" in rotas
    assert "/api/v1/manutencoes" in rotas
    assert "/api/v1/sistemas" in rotas
    assert "409" in rotas["/api/v1/equipamentos"]["post"]["responses"]
    assert "422" in rotas["/api/v1/equipamentos"]["post"]["responses"]
    assert "404" in rotas["/api/v1/equipamentos/{equipamento_id}"]["delete"]["responses"]
    assert "409" in rotas["/api/v1/equipamentos/{equipamento_id}"]["delete"]["responses"]


def test_login_com_senha_protegida_e_retorno_sem_senha(client: TestClient) -> None:
    resposta = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@teste.com", "senha": "senha-admin-123"},
    )
    assert resposta.status_code == 200
    assert resposta.json()["token_type"] == "bearer"
    assert resposta.json()["usuario"]["perfil"] == "admin"
    assert "senha" not in resposta.json()["usuario"]
    assert "senha_hash" not in resposta.json()["usuario"]

    senha_incorreta = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@teste.com", "senha": "senha-errada"},
    )
    assert senha_incorreta.status_code == 401


def test_rotas_exigem_login(client: TestClient) -> None:
    client.headers.pop("Authorization", None)
    resposta = client.get("/api/v1/equipamentos")
    assert resposta.status_code == 401


def test_usuario_comum_pode_consultar_mas_nao_alterar(client: TestClient) -> None:
    novo_usuario = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Pessoa de consulta",
            "email": "consulta@teste.com",
            "senha": "senha-comum-123",
            "cpf": "00000000002",
            "matricula": "USR-TESTE",
            "setor": "Financeiro",
            "perfil": "comum",
        },
    )
    assert novo_usuario.status_code == 201
    assert "senha_hash" not in novo_usuario.json()

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "consulta@teste.com", "senha": "senha-comum-123"},
    )
    client.headers.update(
        {"Authorization": f"Bearer {login.json()['access_token']}"}
    )

    assert client.get("/api/v1/equipamentos").status_code == 200
    assert client.get("/api/v1/relatorios/equipamentos").status_code == 200
    assert client.post(
        "/api/v1/equipamentos", json=payload()
    ).status_code == 403
    assert client.get("/api/v1/usuarios").status_code == 403


def test_administrador_nao_pode_excluir_a_si_mesmo(client: TestClient) -> None:
    resposta = client.delete("/api/v1/usuarios/1")
    assert resposta.status_code == 409
    assert "próprio acesso" in resposta.json()["detail"]


def _criar_usuario_comum(client: TestClient, email: str = "pessoa@teste.com") -> int:
    resposta = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Pessoa de teste",
            "email": email,
            "senha": "senha-atual-123",
            "cpf": "00000000022",
            "matricula": "USR-CREDENCIAIS",
            "setor": "TI",
            "perfil": "comum",
        },
    )
    assert resposta.status_code == 201
    return resposta.json()["id"]


def test_admin_altera_login_e_senha_sem_expor_senha(client: TestClient) -> None:
    usuario_id = _criar_usuario_comum(client)

    alteracao = client.patch(
        f"/api/v1/usuarios/{usuario_id}/credenciais",
        json={"email": "pessoa.nova@teste.com", "nova_senha": "senha-nova-123"},
    )

    assert alteracao.status_code == 200
    assert alteracao.json()["email"] == "pessoa.nova@teste.com"
    assert alteracao.json()["perfil"] == "comum"
    assert "senha" not in alteracao.json()
    assert "senha_hash" not in alteracao.json()
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "pessoa@teste.com", "senha": "senha-atual-123"},
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "pessoa.nova@teste.com", "senha": "senha-nova-123"},
    ).status_code == 200


def test_usuario_comum_pode_alterar_suas_credenciais_e_nao_as_de_terceiros(
    client: TestClient,
) -> None:
    usuario_id = _criar_usuario_comum(client)
    outro_usuario_id = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Outra pessoa",
            "email": "outra@teste.com",
            "senha": "senha-atual-456",
            "cpf": "00000000023",
            "matricula": "USR-OUTRO",
            "setor": "TI",
            "perfil": "comum",
        },
    ).json()["id"]
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "pessoa@teste.com", "senha": "senha-atual-123"},
    )
    client.headers.update(
        {"Authorization": f"Bearer {login.json()['access_token']}"}
    )

    propria_conta = client.patch(
        f"/api/v1/usuarios/{usuario_id}/credenciais",
        json={"email": "pessoa.atualizada@teste.com", "nova_senha": ""},
    )
    tentativa_terceiro = client.patch(
        f"/api/v1/usuarios/{outro_usuario_id}/credenciais",
        json={"email": "alterada@teste.com", "nova_senha": "senha-nova-123"},
    )

    assert propria_conta.status_code == 200
    assert propria_conta.json()["perfil"] == "comum"
    assert "senha" not in propria_conta.json()
    assert "senha_hash" not in propria_conta.json()
    assert tentativa_terceiro.status_code == 403
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "pessoa.atualizada@teste.com", "senha": "senha-atual-123"},
    ).status_code == 200


def test_senha_nova_invalida_e_email_repetido_sao_rejeitados(client: TestClient) -> None:
    usuario_id = _criar_usuario_comum(client)
    senha_curta = client.patch(
        f"/api/v1/usuarios/{usuario_id}/credenciais",
        json={"email": "pessoa@teste.com", "nova_senha": "curta"},
    )
    senha_utf8_longa = client.patch(
        f"/api/v1/usuarios/{usuario_id}/credenciais",
        json={"email": "pessoa@teste.com", "nova_senha": "á" * 37},
    )
    email_repetido = client.patch(
        f"/api/v1/usuarios/{usuario_id}/credenciais",
        json={"email": "admin@teste.com", "nova_senha": ""},
    )

    assert senha_curta.status_code == 422
    assert senha_utf8_longa.status_code == 422
    assert email_repetido.status_code == 409


def test_falha_no_banco_retorna_mensagem_segura(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api import equipamentos as rotas_equipamento

    def falhar_ao_criar(*args, **kwargs):
        raise SQLAlchemyError("detalhe interno que não deve aparecer")

    monkeypatch.setattr(
        rotas_equipamento.equipamento_service, "criar", falhar_ao_criar
    )

    resposta = client.post("/api/v1/equipamentos", json=payload())

    assert resposta.status_code == 503
    assert resposta.json() == {
        "detail": "Banco de dados indisponível. Verifique a conexão e tente novamente."
    }
    assert "detalhe interno" not in resposta.text


def test_url_postgresql_do_supabase_usa_psycopg_e_ssl() -> None:
    url = normalizar_database_url(
        "postgresql://postgres:senha@db.abc123.supabase.co:5432/postgres"
    )
    assert url.drivername == "postgresql+psycopg"
    assert url.query["sslmode"] == "require"


def test_url_postgres_preserva_parametros_existentes() -> None:
    url = normalizar_database_url(
        "postgres://postgres:senha@db.abc123.supabase.co/postgres?sslmode=verify-full"
    )
    assert url.drivername == "postgresql+psycopg"
    assert url.query["sslmode"] == "verify-full"
