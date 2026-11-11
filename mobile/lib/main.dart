import 'package:flutter/material.dart';

import 'brand.dart';
import 'models/equipamento.dart';
import 'screens/tela_login.dart';
import 'screens/tela_gestao.dart';
import 'screens/tela_credenciais.dart';
import 'screens/tela_relatorio.dart';
import 'screens/tela_usuarios.dart';
import 'services/api_service.dart';

void main() {
  runApp(const AtivoTiApp());
}

class AtivoTiApp extends StatefulWidget {
  const AtivoTiApp({super.key});

  @override
  State<AtivoTiApp> createState() => _AtivoTiAppState();
}

class _AtivoTiAppState extends State<AtivoTiApp> {
  final ApiService api = ApiService();
  Map<String, dynamic>? usuario;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AtivoTI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme:
            ColorScheme.fromSeed(
              seedColor: azul,
              brightness: Brightness.light,
            ).copyWith(
              primary: azul,
              secondary: verdeAgua,
              surface: Colors.white,
              onSurface: const Color(0xFF1F2937),
            ),
        scaffoldBackgroundColor: fundo,
        appBarTheme: const AppBarTheme(
          backgroundColor: azulMarinho,
          foregroundColor: Colors.white,
          centerTitle: false,
          elevation: 0,
          surfaceTintColor: Colors.transparent,
          titleTextStyle: TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.w700,
          ),
        ),
        cardTheme: CardThemeData(
          color: Colors.white,
          elevation: 0,
          margin: const EdgeInsets.only(bottom: 12),
          shape: RoundedRectangleBorder(
            side: const BorderSide(color: Color(0xFFE2E8F0)),
            borderRadius: BorderRadius.circular(14),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 14,
            vertical: 13,
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(9),
            borderSide: const BorderSide(color: Color(0xFFDCE4ED)),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(9),
            borderSide: const BorderSide(color: Color(0xFFDCE4ED)),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(9),
            borderSide: const BorderSide(color: azul, width: 1.6),
          ),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            backgroundColor: azul,
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 13),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(9),
            ),
            textStyle: const TextStyle(fontWeight: FontWeight.w600),
          ),
        ),
        navigationBarTheme: NavigationBarThemeData(
          backgroundColor: Colors.white,
          indicatorColor: const Color(0xFFE8F0FF),
          elevation: 8,
          labelTextStyle: WidgetStateProperty.resolveWith<TextStyle>((states) {
            return TextStyle(
              color: states.contains(WidgetState.selected)
                  ? azul
                  : const Color(0xFF64748B),
              fontSize: 10,
              fontWeight: states.contains(WidgetState.selected)
                  ? FontWeight.w700
                  : FontWeight.w500,
            );
          }),
        ),
      ),
      home: usuario == null
          ? TelaLogin(
              api: api,
              aoEntrar: (dados) => setState(() => usuario = dados),
            )
          : AreaPrincipal(
              api: api,
              usuario: usuario!,
              aoSair: () {
                api.sair();
                setState(() => usuario = null);
              },
            ),
    );
  }
}

class AreaPrincipal extends StatefulWidget {
  final ApiService api;
  final Map<String, dynamic> usuario;
  final VoidCallback aoSair;

  const AreaPrincipal({
    super.key,
    required this.api,
    required this.usuario,
    required this.aoSair,
  });

  @override
  State<AreaPrincipal> createState() => _AreaPrincipalState();
}

class _AreaPrincipalState extends State<AreaPrincipal> {
  int indiceSelecionado = 0;
  late final List<Widget?> paginas;

  @override
  void initState() {
    super.initState();
    paginas = List<Widget?>.filled(4, null);
    paginas[0] = criarPagina(0);
  }

  Widget criarPagina(int indice) {
    final usuario = widget.usuario;
    return switch (indice) {
      0 => TelaEquipamentos(
        api: widget.api,
        usuario: usuario,
        aoAbrirGestao: () => selecionarPagina(1),
        aoAbrirMais: () => selecionarPagina(3),
      ),
      1 => TelaGestao(
        api: widget.api,
        podeEditar: usuario['perfil'] == 'admin',
      ),
      2 => TelaRelatorio(api: widget.api),
      _ => TelaMais(
        api: widget.api,
        usuario: usuario,
        aoSair: widget.aoSair,
        aoAbrirGestao: () => selecionarPagina(1),
      ),
    };
  }

  void selecionarPagina(int indice) {
    setState(() {
      paginas[indice] ??= criarPagina(indice);
      indiceSelecionado = indice;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: indiceSelecionado,
        children: [
          for (final pagina in paginas) pagina ?? const SizedBox.shrink(),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: indiceSelecionado,
        onDestinationSelected: selecionarPagina,
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.desktop_windows_outlined),
            selectedIcon: Icon(Icons.desktop_windows_rounded),
            label: 'Equipamentos',
          ),
          NavigationDestination(
            icon: Icon(Icons.swap_horiz_rounded),
            selectedIcon: Icon(Icons.swap_horiz_rounded),
            label: 'Empréstimos',
          ),
          NavigationDestination(
            icon: Icon(Icons.bar_chart_outlined),
            selectedIcon: Icon(Icons.bar_chart_rounded),
            label: 'Relatórios',
          ),
          NavigationDestination(
            icon: Icon(Icons.more_horiz_rounded),
            selectedIcon: Icon(Icons.more_horiz_rounded),
            label: 'Mais',
          ),
        ],
      ),
    );
  }
}

class TelaMais extends StatefulWidget {
  final ApiService api;
  final Map<String, dynamic> usuario;
  final VoidCallback aoSair;
  final VoidCallback aoAbrirGestao;

  const TelaMais({
    super.key,
    required this.api,
    required this.usuario,
    required this.aoSair,
    required this.aoAbrirGestao,
  });

  @override
  State<TelaMais> createState() => _TelaMaisState();
}

class _TelaMaisState extends State<TelaMais> {
  bool usuariosAberto = false;
  bool credenciaisAbertas = false;

  @override
  Widget build(BuildContext context) {
    if (usuariosAberto && widget.usuario['perfil'] == 'admin') {
      return TelaUsuarios(
        api: widget.api,
        usuarioConectadoId: widget.usuario['id'] as int,
        aoVoltar: () => setState(() => usuariosAberto = false),
        aoAtualizarLogin: (email) =>
            setState(() => widget.usuario['email'] = email),
      );
    }
    if (credenciaisAbertas) {
      return TelaCredenciais(
        api: widget.api,
        usuarioId: widget.usuario['id'] as int,
        emailAtual: widget.usuario['email']?.toString() ?? '',
        aoVoltar: () => setState(() => credenciaisAbertas = false),
        aoAtualizarLogin: (email) =>
            setState(() => widget.usuario['email'] = email),
      );
    }
    final nome = widget.usuario['nome']?.toString() ?? 'Usuário';
    final perfil = widget.usuario['perfil'] == 'admin'
        ? 'Administrador'
        : 'Consulta';
    return Scaffold(
      appBar: AppBar(title: const LogoAtivoTI()),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(14, 8, 14, 24),
        children: [
          const TituloPaginaAtivo(
            sobretitulo: 'AtivoTI',
            titulo: 'Mais opções',
            descricao: 'Acesso à gestão da equipe e às configurações da conta.',
          ),
          Card(
            child: ListTile(
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 7,
              ),
              leading: CircleAvatar(
                backgroundColor: const Color(0xFFE8F0FF),
                foregroundColor: azulMarinho,
                child: Text(nome.isEmpty ? 'U' : nome[0].toUpperCase()),
              ),
              title: Text(nome, style: const TextStyle(color: azulMarinho)),
              subtitle: Text(perfil),
              trailing: const Icon(Icons.verified_user_outlined),
            ),
          ),
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.manage_accounts_outlined),
                  title: const Text('Minha conta'),
                  subtitle: const Text('Altere seu e-mail de login ou senha.'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => setState(() => credenciaisAbertas = true),
                ),
                const Divider(height: 1, indent: 56),
                ListTile(
                  leading: const Icon(Icons.people_alt_outlined),
                  title: const Text('Funcionários e históricos'),
                  subtitle: const Text(
                    'Acompanhe entregas, devoluções e manutenções.',
                  ),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: widget.aoAbrirGestao,
                ),
                if (widget.usuario['perfil'] == 'admin') ...[
                  const Divider(height: 1, indent: 56),
                  ListTile(
                    leading: const Icon(Icons.manage_accounts_outlined),
                    title: const Text('Usuários'),
                    subtitle: const Text('Gerencie os acessos ao AtivoTI.'),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => setState(() => usuariosAberto = true),
                  ),
                ],
              ],
            ),
          ),
          Card(
            child: ListTile(
              leading: const Icon(Icons.info_outline),
              title: const Text('Sobre o AtivoTI'),
              subtitle: const Text(
                'Equipamentos organizados. Gestão sem complicação.',
              ),
            ),
          ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: widget.aoSair,
            icon: const Icon(Icons.logout),
            label: const Text('Sair da conta'),
            style: OutlinedButton.styleFrom(
              foregroundColor: azulMarinho,
              padding: const EdgeInsets.symmetric(vertical: 13),
              side: const BorderSide(color: Color(0xFFDCE4ED)),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(9),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class TelaEquipamentos extends StatefulWidget {
  final ApiService api;
  final Map<String, dynamic> usuario;
  final VoidCallback aoAbrirGestao;
  final VoidCallback aoAbrirMais;

  const TelaEquipamentos({
    super.key,
    required this.api,
    required this.usuario,
    required this.aoAbrirGestao,
    required this.aoAbrirMais,
  });

  @override
  State<TelaEquipamentos> createState() => _TelaEquipamentosState();
}

class _TelaEquipamentosState extends State<TelaEquipamentos> {
  final TextEditingController tipoFiltroController = TextEditingController();
  final TextEditingController setorFiltroController = TextEditingController();
  final TextEditingController buscaController = TextEditingController();
  late Future<List<Equipamento>> equipamentosFuture;
  String? statusFiltro;
  bool buscaAberta = false;

  ApiService get api => widget.api;
  bool get podeEditar => widget.usuario['perfil'] == 'admin';

  @override
  void initState() {
    super.initState();
    equipamentosFuture = buscarEquipamentos();
  }

  Future<List<Equipamento>> buscarEquipamentos() {
    return api.listarEquipamentos();
  }

  void carregarEquipamentos() {
    setState(() {
      equipamentosFuture = buscarEquipamentos();
    });
  }

  void limparFiltros() {
    statusFiltro = null;
    tipoFiltroController.clear();
    setorFiltroController.clear();
    buscaController.clear();
    setState(() {});
  }

  Future<void> abrirFiltrosAvancados() async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (contextFolha) => SafeArea(
        child: Padding(
          padding: EdgeInsets.fromLTRB(
            20,
            4,
            20,
            20 + MediaQuery.viewInsetsOf(contextFolha).bottom,
          ),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Filtros avançados',
                  style: TextStyle(
                    color: azulMarinho,
                    fontSize: 19,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  key: ValueKey<String>(statusFiltro ?? ''),
                  initialValue: statusFiltro ?? '',
                  decoration: const InputDecoration(
                    labelText: 'Status',
                    border: OutlineInputBorder(),
                  ),
                  items: const [
                    DropdownMenuItem(value: '', child: Text('Todos')),
                    DropdownMenuItem(value: 'Em uso', child: Text('Em uso')),
                    DropdownMenuItem(
                      value: 'Em estoque',
                      child: Text('Em estoque'),
                    ),
                    DropdownMenuItem(
                      value: 'Emprestado',
                      child: Text('Emprestado'),
                    ),
                    DropdownMenuItem(
                      value: 'Em manutenção',
                      child: Text('Em manutenção'),
                    ),
                    DropdownMenuItem(value: 'Baixado', child: Text('Baixado')),
                    DropdownMenuItem(
                      value: 'Indisponíveis',
                      child: Text('Indisponíveis'),
                    ),
                  ],
                  onChanged: (valor) {
                    setState(() {
                      statusFiltro = valor == null || valor.isEmpty
                          ? null
                          : valor;
                    });
                  },
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: tipoFiltroController,
                  decoration: const InputDecoration(
                    labelText: 'Tipo',
                    hintText: 'Ex.: Notebook',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: setorFiltroController,
                  decoration: const InputDecoration(
                    labelText: 'Setor',
                    hintText: 'Ex.: Laboratório',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: FilledButton(
                        onPressed: () {
                          Navigator.pop(contextFolha);
                          setState(() {});
                        },
                        child: const Text('Aplicar filtros'),
                      ),
                    ),
                    const SizedBox(width: 10),
                    TextButton(
                      onPressed: () {
                        limparFiltros();
                        Navigator.pop(contextFolha);
                      },
                      child: const Text('Limpar'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> atualizarLista() async {
    final novaConsulta = buscarEquipamentos();
    setState(() {
      equipamentosFuture = novaConsulta;
    });
    try {
      await novaConsulta;
    } catch (_) {
      // O FutureBuilder mostra a mensagem de erro na tela.
    }
  }

  @override
  void dispose() {
    tipoFiltroController.dispose();
    setorFiltroController.dispose();
    buscaController.dispose();
    super.dispose();
  }

  Future<void> abrirFormulario([Equipamento? equipamento]) async {
    final salvo = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (context) =>
            TelaFormulario(api: widget.api, equipamento: equipamento),
      ),
    );

    if (salvo == true) {
      carregarEquipamentos();
    }
  }

  Future<void> confirmarExclusao(Equipamento equipamento) async {
    final confirmou = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Excluir equipamento?'),
        content: Text('Deseja excluir "${equipamento.nome}"?'),
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

    if (confirmou != true || equipamento.id == null) {
      return;
    }

    try {
      await api.excluirEquipamento(equipamento.id!);
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Equipamento excluído.')));
      carregarEquipamentos();
    } catch (erro) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(erro.toString().replaceFirst('Exception: ', '')),
        ),
      );
    }
  }

  Widget _etiquetaInfo(String rotulo, String valor) => Container(
    constraints: const BoxConstraints(maxWidth: 260),
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const LogoAtivoTI(),
        actions: [
          IconButton(
            tooltip: buscaAberta ? 'Fechar busca' : 'Buscar equipamento',
            onPressed: () => setState(() => buscaAberta = !buscaAberta),
            icon: Icon(
              buscaAberta ? Icons.close_rounded : Icons.search_rounded,
            ),
          ),
          PopupMenuButton<String>(
            tooltip: 'Abrir menu',
            icon: const Icon(Icons.menu_rounded),
            onSelected: (opcao) {
              if (opcao == 'emprestimos') widget.aoAbrirGestao();
              if (opcao == 'mais') widget.aoAbrirMais();
            },
            itemBuilder: (context) => const [
              PopupMenuItem(value: 'emprestimos', child: Text('Empréstimos')),
              PopupMenuItem(value: 'mais', child: Text('Mais opções')),
            ],
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: Column(
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 8, 16, 0),
            child: TituloPaginaAtivo(
              sobretitulo: 'Inventário de TI',
              titulo: 'Equipamentos',
              descricao: 'Consulte localização, condição e disponibilidade.',
            ),
          ),
          if (buscaAberta)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
              child: TextField(
                controller: buscaController,
                autofocus: true,
                onChanged: (_) => setState(() {}),
                decoration: InputDecoration(
                  hintText: 'Buscar equipamento ou patrimônio',
                  prefixIcon: const Icon(Icons.search_rounded),
                  suffixIcon: buscaController.text.isEmpty
                      ? null
                      : IconButton(
                          tooltip: 'Limpar busca',
                          onPressed: () {
                            buscaController.clear();
                            setState(() {});
                          },
                          icon: const Icon(Icons.close_rounded),
                        ),
                ),
              ),
            ),
          FutureBuilder<List<Equipamento>>(
            future: equipamentosFuture,
            builder: (context, snapshot) {
              final todos = snapshot.data ?? const <Equipamento>[];
              final emUso = todos
                  .where(
                    (item) =>
                        item.status == 'Em uso' || item.status == 'Emprestado',
                  )
                  .length;
              final manutencao = todos
                  .where((item) => item.status == 'Em manutenção')
                  .length;
              final indisponiveis = todos
                  .where((item) => item.status == 'Baixado')
                  .length;
              return SizedBox(
                height: 42,
                child: ListView(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  scrollDirection: Axis.horizontal,
                  children: [
                    ChoiceChip(
                      label: Text('Todos (${todos.length})'),
                      selected: statusFiltro == null,
                      onSelected: (_) => setState(() => statusFiltro = null),
                    ),
                    const SizedBox(width: 7),
                    ChoiceChip(
                      label: Text('Em uso ($emUso)'),
                      selected: statusFiltro == 'Em uso',
                      onSelected: (_) =>
                          setState(() => statusFiltro = 'Em uso'),
                    ),
                    const SizedBox(width: 7),
                    ChoiceChip(
                      label: Text('Manutenção ($manutencao)'),
                      selected: statusFiltro == 'Em manutenção',
                      onSelected: (_) =>
                          setState(() => statusFiltro = 'Em manutenção'),
                    ),
                    const SizedBox(width: 7),
                    ChoiceChip(
                      label: Text('Indisponíveis ($indisponiveis)'),
                      selected: statusFiltro == 'Indisponíveis',
                      onSelected: (_) =>
                          setState(() => statusFiltro = 'Indisponíveis'),
                    ),
                    const SizedBox(width: 3),
                    IconButton(
                      tooltip: 'Filtros avançados',
                      visualDensity: VisualDensity.compact,
                      onPressed: abrirFiltrosAvancados,
                      icon: const Icon(Icons.tune_rounded, size: 19),
                      style: IconButton.styleFrom(
                        foregroundColor: azulMarinho,
                        backgroundColor: const Color(0xFFF1F5F9),
                        minimumSize: const Size(36, 36),
                        maximumSize: const Size(36, 36),
                        padding: EdgeInsets.zero,
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
          Expanded(
            child: RefreshIndicator(
              onRefresh: atualizarLista,
              child: FutureBuilder<List<Equipamento>>(
                future: equipamentosFuture,
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return ListView(
                      children: const [
                        SizedBox(
                          height: 300,
                          child: Center(child: CircularProgressIndicator()),
                        ),
                      ],
                    );
                  }

                  if (snapshot.hasError) {
                    return ListView(
                      padding: const EdgeInsets.all(24),
                      children: [
                        const SizedBox(height: 80),
                        const Icon(
                          Icons.cloud_off,
                          size: 48,
                          color: azulMarinho,
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'Não consegui carregar os equipamentos.',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          snapshot.error.toString().replaceFirst(
                            'Exception: ',
                            '',
                          ),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 16),
                        Center(
                          child: FilledButton.icon(
                            onPressed: carregarEquipamentos,
                            icon: const Icon(Icons.refresh),
                            label: const Text('Tentar novamente'),
                          ),
                        ),
                      ],
                    );
                  }

                  final todos = snapshot.data ?? <Equipamento>[];
                  final termoBusca = buscaController.text.trim().toLowerCase();
                  final tipoBusca = tipoFiltroController.text
                      .trim()
                      .toLowerCase();
                  final setorBusca = setorFiltroController.text
                      .trim()
                      .toLowerCase();
                  final equipamentos = todos.where((item) {
                    final statusOk = switch (statusFiltro) {
                      null => true,
                      'Em uso' =>
                        item.status == 'Em uso' || item.status == 'Emprestado',
                      'Indisponíveis' => item.status == 'Baixado',
                      _ => item.status == statusFiltro,
                    };
                    final texto = [
                      item.nome,
                      item.patrimonio,
                      item.tipo,
                      item.marca ?? '',
                      item.modelo ?? '',
                      item.setor ?? '',
                    ].join(' ').toLowerCase();
                    return statusOk &&
                        (termoBusca.isEmpty || texto.contains(termoBusca)) &&
                        (tipoBusca.isEmpty ||
                            item.tipo.toLowerCase().contains(tipoBusca)) &&
                        (setorBusca.isEmpty ||
                            (item.setor ?? '').toLowerCase().contains(
                              setorBusca,
                            ));
                  }).toList();
                  if (equipamentos.isEmpty) {
                    final temFiltro =
                        statusFiltro != null ||
                        tipoFiltroController.text.trim().isNotEmpty ||
                        setorFiltroController.text.trim().isNotEmpty ||
                        buscaController.text.trim().isNotEmpty;
                    return ListView(
                      padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                      children: [
                        Card(
                          child: Column(
                            children: [
                              EstadoVazioAtivo(
                                compacto: false,
                                titulo: temFiltro
                                    ? 'Nenhum equipamento encontrado'
                                    : 'Seu inventário ainda está vazio',
                                descricao: temFiltro
                                    ? 'Revise os filtros para encontrar outros itens.'
                                    : 'Cadastre o primeiro equipamento e acompanhe seus dados aqui.',
                              ),
                              if (temFiltro)
                                Padding(
                                  padding: const EdgeInsets.only(bottom: 15),
                                  child: TextButton.icon(
                                    onPressed: limparFiltros,
                                    icon: const Icon(Icons.filter_alt_off),
                                    label: const Text('Limpar filtros'),
                                  ),
                                ),
                            ],
                          ),
                        ),
                      ],
                    );
                  }

                  return ListView.builder(
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
                    itemCount: equipamentos.length,
                    itemBuilder: (context, index) {
                      final equipamento = equipamentos[index];
                      return Card(
                        color: Colors.white,
                        margin: const EdgeInsets.only(bottom: 9),
                        child: Padding(
                          padding: const EdgeInsets.all(13),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Container(
                                    width: 38,
                                    height: 38,
                                    margin: const EdgeInsets.only(right: 10),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFFF1F5FB),
                                      borderRadius: BorderRadius.circular(9),
                                    ),
                                    child: const Icon(
                                      Icons.desktop_windows_outlined,
                                      color: azulMarinho,
                                      size: 19,
                                    ),
                                  ),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          equipamento.nome,
                                          maxLines: 2,
                                          overflow: TextOverflow.ellipsis,
                                          style: const TextStyle(
                                            color: azulMarinho,
                                            fontSize: 14,
                                            fontWeight: FontWeight.w700,
                                          ),
                                        ),
                                        const SizedBox(height: 3),
                                        Text(
                                          '${equipamento.tipo} · ${equipamento.patrimonio}',
                                          style: const TextStyle(
                                            color: Color(0xFF64748B),
                                            fontSize: 11,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  if (podeEditar)
                                    PopupMenuButton<String>(
                                      tooltip: 'Ações do equipamento',
                                      padding: EdgeInsets.zero,
                                      onSelected: (acao) {
                                        if (acao == 'editar') {
                                          abrirFormulario(equipamento);
                                        } else {
                                          confirmarExclusao(equipamento);
                                        }
                                      },
                                      itemBuilder: (context) => [
                                        const PopupMenuItem(
                                          value: 'editar',
                                          child: Text('Editar'),
                                        ),
                                        if (equipamento.status == 'Baixado')
                                          const PopupMenuItem(
                                            value: 'excluir',
                                            child: Text('Excluir'),
                                          ),
                                      ],
                                    ),
                                ],
                              ),
                              const SizedBox(height: 9),
                              Wrap(
                                spacing: 7,
                                runSpacing: 5,
                                crossAxisAlignment: WrapCrossAlignment.center,
                                children: [
                                  ChipStatusAtivo(equipamento.status),
                                  _etiquetaInfo(
                                    'Setor',
                                    equipamento.setor ?? 'Sem setor',
                                  ),
                                  _etiquetaInfo(
                                    'Condição',
                                    equipamento.condicao,
                                  ),
                                  if ((equipamento.marca ?? '').isNotEmpty ||
                                      (equipamento.modelo ?? '').isNotEmpty)
                                    _etiquetaInfo(
                                      'Modelo',
                                      '${equipamento.marca ?? ''} ${equipamento.modelo ?? ''}'
                                          .trim(),
                                    ),
                                  if (equipamento.numeroSerie != null)
                                    _etiquetaInfo(
                                      'Série',
                                      equipamento.numeroSerie!,
                                    ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  );
                },
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: podeEditar
          ? FloatingActionButton.extended(
              onPressed: () => abrirFormulario(),
              icon: const Icon(Icons.add),
              label: const Text('Novo equipamento'),
            )
          : null,
    );
  }
}

class TelaFormulario extends StatefulWidget {
  final ApiService api;
  final Equipamento? equipamento;

  const TelaFormulario({super.key, required this.api, this.equipamento});

  @override
  State<TelaFormulario> createState() => _TelaFormularioState();
}

class _TelaFormularioState extends State<TelaFormulario> {
  final GlobalKey<FormState> chaveFormulario = GlobalKey<FormState>();
  late final TextEditingController nomeController;
  late final TextEditingController tipoController;
  late final TextEditingController numeroSerieController;
  late final TextEditingController marcaController;
  late final TextEditingController modeloController;
  late final TextEditingController setorController;
  late final TextEditingController observacaoController;

  String statusSelecionado = 'Em estoque';
  String condicaoSelecionada = '';
  bool salvando = false;

  ApiService get api => widget.api;

  List<String> get statusDisponiveis {
    if (widget.equipamento == null) return ['Em estoque'];
    final status = widget.equipamento!.status;
    if (status == 'Em uso' || status == 'Emprestado') return [status];
    if (status == 'Baixado') return ['Baixado'];
    if (status == 'Em manutenção') return [status];
    return ['Em estoque', 'Em manutenção'];
  }

  final List<String> condicoesEquipamento = ['Novo', 'Usado'];

  @override
  void initState() {
    super.initState();
    final equipamento = widget.equipamento;
    nomeController = TextEditingController(text: equipamento?.nome ?? '');
    tipoController = TextEditingController(text: equipamento?.tipo ?? '');
    numeroSerieController = TextEditingController(
      text: equipamento?.numeroSerie ?? '',
    );
    marcaController = TextEditingController(text: equipamento?.marca ?? '');
    modeloController = TextEditingController(text: equipamento?.modelo ?? '');
    setorController = TextEditingController(text: equipamento?.setor ?? '');
    observacaoController = TextEditingController(
      text: equipamento?.observacao ?? '',
    );
    statusSelecionado = equipamento?.status ?? 'Em estoque';
    condicaoSelecionada = equipamento?.condicao ?? '';
  }

  @override
  void dispose() {
    nomeController.dispose();
    tipoController.dispose();
    numeroSerieController.dispose();
    marcaController.dispose();
    modeloController.dispose();
    setorController.dispose();
    observacaoController.dispose();
    super.dispose();
  }

  Future<void> salvarEquipamento() async {
    if (salvando) return;
    if (!(chaveFormulario.currentState?.validate() ?? false)) {
      return;
    }

    final equipamento = Equipamento(
      id: widget.equipamento?.id,
      nome: nomeController.text.trim(),
      tipo: tipoController.text.trim(),
      numeroSerie: valorOpcional(numeroSerieController.text),
      marca: valorOpcional(marcaController.text),
      modelo: valorOpcional(modeloController.text),
      setor: valorOpcional(setorController.text),
      condicao: condicaoSelecionada,
      status: statusSelecionado,
      observacao: valorOpcional(observacaoController.text),
    );

    setState(() => salvando = true);
    try {
      if (widget.equipamento == null) {
        await api.criarEquipamento(equipamento);
      } else {
        await api.atualizarEquipamento(equipamento);
      }
      if (mounted) Navigator.pop(context, true);
    } catch (erro) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(erro.toString().replaceFirst('Exception: ', '')),
        ),
      );
    } finally {
      if (mounted) setState(() => salvando = false);
    }
  }

  String? valorOpcional(String texto) {
    final valor = texto.trim();
    return valor.isEmpty ? null : valor;
  }

  Widget campoTexto(
    String rotulo,
    TextEditingController controller, {
    bool obrigatorio = false,
    int maxLength = 150,
    int maxLines = 1,
  }) {
    return TextFormField(
      controller: controller,
      maxLength: maxLength,
      maxLines: maxLines,
      decoration: InputDecoration(
        labelText: obrigatorio ? '$rotulo *' : rotulo,
        border: const OutlineInputBorder(),
        counterText: '',
      ),
      validator: obrigatorio
          ? (valor) {
              if (valor == null || valor.trim().isEmpty) {
                return 'Preencha este campo.';
              }
              return null;
            }
          : null,
    );
  }

  @override
  Widget build(BuildContext context) {
    final editando = widget.equipamento != null;

    return Scaffold(
      appBar: AppBar(
        title: Text(editando ? 'Editar equipamento' : 'Novo equipamento'),
      ),
      body: Form(
        key: chaveFormulario,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            if (editando)
              Padding(
                padding: const EdgeInsets.only(bottom: 14),
                child: Text('Patrimônio: ${widget.equipamento!.patrimonio}'),
              )
            else
              const Padding(
                padding: EdgeInsets.only(bottom: 14),
                child: Text('O número de patrimônio será gerado ao salvar.'),
              ),
            campoTexto('Nome', nomeController, obrigatorio: true),
            const SizedBox(height: 14),
            campoTexto(
              'Tipo',
              tipoController,
              obrigatorio: true,
              maxLength: 80,
            ),
            const SizedBox(height: 14),
            campoTexto(
              'Número de série',
              numeroSerieController,
              maxLength: 100,
            ),
            const SizedBox(height: 14),
            campoTexto('Marca', marcaController, maxLength: 100),
            const SizedBox(height: 14),
            campoTexto('Modelo', modeloController, maxLength: 100),
            const SizedBox(height: 14),
            campoTexto('Setor', setorController, maxLength: 100),
            const SizedBox(height: 14),
            DropdownButtonFormField<String>(
              initialValue: condicaoSelecionada,
              decoration: const InputDecoration(
                labelText: 'Condição *',
                border: OutlineInputBorder(),
              ),
              items: [
                const DropdownMenuItem(value: '', child: Text('Selecione')),
                ...condicoesEquipamento.map((condicao) {
                  return DropdownMenuItem(
                    value: condicao,
                    child: Text(condicao),
                  );
                }),
              ],
              validator: (valor) => valor == null || valor.isEmpty
                  ? 'Selecione a condição.'
                  : null,
              onChanged: (condicao) {
                if (condicao != null) {
                  setState(() => condicaoSelecionada = condicao);
                }
              },
            ),
            const SizedBox(height: 14),
            DropdownButtonFormField<String>(
              initialValue: statusSelecionado,
              decoration: const InputDecoration(
                labelText: 'Status',
                border: OutlineInputBorder(),
              ),
              items: statusDisponiveis.map((status) {
                return DropdownMenuItem(value: status, child: Text(status));
              }).toList(),
              onChanged: (status) {
                if (status != null) {
                  setState(() => statusSelecionado = status);
                }
              },
            ),
            const Padding(
              padding: EdgeInsets.only(top: 6),
              child: Text(
                'Registre entregas pela alocação. Encerre a manutenção ou dê baixa pelo laudo.',
                style: TextStyle(fontSize: 12),
              ),
            ),
            const SizedBox(height: 14),
            campoTexto(
              'Observação',
              observacaoController,
              maxLength: 500,
              maxLines: 3,
            ),
            const SizedBox(height: 18),
            FilledButton.icon(
              onPressed: salvando ? null : salvarEquipamento,
              icon: salvando
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.save_outlined),
              label: Text(salvando ? 'Salvando...' : 'Salvar equipamento'),
            ),
            const SizedBox(height: 8),
            OutlinedButton(
              onPressed: salvando ? null : () => Navigator.pop(context, false),
              child: const Text('Cancelar'),
            ),
          ],
        ),
      ),
    );
  }
}
