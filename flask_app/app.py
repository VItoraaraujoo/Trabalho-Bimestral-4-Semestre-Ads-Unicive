import os
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

import requests
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "ativoti-chave-local")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("FLASK_COOKIE_SECURE", "false").lower()
    == "true",
)


@app.template_filter("cpf_mascarado")
def cpf_mascarado(valor: object) -> str:
    """Oculta o CPF em telas de consulta e preserva apenas os dois últimos dígitos."""
    texto = str(valor or "").strip()
    digitos = "".join(caractere for caractere in texto if caractere.isdigit())
    if len(digitos) != 11:
        return texto or "—"
    return f"***.***.***-{digitos[-2:]}"

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")
URL_EQUIPAMENTOS = f"{API_URL}/equipamentos"
URL_AUTENTICACAO = f"{API_URL}/auth"
URL_USUARIOS = f"{API_URL}/usuarios"
URL_RELATORIO = f"{API_URL}/relatorios/equipamentos"
URL_FUNCIONARIOS = f"{API_URL}/funcionarios"
URL_ALOCACOES = f"{API_URL}/alocacoes"
URL_MANUTENCOES = f"{API_URL}/manutencoes"
URL_SISTEMAS = f"{API_URL}/sistemas"
STATUS_EQUIPAMENTO = [
    "Em estoque",
    "Em uso",
    "Emprestado",
    "Em manutenção",
    "Baixado",
]
CONDICAO_EQUIPAMENTO = [
    "Novo",
    "Usado",
]


@app.errorhandler(403)
def acesso_negado(_erro):
    return (
        render_template("erro_permissao.html"),
        403,
    )


def mensagem_erro_api(resposta: requests.Response) -> str:
    try:
        detalhe = resposta.json().get("detail", "A API recusou a solicitação.")
    except ValueError:
        return "A API respondeu com um erro. Tente novamente."

    if isinstance(detalhe, list):
        return "Confira os campos obrigatórios e tente novamente."
    return str(detalhe)


def cabecalhos_api() -> dict[str, str]:
    return {"Authorization": f"Bearer {session['access_token']}"}


def login_obrigatorio(funcao):
    @wraps(funcao)
    def verificar_login(*args, **kwargs):
        if not session.get("access_token"):
            return redirect(url_for("entrar"))
        return funcao(*args, **kwargs)

    return verificar_login


def administrador_obrigatorio(funcao):
    @wraps(funcao)
    @login_obrigatorio
    def verificar_perfil(*args, **kwargs):
        usuario = session.get("usuario", {})
        if usuario.get("perfil") != "admin":
            abort(403)
        return funcao(*args, **kwargs)

    return verificar_perfil


def dados_do_formulario() -> dict[str, str | None]:
    campos = [
        "nome",
        "tipo",
        "numero_serie",
        "marca",
        "modelo",
        "setor",
        "condicao",
        "status",
        "observacao",
    ]
    dados = {}
    for campo in campos:
        valor = request.form.get(campo, "").strip()
        dados[campo] = valor or None
    return dados


def status_editaveis(status_atual: str | None = None) -> list[str]:
    if status_atual in {"Em uso", "Emprestado", "Baixado"}:
        return [status_atual]
    if status_atual == "Em manutenção":
        return ["Em manutenção"]
    return ["Em estoque", "Em manutenção"]


@app.route("/entrar", methods=["GET", "POST"])
def entrar():
    if session.get("access_token"):
        return redirect(url_for("inicio"))
    if request.method == "POST":
        try:
            resposta = requests.post(
                f"{URL_AUTENTICACAO}/login",
                json={
                    "email": request.form.get("email", "").strip(),
                    "senha": request.form.get("senha", ""),
                },
                timeout=5,
            )
            if resposta.ok:
                dados = resposta.json()
                session["access_token"] = dados["access_token"]
                session["usuario"] = dados["usuario"]
                return redirect(url_for("inicio"))
            flash(mensagem_erro_api(resposta), "erro")
        except (requests.RequestException, ValueError, KeyError):
            flash("Não consegui acessar a API. Confira se o FastAPI está em execução.", "erro")
    return render_template("entrar.html")


@app.post("/sair")
def sair():
    session.clear()
    return redirect(url_for("entrar"))


@app.get("/dashboard")
@login_obrigatorio
def dashboard():
    equipamentos = []
    erro = None
    try:
        equipamentos = _get_lista_api(URL_EQUIPAMENTOS)
    except (requests.RequestException, ValueError):
        erro = "Não consegui carregar o resumo. Confira se o FastAPI está em execução."

    resumo = {
        "total": len(equipamentos),
        "em_uso": sum(
            item.get("status") in {"Em uso", "Emprestado"} for item in equipamentos
        ),
        "manutencao": sum(
            item.get("status") == "Em manutenção" for item in equipamentos
        ),
        "indisponiveis": sum(
            item.get("status") == "Baixado" for item in equipamentos
        ),
    }
    return render_template(
        "dashboard.html",
        resumo=resumo,
        equipamentos=equipamentos[:6],
        erro=erro,
    )


@app.get("/relatorio")
@login_obrigatorio
def relatorio():
    dados = None
    erro = None
    try:
        resposta = requests.get(
            URL_RELATORIO,
            headers=cabecalhos_api(),
            timeout=5,
        )
        resposta.raise_for_status()
        dados = resposta.json()
    except requests.RequestException:
        erro = "Não consegui carregar o relatório. Confira se o FastAPI está em execução."
    except ValueError:
        erro = "A resposta da API não pôde ser lida."
    return render_template("relatorio.html", relatorio=dados, erro=erro)


@app.get("/")
@login_obrigatorio
def inicio():
    filtros = {
        "status": request.args.get("status", ""),
        "tipo": request.args.get("tipo", "").strip(),
        "setor": request.args.get("setor", "").strip(),
        "q": request.args.get("q", "").strip(),
    }
    parametros = {
        chave: filtros[chave]
        for chave in ("status", "tipo", "setor")
        if filtros[chave]
    }
    equipamentos = []
    todos_equipamentos = []
    erro = None
    try:
        if parametros:
            equipamentos, todos_equipamentos = _get_listas_api(
                [URL_EQUIPAMENTOS, URL_EQUIPAMENTOS], [parametros, None]
            )
        else:
            equipamentos = _get_lista_api(URL_EQUIPAMENTOS)
            todos_equipamentos = equipamentos
    except requests.RequestException:
        erro = "Não consegui acessar a API. Confira se o FastAPI está em execução."
    except ValueError:
        erro = "A resposta da API não pôde ser lida."

    if filtros["q"]:
        consulta = filtros["q"].casefold()
        equipamentos = [
            item
            for item in equipamentos
            if consulta
            in " ".join(
                str(item.get(campo) or "")
                for campo in ("nome", "patrimonio", "tipo", "marca", "modelo", "setor")
            ).casefold()
        ]

    resumo = {
        "total": len(todos_equipamentos),
        "em_uso": sum(
            item.get("status") in {"Em uso", "Emprestado"}
            for item in todos_equipamentos
        ),
        "manutencao": sum(
            item.get("status") == "Em manutenção" for item in todos_equipamentos
        ),
        "estoque": sum(
            item.get("status") == "Em estoque" for item in todos_equipamentos
        ),
        "indisponiveis": sum(
            item.get("status") == "Baixado" for item in todos_equipamentos
        ),
    }

    return render_template(
        "index.html",
        equipamentos=equipamentos,
        resumo=resumo,
        erro=erro,
        filtros=filtros,
        status_equipamento=STATUS_EQUIPAMENTO,
        condicao_equipamento=CONDICAO_EQUIPAMENTO,
        pode_editar=session.get("usuario", {}).get("perfil") == "admin",
    )


@app.route("/novo", methods=["GET", "POST"])
@administrador_obrigatorio
def novo_equipamento():
    status_formulario = ["Em estoque"]
    if request.method == "POST":
        dados = dados_do_formulario()
        if not dados["nome"] or not dados["tipo"]:
            flash("Preencha o nome e o tipo do equipamento.", "erro")
            return render_template(
                "formulario.html",
                equipamento=dados,
                status_equipamento=status_formulario,
                condicao_equipamento=CONDICAO_EQUIPAMENTO,
            )

        try:
            resposta = requests.post(
                URL_EQUIPAMENTOS,
                json=dados,
                headers=cabecalhos_api(),
                timeout=5,
            )
            if resposta.ok:
                flash("Equipamento cadastrado.", "sucesso")
                return redirect(url_for("inicio"))
            flash(mensagem_erro_api(resposta), "erro")
        except requests.RequestException:
            flash("Não consegui acessar a API. Confira se o FastAPI está em execução.", "erro")

        return render_template(
            "formulario.html",
            equipamento=dados,
            status_equipamento=status_formulario,
            condicao_equipamento=CONDICAO_EQUIPAMENTO,
        )

    return render_template(
        "formulario.html",
        equipamento=None,
        status_equipamento=status_formulario,
        condicao_equipamento=CONDICAO_EQUIPAMENTO,
    )


@app.route("/editar/<int:equipamento_id>", methods=["GET", "POST"])
@administrador_obrigatorio
def editar_equipamento(equipamento_id: int):
    if request.method == "POST":
        dados = dados_do_formulario()
        status_original = request.form.get("status_original", "Em estoque")
        dados["status_original"] = status_original
        status_formulario = status_editaveis(status_original)
        if not dados["nome"] or not dados["tipo"]:
            flash("Preencha o nome e o tipo do equipamento.", "erro")
            dados["id"] = equipamento_id
            return render_template(
                "formulario.html",
                equipamento=dados,
                status_equipamento=status_formulario,
                condicao_equipamento=CONDICAO_EQUIPAMENTO,
            )

        try:
            resposta = requests.put(
                f"{URL_EQUIPAMENTOS}/{equipamento_id}",
                json={campo: valor for campo, valor in dados.items() if campo != "status_original"},
                headers=cabecalhos_api(),
                timeout=5,
            )
            if resposta.ok:
                flash("Equipamento atualizado.", "sucesso")
                return redirect(url_for("inicio"))
            flash(mensagem_erro_api(resposta), "erro")
        except requests.RequestException:
            flash("Não consegui acessar a API. Confira se o FastAPI está em execução.", "erro")

        dados["id"] = equipamento_id
        return render_template(
            "formulario.html",
            equipamento=dados,
            status_equipamento=status_formulario,
            condicao_equipamento=CONDICAO_EQUIPAMENTO,
        )

    try:
        resposta = requests.get(
            f"{URL_EQUIPAMENTOS}/{equipamento_id}",
            headers=cabecalhos_api(),
            timeout=5,
        )
        if resposta.status_code == 404:
            flash("Equipamento não encontrado.", "erro")
            return redirect(url_for("inicio"))
        resposta.raise_for_status()
        equipamento = resposta.json()
    except requests.RequestException:
        flash("Não consegui acessar a API. Confira se o FastAPI está em execução.", "erro")
        return redirect(url_for("inicio"))

    return render_template(
        "formulario.html",
        equipamento=equipamento,
        status_equipamento=status_editaveis(equipamento.get("status")),
        condicao_equipamento=CONDICAO_EQUIPAMENTO,
    )


@app.post("/excluir/<int:equipamento_id>")
@administrador_obrigatorio
def excluir_equipamento(equipamento_id: int):
    try:
        resposta = requests.delete(
            f"{URL_EQUIPAMENTOS}/{equipamento_id}",
            headers=cabecalhos_api(),
            timeout=5,
        )
        if resposta.status_code == 204:
            flash("Equipamento excluído.", "sucesso")
        else:
            flash(mensagem_erro_api(resposta), "erro")
    except requests.RequestException:
        flash("Não consegui acessar a API. Confira se o FastAPI está em execução.", "erro")
    return redirect(url_for("inicio"))


@app.route("/usuarios", methods=["GET", "POST"])
@administrador_obrigatorio
def usuarios():
    if request.method == "POST":
        dados = {
            "nome": request.form.get("nome", "").strip(),
            "email": request.form.get("email", "").strip(),
            "senha": request.form.get("senha", ""),
            "cpf": request.form.get("cpf", "").strip(),
            "matricula": request.form.get("matricula", "").strip(),
            "setor": request.form.get("setor", "").strip(),
            "perfil": request.form.get("perfil", "comum"),
        }
        try:
            resposta = requests.post(
                URL_USUARIOS,
                json=dados,
                headers=cabecalhos_api(),
                timeout=5,
            )
            if resposta.status_code == 201:
                flash("Usuário cadastrado.", "sucesso")
                return redirect(url_for("usuarios"))
            flash(mensagem_erro_api(resposta), "erro")
        except requests.RequestException:
            flash("Não consegui acessar a API. Confira se o FastAPI está em execução.", "erro")

    lista = []
    erro = None
    try:
        resposta = requests.get(URL_USUARIOS, headers=cabecalhos_api(), timeout=5)
        resposta.raise_for_status()
        lista = resposta.json()
    except requests.RequestException:
        erro = "Não consegui carregar os usuários. Confira se o FastAPI está em execução."
    except ValueError:
        erro = "A resposta da API não pôde ser lida."
    return render_template("usuarios.html", usuarios=lista, erro=erro)


@app.post("/usuarios/excluir/<int:usuario_id>")
@administrador_obrigatorio
def excluir_usuario(usuario_id: int):
    if usuario_id == session.get("usuario", {}).get("id"):
        flash("Não é possível excluir o usuário conectado.", "erro")
        return redirect(url_for("usuarios"))
    try:
        resposta = requests.delete(
            f"{URL_USUARIOS}/{usuario_id}",
            headers=cabecalhos_api(),
            timeout=5,
        )
        if resposta.status_code == 204:
            flash("Usuário excluído.", "sucesso")
        else:
            flash(mensagem_erro_api(resposta), "erro")
    except requests.RequestException:
        flash("Não consegui acessar a API. Confira se o FastAPI está em execução.", "erro")
    return redirect(url_for("usuarios"))


def _url_destino_credenciais(destino: str, usuario_id: int):
    if destino == "editar_credenciais_usuario":
        return url_for(destino, usuario_id=usuario_id)
    return url_for(destino)


def _salvar_credenciais(usuario_id: int, destino: str):
    email = request.form.get("email", "").strip()
    nova_senha = request.form.get("nova_senha", "")
    if not email or "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        flash("Informe um e-mail válido para o login.", "erro")
        return redirect(_url_destino_credenciais(destino, usuario_id))
    if nova_senha.strip() and len(nova_senha) < 8:
        flash("A nova senha deve ter pelo menos 8 caracteres.", "erro")
        return redirect(_url_destino_credenciais(destino, usuario_id))
    if nova_senha.strip() and len(nova_senha.encode("utf-8")) > 72:
        flash("A nova senha deve ter no máximo 72 bytes.", "erro")
        return redirect(_url_destino_credenciais(destino, usuario_id))

    try:
        resposta = requests.patch(
            f"{URL_USUARIOS}/{usuario_id}/credenciais",
            json={"email": email, "nova_senha": nova_senha},
            headers=cabecalhos_api(),
            timeout=5,
        )
        if resposta.status_code == 200:
            usuario_atualizado = resposta.json()
            if usuario_id == session.get("usuario", {}).get("id"):
                session["usuario"] = usuario_atualizado
            flash("Credenciais atualizadas com sucesso.", "sucesso")
            return redirect(_url_destino_credenciais(destino, usuario_id))
        flash(mensagem_erro_api(resposta), "erro")
    except requests.RequestException:
        flash("Não consegui acessar a API. Confira se o FastAPI está em execução.", "erro")
    except ValueError:
        flash("A resposta da API não pôde ser lida.", "erro")
    return redirect(_url_destino_credenciais(destino, usuario_id))


@app.route("/minha-conta", methods=["GET", "POST"])
@login_obrigatorio
def minha_conta():
    usuario = session.get("usuario", {})
    if request.method == "POST":
        return _salvar_credenciais(usuario.get("id"), "minha_conta")
    return render_template(
        "credenciais.html",
        usuario_alvo=usuario,
        modo_admin=False,
    )


@app.route("/usuarios/editar/<int:usuario_id>", methods=["GET", "POST"])
@administrador_obrigatorio
def editar_credenciais_usuario(usuario_id: int):
    if request.method == "POST":
        return _salvar_credenciais(usuario_id, "editar_credenciais_usuario")
    try:
        lista = _get_lista_api(URL_USUARIOS)
    except (requests.RequestException, ValueError):
        flash("Não consegui carregar os usuários. Confira se o FastAPI está em execução.", "erro")
        return redirect(url_for("usuarios"))
    usuario_alvo = next((item for item in lista if item.get("id") == usuario_id), None)
    if usuario_alvo is None:
        abort(404)
    return render_template(
        "credenciais.html",
        usuario_alvo=usuario_alvo,
        modo_admin=True,
    )


def _get_lista_api(url: str) -> list[dict]:
    resposta = requests.get(url, headers=cabecalhos_api(), timeout=5)
    resposta.raise_for_status()
    return resposta.json()


def _get_listas_api(
    urls: list[str], parametros: list[dict | None] | None = None
) -> list[list[dict]]:
    if not urls:
        return []

    cabecalhos = cabecalhos_api()
    if parametros is None:
        parametros = [None] * len(urls)
    with ThreadPoolExecutor(max_workers=len(urls)) as executor:
        consultas = [
            executor.submit(_get_lista_api_com_parametros, url, params, cabecalhos)
            for url, params in zip(urls, parametros)
        ]
        return [consulta.result() for consulta in consultas]


def _get_lista_api_com_parametros(
    url: str, parametros: dict | None, cabecalhos: dict[str, str]
) -> list[dict]:
    opcoes = {"headers": cabecalhos, "timeout": 5}
    if parametros:
        opcoes["params"] = parametros
    resposta = requests.get(url, **opcoes)
    resposta.raise_for_status()
    return resposta.json()


@app.get("/gestao")
@login_obrigatorio
def gestao():
    return render_template("gestao.html")


@app.get("/funcionarios")
@login_obrigatorio
def funcionarios():
    consulta = request.args.get("q", "").strip().casefold()
    try:
        dados = _get_lista_api(URL_FUNCIONARIOS)
        erro = None
    except (requests.RequestException, ValueError):
        dados = []
        erro = "Não consegui carregar os funcionários. Confira se o FastAPI está em execução."
    if consulta:
        dados = [
            pessoa
            for pessoa in dados
            if consulta
            in " ".join(
                str(pessoa.get(campo) or "")
                for campo in ("nome", "cpf", "matricula", "setor")
            ).casefold()
        ]
    return render_template(
        "funcionarios.html",
        funcionarios=dados,
        erro=erro,
        pode_editar=session.get("usuario", {}).get("perfil") == "admin",
    )


@app.get("/funcionarios/novo")
@administrador_obrigatorio
def novo_funcionario():
    return render_template("funcionario_novo.html")


@app.get("/funcionarios/consulta")
@login_obrigatorio
def consulta_funcionarios():
    consulta = request.args.get("q", "").strip()
    funcionario_id = request.args.get("funcionario_id", type=int)
    pode_editar = session.get("usuario", {}).get("perfil") == "admin"
    parametros = {"incluir_inativos": "true"}
    funcionarios_encontrados = []
    funcionario = None
    alocacoes = []
    sistemas = []
    erro = None
    try:
        funcionarios_encontrados = _get_lista_api_com_parametros(
            URL_FUNCIONARIOS, parametros, cabecalhos_api()
        )
        if consulta:
            termo = consulta.casefold()
            digitos = "".join(caractere for caractere in termo if caractere.isdigit())
            funcionarios_encontrados = [
                pessoa
                for pessoa in funcionarios_encontrados
                if termo
                in " ".join(
                    str(pessoa.get(campo) or "")
                    for campo in ("nome", "matricula", "setor")
                ).casefold()
                or (digitos and digitos in str(pessoa.get("cpf") or ""))
            ]
        if funcionario_id is not None:
            funcionario = next(
                (
                    pessoa
                    for pessoa in funcionarios_encontrados
                    if pessoa.get("id") == funcionario_id
                ),
                None,
            )
        elif consulta and len(funcionarios_encontrados) == 1:
            funcionario = funcionarios_encontrados[0]
        if funcionario:
            alocacoes, sistemas = _get_listas_api(
                [URL_ALOCACOES, URL_SISTEMAS],
                [
                    {"funcionario_id": funcionario["id"]},
                    {"funcionario_id": funcionario["id"]},
                ],
            )
    except (requests.RequestException, ValueError):
        erro = "Não consegui carregar a consulta. Confira se o FastAPI está em execução."
    return render_template(
        "consulta_funcionario.html",
        consulta=consulta,
        funcionarios=funcionarios_encontrados,
        funcionario=funcionario,
        alocacoes=alocacoes,
        sistemas=sistemas,
        erro=erro,
        pode_editar=pode_editar,
    )


@app.get("/emprestimos")
@login_obrigatorio
def emprestimos():
    try:
        funcionarios, equipamentos, alocacoes = _get_listas_api(
            [URL_FUNCIONARIOS, URL_EQUIPAMENTOS, URL_ALOCACOES]
        )
        erro = None
    except (requests.RequestException, ValueError):
        funcionarios, equipamentos, alocacoes = [], [], []
        erro = "Não consegui carregar os empréstimos. Confira se o FastAPI está em execução."
    return render_template(
        "emprestimos.html",
        funcionarios=funcionarios,
        equipamentos=equipamentos,
        alocacoes=alocacoes,
        erro=erro,
        pode_editar=session.get("usuario", {}).get("perfil") == "admin",
    )


@app.get("/manutencoes")
@login_obrigatorio
def manutencoes():
    try:
        equipamentos, registros = _get_listas_api(
            [URL_EQUIPAMENTOS, URL_MANUTENCOES]
        )
        erro = None
    except (requests.RequestException, ValueError):
        equipamentos, registros = [], []
        erro = "Não consegui carregar as manutenções. Confira se o FastAPI está em execução."
    return render_template(
        "manutencoes.html",
        equipamentos=equipamentos,
        manutencoes=registros,
        erro=erro,
        pode_editar=session.get("usuario", {}).get("perfil") == "admin",
    )


@app.get("/sistemas")
@login_obrigatorio
def sistemas():
    try:
        funcionarios, registros = _get_listas_api([URL_FUNCIONARIOS, URL_SISTEMAS])
        erro = None
    except (requests.RequestException, ValueError):
        funcionarios, registros = [], []
        erro = "Não consegui carregar os sistemas. Confira se o FastAPI está em execução."
    return render_template(
        "sistemas.html",
        funcionarios=funcionarios,
        sistemas=registros,
        erro=erro,
        pode_editar=session.get("usuario", {}).get("perfil") == "admin",
    )


@app.post("/funcionarios")
@administrador_obrigatorio
def criar_funcionario():
    dados = {
        "nome": request.form.get("nome", "").strip(),
        "cpf": request.form.get("cpf", "").strip(),
        "matricula": request.form.get("matricula", "").strip(),
        "setor": request.form.get("setor", "").strip(),
    }
    try:
        resposta = requests.post(
            URL_FUNCIONARIOS, json=dados, headers=cabecalhos_api(), timeout=5
        )
        if resposta.status_code == 201:
            flash("Funcionário cadastrado.", "sucesso")
        else:
            flash(mensagem_erro_api(resposta), "erro")
    except requests.RequestException:
        flash("Não consegui acessar a API. Confira se o FastAPI está em execução.", "erro")
    return redirect(url_for("funcionarios"))


@app.route("/funcionarios/editar/<int:funcionario_id>", methods=["GET", "POST"])
@administrador_obrigatorio
def editar_funcionario(funcionario_id: int):
    if request.method == "POST":
        funcionario = {
            "nome": request.form.get("nome", "").strip(),
            "cpf": request.form.get("cpf", "").strip(),
            "matricula": request.form.get("matricula", "").strip(),
            "setor": request.form.get("setor", "").strip(),
            "id": funcionario_id,
        }
        try:
            resposta = requests.put(
                f"{URL_FUNCIONARIOS}/{funcionario_id}",
                json={chave: valor for chave, valor in funcionario.items() if chave != "id"},
                headers=cabecalhos_api(),
                timeout=5,
            )
            if resposta.ok:
                flash("Funcionário atualizado.", "sucesso")
                return redirect(
                    url_for("consulta_funcionarios", funcionario_id=funcionario_id)
                )
            flash(mensagem_erro_api(resposta), "erro")
        except requests.RequestException:
            flash("Não consegui acessar a API. Confira se o FastAPI está em execução.", "erro")
        return render_template("funcionario_formulario.html", funcionario=funcionario)

    try:
        resposta = requests.get(
            f"{URL_FUNCIONARIOS}/{funcionario_id}",
            headers=cabecalhos_api(),
            timeout=5,
        )
        resposta.raise_for_status()
        funcionario = resposta.json()
    except requests.RequestException:
        flash("Não consegui carregar o funcionário.", "erro")
        return redirect(url_for("funcionarios"))
    return render_template("funcionario_formulario.html", funcionario=funcionario)


@app.post("/funcionarios/excluir/<int:funcionario_id>")
@administrador_obrigatorio
def excluir_funcionario(funcionario_id: int):
    try:
        resposta = requests.delete(
            f"{URL_FUNCIONARIOS}/{funcionario_id}",
            headers=cabecalhos_api(),
            timeout=5,
        )
        if resposta.status_code == 204:
            flash("Funcionário removido da empresa. O histórico foi mantido.", "sucesso")
        else:
            flash(mensagem_erro_api(resposta), "erro")
    except requests.RequestException:
        flash("Não consegui acessar a API. Confira se o FastAPI está em execução.", "erro")
    return redirect(url_for("funcionarios"))


@app.post("/alocacoes")
@administrador_obrigatorio
def criar_alocacao():
    dados = {
        "equipamento_id": request.form.get("equipamento_id", type=int),
        "funcionario_id": request.form.get("funcionario_id", type=int),
        "situacao": request.form.get("situacao", "Em uso"),
        "observacao": request.form.get("observacao", "").strip() or None,
    }
    try:
        resposta = requests.post(
            URL_ALOCACOES, json=dados, headers=cabecalhos_api(), timeout=5
        )
        if resposta.status_code == 201:
            flash("Equipamento entregue ao funcionário.", "sucesso")
        else:
            flash(mensagem_erro_api(resposta), "erro")
    except requests.RequestException:
        flash("Não consegui acessar a API. Confira se o FastAPI está em execução.", "erro")
    return redirect(url_for("emprestimos"))


@app.post("/alocacoes/<int:alocacao_id>/devolver")
@administrador_obrigatorio
def devolver_equipamento(alocacao_id: int):
    try:
        resposta = requests.post(
            f"{URL_ALOCACOES}/{alocacao_id}/devolver",
            headers=cabecalhos_api(),
            timeout=5,
        )
        if resposta.ok:
            flash("Equipamento devolvido ao estoque.", "sucesso")
        else:
            flash(mensagem_erro_api(resposta), "erro")
    except requests.RequestException:
        flash("Não consegui acessar a API. Confira se o FastAPI está em execução.", "erro")
    return redirect(url_for("emprestimos"))


@app.post("/manutencoes")
@administrador_obrigatorio
def criar_manutencao():
    dados = {
        "equipamento_id": request.form.get("equipamento_id", type=int),
        "laudo": request.form.get("laudo", "").strip(),
        "sem_conserto": request.form.get("sem_conserto") == "on",
    }
    try:
        resposta = requests.post(
            URL_MANUTENCOES, json=dados, headers=cabecalhos_api(), timeout=5
        )
        if resposta.status_code == 201:
            flash("Laudo de manutenção registrado.", "sucesso")
        else:
            flash(mensagem_erro_api(resposta), "erro")
    except requests.RequestException:
        flash("Não consegui acessar a API. Confira se o FastAPI está em execução.", "erro")
    return redirect(url_for("manutencoes"))


@app.post("/sistemas")
@administrador_obrigatorio
def criar_sistema():
    dados = {
        "funcionario_id": request.form.get("funcionario_id", type=int),
        "nome_sistema": request.form.get("nome_sistema", "").strip(),
    }
    try:
        resposta = requests.post(
            URL_SISTEMAS, json=dados, headers=cabecalhos_api(), timeout=5
        )
        if resposta.status_code == 201:
            flash("Sistema registrado para o funcionário.", "sucesso")
        else:
            flash(mensagem_erro_api(resposta), "erro")
    except requests.RequestException:
        flash("Não consegui acessar a API. Confira se o FastAPI está em execução.", "erro")
    return redirect(url_for("sistemas"))


@app.post("/sistemas/<int:sistema_id>/finalizar")
@administrador_obrigatorio
def finalizar_sistema(sistema_id: int):
    try:
        resposta = requests.patch(
            f"{URL_SISTEMAS}/{sistema_id}/finalizar",
            headers=cabecalhos_api(),
            timeout=5,
        )
        if resposta.ok:
            flash("Uso do sistema encerrado. O histórico foi mantido.", "sucesso")
        else:
            flash(mensagem_erro_api(resposta), "erro")
    except requests.RequestException:
        flash("Não consegui acessar a API. Confira se o FastAPI está em execução.", "erro")
    return redirect(url_for("sistemas"))


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("FLASK_PORT", "5001")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
