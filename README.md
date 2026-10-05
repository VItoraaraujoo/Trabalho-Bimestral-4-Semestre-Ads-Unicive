# Gestão de Equipamentos de TI

Projeto acadêmico para administrar equipamentos por uma API FastAPI. A estrutura separa persistência, regras de negócio e rotas para facilitar a integração posterior com Flutter e Tkinter.

## Executar a API

Na raiz do projeto:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

No Windows, ative o ambiente com `.venv\\Scripts\\activate`.

A API ficará em `http://127.0.0.1:8000` e a documentação Swagger em `http://127.0.0.1:8000/docs`.

O SQLite cria `equipamentos.db` na raiz do projeto ao iniciar. Para apontar para outro banco compatível com SQLAlchemy, defina `DATABASE_URL`.

## Rotas disponíveis

| Método | Rota | Ação |
|---|---|---|
| `POST` | `/equipamentos` | Cadastrar equipamento |
| `GET` | `/equipamentos` | Listar e filtrar equipamentos |
| `GET` | `/equipamentos/{id}` | Consultar equipamento |
| `PUT` | `/equipamentos/{id}` | Atualizar equipamento |
| `DELETE` | `/equipamentos/{id}` | Excluir equipamento |

A listagem aceita os filtros opcionais `status`, `tipo` e `setor`. Os status válidos são `Em uso`, `Disponível`, `Em manutenção` e `Descartado`.
