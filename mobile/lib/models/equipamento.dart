class Equipamento {
  final int? id;
  final String nome;
  final String tipo;
  final String? patrimonio;
  final String? numeroSerie;
  final String? marca;
  final String? modelo;
  final String? setor;
  final String condicao;
  final String status;
  final String? observacao;

  const Equipamento({
    this.id,
    required this.nome,
    required this.tipo,
    this.patrimonio,
    this.numeroSerie,
    this.marca,
    this.modelo,
    this.setor,
    required this.condicao,
    this.status = 'Em estoque',
    this.observacao,
  });

  factory Equipamento.fromJson(Map<String, dynamic> json) {
    return Equipamento(
      id: json['id'] as int?,
      nome: json['nome']?.toString() ?? '',
      tipo: json['tipo']?.toString() ?? '',
      patrimonio: json['patrimonio']?.toString(),
      numeroSerie: json['numero_serie']?.toString(),
      marca: json['marca']?.toString(),
      modelo: json['modelo']?.toString(),
      setor: json['setor']?.toString(),
      condicao: json['condicao']?.toString() ?? 'Usado',
      status: json['status']?.toString() ?? 'Em estoque',
      observacao: json['observacao']?.toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'nome': nome,
      'tipo': tipo,
      'numero_serie': numeroSerie,
      'marca': marca,
      'modelo': modelo,
      'setor': setor,
      'condicao': condicao,
      'status': status,
      'observacao': observacao,
    };
  }
}
