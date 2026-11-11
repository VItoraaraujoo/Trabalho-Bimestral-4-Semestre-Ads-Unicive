import 'package:flutter/material.dart';

const Color azulMarinho = Color(0xFF0F2742);
const Color azul = Color(0xFF2563EB);
const Color verdeAgua = Color(0xFF14B8A6);
const Color fundo = Color(0xFFF8FAFC);
const Color azulClaro = Color(0xFF60A5FA);

Color corStatusAtivo(String status) => switch (status) {
  'Em manutenção' => const Color(0xFFB7791F),
  'Baixado' => const Color(0xFFB42318),
  'Emprestado' => const Color(0xFF6254B8),
  'Em uso' => azul,
  _ => const Color(0xFF0B8978),
};

class ChipStatusAtivo extends StatelessWidget {
  final String status;

  const ChipStatusAtivo(this.status, {super.key});

  @override
  Widget build(BuildContext context) {
    final cor = corStatusAtivo(status);
    return Container(
      constraints: const BoxConstraints(maxWidth: 150),
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: cor.withValues(alpha: .10),
        borderRadius: BorderRadius.circular(99),
      ),
      child: Text(
        status,
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
        textAlign: TextAlign.center,
        style: TextStyle(
          fontSize: 10,
          height: 1.2,
          color: cor,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class TituloPaginaAtivo extends StatelessWidget {
  final String sobretitulo;
  final String titulo;
  final String descricao;

  const TituloPaginaAtivo({
    super.key,
    required this.sobretitulo,
    required this.titulo,
    required this.descricao,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(4, 8, 4, 13),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            sobretitulo.toUpperCase(),
            style: const TextStyle(
              color: azul,
              fontSize: 9,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.15,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            titulo,
            style: const TextStyle(
              color: azulMarinho,
              fontSize: 21,
              height: 1.2,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            descricao,
            style: const TextStyle(
              color: Color(0xFF64748B),
              fontSize: 11,
              height: 1.35,
            ),
          ),
        ],
      ),
    );
  }
}

class EstadoVazioAtivo extends StatelessWidget {
  final String titulo;
  final String descricao;
  final IconData icone;
  final bool compacto;

  const EstadoVazioAtivo({
    super.key,
    required this.titulo,
    required this.descricao,
    this.icone = Icons.inventory_2_outlined,
    this.compacto = true,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.all(compacto ? 14 : 22),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: compacto ? 34 : 42,
            height: compacto ? 34 : 42,
            decoration: BoxDecoration(
              color: const Color(0xFFE8F0FF),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icone, color: azul, size: compacto ? 18 : 22),
          ),
          const SizedBox(width: 11),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  titulo,
                  style: const TextStyle(
                    color: azulMarinho,
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  descricao,
                  style: const TextStyle(
                    color: Color(0xFF64748B),
                    fontSize: 10,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class LogoAtivoTI extends StatelessWidget {
  final bool sobreFundoEscuro;

  const LogoAtivoTI({super.key, this.sobreFundoEscuro = true});

  @override
  Widget build(BuildContext context) {
    final corNome = sobreFundoEscuro ? Colors.white : azulMarinho;
    final corSufixo = sobreFundoEscuro ? azulClaro : azul;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: azul,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Stack(
            alignment: Alignment.center,
            children: [
              const Icon(
                Icons.desktop_windows_outlined,
                color: Colors.white,
                size: 25,
              ),
              Positioned(
                right: 4,
                bottom: 9,
                child: Container(
                  width: 14,
                  height: 14,
                  decoration: const BoxDecoration(
                    color: azul,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.check, color: verdeAgua, size: 12),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 9),
        Text.rich(
          TextSpan(
            children: [
              TextSpan(
                text: 'Ativo',
                style: TextStyle(color: corNome, fontWeight: FontWeight.w700),
              ),
              TextSpan(
                text: 'TI',
                style: TextStyle(color: corSufixo, fontWeight: FontWeight.w700),
              ),
            ],
          ),
          style: const TextStyle(fontSize: 21),
        ),
      ],
    );
  }
}
