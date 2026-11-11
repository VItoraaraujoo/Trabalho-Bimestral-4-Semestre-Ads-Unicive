import 'package:flutter/material.dart';

import '../brand.dart';
import '../services/api_service.dart';

class TelaRelatorio extends StatefulWidget {
  final ApiService api;

  const TelaRelatorio({super.key, required this.api});

  @override
  State<TelaRelatorio> createState() => _TelaRelatorioState();
}

class _TelaRelatorioState extends State<TelaRelatorio> {
  late Future<Map<String, dynamic>> relatorioFuture;

  @override
  void initState() {
    super.initState();
    relatorioFuture = widget.api.relatorioEquipamentos();
  }

  void atualizar() {
    setState(() => relatorioFuture = widget.api.relatorioEquipamentos());
  }

  Widget secao(String titulo, List<dynamic> grupos, int total) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(14, 13, 14, 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              titulo,
              style: const TextStyle(
                color: azulMarinho,
                fontSize: 14,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 8),
            if (grupos.isEmpty)
              const Padding(
                padding: EdgeInsets.only(bottom: 7),
                child: Text(
                  'Sem dados para mostrar.',
                  style: TextStyle(color: Color(0xFF64748B), fontSize: 11),
                ),
              ),
            ...grupos.map((grupo) {
              final dado = grupo as Map<String, dynamic>;
              final quantidade = (dado['quantidade'] as num?)?.toInt() ?? 0;
              final proporcao = total == 0
                  ? 0.0
                  : (quantidade / total).clamp(0.0, 1.0);
              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            dado['nome']?.toString() ?? 'Não informado',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              color: Color(0xFF40556C),
                              fontSize: 11,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          '$quantidade',
                          style: const TextStyle(
                            color: azulMarinho,
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 5),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(99),
                      child: LinearProgressIndicator(
                        value: proporcao,
                        minHeight: 5,
                        backgroundColor: const Color(0xFFEDF2F8),
                        color: azul,
                      ),
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget detalhe(String rotulo, String valor, IconData icone) => Container(
    constraints: const BoxConstraints(maxWidth: 320),
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
    decoration: BoxDecoration(
      color: const Color(0xFFF3F7FB),
      borderRadius: BorderRadius.circular(7),
    ),
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icone, size: 13, color: const Color(0xFF64748B)),
        const SizedBox(width: 5),
        Flexible(
          child: Text(
            '$rotulo · $valor',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: Color(0xFF52677F), fontSize: 10),
          ),
        ),
      ],
    ),
  );

  Widget equipamentoDetalhado(Map<String, dynamic> item) {
    final responsavel = item['nome_funcionario']?.toString();
    final marcaModelo = '${item['marca'] ?? ''} ${item['modelo'] ?? ''}'.trim();
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(13),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    '${item['nome']} · ${item['patrimonio'] ?? 'Sem patrimônio'}',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: azulMarinho,
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                ChipStatusAtivo(item['status']?.toString() ?? 'Em estoque'),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 7,
              runSpacing: 6,
              children: [
                detalhe(
                  'Tipo',
                  item['tipo']?.toString() ?? 'Não informado',
                  Icons.category_outlined,
                ),
                detalhe(
                  'Condição',
                  item['condicao']?.toString() ?? 'Não informada',
                  Icons.check_circle_outline,
                ),
                detalhe(
                  'Setor',
                  item['setor']?.toString() ?? 'Sem setor',
                  Icons.location_on_outlined,
                ),
                if (marcaModelo.isNotEmpty)
                  detalhe('Modelo', marcaModelo, Icons.devices_outlined),
                if (item['numero_serie'] != null)
                  detalhe(
                    'Série',
                    item['numero_serie'].toString(),
                    Icons.qr_code_2,
                  ),
                detalhe(
                  'Responsável',
                  responsavel == null
                      ? 'Sem responsável'
                      : '$responsavel · ${item['matricula_funcionario']}',
                  Icons.person_outline,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const LogoAtivoTI(),
        actions: [
          IconButton(
            tooltip: 'Atualizar relatório',
            onPressed: atualizar,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: FutureBuilder<Map<String, dynamic>>(
        future: relatorioFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(22),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    EstadoVazioAtivo(
                      compacto: false,
                      titulo: 'Não foi possível carregar o relatório',
                      descricao: snapshot.error.toString().replaceFirst(
                        'Exception: ',
                        '',
                      ),
                      icone: Icons.cloud_off_outlined,
                    ),
                    TextButton.icon(
                      onPressed: atualizar,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Tentar novamente'),
                    ),
                  ],
                ),
              ),
            );
          }
          final dados = snapshot.data!;
          final total = (dados['total_equipamentos'] as num?)?.toInt() ?? 0;
          final equipamentos = dados['equipamentos'] as List<dynamic>;
          return RefreshIndicator(
            onRefresh: () async => atualizar(),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(14, 8, 14, 26),
              children: [
                const TituloPaginaAtivo(
                  sobretitulo: 'Resumo do patrimônio de TI',
                  titulo: 'Relatórios',
                  descricao: 'Distribuição e detalhes do inventário atual.',
                ),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 15,
                      vertical: 13,
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 42,
                          height: 42,
                          decoration: BoxDecoration(
                            color: const Color(0xFFE8F0FF),
                            borderRadius: BorderRadius.circular(11),
                          ),
                          child: const Icon(
                            Icons.inventory_2_outlined,
                            color: azul,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Text(
                          '$total',
                          style: const TextStyle(
                            color: azulMarinho,
                            fontSize: 30,
                            height: 1,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(width: 10),
                        const Expanded(
                          child: Text(
                            'equipamentos cadastrados',
                            style: TextStyle(
                              color: Color(0xFF64748B),
                              fontSize: 11,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(4, 7, 4, 2),
                  child: Text(
                    'Distribuição',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: azulMarinho,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                secao(
                  'Por status',
                  dados['por_status'] as List<dynamic>,
                  total,
                ),
                secao('Por tipo', dados['por_tipo'] as List<dynamic>, total),
                secao('Por setor', dados['por_setor'] as List<dynamic>, total),
                Padding(
                  padding: const EdgeInsets.fromLTRB(4, 7, 4, 2),
                  child: Text(
                    'Inventário detalhado · ${equipamentos.length}',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: azulMarinho,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                if (equipamentos.isEmpty)
                  const Card(
                    child: EstadoVazioAtivo(
                      titulo: 'Nenhum equipamento cadastrado',
                      descricao:
                          'Os equipamentos cadastrados aparecem nesta lista.',
                    ),
                  )
                else
                  ...equipamentos.map(
                    (item) =>
                        equipamentoDetalhado(item as Map<String, dynamic>),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}
