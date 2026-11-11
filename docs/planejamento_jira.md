# Planejamento a partir do Jira

Revisão somente de leitura feita em 20/10/2026. Não alterei tarefas nem status no Jira.

## O que está no Jira

| Tarefa | Situação vista | O que falta para concluir |
|---|---|---|
| KAN-31 — testar CRUD entre Flutter, FastAPI e Flask | Em andamento | Demonstrar cadastro, consulta, edição e exclusão nas telas visíveis e registrar o resultado observado; os fluxos via API HTTP já passaram |
| KAN-32 — validar sincronização e falhas | Em andamento | Demonstrar a atualização entre as telas e a mensagem de erro com a API parada; os testes automatizados e o fluxo Flask/API por HTTP já passaram |
| KAN-33 — documentar projeto e README | Concluído | A documentação foi ampliada para incluir funcionários, históricos e manutenção |
| KAN-34 — preparar demonstração final | Em andamento | Rodar o sistema no computador, concluir o roteiro e preencher o registro de validação |

O KAN-34 depende dos testes KAN-31 e KAN-32, dos clientes Flutter e Flask (KAN-7 e KAN-8) e da documentação KAN-33. O próprio ticket diz que a demonstração manual ainda precisa ser feita com API, banco, Flutter e Flask configurados.

## Ordem para fechar as tarefas

1. Preparar um banco SQLite temporário e instalar as dependências: concluído para esta validação.
2. Rodar `python -m pytest -q` para validar API, regras de acesso, históricos e Flask: 27 testes passaram.
3. Rodar a análise Dart e os testes Flutter: análise sem problemas e 5 testes passaram.
4. Aplicar as migrations em SQLite vazio e configurar o Supabase até a revisão `0005`: concluído. O painel confirmou as tabelas e a proteção por linha.
5. Configurar a URI do Supabase em `.env` e iniciar a API, o Flask e o Flutter no computador de desenvolvimento.
6. Demonstrar cadastro e edição de equipamentos entre as telas; confirmar que a exclusão só acontece depois do laudo sem conserto e da baixa.
7. Demonstrar funcionário, entrega, devolução ao estoque, histórico do sistema usado e remoção do funcionário mantendo o histórico.
8. Testar usuário comum, relatório detalhado e falha de conexão; registrar o resultado observado em `registro_de_validacao.md`.
9. Só depois de ver esses resultados, atualizar os tickets KAN-31, KAN-32 e KAN-34 no Jira.

## Estado deste ambiente

Os testes Python e Flutter passaram usando bancos e SDK temporários. Também foi executado o fluxo real do `ApiService` Flutter e do Flask contra a API FastAPI por HTTP. O Supabase foi configurado até a revisão `0005`; a conexão da aplicação ainda precisa da URI com a senha do banco no `.env`. A demonstração visual nas telas continua pendente; este ambiente não tem Android SDK nem Xcode para abrir o app Flutter. Os status do Jira continuam iguais aos que foram vistos na revisão.
