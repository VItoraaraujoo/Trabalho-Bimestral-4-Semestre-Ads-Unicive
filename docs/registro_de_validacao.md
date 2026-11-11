# Registro de validação — AtivoTI

Data: 21/10/2026

## Verificação mais recente

- `python -m pytest -q`: 37 testes passaram; há 6 avisos de depreciação do cliente de testes.
- `docker compose config -q`, a validação dos arquivos JSON do VS Code e `git diff --check` passaram.
- A tentativa de iniciar os containers foi bloqueada por `permission denied` no socket do Docker (`~/.docker/run/docker.sock`). Portanto, o PostgreSQL e a API não foram iniciados nesta sessão; a execução pelo VS Code ainda precisa ser conferida com acesso ao Docker Desktop.

## O que foi testado

- Os 28 testes Python passaram. Eles usam bancos temporários e não alteram os dados do Supabase. Houve 6 avisos de compatibilidade do cliente de testes, sem falhas.
- A API rodou com Uvicorn ligada a um SQLite temporário. 24 verificações HTTP passaram, incluindo login, permissões, cadastro e edição de equipamento, patrimônio sequencial, série opcional, funcionários, entregas, devoluções, sistemas usados, laudos, baixa, exclusão e relatório.
- A interface Flask foi aberta no navegador e testada com usuários temporários. Foram conferidas as telas de equipamentos, funcionários, históricos, usuários e relatórios. O perfil comum pôde consultar e gerar relatório, mas não pôde abrir o cadastro.
- O teste de acesso bloqueado mostrou a página padrão do Flask em inglês. Ela foi trocada por uma mensagem simples em português, e um teste automatizado foi incluído.
- A cadeia de migrações foi aplicada a um SQLite temporário vazio até a revisão `0005`; as tabelas esperadas foram criadas.
- No Flutter, `dart --suppress-analytics analyze` terminou com `No issues found`; `dart format --output=none --set-exit-if-changed lib test` não encontrou arquivos fora do padrão; os 5 testes Flutter passaram.
- `python -m compileall -q app flask_app tests migrations` e `git diff --check` passaram.

## Supabase

Em uma conferência anterior, o painel mostrou as tabelas e a revisão `0005`, com a proteção por linha ativa. Também foi registrado um login bem-sucedido após usar um e-mail válido.

Nesta execução, o endereço, usuário e porta da `DATABASE_URL` foram conferidos com a opção **Session pooler** exibida no painel Supabase. A API local iniciou, mas a consulta `dig +time=2 +tries=1 aws-0-us-east-1.pooler.supabase.com` terminou com `connection timed out; no servers could be reached`. O `/health` respondeu `503` porque o ambiente não consegue alcançar o servidor DNS. Por isso, não foi possível repetir o login nem as operações ao vivo. Nenhuma tabela ou dado real foi alterado nesta homologação; os testes com gravação usaram somente o SQLite temporário. A API agora registra o erro técnico no terminal para facilitar o diagnóstico.

## O que falta conferir

- A aparência e o funcionamento do Flutter em um celular ou emulador. Nesta sessão, só apareceram macOS e Chrome como dispositivos; não havia Android conectado.
- O comando padrão `flutter analyze` não terminou porque o servidor de análise tentou gravar um arquivo de telemetria na pasta pessoal, sem permissão de escrita nesta sessão. A análise direta com Dart passou.
- Repetir o login e as operações no Supabase quando a rede do computador de desenvolvimento permitir a resolução do host e a conexão de saída na porta `5432`.

## Comandos para repetir no computador de desenvolvimento

Na pasta principal do projeto:

```bash
python -m pytest -q
```

Na pasta `mobile/`:

```bash
flutter analyze
flutter test
```

A aplicação usa o Supabase configurado em `DATABASE_URL`. O SQLite foi usado apenas nos testes temporários; ele não é o banco padrão do sistema.
