from fastapi.testclient import TestClient

def payload() -> dict[str, str | None]:
    return {
        "nome": "Equipamento de teste",
        "tipo": "Notebook",
        "numero_serie": None,
        "marca": "Exemplo",
        "modelo": "Modelo A",
        "setor": "TI",
        "condicao": "Usado",
        "status": "Em estoque",
        "observacao": None,
    }


def criar_funcionario(client: TestClient, matricula: str = "MAT-001") -> dict:
    resposta = client.post(
        "/api/v1/funcionarios",
        json={
            "nome": "Ana de Souza",
            "cpf": "123.456.789-01",
            "matricula": matricula,
            "setor": "Financeiro",
        },
    )
    assert resposta.status_code == 201
    return resposta.json()


def criar_equipamento(client: TestClient, nome: str) -> dict:
    resposta = client.post(
        "/api/v1/equipamentos",
        json={**payload(), "nome": nome, "tipo": "Notebook"},
    )
    assert resposta.status_code == 201
    return resposta.json()


def test_entrega_devolucao_laudo_baixa_e_historico(client: TestClient) -> None:
    funcionario = criar_funcionario(client)
    assert client.get(f"/api/v1/funcionarios/{funcionario['id']}").status_code == 200
    equipamento = criar_equipamento(client, "Notebook da Ana")
    dados_alocacao = {
        "equipamento_id": equipamento["id"],
        "funcionario_id": funcionario["id"],
        "situacao": "Emprestado",
        "observacao": "Empréstimo para viagem.",
    }

    alocacao = client.post("/api/v1/alocacoes", json=dados_alocacao)
    assert alocacao.status_code == 201
    assert alocacao.json()["cpf_funcionario"] == "12345678901"
    assert client.get(f"/api/v1/equipamentos/{equipamento['id']}").json()["status"] == "Emprestado"
    assert client.post("/api/v1/alocacoes", json=dados_alocacao).status_code == 409

    devolucao = client.post(f"/api/v1/alocacoes/{alocacao.json()['id']}/devolver")
    assert devolucao.status_code == 200
    assert devolucao.json()["data_devolucao"] is not None
    assert client.get(f"/api/v1/equipamentos/{equipamento['id']}").json()["status"] == "Em estoque"

    laudo = client.post(
        "/api/v1/manutencoes",
        json={
            "equipamento_id": equipamento["id"],
            "laudo": "Placa principal danificada e sem peça para reposição.",
            "sem_conserto": True,
        },
    )
    assert laudo.status_code == 201
    assert laudo.json()["sem_conserto"] is True
    assert client.get(f"/api/v1/equipamentos/{equipamento['id']}").json()["status"] == "Baixado"

    assert client.delete(f"/api/v1/equipamentos/{equipamento['id']}").status_code == 204
    historico = client.get("/api/v1/manutencoes").json()
    assert historico[0]["equipamento_id"] is None
    assert historico[0]["patrimonio"] == equipamento["patrimonio"]
    assert historico[0]["laudo"].startswith("Placa principal")
    alocacoes = client.get("/api/v1/alocacoes", params={"funcionario_id": funcionario["id"]}).json()
    assert len(alocacoes) == 1
    assert alocacoes[0]["nome_equipamento"] == "Notebook da Ana"


def test_remover_funcionario_fecha_vinculos_e_preserva_historicos(client: TestClient) -> None:
    funcionario = criar_funcionario(client, "MAT-002")
    equipamento = criar_equipamento(client, "Notebook reserva")
    alocacao = client.post(
        "/api/v1/alocacoes",
        json={
            "equipamento_id": equipamento["id"],
            "funcionario_id": funcionario["id"],
            "situacao": "Em uso",
        },
    ).json()
    sistema = client.post(
        "/api/v1/sistemas",
        json={"funcionario_id": funcionario["id"], "nome_sistema": "Microsoft 365"},
    )
    assert sistema.status_code == 201
    duplicado = client.post(
        "/api/v1/sistemas",
        json={"funcionario_id": funcionario["id"], "nome_sistema": "microsoft 365"},
    )
    assert duplicado.status_code == 409

    atualizacao = client.put(
        f"/api/v1/funcionarios/{funcionario['id']}",
        json={
            "nome": "Ana Silva",
            "cpf": "12345678901",
            "matricula": "MAT-002",
            "setor": "TI",
        },
    )
    assert atualizacao.status_code == 200

    removido = client.delete(f"/api/v1/funcionarios/{funcionario['id']}")
    assert removido.status_code == 204
    assert client.get(f"/api/v1/equipamentos/{equipamento['id']}").json()["status"] == "Em estoque"
    assert client.get("/api/v1/alocacoes").json()[0]["data_devolucao"] is not None
    assert client.get("/api/v1/sistemas").json()[0]["data_fim"] is not None
    assert client.get("/api/v1/funcionarios").json() == []
    arquivados = client.get("/api/v1/funcionarios", params={"incluir_inativos": True}).json()
    assert arquivados[0]["ativo"] is False
    assert client.post(f"/api/v1/alocacoes/{alocacao['id']}/devolver").status_code == 409
    assert client.get("/api/v1/alocacoes").json()[0]["nome_funcionario"] == "Ana de Souza"


def test_usuario_comum_pode_ler_historicos_mas_nao_altera(client: TestClient) -> None:
    resposta_usuario = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Consulta",
            "email": "consulta-historicos@teste.com",
            "senha": "senha-comum-123",
            "cpf": "00000000021",
            "matricula": "USR-HIST",
            "setor": "TI",
            "perfil": "comum",
        },
    )
    assert resposta_usuario.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "consulta-historicos@teste.com", "senha": "senha-comum-123"},
    ).json()
    client.headers.update({"Authorization": f"Bearer {login['access_token']}"})
    assert client.get("/api/v1/funcionarios").status_code == 200
    assert client.get("/api/v1/alocacoes").status_code == 200
    assert client.get("/api/v1/manutencoes").status_code == 200
    assert client.get("/api/v1/sistemas").status_code == 200
    assert client.post(
        "/api/v1/funcionarios",
        json={"nome": "Bloqueado", "cpf": "00000000022", "matricula": "X", "setor": "TI"},
    ).status_code == 403
