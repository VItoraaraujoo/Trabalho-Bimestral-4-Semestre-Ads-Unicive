from types import SimpleNamespace
import requests
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import create_app
from app.models import Usuario
from app.core.seguranca import criar_hash_senha
import flask_app.app as flask_app_module


class RespostaFalsa:
    def __init__(self, dados, status_code=200):
        self.dados = dados
        self.status_code = status_code
        self.ok = 200 <= status_code < 300

    def json(self):
        return self.dados

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError()


def autenticar(cliente, perfil="admin", usuario_id=1):
    with cliente.session_transaction() as sessao:
        sessao["access_token"] = "token-de-teste"
        sessao["usuario"] = {
            "id": usuario_id,
            "nome": "Pessoa de teste",
            "perfil": perfil,
        }


def test_pagina_lista_equipamento_da_api(monkeypatch):
    monkeypatch.setattr(
        flask_app_module.requests,
        "get",
        lambda *args, **kwargs: RespostaFalsa(
            [
                {
                    "id": 1,
                    "nome": "Notebook de teste",
                    "tipo": "Notebook",
                    "numero_serie": "SN-001",
                    "marca": "Exemplo",
                    "modelo": "Modelo A",
                    "setor": "Laboratório",
                    "condicao": "Usado",
                    "status": "Em estoque",
                    "patrimonio": "ATI-000001",
                }
            ]
        ),
    )
    cliente = flask_app_module.app.test_client()
    autenticar(cliente)

    resposta = cliente.get("/")

    assert resposta.status_code == 200
    assert b"Notebook de teste" in resposta.data
    assert b"ATI-000001" in resposta.data


def test_pagina_principal_pede_login_sem_sessao():
    resposta = flask_app_module.app.test_client().get("/")
    assert resposta.status_code == 302
    assert "/entrar" in resposta.headers["Location"]


def test_usuario_comum_recebe_mensagem_clara_ao_tentar_cadastrar():
    cliente = flask_app_module.app.test_client()
    autenticar(cliente, perfil="comum", usuario_id=2)

    resposta = cliente.get("/novo")

    assert resposta.status_code == 403
    assert "Acesso não permitido".encode("utf-8") in resposta.data
    assert "não tem permissão".encode("utf-8") in resposta.data


def test_usuario_comum_pode_editar_somente_o_proprio_login_no_flask(monkeypatch):
    chamadas = {}

    def atualizar(url, json, headers, timeout):
        chamadas.update(url=url, json=json, headers=headers)
        return RespostaFalsa(
            {
                "id": 2,
                "nome": "Pessoa de teste",
                "email": json["email"],
                "perfil": "comum",
            }
        )

    monkeypatch.setattr(flask_app_module.requests, "patch", atualizar)
    cliente = flask_app_module.app.test_client()
    autenticar(cliente, perfil="comum", usuario_id=2)
    with cliente.session_transaction() as sessao:
        sessao["usuario"]["email"] = "pessoa@teste.com"

    formulario = cliente.get("/minha-conta")
    resposta = cliente.post(
        "/minha-conta",
        data={"email": "pessoa.nova@teste.com", "nova_senha": "senha-nova-123"},
    )
    tentativa_terceiro = cliente.get("/usuarios/editar/1")

    assert formulario.status_code == 200
    assert b"Deixe a senha em branco" in formulario.data
    assert b"senha_hash" not in formulario.data
    assert resposta.status_code == 302
    assert chamadas["url"].endswith("/usuarios/2/credenciais")
    assert chamadas["json"] == {
        "email": "pessoa.nova@teste.com",
        "nova_senha": "senha-nova-123",
    }
    assert tentativa_terceiro.status_code == 403
    with cliente.session_transaction() as sessao:
        assert sessao["usuario"]["email"] == "pessoa.nova@teste.com"


def test_login_guarda_o_token_devolvido_pela_api(monkeypatch):
    monkeypatch.setattr(
        flask_app_module.requests,
        "post",
        lambda *args, **kwargs: RespostaFalsa(
            {
                "access_token": "token-de-teste",
                "usuario": {"id": 1, "nome": "Admin", "perfil": "admin"},
            }
        ),
    )
    monkeypatch.setattr(
        flask_app_module.requests,
        "get",
        lambda *args, **kwargs: RespostaFalsa([]),
    )
    cliente = flask_app_module.app.test_client()

    resposta = cliente.post(
        "/entrar",
        data={"email": "admin@teste.com", "senha": "senha-admin-123"},
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    with cliente.session_transaction() as sessao:
        assert sessao["access_token"] == "token-de-teste"
        assert sessao["usuario"]["perfil"] == "admin"


def test_filtros_sao_enviados_para_a_api(monkeypatch):
    filtros_recebidos = {}

    def listar_com_filtros(url, params=None, headers=None, timeout=5):
        if params:
            filtros_recebidos.update(params)
        return RespostaFalsa([])

    monkeypatch.setattr(flask_app_module.requests, "get", listar_com_filtros)

    cliente = flask_app_module.app.test_client()
    autenticar(cliente)
    resposta = cliente.get("/?status=Em+uso&tipo=note&setor=labor")

    assert resposta.status_code == 200
    assert filtros_recebidos == {
        "status": "Em uso",
        "tipo": "note",
        "setor": "labor",
    }


def test_gestao_abre_rotinas_em_telas_separadas():
    cliente = flask_app_module.app.test_client()
    autenticar(cliente)

    resposta = cliente.get("/gestao")

    assert resposta.status_code == 200
    assert b'href="/funcionarios"' in resposta.data
    assert b'href="/emprestimos"' in resposta.data
    assert b'href="/manutencoes"' in resposta.data
    assert b'href="/sistemas"' in resposta.data
    assert b"/gestao#" not in resposta.data


def test_consulta_funcionario_mostra_cadastro_e_vinculos(monkeypatch):
    funcionario = {
        "id": 7,
        "nome": "Ana Souza",
        "cpf": "12345678901",
        "matricula": "MAT-007",
        "setor": "Financeiro",
        "ativo": True,
    }
    alocacao = {
        "id": 4,
        "funcionario_id": 7,
        "nome_funcionario": "Ana Souza",
        "nome_equipamento": "Notebook de teste",
        "patrimonio": "ATI-007",
        "situacao": "Em uso",
        "data_alocacao": "2026-10-20T10:00:00",
        "data_devolucao": None,
        "observacao": "Trabalho remoto",
    }
    sistema = {
        "id": 3,
        "funcionario_id": 7,
        "nome_funcionario": "Ana Souza",
        "matricula_funcionario": "MAT-007",
        "nome_sistema": "Sistema Financeiro",
        "data_inicio": "2026-10-01T10:00:00",
        "data_fim": None,
    }

    def listar(url, params=None, headers=None, timeout=5):
        if url.endswith("/funcionarios"):
            return RespostaFalsa([funcionario])
        if url.endswith("/alocacoes"):
            return RespostaFalsa([alocacao])
        if url.endswith("/sistemas"):
            return RespostaFalsa([sistema])
        raise AssertionError(f"Rota inesperada: {url}")

    monkeypatch.setattr(flask_app_module.requests, "get", listar)
    cliente = flask_app_module.app.test_client()
    autenticar(cliente)

    resposta = cliente.get("/funcionarios/consulta?q=Ana")

    assert resposta.status_code == 200
    assert b"Ana Souza" in resposta.data
    assert b"MAT-007" in resposta.data
    assert b"Financeiro" in resposta.data
    assert b"Notebook de teste" in resposta.data
    assert b"Sistema Financeiro" in resposta.data
    assert b"Trabalho remoto" in resposta.data


def test_formulario_cadastra_equipamento(monkeypatch):
    dados_enviados = {}
    monkeypatch.setattr(
        flask_app_module.requests,
        "post",
        lambda url, json, headers, timeout: (
            dados_enviados.update(json) or RespostaFalsa({}, 201)
        ),
    )
    monkeypatch.setattr(
        flask_app_module.requests,
        "get",
        lambda *args, **kwargs: RespostaFalsa([]),
    )
    cliente = flask_app_module.app.test_client()
    autenticar(cliente)

    resposta = cliente.post(
        "/novo",
        data={
            "nome": "Monitor",
            "tipo": "Monitor",
            "condicao": "Novo",
            "status": "Em estoque",
        },
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert dados_enviados["nome"] == "Monitor"
    assert dados_enviados["tipo"] == "Monitor"
    assert dados_enviados["condicao"] == "Novo"
    assert b"Equipamento cadastrado" in resposta.data


def test_api_indisponivel_mostra_opcao_para_tentar_novamente(monkeypatch):
    def api_indisponivel(*args, **kwargs):
        raise requests.ConnectionError()

    monkeypatch.setattr(flask_app_module.requests, "get", api_indisponivel)
    cliente = flask_app_module.app.test_client()
    autenticar(cliente)

    resposta = cliente.get("/")

    assert resposta.status_code == 200
    assert b"Confira se o FastAPI est" in resposta.data
    assert b"Tentar novamente" in resposta.data


def test_relatorio_mostra_resumo_recebido_da_api(monkeypatch):
    monkeypatch.setattr(
        flask_app_module.requests,
        "get",
        lambda *args, **kwargs: RespostaFalsa(
            {
                "total_equipamentos": 1,
                "por_status": [{"nome": "Em estoque", "quantidade": 1}],
                "por_tipo": [{"nome": "Notebook", "quantidade": 1}],
                "por_setor": [{"nome": "TI", "quantidade": 1}],
                "equipamentos": [
                    {
                        "id": 1,
                        "patrimonio": "ATI-000001",
                        "nome": "Notebook de teste",
                        "tipo": "Notebook",
                        "numero_serie": "SN-001",
                        "marca": "Exemplo",
                        "modelo": "Modelo A",
                        "condicao": "Usado",
                        "status": "Em estoque",
                        "setor": "TI",
                        "funcionario_id": None,
                        "nome_funcionario": None,
                        "cpf_funcionario": None,
                        "matricula_funcionario": None,
                    }
                ],
            }
        ),
    )
    cliente = flask_app_module.app.test_client()
    autenticar(cliente, perfil="comum", usuario_id=2)

    resposta = cliente.get("/relatorio")

    assert resposta.status_code == 200
    assert "Relatório de equipamentos".encode("utf-8") in resposta.data
    assert b"Notebook" in resposta.data


def test_flask_e_api_compartilham_o_mesmo_cadastro(monkeypatch, tmp_path):
    arquivo_banco = tmp_path / "integracao.db"
    engine_teste = create_engine(
        f"sqlite:///{arquivo_banco.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine_teste)
    sessao_teste = sessionmaker(bind=engine_teste, expire_on_commit=False)
    with sessao_teste() as db:
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

    def abrir_sessao_teste():
        db = sessao_teste()
        try:
            yield db
        finally:
            db.close()

    api = create_app()
    api.dependency_overrides[get_db] = abrir_sessao_teste

    def resposta_requests(resposta_api):
        resposta = requests.Response()
        resposta.status_code = resposta_api.status_code
        resposta._content = resposta_api.content
        resposta.headers.update(resposta_api.headers)
        return resposta

    with TestClient(api) as cliente_api:
        def caminho_api(url):
            return url.replace("http://127.0.0.1:8000", "")

        def consultar_api(url, timeout, params=None, headers=None):
            return resposta_requests(
                cliente_api.get(
                    caminho_api(url), params=params, headers=headers, timeout=timeout
                )
            )

        login = cliente_api.post(
            "/api/v1/auth/login",
            json={"email": "admin@teste.com", "senha": "senha-admin-123"},
        ).json()

        requisicoes_falsas = SimpleNamespace(
            Response=requests.Response,
            RequestException=requests.RequestException,
            get=consultar_api,
            post=lambda url, json=None, headers=None, timeout=5: resposta_requests(
                cliente_api.post(
                    caminho_api(url), json=json, headers=headers, timeout=timeout
                )
            ),
            put=lambda url, json, headers=None, timeout=5: resposta_requests(
                cliente_api.put(
                    caminho_api(url), json=json, headers=headers, timeout=timeout
                )
            ),
            delete=lambda url, headers=None, timeout=5: resposta_requests(
                cliente_api.delete(
                    caminho_api(url), headers=headers, timeout=timeout
                )
            ),
            patch=lambda url, headers=None, timeout=5: resposta_requests(
                cliente_api.patch(
                    caminho_api(url), headers=headers, timeout=timeout
                )
            ),
        )
        monkeypatch.setattr(flask_app_module, "requests", requisicoes_falsas)
        cliente_flask = flask_app_module.app.test_client()
        with cliente_flask.session_transaction() as sessao:
            sessao["access_token"] = login["access_token"]
            sessao["usuario"] = login["usuario"]

        cadastro = cliente_flask.post(
            "/novo",
            data={
                "nome": "Notebook integrado",
                "tipo": "Notebook",
                "condicao": "Usado",
                "status": "Em estoque",
            },
            follow_redirects=True,
        )
        assert cadastro.status_code == 200
        assert b"Notebook integrado" in cadastro.data

        edicao = cliente_flask.post(
            "/editar/1",
            data={
                "nome": "Notebook atualizado",
                "tipo": "Notebook",
                "condicao": "Usado",
                "status": "Em estoque",
            },
            follow_redirects=True,
        )
        assert edicao.status_code == 200
        cabecalho = {"Authorization": f"Bearer {login['access_token']}"}
        equipamento = cliente_api.get(
            "/api/v1/equipamentos/1", headers=cabecalho
        ).json()
        assert equipamento["nome"] == "Notebook atualizado"
        assert equipamento["status"] == "Em estoque"

        cadastro_funcionario = cliente_flask.post(
            "/funcionarios",
            data={
                "nome": "Pessoa integrada",
                "cpf": "00000000031",
                "matricula": "MAT-FLASK",
                "setor": "TI",
            },
        )
        assert cadastro_funcionario.status_code == 302
        funcionario = cliente_api.get(
            "/api/v1/funcionarios", headers=cabecalho
        ).json()[0]
        atualizacao_funcionario = cliente_flask.post(
            f"/funcionarios/editar/{funcionario['id']}",
            data={
                "nome": "Pessoa integrada",
                "cpf": "00000000031",
                "matricula": "MAT-FLASK",
                "setor": "Financeiro",
            },
        )
        assert atualizacao_funcionario.status_code == 302
        entrega = cliente_flask.post(
            "/alocacoes",
            data={
                "equipamento_id": 1,
                "funcionario_id": funcionario["id"],
                "situacao": "Em uso",
            },
        )
        assert entrega.status_code == 302
        assert cliente_api.get(
            "/api/v1/equipamentos/1", headers=cabecalho
        ).json()["status"] == "Em uso"

        sistema = cliente_flask.post(
            "/sistemas",
            data={
                "funcionario_id": funcionario["id"],
                "nome_sistema": "Microsoft 365",
            },
        )
        assert sistema.status_code == 302
        pagina_funcionario = cliente_flask.get(
            f"/funcionarios/consulta?q=Pessoa+integrada&funcionario_id={funcionario['id']}"
        )
        assert pagina_funcionario.status_code == 200
        assert b"Pessoa integrada" in pagina_funcionario.data
        assert b"Microsoft 365" in pagina_funcionario.data
        assert b"Notebook atualizado" in pagina_funcionario.data
        registro_sistema = cliente_api.get(
            "/api/v1/sistemas", headers=cabecalho
        ).json()[0]
        cliente_flask.post(
            f"/sistemas/{registro_sistema['id']}/finalizar", follow_redirects=True
        )

        alocacao = cliente_api.get(
            "/api/v1/alocacoes", headers=cabecalho
        ).json()[0]
        cliente_flask.post(
            f"/alocacoes/{alocacao['id']}/devolver", follow_redirects=True
        )
        assert cliente_api.get(
            "/api/v1/equipamentos/1", headers=cabecalho
        ).json()["status"] == "Em estoque"

        exclusao_bloqueada = cliente_flask.post("/excluir/1", follow_redirects=True)
        assert b"precisa receber baixa" in exclusao_bloqueada.data
        assert cliente_api.get(
            "/api/v1/equipamentos/1", headers=cabecalho
        ).status_code == 200

        cliente_flask.post(
            "/editar/1",
            data={
                "nome": "Notebook atualizado",
                "tipo": "Notebook",
                "condicao": "Usado",
                "status": "Em manutenção",
            },
            follow_redirects=True,
        )
        laudo = cliente_flask.post(
            "/manutencoes",
            data={
                "equipamento_id": 1,
                "laudo": "Não foi possível reparar.",
                "sem_conserto": "on",
            },
            follow_redirects=True,
        )
        assert "Laudo de manutenção registrado".encode("utf-8") in laudo.data
        exclusao = cliente_flask.post("/excluir/1", follow_redirects=True)
        assert exclusao.status_code == 200
        assert cliente_api.get(
            "/api/v1/equipamentos/1", headers=cabecalho
        ).status_code == 404

    api.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine_teste)
    engine_teste.dispose()
