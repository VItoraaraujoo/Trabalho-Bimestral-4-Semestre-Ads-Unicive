# Gestão de Equipamentos de TI — AtivoTI

Projeto acadêmico para cadastrar e administrar equipamentos de TI. O FastAPI é a API central, a interface web Flask é o cliente usado na apresentação e uma rotina Python no backend gera relatórios mensais em PDF. O aplicativo Flutter permanece como cliente opcional. Há dois perfis: `admin`, que gerencia os cadastros, e `comum`, que consulta os dados e relatórios.

## Contrato dos equipamentos

| Campo | Regra usada no projeto |
|---|---|
| `id` | Número criado pelo banco; não é enviado pelo formulário |
| `nome` | Obrigatório, texto com até 150 caracteres |
| `tipo` | Obrigatório, texto com até 80 caracteres |
| `patrimonio` | Criado pela API em sequência, no formato `ATI-000001` |
| `numero_serie` | Opcional; pode ficar em branco quando o equipamento não tiver série; não pode se repetir |
| `marca` | Opcional, até 100 caracteres |
| `modelo` | Opcional, até 100 caracteres |
| `setor` | Opcional, até 100 caracteres |
| `condicao` | `Novo` ou `Usado`; escolhido no cadastro |
| `status` | `Em estoque`, `Em uso`, `Emprestado`, `Em manutenção` ou `Baixado`; padrão `Em estoque` |
| `observacao` | Opcional, até 500 caracteres |

Os filtros da listagem são `status`, `tipo` e `setor`. O status é exato; tipo e setor aceitam parte do texto. O sistema controla `Em uso` e `Emprestado` pelas alocações. Um laudo escrito encerra a manutenção; se disser que não há conserto, o equipamento recebe baixa e pode ser excluído.

Funcionários são cadastros separados dos usuários que entram no sistema. Cada funcionário tem nome, CPF, matrícula, setor e ID. O administrador pode alocar equipamentos, registrar devoluções, manter a lista dos sistemas que cada pessoa usa e registrar laudos escritos de manutenção. Se a manutenção indicar que não há conserto, o equipamento recebe baixa. Quando um funcionário é removido da empresa, o cadastro sai da lista ativa, as entregas e os sistemas em aberto são encerrados e o histórico continua disponível.

## Acesso ao sistema

Cada pessoa entra com e-mail e senha. O banco guarda somente a senha protegida, nunca a senha escrita. O perfil comum pode consultar equipamentos, funcionários e históricos, além de gerar relatórios. Somente o administrador pode cadastrar e alterar dados. Cada usuário de acesso tem nome, e-mail, CPF, matrícula, setor, ID e perfil.

O primeiro administrador é criado no computador do projeto depois de aplicar as migrations. O comando pede os dados e a senha sem gravá-los no código. Para publicar a interface web com HTTPS, configure `FLASK_COOKIE_SECURE=true` no ambiente:

```bash
python -m app.core.criar_admin
```

Use um e-mail com domínio completo, como `admin@empresa.com`. Um endereço sem ponto depois do `@`, como `admin@admin`, não é aceito.

O login devolve um token JWT. Os clientes enviam esse token nas chamadas seguintes. Em produção, defina `JWT_SECRET_KEY` com uma chave aleatória e mantenha o site em HTTPS. A chave `FLASK_SECRET_KEY` também deve ser alterada antes de publicar a interface web.

## Como as partes se comunicam

```text
Flask ─────── HTTP/JSON ──> FastAPI ──> PostgreSQL local (Docker)
Flutter ───── HTTP/JSON ──>   │
                              └── rotina mensal ──> PDF arquivado
```

As interfaces não acessam o banco diretamente. No modo local, o Compose conecta a API ao PostgreSQL pelo nome interno `db`; essa configuração não usa o banco Supabase.

## Rodar o sistema completo em Docker

Abra o Docker Desktop e, na raiz do projeto, inicie o banco e a API:

```bash
docker compose up -d --build --wait
```

O Compose inicia PostgreSQL, FastAPI e Flask. A API aplica as migrations e só fica saudável quando `/health` confirma a conexão com o banco; depois disso, a interface web inicia. `--wait` aguarda os serviços ficarem saudáveis antes de concluir.

- Sistema web: `http://127.0.0.1:15002/entrar`
- API: `http://127.0.0.1:18001`
- Swagger: `http://127.0.0.1:18001/docs`
- Banco no computador: `localhost:5433`, usuário `ativoti`, senha `ativoti_local`, banco `ativoti`

Crie o primeiro administrador dentro do container da API:

```bash
docker compose exec api python -m app.core.criar_admin
```

Para redefinir a senha de um administrador ativo sem apagar os dados do banco, execute:

```bash
docker compose exec api python -m app.core.redefinir_senha_admin
```

No VS Code, abra **Executar e Depurar**, escolha `AtivoTI: iniciar no navegador` e pressione **F5**. Essa configuração inicia o banco, a API e a interface web em containers Docker e abre o navegador na tela de login.

Para gerar o PDF manualmente usando o banco local:

```bash
docker compose exec api python -m app.services.relatorio_automatico
```

Os dados do PostgreSQL ficam em um volume persistente e os PDFs são gravados na pasta `relatorios/` do projeto. Para parar e remover os containers sem apagar o banco, execute `docker compose down`. Evite `docker compose down -v`: a opção `-v` também remove o volume e os dados locais.

O arquivo `.env` com a conexão Supabase não é necessário para esse modo. As seções seguintes descrevem a execução manual com Supabase como alternativa.

## Entender o caminho de um cadastro

1. A pessoa preenche o formulário no Flutter ou no Flask.
2. A tela envia os campos em JSON para `POST /api/v1/equipamentos`.
3. A rota em `app/api/equipamentos.py` recebe os dados; o schema em `app/schemas/equipamento.py` verifica os campos obrigatórios e seus limites. O patrimônio é criado pelo backend depois do cadastro.
4. A regra de cadastro fica em `app/services/equipamento_service.py`, e as consultas ao banco ficam em `app/repositories/equipamento_repository.py`.
5. A API devolve o equipamento em JSON, e a tela atualiza a lista.

Para acompanhar o projeto sem ler tudo de uma vez, comece pela rota de listagem e siga o mesmo caminho entre tela, API e banco. O modelo da tabela está em `app/models/equipamento.py`.

## 1. Configurar o Supabase para execução manual

É necessário ter Python 3.10 ou superior. A URI do projeto já está como modelo em `.env.example`. Abra **Connect** e escolha **Session pooler** para copiar o endereço. Troque o campo de senha pela senha definida para o banco quando o projeto foi criado. O pooler funciona em redes IPv4, comuns em servidores. Não compartilhe a senha.

O Supabase guarda os dados em PostgreSQL. O FastAPI conversa com esse banco; para usar o aplicativo e os formulários, você não precisa escrever comandos SQL.

Na raiz do repositório:

```bash
cp .env.example .env
```

Edite `.env` e troque `SENHA_DO_BANCO` pela senha do banco. Se a senha tiver caracteres reservados de URL, como `@`, `#`, `?`, `&` ou espaços, codifique esses caracteres. O backend seleciona o driver psycopg e pede SSL para hosts do Supabase.

Não compartilhe nem envie `.env` ao GitHub. O arquivo já está no `.gitignore`. `.env.example` já informa o endereço e o usuário do pooler deste projeto, mas não contém a senha do banco.

Na execução manual, o Supabase é o banco usado pela aplicação. Sem `DATABASE_URL`, a API para com uma mensagem explicando como configurar a conexão; ela não cria um banco local automaticamente. Os testes automatizados usam SQLite temporário isolado e não acessam o Supabase.

Se `GET /health` responder `503`, confira se o projeto Supabase está ativo, se o `.env` usa a conexão **Session pooler** mostrada em **Connect** e se a rede permite conexões de saída para a porta `5432`. A senha precisa estar codificada na URL quando tiver caracteres especiais. O terminal onde o Uvicorn está rodando mostra o motivo técnico da falha. Depois de alterar `.env`, pare e inicie o Uvicorn novamente.

## 2. Instalar e iniciar a API

Na raiz do repositório:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0
```

Depois de configurar `DATABASE_URL` com a conexão do Supabase, confira a versão das migrations:

```bash
alembic current
```

Em um projeto Supabase novo, aplique todas as migrations:

```bash
alembic upgrade head
```

O projeto Supabase usado neste trabalho já foi configurado até a migration `0005`. Ela cria as tabelas de usuários, funcionários, alocações, manutenções e sistemas usados, atualiza os equipamentos e ativa a proteção por linha. Os clientes Flutter e Flask usam a API FastAPI; o acesso direto pela API pública do Supabase fica bloqueado. Não use `alembic downgrade base` neste projeto.

Tanto a migration quanto a API usam a mesma `DATABASE_URL`.

Depois das migrations, crie o primeiro administrador com `python -m app.core.criar_admin`.

### Automação de relatórios mensais

Ao iniciar a API, o backend agenda a geração de um PDF no primeiro dia de cada mês, às 08h no fuso `America/Sao_Paulo`. O relatório mostra a posição do inventário na hora da geração, com totais por status, tipo e setor e a lista dos equipamentos. O arquivo usa o nome `relatorio_equipamentos_AAAA-MM.pdf` e fica na pasta `relatorios` da raiz do projeto. No modo Docker local, a pasta é compartilhada com o host.

Para gerar o relatório do mês imediatamente, sem esperar a data agendada:

```bash
source .venv/bin/activate
python -m app.services.relatorio_automatico
```

`RELATORIOS_DIR` altera a pasta de saída e `RELATORIO_TIMEZONE` altera o fuso. A API deve estar ativa no horário agendado; a geração manual serve para testar e apresentar a automação. No modo Docker local, use o comando com `docker compose exec api` indicado acima.

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`
- Verificação do banco: `http://127.0.0.1:8000/health`

O `--host 0.0.0.0` permite que o emulador Android ou um celular na rede local acesse a API. Para uso apenas no computador, também é possível iniciar sem essa opção.

## 3. Usar a API

| Método | Rota | Resultado |
|---|---|---|
| `POST` | `/api/v1/equipamentos` | Cadastra; responde `201` |
| `GET` | `/api/v1/equipamentos` | Lista equipamentos |
| `GET` | `/api/v1/equipamentos?status=Em%20uso` | Filtra por status |
| `GET` | `/api/v1/equipamentos?tipo=note&setor=labor` | Busca parte do tipo e do setor |
| `GET` | `/api/v1/equipamentos/{id}` | Consulta pelo identificador |
| `PUT` | `/api/v1/equipamentos/{id}` | Atualiza os campos do equipamento |
| `DELETE` | `/api/v1/equipamentos/{id}` | Exclui somente depois da baixa; responde `204` |
| `POST` | `/api/v1/auth/login` | Confere e-mail e senha e devolve o token JWT |
| `GET` | `/api/v1/auth/me` | Mostra os dados de quem entrou |
| `GET` | `/api/v1/usuarios` | Lista usuários; apenas administrador |
| `POST` | `/api/v1/usuarios` | Cadastra usuário; apenas administrador |
| `PUT` | `/api/v1/usuarios/{id}` | Atualiza usuário; apenas administrador |
| `DELETE` | `/api/v1/usuarios/{id}` | Exclui usuário; não permite excluir o próprio acesso nem o último administrador |
| `GET` | `/api/v1/relatorios/equipamentos` | Mostra totais por status, tipo e setor e um inventário detalhado com responsável atual |
| `GET`, `POST` | `/api/v1/funcionarios` | Consulta ou cadastra funcionários; cadastro apenas pelo administrador |
| `GET`, `PUT`, `DELETE` | `/api/v1/funcionarios/{id}` | Consulta, atualiza ou remove da lista ativa; o histórico fica guardado |
| `GET`, `POST` | `/api/v1/alocacoes` | Consulta o histórico ou entrega equipamento a funcionário |
| `POST` | `/api/v1/alocacoes/{id}/devolver` | Registra a devolução e retorna o equipamento ao estoque |
| `GET`, `POST` | `/api/v1/manutencoes` | Consulta ou registra laudo escrito e informa se há conserto |
| `GET`, `POST` | `/api/v1/sistemas` | Consulta ou registra um sistema usado pelo funcionário |
| `PATCH` | `/api/v1/sistemas/{id}/finalizar` | Encerra o uso atual sem apagar o histórico |
| `GET` | `/health` | Confere API e conexão com o banco |

### Exemplos de requisições protegidas

Primeiro, faça login. Copie o valor de `access_token` que a resposta mostrar:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@empresa.com","senha":"sua-senha"}'
```

Use o token no cabeçalho `Authorization` para consultar os equipamentos:

```bash
curl http://127.0.0.1:8000/api/v1/equipamentos \
  -H 'Authorization: Bearer COLE_SEU_TOKEN_AQUI'
```

Cadastre um equipamento. A resposta inclui o patrimônio criado pela API:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/equipamentos \
  -H 'Authorization: Bearer COLE_SEU_TOKEN_AQUI' \
  -H 'Content-Type: application/json' \
  -d '{"nome":"Notebook do laboratório","tipo":"Notebook","numero_serie":"SN-001","marca":"Exemplo","modelo":"Modelo A","setor":"Laboratório","condicao":"Usado","status":"Em estoque","observacao":"Cadastro de teste"}'
```

Para consultar um item pelo ID, use `GET /api/v1/equipamentos/1`. Para atualizar, envie os campos novamente com `PUT`:

```bash
curl -X PUT http://127.0.0.1:8000/api/v1/equipamentos/1 \
  -H 'Authorization: Bearer COLE_SEU_TOKEN_AQUI' \
  -H 'Content-Type: application/json' \
  -d '{"nome":"Notebook do laboratório","tipo":"Notebook","numero_serie":"SN-001","marca":"Exemplo","modelo":"Modelo A","setor":"TI","condicao":"Usado","status":"Em estoque","observacao":"Setor atualizado"}'
```

O equipamento só pode ser excluído depois da baixa. Para dar baixa por falta de conserto, envie o laudo:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/manutencoes \
  -H 'Authorization: Bearer COLE_SEU_TOKEN_AQUI' \
  -H 'Content-Type: application/json' \
  -d '{"equipamento_id":1,"laudo":"Placa principal sem reparo possível.","sem_conserto":true}'
```

Depois do laudo, exclua o cadastro do equipamento:

```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/equipamentos/1 \
  -H 'Authorization: Bearer COLE_SEU_TOKEN_AQUI'
```

Exemplo do corpo de login:

```json
{
  "email": "admin@empresa.com",
  "senha": "senha-digitada-no-login"
}
```

Para abrir as rotas protegidas no Swagger, clique em **Authorize** e informe `Bearer` seguido do token recebido no login. Sem token válido, a API responde `401`; um perfil comum que tenta alterar dados recebe `403`.

Um exemplo de corpo para `POST` ou `PUT`:

```json
{
  "nome": "Notebook do laboratório",
  "tipo": "Notebook",
  "numero_serie": "SN-001",
  "marca": "Exemplo",
  "modelo": "Modelo A",
  "setor": "Laboratório",
  "condicao": "Novo",
  "status": "Em estoque",
  "observacao": "Equipamento de demonstração"
}
```

A API responde `404` quando o ID não existe, `409` quando um dado já está cadastrado ou quando a ação não segue as regras de entrega, manutenção ou baixa, e `422` quando os dados não passam pela validação.

## 4. Iniciar a interface Flask

Com a API em execução, abra outro terminal na raiz do repositório e ative o ambiente Python:

```bash
source .venv/bin/activate
python flask_app/app.py
```

Abra `http://127.0.0.1:5001` e entre com o usuário criado. A interface usa a porta `5001` por padrão para evitar conflito com um serviço do macOS na porta `5000`; você pode alterar com a variável `FLASK_PORT`. A página lista os equipamentos e oferece filtros por status, tipo e setor. Funcionários, consulta de fichas, empréstimos, sistemas e manutenções ficam em telas separadas. A ficha de cada funcionário reúne seus dados, equipamentos vinculados e sistemas utilizados, incluindo o histórico. O perfil comum consulta essas informações. Ambos podem abrir e imprimir o relatório detalhado com o responsável atual. A página chama a mesma API por HTTP. Ao mudar o endereço da API, configure `API_URL` antes de iniciar o Flask:

```bash
API_URL=http://127.0.0.1:8000/api/v1 FLASK_PORT=5001 python flask_app/app.py
```

## 5. Cliente Flutter opcional

Esta etapa é opcional para a apresentação, que pode usar somente a interface web. Para testar também o cliente mobile, instale Flutter e mantenha a API em execução:

```bash
cd mobile
flutter pub get
flutter run
```

No emulador Android, o endereço padrão `http://10.0.2.2:8000/api/v1` aponta para o computador que executa a API. Entre com seu e-mail e senha. Todos os perfis podem consultar funcionários e históricos e abrir o resumo; o administrador também pode cadastrar e editar equipamentos, funcionários e usuários, além de registrar entregas, devoluções e históricos. Para usar um celular físico, troque `192.168.1.20` pelo endereço do computador na rede local:

```bash
flutter run --dart-define=API_BASE_URL=http://192.168.1.20:8000/api/v1
```

O endereço fica em um só lugar (`API_BASE_URL`), não espalhado pelas telas. O Android precisa estar na mesma rede do computador. A permissão de HTTP sem TLS no `AndroidManifest.xml` atende ao servidor local de desenvolvimento; para um servidor publicado, configure HTTPS.

## Rodar o sistema web pelo VS Code

Abra no VS Code a pasta raiz do projeto, que contém `.vscode`, `app` e `flask_app`. Com o Docker Desktop aberto, em **Executar e Depurar**, escolha `AtivoTI: iniciar no navegador` e pressione **F5**. O VS Code inicia PostgreSQL, FastAPI e Flask em containers Docker.

O navegador abre `http://localhost:15002/entrar`. A API fica disponível em `http://127.0.0.1:18001/docs`. Os perfis Flutter continuam disponíveis caso seja necessário testar o cliente mobile.

## Testes e checagens

Testes do backend e da interface Flask:

```bash
source .venv/bin/activate
python -m pytest -q
```

Os testes Python usam SQLite temporário para o CRUD da API e verificam login, senhas protegidas, perfis, patrimônio sequencial, série opcional, bloqueio de exclusão antes da baixa, devolução ao estoque, histórico de funcionários e sistemas, laudos, documentação OpenAPI e geração/agendamento do PDF. Um teste liga a interface Flask à API de teste; os demais usam dados temporários. Assim, os testes não apagam dados do Supabase. Os testes Flutter verificam o modelo JSON e as chamadas do cliente HTTP.

O registro das checagens feitas neste ambiente e do roteiro manual pendente está em [`docs/registro_de_validacao.md`](docs/registro_de_validacao.md).
O roteiro de apresentação com comandos e passos de demonstração está em [`docs/roteiro_de_apresentacao.md`](docs/roteiro_de_apresentacao.md).
As etapas já feitas e as próximas partes do escopo estão em [`docs/escopo_e_etapas.md`](docs/escopo_e_etapas.md).
O plano para concluir as tarefas de integração e apresentação do Jira está em [`docs/planejamento_jira.md`](docs/planejamento_jira.md).

Checagens do Flutter:

```bash
cd mobile
flutter analyze
flutter test
```

## Roteiro da integração e da apresentação

1. Inicie a API e a interface Flask pelo VS Code e entre como administrador.
2. Cadastre um funcionário e um equipamento; mostre os dados na interface web.
3. Registre uma entrega, uma devolução e um laudo de manutenção.
4. Consulte o relatório atual pela página **Relatórios**.
5. Execute `python -m app.services.relatorio_automatico` e abra o PDF criado em `relatorios/`.
6. Mostre no terminal o log da API indicando que o agendamento mensal foi iniciado.
7. Entre como usuário comum e confirme que consegue consultar e gerar relatórios, mas não alterar os dados.
8. Consulte um ID inexistente em `/docs` e pare a API para mostrar as mensagens de erro.

Use um cadastro de demonstração com patrimônio único. Se estiver conectado ao Supabase, apague apenas esse cadastro de teste ao terminar.

## Identidade visual

- **Nome:** AtivoTI
- **Assinatura:** “Equipamentos organizados. Gestão sem complicação.”
- **Símbolo:** etiqueta de inventário com marca de confirmação.
- **Cores:** azul-marinho `#0F2742`, azul `#2563EB`, verde-azulado `#14B8A6`, fundo `#F8FAFC`, texto `#1F2937`, apoio `#64748B` e borda `#E2E8F0`.
- **Status:** verde `#16A34A` para estoque, azul para em uso, âmbar `#F59E0B` para manutenção, roxo para emprestado e vermelho `#DC2626` para baixado. A tela sempre mostra também o rótulo.
- **Fonte:** Inter quando disponível; nas demais instalações, fonte sem serifa do sistema.
- **Logo:** `flask_app/static/logo-horizontal.svg`, `logo-icone.svg` e `logo-monocromatico.svg`.

## Estrutura do projeto

- `app/api`: rotas HTTP da API
- `app/schemas`: validação dos dados enviados e recebidos
- `app/models`: tabela SQLAlchemy
- `app/repositories`: consultas e persistência
- `app/services`: operações e regras do cadastro
- `app/core`: configuração e conexão com o banco
- `migrations`: histórico de criação e alteração das tabelas
- `flask_app`: interface web Python
- `mobile`: aplicativo Flutter
- `tests`: testes Python
