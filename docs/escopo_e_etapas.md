# Etapas do AtivoTI

Este arquivo registra o que já está no projeto e o que falta fazer, usando o escopo combinado para a atividade.

## Recursos implementados

- [x] API FastAPI central com cadastro, consulta, edição e exclusão de equipamentos.
- [x] Interface web Flask usando a API FastAPI; o aplicativo Flutter permanece como cliente opcional.
- [x] Número de patrimônio sequencial gerado pelo sistema.
- [x] Número de série opcional e condição do equipamento: novo ou usado.
- [x] Tipos de equipamentos livres para cadastrar notebooks, periféricos, placas de vídeo e outros itens de TI.
- [x] Exclusão de equipamento permitida somente depois de marcar como `Baixado`.
- [x] Login por e-mail e senha, com senha protegida no banco.
- [x] Perfil administrador para alterar dados e perfil comum para consultar e ver relatórios.
- [x] Cadastro dos dados básicos de acesso: nome, setor, CPF, matrícula e identificador criado pelo banco.
- [x] Relatório simples com totais por status, tipo e setor.
- [x] Automação Python no backend para gerar e arquivar um PDF mensal do inventário.
- [x] Cadastro de funcionários separado das contas de acesso, com nome, CPF, matrícula, setor e ID.
- [x] Entrega de equipamentos como `Em uso` ou `Emprestado`, com funcionário responsável, data e observação.
- [x] Devolução que fecha a entrega, mantém o histórico e coloca o equipamento de volta no estoque.
- [x] Remoção de funcionário da lista ativa sem apagar as entregas e os sistemas que já usou.
- [x] Cadastro do nome de cada sistema usado por funcionário e histórico de início/fim.
- [x] Laudo escrito de manutenção com opção de informar que o equipamento não tem conserto.
- [x] Baixa após o laudo sem conserto; exclusão de equipamento só depois da baixa.
- [x] As telas do Flask e do Flutter usam a mesma API para essas funções; o perfil comum consulta e o administrador altera.
- [x] Migration `0004` criada e aplicada ao Supabase para funcionários e históricos.
- [x] Migration `0005` ativa proteção por linha nas tabelas do sistema; aplicada e conferida no Supabase.

## Validação antes da entrega e publicação

- [x] Executar `python -m pytest -q` em SQLite temporário: 37 testes passaram.
- [x] Executar a análise Dart e os testes Flutter: 5 testes passaram.
- [x] Validar o `ApiService` Flutter e o Flask contra a API FastAPI real por HTTP, usando banco temporário.
- [x] Testar as migrations em um banco SQLite vazio; as revisões `0001` a `0005` criam as tabelas esperadas.
- [x] Configurar o projeto Supabase e conferir as tabelas e a revisão `0005`.
- [ ] Executar o roteiro de apresentação pela interface web e demonstrar a geração do PDF.

O roteiro para fechar os tickets de integração e entrega do Jira está em [`planejamento_jira.md`](planejamento_jira.md). A consulta ao Jira foi somente de leitura. O esquema do Supabase está pronto. Para conectar a API neste computador, ainda é necessário colocar a URI de conexão e a senha do banco no `.env`; não compartilhe esse arquivo. Também falta demonstrar manualmente o fluxo web e a geração do PDF antes de concluir os tickets.

## Regras que devem continuar valendo

- Somente a equipe de TI usa o sistema.
- O perfil comum só consulta e gera relatórios.
- O patrimônio é criado pela API e não pode ser escolhido no formulário.
- O número de série só precisa ser preenchido quando existe.
- Ao devolver um equipamento, ele volta para `Em estoque` e o histórico de uso é mantido.
- Ao remover um funcionário da empresa, as entregas e sistemas abertos são encerrados e o histórico permanece consultável.
- A exclusão de equipamento só acontece depois da baixa.
- A migration do Supabase não deve ser executada antes de ser conferida e testada.
