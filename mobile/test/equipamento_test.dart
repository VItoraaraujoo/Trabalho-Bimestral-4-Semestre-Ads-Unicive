import 'package:ativoti/models/equipamento.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('lê um equipamento recebido da API', () {
    final equipamento = Equipamento.fromJson({
      'id': 7,
      'nome': 'Notebook de teste',
      'tipo': 'Notebook',
      'patrimonio': 'ATI-000007',
      'numero_serie': 'SN-007',
      'marca': 'Exemplo',
      'modelo': 'Modelo A',
      'setor': 'Laboratório',
      'condicao': 'Usado',
      'status': 'Em estoque',
      'observacao': 'Equipamento para a sala',
    });

    expect(equipamento.id, 7);
    expect(equipamento.nome, 'Notebook de teste');
    expect(equipamento.status, 'Em estoque');
    expect(equipamento.patrimonio, 'ATI-000007');
    expect(equipamento.numeroSerie, 'SN-007');
    expect(equipamento.condicao, 'Usado');
  });

  test('monta o JSON que a API espera para criar um equipamento', () {
    const equipamento = Equipamento(
      nome: 'Monitor',
      tipo: 'Monitor',
      condicao: 'Novo',
      status: 'Em uso',
    );

    expect(equipamento.toJson(), {
      'nome': 'Monitor',
      'tipo': 'Monitor',
      'numero_serie': null,
      'marca': null,
      'modelo': null,
      'setor': null,
      'condicao': 'Novo',
      'status': 'Em uso',
      'observacao': null,
    });
  });
}
