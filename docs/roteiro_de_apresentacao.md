# Roteiro de apresentação — AtivoTI

Este roteiro ajuda a demonstrar o projeto em etapas. Use um cadastro de teste e explique com suas palavras o que cada parte faz.

## 1. Preparar o ambiente

Abra a pasta principal do projeto no VS Code. Para a interface Flask, crie o ambiente Python e instale as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Abra o Docker Desktop. O PostgreSQL e a API serão iniciados em containers; o banco local não usa a conexão do Supabase. Na raiz do projeto, você pode iniciá-los pelo terminal:

```bash
docker compose up -d --build --wait db api
```

O container da API aplica as migrations ao iniciar. Crie o primeiro administrador:

```bash
docker compose exec api python -m app.core.criar_admin
```

## 2. Iniciar o sistema no VS Code

Em **Executar e Depurar**, escolha `AtivoTI: iniciar no navegador` e pressione **F5**. O VS Code sobe o banco e a API em Docker, inicia a interface Flask e abre o navegador. Os endereços ficam em `http://localhost:5002/entrar` e `http://127.0.0.1:8001/docs`.

Se preferir iniciar só os containers pelo terminal, use o comando da seção anterior e rode a interface web localmente:

```bash
source .venv/bin/activate
API_URL=http://127.0.0.1:8001/api/v1 FLASK_PORT=5002 python flask_app/app.py
```

Entre com o administrador e mostre a lista de equipamentos e a página **Funcionários e históricos**. Mostre também `/health` no Swagger para confirmar a conexão da API com o PostgreSQL.

## 4. Gerar o relatório periódico

Com os containers em execução, gere o PDF do mês sem esperar o próximo agendamento:

```bash
docker compose exec api python -m app.services.relatorio_automatico
```

Abra o arquivo indicado no terminal dentro da pasta `relatorios/`. O agendamento automático roda no primeiro dia de cada mês às 08h, no fuso de São Paulo, enquanto a API estiver ativa. O cliente Flutter permanece opcional e não é necessário para demonstrar a automação.

## 5. Demonstrar o sistema web e os históricos

1. Cadastre um equipamento e mostre o patrimônio sequencial criado pela API.
2. Cadastre um funcionário e mostre nome, CPF, matrícula, setor e ID.
3. Entregue o equipamento ao funcionário; confira o responsável e o status `Em uso` ou `Emprestado`.
4. Faça a devolução e mostre que o equipamento voltou ao estoque e a entrega anterior continua no histórico.
5. Registre um sistema, por exemplo Microsoft 365, ChatGPT ou Claude, e depois finalize o uso para manter as datas no histórico.
6. Registre um laudo escrito de manutenção. Marque outro equipamento como sem conserto, confira a baixa e só depois exclua o cadastro.
7. Mostre `/docs` e explique que os equipamentos têm operações para criar, listar, consultar por ID, atualizar e excluir.
8. Entre com uma conta comum, consulte funcionários e históricos, abra o relatório e confirme que ela não pode alterar dados.
9. Gere o PDF mensal pelo comando da seção anterior e mostre o arquivo arquivado.

## 6. Mostrar validação e erro de conexão

- Tente salvar sem preencher nome, tipo ou condição. A API deve rejeitar os dados inválidos.
- Tente entregar o mesmo equipamento duas vezes sem devolvê-lo. A API deve impedir a segunda entrega.
- Consulte em `/docs` um ID que não existe. A API deve retornar `404`.
- Consulte um ID inexistente em `/docs`; a API deve retornar `404`.
- Pare a API e tente atualizar a interface web; ela deve mostrar uma mensagem de conexão. Reinicie a API e tente novamente.

Para encerrar a demonstração sem remover o banco local, execute `docker compose down`. Esses passos precisam ser conferidos no computador da apresentação; registre os resultados em [`registro_de_validacao.md`](registro_de_validacao.md).
