import 'dart:convert';

import 'package:flutter/material.dart';

import '../brand.dart';
import '../services/api_service.dart';

class TelaUsuarios extends StatefulWidget {
  final ApiService api;
  final int usuarioConectadoId;
  final VoidCallback? aoVoltar;
  final ValueChanged<String>? aoAtualizarLogin;

  const TelaUsuarios({
    super.key,
    required this.api,
    required this.usuarioConectadoId,
    this.aoVoltar,
    this.aoAtualizarLogin,
  });

  @override
  State<TelaUsuarios> createState() => _TelaUsuariosState();
}

class _TelaUsuariosState extends State<TelaUsuarios> {
  late Future<List<Map<String, dynamic>>> usuariosFuture;

  @override
  void initState() {
    super.initState();
    usuariosFuture = widget.api.listarUsuarios();
  }

  void atualizarLista() {
    setState(() => usuariosFuture = widget.api.listarUsuarios());
  }

  Widget dado(String rotulo, String valor) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
    decoration: BoxDecoration(
      color: const Color(0xFFF3F7FB),
      borderRadius: BorderRadius.circular(7),
    ),
    child: Text(
      '$rotulo · $valor',
      maxLines: 1,
      overflow: TextOverflow.ellipsis,
      style: const TextStyle(color: Color(0xFF52677F), fontSize: 10),
    ),
  );

  Future<void> novoUsuario() async {
    final criado = await showDialog<bool>(
      context: context,
      builder: (_) => _DialogoNovoUsuario(api: widget.api),
    );
    if (criado == true) atualizarLista();
  }

  Future<void> editarCredenciais(Map<String, dynamic> usuario) async {
    final email = await showDialog<String>(
      context: context,
      builder: (_) => _DialogoEditarCredenciais(
        api: widget.api,
        usuarioId: usuario['id'] as int,
        emailAtual: usuario['email']?.toString() ?? '',
      ),
    );
    if (email == null) return;
    atualizarLista();
    if (usuario['id'] == widget.usuarioConectadoId) {
      widget.aoAtualizarLogin?.call(email);
    }
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Credenciais atualizadas com sucesso.')),
      );
    }
  }

  Future<void> excluirUsuario(Map<String, dynamic> usuario) async {
    final confirmou = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Excluir usuário?'),
        content: Text('Deseja excluir ${usuario['nome']}?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Excluir'),
          ),
        ],
      ),
    );
    if (confirmou != true) return;
    try {
      await widget.api.excluirUsuario(usuario['id'] as int);
      atualizarLista();
    } catch (falha) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(falha.toString().replaceFirst('Exception: ', '')),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: widget.aoVoltar == null
            ? null
            : IconButton(
                tooltip: 'Voltar',
                onPressed: widget.aoVoltar,
                icon: const Icon(Icons.arrow_back),
              ),
        title: const LogoAtivoTI(),
      ),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: usuariosFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    snapshot.error.toString().replaceFirst('Exception: ', ''),
                  ),
                  TextButton(
                    onPressed: atualizarLista,
                    child: const Text('Tentar novamente'),
                  ),
                ],
              ),
            );
          }
          final usuarios = snapshot.data ?? [];
          return RefreshIndicator(
            onRefresh: () async => atualizarLista(),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const TituloPaginaAtivo(
                  sobretitulo: 'Equipe de TI',
                  titulo: 'Usuários e perfis',
                  descricao: 'Acessos de administrador e consulta.',
                ),
                FilledButton.icon(
                  onPressed: novoUsuario,
                  icon: const Icon(Icons.person_add_alt_1),
                  label: const Text('Cadastrar usuário'),
                ),
                const SizedBox(height: 16),
                if (usuarios.isEmpty)
                  const Card(
                    child: EstadoVazioAtivo(
                      titulo: 'Nenhum usuário cadastrado',
                      descricao: 'Cadastre um acesso para a equipe de TI.',
                      icone: Icons.manage_accounts_outlined,
                    ),
                  ),
                ...usuarios.map((usuario) {
                  final conectado = usuario['id'] == widget.usuarioConectadoId;
                  final administrador = usuario['perfil'] == 'admin';
                  return Card(
                    color: Colors.white,
                    child: Padding(
                      padding: const EdgeInsets.all(13),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              CircleAvatar(
                                radius: 19,
                                backgroundColor: const Color(0xFFE8F0FF),
                                foregroundColor: azulMarinho,
                                child: Text(
                                  usuario['nome']?.toString().isNotEmpty == true
                                      ? usuario['nome']
                                            .toString()[0]
                                            .toUpperCase()
                                      : 'U',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      usuario['nome']?.toString() ?? 'Usuário',
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(
                                        color: azulMarinho,
                                        fontSize: 13,
                                        fontWeight: FontWeight.w700,
                                      ),
                                    ),
                                    const SizedBox(height: 2),
                                    Text(
                                      usuario['email']?.toString() ?? '',
                                      maxLines: 2,
                                      overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(
                                        color: Color(0xFF64748B),
                                        fontSize: 10,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              IconButton(
                                tooltip: 'Editar login e senha',
                                visualDensity: VisualDensity.compact,
                                onPressed: () => editarCredenciais(usuario),
                                icon: const Icon(Icons.edit_outlined),
                              ),
                              if (!conectado)
                                IconButton(
                                  tooltip: 'Excluir usuário',
                                  visualDensity: VisualDensity.compact,
                                  onPressed: () => excluirUsuario(usuario),
                                  icon: const Icon(Icons.delete_outline),
                                ),
                            ],
                          ),
                          const SizedBox(height: 9),
                          Wrap(
                            spacing: 7,
                            runSpacing: 6,
                            crossAxisAlignment: WrapCrossAlignment.center,
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 9,
                                  vertical: 5,
                                ),
                                decoration: BoxDecoration(
                                  color: administrador
                                      ? const Color(0xFFE8F0FF)
                                      : const Color(0xFFE7FAF5),
                                  borderRadius: BorderRadius.circular(99),
                                ),
                                child: Text(
                                  administrador ? 'Administrador' : 'Consulta',
                                  style: TextStyle(
                                    color: administrador
                                        ? azul
                                        : const Color(0xFF087E6D),
                                    fontSize: 10,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                              if (conectado)
                                const Text(
                                  'Conectado',
                                  style: TextStyle(
                                    color: Color(0xFF087E6D),
                                    fontSize: 10,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              dado(
                                'Matrícula',
                                usuario['matricula']?.toString() ?? '—',
                              ),
                              dado(
                                'Setor',
                                usuario['setor']?.toString() ?? '—',
                              ),
                              dado('CPF', usuario['cpf']?.toString() ?? '—'),
                            ],
                          ),
                        ],
                      ),
                    ),
                  );
                }),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _DialogoNovoUsuario extends StatefulWidget {
  final ApiService api;

  const _DialogoNovoUsuario({required this.api});

  @override
  State<_DialogoNovoUsuario> createState() => _DialogoNovoUsuarioState();
}

class _DialogoNovoUsuarioState extends State<_DialogoNovoUsuario> {
  final chaveFormulario = GlobalKey<FormState>();
  final nome = TextEditingController();
  final email = TextEditingController();
  final senha = TextEditingController();
  final cpf = TextEditingController();
  final matricula = TextEditingController();
  final setor = TextEditingController();
  String perfil = 'comum';
  bool salvando = false;
  String? erro;

  @override
  void dispose() {
    nome.dispose();
    email.dispose();
    senha.dispose();
    cpf.dispose();
    matricula.dispose();
    setor.dispose();
    super.dispose();
  }

  Future<void> salvar() async {
    if (salvando) return;
    if (!(chaveFormulario.currentState?.validate() ?? false)) return;
    setState(() {
      salvando = true;
      erro = null;
    });
    try {
      await widget.api.criarUsuario({
        'nome': nome.text.trim(),
        'email': email.text.trim(),
        'senha': senha.text,
        'cpf': cpf.text.trim(),
        'matricula': matricula.text.trim(),
        'setor': setor.text.trim(),
        'perfil': perfil,
      });
      if (mounted) Navigator.pop(context, true);
    } catch (falha) {
      if (mounted) {
        setState(() => erro = falha.toString().replaceFirst('Exception: ', ''));
      }
    } finally {
      if (mounted) setState(() => salvando = false);
    }
  }

  Widget campo(
    String rotulo,
    TextEditingController controlador, {
    bool senha = false,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: controlador,
        obscureText: senha,
        decoration: InputDecoration(
          labelText: rotulo,
          border: const OutlineInputBorder(),
        ),
        validator: (valor) {
          if (valor == null || valor.trim().isEmpty) {
            return 'Preencha este campo.';
          }
          if (senha && valor.length < 8) {
            return 'Use pelo menos 8 caracteres.';
          }
          return null;
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Cadastrar usuário'),
      content: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 420),
        child: SingleChildScrollView(
          child: Form(
            key: chaveFormulario,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                campo('Nome completo', nome),
                campo('E-mail', email),
                campo('Senha (mínimo 8 caracteres)', senha, senha: true),
                campo('CPF (11 números)', cpf),
                campo('Matrícula', matricula),
                campo('Setor', setor),
                DropdownButtonFormField<String>(
                  initialValue: perfil,
                  decoration: const InputDecoration(labelText: 'Perfil'),
                  items: const [
                    DropdownMenuItem(
                      value: 'comum',
                      child: Text('Somente consulta'),
                    ),
                    DropdownMenuItem(
                      value: 'admin',
                      child: Text('Administrador'),
                    ),
                  ],
                  onChanged: (valor) {
                    if (valor != null) setState(() => perfil = valor);
                  },
                ),
                if (erro != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    erro!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: salvando ? null : () => Navigator.pop(context, false),
          child: const Text('Cancelar'),
        ),
        FilledButton(
          onPressed: salvando ? null : salvar,
          child: const Text('Salvar'),
        ),
      ],
    );
  }
}

class _DialogoEditarCredenciais extends StatefulWidget {
  final ApiService api;
  final int usuarioId;
  final String emailAtual;

  const _DialogoEditarCredenciais({
    required this.api,
    required this.usuarioId,
    required this.emailAtual,
  });

  @override
  State<_DialogoEditarCredenciais> createState() =>
      _DialogoEditarCredenciaisState();
}

class _DialogoEditarCredenciaisState extends State<_DialogoEditarCredenciais> {
  final chaveFormulario = GlobalKey<FormState>();
  late final TextEditingController email;
  final novaSenha = TextEditingController();
  bool salvando = false;
  String? erro;

  @override
  void initState() {
    super.initState();
    email = TextEditingController(text: widget.emailAtual);
  }

  @override
  void dispose() {
    email.dispose();
    novaSenha.dispose();
    super.dispose();
  }

  Future<void> salvar() async {
    if (!(chaveFormulario.currentState?.validate() ?? false)) return;
    setState(() {
      salvando = true;
      erro = null;
    });
    try {
      await widget.api.atualizarCredenciais(
        widget.usuarioId,
        email.text,
        novaSenha: novaSenha.text,
      );
      if (mounted) Navigator.pop(context, email.text.trim());
    } catch (falha) {
      if (mounted) {
        setState(() => erro = falha.toString().replaceFirst('Exception: ', ''));
      }
    } finally {
      if (mounted) setState(() => salvando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Editar credenciais'),
      content: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 420),
        child: SingleChildScrollView(
          child: Form(
            key: chaveFormulario,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextFormField(
                  controller: email,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(
                    labelText: 'E-mail de login',
                  ),
                  validator: (valor) {
                    final texto = valor?.trim() ?? '';
                    return RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(texto)
                        ? null
                        : 'Informe um e-mail válido.';
                  },
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: novaSenha,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Nova senha (opcional)',
                  ),
                  validator: (valor) {
                    if (valor != null &&
                        valor.trim().isNotEmpty &&
                        valor.length < 8) {
                      return 'Use pelo menos 8 caracteres.';
                    }
                    if (valor != null &&
                        valor.trim().isNotEmpty &&
                        utf8.encode(valor).length > 72) {
                      return 'A senha deve ter no máximo 72 bytes.';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 8),
                const Text(
                  'Deixe em branco para manter a senha atual. Use ao menos 8 caracteres e até 72 bytes. A senha atual nunca é exibida.',
                  style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                ),
                if (erro != null) ...[
                  const SizedBox(height: 10),
                  Text(
                    erro!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: salvando ? null : () => Navigator.pop(context),
          child: const Text('Cancelar'),
        ),
        FilledButton(
          onPressed: salvando ? null : salvar,
          child: Text(salvando ? 'Salvando...' : 'Salvar'),
        ),
      ],
    );
  }
}
