import 'package:ativoti/services/api_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  test('envia os filtros para a API', () async {
    Uri? enderecoRecebido;
    final clienteFalso = MockClient((requisicao) async {
      enderecoRecebido = requisicao.url;
      return http.Response('[]', 200);
    });
    final api = ApiService(cliente: clienteFalso);

    await api.listarEquipamentos(
      status: 'Em uso',
      tipo: ' note ',
      setor: 'Laboratório',
    );

    expect(enderecoRecebido?.path, '/api/v1/equipamentos');
    expect(enderecoRecebido?.queryParameters, {
      'status': 'Em uso',
      'tipo': 'note',
      'setor': 'Laboratório',
    });
  });

  test('não envia filtros vazios', () async {
    Uri? enderecoRecebido;
    final clienteFalso = MockClient((requisicao) async {
      enderecoRecebido = requisicao.url;
      return http.Response('[]', 200);
    });
    final api = ApiService(cliente: clienteFalso);

    await api.listarEquipamentos(tipo: '  ', setor: '');

    expect(enderecoRecebido?.query, isEmpty);
  });

  test('envia token nas ações de entrega e devolução', () async {
    final requisicoes = <http.Request>[];
    final clienteFalso = MockClient((requisicao) async {
      requisicoes.add(requisicao);
      if (requisicao.url.path.endsWith('/auth/login')) {
        return http.Response(
          '{"access_token":"token-teste","usuario":{"id":1}}',
          200,
        );
      }
      if (requisicao.url.path.endsWith('/alocacoes')) {
        return http.Response('{}', 201);
      }
      return http.Response('{}', 200);
    });
    final api = ApiService(cliente: clienteFalso);

    await api.entrar('ti@teste.com', 'senha-de-teste');
    await api.criarAlocacao({
      'equipamento_id': 4,
      'funcionario_id': 2,
      'situacao': 'Em uso',
    });
    await api.devolverEquipamento(9);

    expect(requisicoes[1].url.path, '/api/v1/alocacoes');
    expect(requisicoes[1].headers['Authorization'], 'Bearer token-teste');
    expect(requisicoes[2].url.path, '/api/v1/alocacoes/9/devolver');
    expect(requisicoes[2].headers['Authorization'], 'Bearer token-teste');
  });

  test('atualiza credenciais pela API e omite senha em branco', () async {
    final requisicoes = <http.Request>[];
    final clienteFalso = MockClient((requisicao) async {
      requisicoes.add(requisicao);
      if (requisicao.url.path.endsWith('/auth/login')) {
        return http.Response(
          '{"access_token":"token-teste","usuario":{"id":1}}',
          200,
        );
      }
      return http.Response('{}', 200);
    });
    final api = ApiService(cliente: clienteFalso);

    await api.entrar('admin@teste.com', 'senha-de-teste');
    await api.atualizarCredenciais(7, 'novo@teste.com', novaSenha: '');

    final requisicao = requisicoes.last;
    expect(requisicao.method, 'PATCH');
    expect(requisicao.url.path, '/api/v1/usuarios/7/credenciais');
    expect(requisicao.headers['Authorization'], 'Bearer token-teste');
    expect(requisicao.body, '{"email":"novo@teste.com"}');
  });
}
