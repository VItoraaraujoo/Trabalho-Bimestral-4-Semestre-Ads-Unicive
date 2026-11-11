import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../models/equipamento.dart';

class ApiService {
  ApiService({http.Client? cliente}) : _cliente = cliente ?? http.Client();

  final http.Client _cliente;
  String? _token;

  static const String enderecoApi = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1',
  );

  String get urlEquipamentos =>
      '${enderecoApi.replaceAll(RegExp(r'/$'), '')}/equipamentos';

  String get urlBase => enderecoApi.replaceAll(RegExp(r'/$'), '');

  Map<String, String> get _cabecalhosAutenticados => {
    if (_token != null) 'Authorization': 'Bearer $_token',
  };

  Future<Map<String, dynamic>> entrar(String email, String senha) async {
    final resposta = await _enviar(
      () => _cliente.post(
        Uri.parse('$urlBase/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'senha': senha}),
      ),
    );
    _exigirStatus(resposta, 200);
    final dados = jsonDecode(resposta.body) as Map<String, dynamic>;
    _token = dados['access_token']?.toString();
    return dados['usuario'] as Map<String, dynamic>;
  }

  void sair() => _token = null;

  Future<List<Map<String, dynamic>>> listarUsuarios() =>
      _listarRegistros('usuarios');

  Future<Map<String, dynamic>> relatorioEquipamentos() async {
    final resposta = await _enviar(
      () => _cliente.get(
        Uri.parse('$urlBase/relatorios/equipamentos'),
        headers: _cabecalhosAutenticados,
      ),
    );
    _exigirStatus(resposta, 200);
    return jsonDecode(resposta.body) as Map<String, dynamic>;
  }

  Future<void> criarUsuario(Map<String, dynamic> usuario) => _enviarRegistro(
    'usuarios',
    metodo: 'POST',
    dados: usuario,
    statusEsperado: 201,
  );

  Future<void> excluirUsuario(int id) =>
      _enviarRegistro('usuarios/$id', metodo: 'DELETE', statusEsperado: 204);

  Future<void> atualizarCredenciais(
    int id,
    String email, {
    String? novaSenha,
  }) => _enviarRegistro(
    'usuarios/$id/credenciais',
    metodo: 'PATCH',
    dados: {
      'email': email.trim(),
      if (novaSenha != null && novaSenha.trim().isNotEmpty)
        'nova_senha': novaSenha,
    },
  );

  Future<List<Map<String, dynamic>>> _listarRegistros(String caminho) async {
    final resposta = await _enviar(
      () => _cliente.get(
        Uri.parse('$urlBase/$caminho'),
        headers: _cabecalhosAutenticados,
      ),
    );
    _exigirStatus(resposta, 200);
    final List<dynamic> dados = jsonDecode(resposta.body) as List<dynamic>;
    return dados.cast<Map<String, dynamic>>();
  }

  Future<void> _enviarRegistro(
    String caminho, {
    required String metodo,
    Map<String, dynamic>? dados,
    int statusEsperado = 200,
  }) async {
    final endereco = Uri.parse('$urlBase/$caminho');
    final resposta = await _enviar(() {
      final cabecalhos = {
        if (dados != null) 'Content-Type': 'application/json',
        ..._cabecalhosAutenticados,
      };
      final corpo = dados == null ? null : jsonEncode(dados);
      switch (metodo) {
        case 'POST':
          return _cliente.post(endereco, headers: cabecalhos, body: corpo);
        case 'PATCH':
          return _cliente.patch(endereco, headers: cabecalhos, body: corpo);
        case 'DELETE':
          return _cliente.delete(endereco, headers: cabecalhos);
        default:
          return _cliente.put(endereco, headers: cabecalhos, body: corpo);
      }
    });
    _exigirStatus(resposta, statusEsperado);
  }

  Future<List<Map<String, dynamic>>> listarFuncionarios() =>
      _listarRegistros('funcionarios');

  Future<void> criarFuncionario(Map<String, dynamic> dados) => _enviarRegistro(
    'funcionarios',
    metodo: 'POST',
    dados: dados,
    statusEsperado: 201,
  );

  Future<void> atualizarFuncionario(int id, Map<String, dynamic> dados) =>
      _enviarRegistro('funcionarios/$id', metodo: 'PUT', dados: dados);

  Future<void> excluirFuncionario(int id) => _enviarRegistro(
    'funcionarios/$id',
    metodo: 'DELETE',
    statusEsperado: 204,
  );

  Future<List<Map<String, dynamic>>> listarAlocacoes() =>
      _listarRegistros('alocacoes');

  Future<void> criarAlocacao(Map<String, dynamic> dados) => _enviarRegistro(
    'alocacoes',
    metodo: 'POST',
    dados: dados,
    statusEsperado: 201,
  );

  Future<void> devolverEquipamento(int alocacaoId) =>
      _enviarRegistro('alocacoes/$alocacaoId/devolver', metodo: 'POST');

  Future<List<Map<String, dynamic>>> listarManutencoes() =>
      _listarRegistros('manutencoes');

  Future<void> criarManutencao(Map<String, dynamic> dados) => _enviarRegistro(
    'manutencoes',
    metodo: 'POST',
    dados: dados,
    statusEsperado: 201,
  );

  Future<List<Map<String, dynamic>>> listarSistemas() =>
      _listarRegistros('sistemas');

  Future<void> criarSistema(Map<String, dynamic> dados) => _enviarRegistro(
    'sistemas',
    metodo: 'POST',
    dados: dados,
    statusEsperado: 201,
  );

  Future<void> finalizarSistema(int sistemaId) =>
      _enviarRegistro('sistemas/$sistemaId/finalizar', metodo: 'PATCH');

  Future<List<Equipamento>> listarEquipamentos({
    String? status,
    String? tipo,
    String? setor,
  }) async {
    final filtros = <String, String>{};
    if (status != null && status.isNotEmpty) filtros['status'] = status;
    if (tipo != null && tipo.trim().isNotEmpty) filtros['tipo'] = tipo.trim();
    if (setor != null && setor.trim().isNotEmpty) {
      filtros['setor'] = setor.trim();
    }
    final endereco = Uri.parse(
      urlEquipamentos,
    ).replace(queryParameters: filtros.isEmpty ? null : filtros);
    final resposta = await _enviar(
      () => _cliente.get(endereco, headers: _cabecalhosAutenticados),
    );

    _exigirStatus(resposta, 200);

    final List<dynamic> dados = jsonDecode(resposta.body) as List<dynamic>;
    return dados
        .map((item) => Equipamento.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<void> criarEquipamento(Equipamento equipamento) => _enviarRegistro(
    'equipamentos',
    metodo: 'POST',
    dados: equipamento.toJson(),
    statusEsperado: 201,
  );

  Future<void> atualizarEquipamento(Equipamento equipamento) => _enviarRegistro(
    'equipamentos/${equipamento.id}',
    metodo: 'PUT',
    dados: equipamento.toJson(),
  );

  Future<void> excluirEquipamento(int id) => _enviarRegistro(
    'equipamentos/$id',
    metodo: 'DELETE',
    statusEsperado: 204,
  );

  String _mensagemErro(http.Response resposta) {
    try {
      final dados = jsonDecode(resposta.body) as Map<String, dynamic>;
      final detalhe = dados['detail'];
      if (detalhe is String) {
        return detalhe;
      }
      return 'Revise os campos e tente novamente (HTTP ${resposta.statusCode}).';
    } catch (_) {
      return 'Falha na comunicação com a API (HTTP ${resposta.statusCode}).';
    }
  }

  void _exigirStatus(http.Response resposta, int statusEsperado) {
    if (resposta.statusCode != statusEsperado) {
      throw Exception(_mensagemErro(resposta));
    }
  }

  Future<http.Response> _enviar(
    Future<http.Response> Function() requisicao,
  ) async {
    try {
      return await requisicao().timeout(const Duration(seconds: 5));
    } on TimeoutException {
      throw Exception('A API demorou para responder. Tente novamente.');
    } on http.ClientException {
      throw Exception(
        'Não foi possível conectar à API. Confira se o FastAPI está em execução.',
      );
    } on SocketException {
      throw Exception(
        'Não foi possível conectar à API. Confira se o FastAPI está em execução.',
      );
    }
  }
}
