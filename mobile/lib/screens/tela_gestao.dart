import 'package:flutter/material.dart';

import '../brand.dart';
import '../models/equipamento.dart';
import '../services/api_service.dart';

class TelaGestao extends StatefulWidget {
  final ApiService api;
  final bool podeEditar;

  const TelaGestao({super.key, required this.api, required this.podeEditar});

  @override
  State<TelaGestao> createState() => _TelaGestaoState();
}

class _TelaGestaoState extends State<TelaGestao> {
  late Future<Map<String, List<Map<String, dynamic>>>> dadosFuture;
  bool salvando = false;

  @override
  void initState() {
    super.initState();
    dadosFuture = carregarDados();
  }

  Future<Map<String, List<Map<String, dynamic>>>> carregarDados() async {
    final resultados = await Future.wait<Object>([
      widget.api.listarFuncionarios(),
      widget.api.listarEquipamentos(),
      widget.api.listarAlocacoes(),
      widget.api.listarManutencoes(),
      widget.api.listarSistemas(),
    ]);
    final funcionarios = resultados[0] as List<Map<String, dynamic>>;
    final equipamentos = resultados[1] as List<Equipamento>;
    final alocacoes = resultados[2] as List<Map<String, dynamic>>;
    final manutencoes = resultados[3] as List<Map<String, dynamic>>;
    final sistemas = resultados[4] as List<Map<String, dynamic>>;
    return {
      'funcionarios': funcionarios,
      'equipamentos': equipamentos
          .map(
            (item) => {
              'id': item.id,
              'nome': item.nome,
              'patrimonio': item.patrimonio,
              'status': item.status,
            },
          )
          .toList(),
      'alocacoes': alocacoes,
      'manutencoes': manutencoes,
      'sistemas': sistemas,
    };
  }

  void atualizar() => setState(() => dadosFuture = carregarDados());

  void mostrarMensagem(String texto) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(texto)));
  }

  Future<void> salvar(Future<void> Function() acao) async {
    if (salvando) return;
    salvando = true;
    try {
      await acao();
      if (!mounted) return;
      Navigator.of(context).pop();
      atualizar();
    } catch (erro) {
      mostrarMensagem(erro.toString().replaceFirst('Exception: ', ''));
    } finally {
      salvando = false;
    }
  }

  Future<void> novoFuncionario([Map<String, dynamic>? pessoa]) async {
    final nome = TextEditingController(text: pessoa?['nome']?.toString() ?? '');
    final cpf = TextEditingController(text: pessoa?['cpf']?.toString() ?? '');
    final matricula = TextEditingController(
      text: pessoa?['matricula']?.toString() ?? '',
    );
    final setor = TextEditingController(
      text: pessoa?['setor']?.toString() ?? '',
    );
    final editando = pessoa != null;
    await showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(editando ? 'Editar funcionário' : 'Cadastrar funcionário'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nome,
                decoration: const InputDecoration(labelText: 'Nome completo'),
              ),
              TextField(
                controller: cpf,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'CPF (11 números)',
                ),
              ),
              TextField(
                controller: matricula,
                decoration: const InputDecoration(labelText: 'Matrícula'),
              ),
              TextField(
                controller: setor,
                decoration: const InputDecoration(labelText: 'Setor'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () async {
              if ([
                nome,
                cpf,
                matricula,
                setor,
              ].any((item) => item.text.trim().isEmpty)) {
                mostrarMensagem('Preencha todos os campos.');
                return;
              }
              final dados = {
                'nome': nome.text.trim(),
                'cpf': cpf.text.trim(),
                'matricula': matricula.text.trim(),
                'setor': setor.text.trim(),
              };
              await salvar(() async {
                if (editando) {
                  await widget.api.atualizarFuncionario(
                    pessoa['id'] as int,
                    dados,
                  );
                } else {
                  await widget.api.criarFuncionario(dados);
                }
              });
            },
            child: Text(editando ? 'Salvar alterações' : 'Salvar'),
          ),
        ],
      ),
    );
    nome.dispose();
    cpf.dispose();
    matricula.dispose();
    setor.dispose();
  }

  Future<void> novaAlocacao(
    List<Map<String, dynamic>> funcionarios,
    List<Map<String, dynamic>> equipamentos,
  ) async {
    final disponiveis = equipamentos
        .where((item) => item['status'] == 'Em estoque')
        .toList();
    if (funcionarios.isEmpty || disponiveis.isEmpty) {
      mostrarMensagem(
        'Cadastre um funcionário e deixe um equipamento em estoque.',
      );
      return;
    }
    int? funcionarioId;
    int? equipamentoId;
    String situacao = 'Em uso';
    final observacao = TextEditingController();
    await showDialog<void>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, atualizarDialogo) => AlertDialog(
          title: const Text('Entregar equipamento'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButtonFormField<int>(
                  initialValue: equipamentoId,
                  decoration: const InputDecoration(labelText: 'Equipamento'),
                  items: disponiveis
                      .map(
                        (item) => DropdownMenuItem<int>(
                          value: item['id'] as int,
                          child: Text(
                            '${item['patrimonio']} · ${item['nome']}',
                          ),
                        ),
                      )
                      .toList(),
                  onChanged: (valor) =>
                      atualizarDialogo(() => equipamentoId = valor),
                ),
                DropdownButtonFormField<int>(
                  initialValue: funcionarioId,
                  decoration: const InputDecoration(labelText: 'Funcionário'),
                  items: funcionarios
                      .map(
                        (item) => DropdownMenuItem<int>(
                          value: item['id'] as int,
                          child: Text('${item['nome']} · ${item['matricula']}'),
                        ),
                      )
                      .toList(),
                  onChanged: (valor) =>
                      atualizarDialogo(() => funcionarioId = valor),
                ),
                DropdownButtonFormField<String>(
                  initialValue: situacao,
                  decoration: const InputDecoration(
                    labelText: 'Tipo de entrega',
                  ),
                  items: const [
                    DropdownMenuItem(value: 'Em uso', child: Text('Em uso')),
                    DropdownMenuItem(
                      value: 'Emprestado',
                      child: Text('Emprestado'),
                    ),
                  ],
                  onChanged: (valor) =>
                      atualizarDialogo(() => situacao = valor ?? 'Em uso'),
                ),
                TextField(
                  controller: observacao,
                  decoration: const InputDecoration(labelText: 'Observação'),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () async {
                if (equipamentoId == null || funcionarioId == null) {
                  mostrarMensagem('Escolha o equipamento e o funcionário.');
                  return;
                }
                await salvar(
                  () => widget.api.criarAlocacao({
                    'equipamento_id': equipamentoId,
                    'funcionario_id': funcionarioId,
                    'situacao': situacao,
                    'observacao': observacao.text.trim().isEmpty
                        ? null
                        : observacao.text.trim(),
                  }),
                );
              },
              child: const Text('Registrar entrega'),
            ),
          ],
        ),
      ),
    );
    observacao.dispose();
  }

  Future<void> novaManutencao(List<Map<String, dynamic>> equipamentos) async {
    final disponiveis = equipamentos
        .where(
          (item) =>
              item['status'] == 'Em estoque' ||
              item['status'] == 'Em manutenção',
        )
        .toList();
    if (disponiveis.isEmpty) {
      mostrarMensagem('Não há equipamento em estoque para manutenção.');
      return;
    }
    int? equipamentoId;
    bool semConserto = false;
    final laudo = TextEditingController();
    await showDialog<void>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, atualizarDialogo) => AlertDialog(
          title: const Text('Registrar laudo de manutenção'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButtonFormField<int>(
                  initialValue: equipamentoId,
                  decoration: const InputDecoration(labelText: 'Equipamento'),
                  items: disponiveis
                      .map(
                        (item) => DropdownMenuItem<int>(
                          value: item['id'] as int,
                          child: Text(
                            '${item['patrimonio']} · ${item['nome']}',
                          ),
                        ),
                      )
                      .toList(),
                  onChanged: (valor) =>
                      atualizarDialogo(() => equipamentoId = valor),
                ),
                TextField(
                  controller: laudo,
                  maxLines: 4,
                  decoration: const InputDecoration(labelText: 'Laudo escrito'),
                ),
                CheckboxListTile(
                  contentPadding: EdgeInsets.zero,
                  value: semConserto,
                  title: const Text('Não tem conserto (dar baixa)'),
                  onChanged: (valor) =>
                      atualizarDialogo(() => semConserto = valor ?? false),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () async {
                if (equipamentoId == null || laudo.text.trim().isEmpty) {
                  mostrarMensagem('Escolha o equipamento e escreva o laudo.');
                  return;
                }
                await salvar(
                  () => widget.api.criarManutencao({
                    'equipamento_id': equipamentoId,
                    'laudo': laudo.text.trim(),
                    'sem_conserto': semConserto,
                  }),
                );
              },
              child: const Text('Salvar laudo'),
            ),
          ],
        ),
      ),
    );
    laudo.dispose();
  }

  Future<void> novoSistema(List<Map<String, dynamic>> funcionarios) async {
    if (funcionarios.isEmpty) {
      mostrarMensagem('Cadastre um funcionário antes de adicionar um sistema.');
      return;
    }
    int? funcionarioId;
    final nome = TextEditingController();
    await showDialog<void>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, atualizarDialogo) => AlertDialog(
          title: const Text('Adicionar sistema usado'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<int>(
                initialValue: funcionarioId,
                decoration: const InputDecoration(labelText: 'Funcionário'),
                items: funcionarios
                    .map(
                      (item) => DropdownMenuItem<int>(
                        value: item['id'] as int,
                        child: Text('${item['nome']} · ${item['matricula']}'),
                      ),
                    )
                    .toList(),
                onChanged: (valor) =>
                    atualizarDialogo(() => funcionarioId = valor),
              ),
              TextField(
                controller: nome,
                decoration: const InputDecoration(
                  labelText: 'Sistema (ex.: Microsoft 365, ChatGPT, Claude)',
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () async {
                if (funcionarioId == null || nome.text.trim().isEmpty) {
                  mostrarMensagem('Escolha o funcionário e informe o sistema.');
                  return;
                }
                await salvar(
                  () => widget.api.criarSistema({
                    'funcionario_id': funcionarioId,
                    'nome_sistema': nome.text.trim(),
                  }),
                );
              },
              child: const Text('Salvar'),
            ),
          ],
        ),
      ),
    );
    nome.dispose();
  }

  Future<void> removerFuncionario(Map<String, dynamic> pessoa) async {
    final confirmou = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Remover funcionário?'),
        content: Text(
          'Deseja remover ${pessoa['nome']} da empresa? O histórico será mantido e equipamentos ativos voltarão ao estoque.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Remover'),
          ),
        ],
      ),
    );
    if (confirmou != true) return;
    try {
      await widget.api.excluirFuncionario(pessoa['id'] as int);
      atualizar();
    } catch (erro) {
      mostrarMensagem(erro.toString().replaceFirst('Exception: ', ''));
    }
  }

  Future<void> devolver(Map<String, dynamic> item) async {
    try {
      await widget.api.devolverEquipamento(item['id'] as int);
      atualizar();
    } catch (erro) {
      mostrarMensagem(erro.toString().replaceFirst('Exception: ', ''));
    }
  }

  Future<void> finalizarSistema(Map<String, dynamic> item) async {
    try {
      await widget.api.finalizarSistema(item['id'] as int);
      atualizar();
    } catch (erro) {
      mostrarMensagem(erro.toString().replaceFirst('Exception: ', ''));
    }
  }

  Widget bloco(String titulo, List<Widget> filhos) => Card(
    color: Colors.white,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 14, 13, 9),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  titulo,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: azulMarinho,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFFF1F5F9),
                  borderRadius: BorderRadius.circular(99),
                ),
                child: Text(
                  '${filhos.length}',
                  style: const TextStyle(
                    color: Color(0xFF64748B),
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
        ),
        if (filhos.isEmpty)
          const EstadoVazioAtivo(
            titulo: 'Sem registros nesta seção',
            descricao: 'Os novos registros aparecem aqui após serem salvos.',
            icone: Icons.history_rounded,
          )
        else
          ...filhos,
      ],
    ),
  );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const LogoAtivoTI(),
        actions: [
          IconButton(
            tooltip: 'Atualizar',
            onPressed: atualizar,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: FutureBuilder<Map<String, List<Map<String, dynamic>>>>(
        future: dadosFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      snapshot.error.toString().replaceFirst('Exception: ', ''),
                      textAlign: TextAlign.center,
                    ),
                    TextButton(
                      onPressed: atualizar,
                      child: const Text('Tentar novamente'),
                    ),
                  ],
                ),
              ),
            );
          }
          final dados = snapshot.data!;
          final funcionarios = dados['funcionarios']!;
          final equipamentos = dados['equipamentos']!;
          final alocacoes = dados['alocacoes']!;
          final manutencoes = dados['manutencoes']!;
          final sistemas = dados['sistemas']!;
          return RefreshIndicator(
            onRefresh: () async => atualizar(),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(14, 7, 14, 24),
              children: [
                const TituloPaginaAtivo(
                  sobretitulo: 'Equipe e responsabilidades',
                  titulo: 'Gestão',
                  descricao:
                      'Funcionários, entregas, sistemas e manutenções no mesmo histórico.',
                ),
                if (widget.podeEditar) ...[
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      FilledButton.icon(
                        onPressed: novoFuncionario,
                        icon: const Icon(Icons.person_add_alt_1),
                        label: const Text('Funcionário'),
                      ),
                      FilledButton.tonalIcon(
                        onPressed: () =>
                            novaAlocacao(funcionarios, equipamentos),
                        icon: const Icon(Icons.assignment_ind_outlined),
                        label: const Text('Entregar equipamento'),
                      ),
                      FilledButton.tonalIcon(
                        onPressed: () => novaManutencao(equipamentos),
                        icon: const Icon(Icons.build_outlined),
                        label: const Text('Laudo'),
                      ),
                      FilledButton.tonalIcon(
                        onPressed: () => novoSistema(funcionarios),
                        icon: const Icon(Icons.apps),
                        label: const Text('Sistema'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                ],
                bloco(
                  'Funcionários ativos',
                  funcionarios
                      .map(
                        (pessoa) => ListTile(
                          dense: true,
                          title: Text(
                            pessoa['nome']?.toString() ?? '',
                            style: const TextStyle(
                              color: azulMarinho,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          subtitle: Text(
                            'CPF: ${pessoa['cpf']} · Matrícula: ${pessoa['matricula']}\nSetor: ${pessoa['setor']} · ID: ${pessoa['id']}',
                          ),
                          isThreeLine: true,
                          trailing: widget.podeEditar
                              ? PopupMenuButton<String>(
                                  tooltip: 'Ações do funcionário',
                                  onSelected: (acao) {
                                    if (acao == 'editar') {
                                      novoFuncionario(pessoa);
                                    } else {
                                      removerFuncionario(pessoa);
                                    }
                                  },
                                  itemBuilder: (_) => const [
                                    PopupMenuItem(
                                      value: 'editar',
                                      child: Text('Editar'),
                                    ),
                                    PopupMenuItem(
                                      value: 'remover',
                                      child: Text('Remover da empresa'),
                                    ),
                                  ],
                                )
                              : null,
                        ),
                      )
                      .toList(),
                ),
                bloco(
                  'Entregas e devoluções',
                  alocacoes
                      .map(
                        (item) => ListTile(
                          title: Text(
                            '${item['patrimonio']} · ${item['nome_equipamento']}',
                          ),
                          subtitle: Text(
                            '${item['nome_funcionario']} · ID ${item['funcionario_id']} · Matrícula ${item['matricula_funcionario']} · ${item['setor_funcionario']}\n${item['situacao']} · Entrega ${item['data_alocacao'].toString().split('T').first} · Devolução ${item['data_devolucao']?.toString().split('T').first ?? 'em aberto'}',
                          ),
                          isThreeLine: true,
                          trailing:
                              widget.podeEditar &&
                                  item['data_devolucao'] == null
                              ? TextButton(
                                  onPressed: () => devolver(item),
                                  child: const Text('Devolver'),
                                )
                              : null,
                        ),
                      )
                      .toList(),
                ),
                bloco(
                  'Sistemas usados',
                  sistemas
                      .map(
                        (item) => ListTile(
                          title: Text(
                            '${item['nome_sistema']} · ${item['nome_funcionario']}',
                          ),
                          subtitle: Text(
                            'ID ${item['funcionario_id']} · Matrícula ${item['matricula_funcionario']} · Desde ${item['data_inicio'].toString().split('T').first} · Até ${item['data_fim']?.toString().split('T').first ?? 'em uso'}',
                          ),
                          trailing:
                              widget.podeEditar && item['data_fim'] == null
                              ? TextButton(
                                  onPressed: () => finalizarSistema(item),
                                  child: const Text('Finalizar'),
                                )
                              : null,
                        ),
                      )
                      .toList(),
                ),
                bloco(
                  'Laudos de manutenção',
                  manutencoes
                      .map(
                        (item) => ListTile(
                          title: Text(
                            '${item['patrimonio']} · ${item['nome_equipamento']}',
                          ),
                          subtitle: Text(
                            '${item['data'].toString().split('T').first} · ${item['sem_conserto'] == true ? 'Sem conserto; equipamento baixado' : 'Consertado; voltou ao estoque'}\nLaudo: ${item['laudo']}',
                          ),
                          isThreeLine: true,
                        ),
                      )
                      .toList(),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
