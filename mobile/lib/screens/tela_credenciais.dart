import 'dart:convert';

import 'package:flutter/material.dart';

import '../brand.dart';
import '../services/api_service.dart';

class TelaCredenciais extends StatefulWidget {
  final ApiService api;
  final int usuarioId;
  final String emailAtual;
  final VoidCallback aoVoltar;
  final ValueChanged<String> aoAtualizarLogin;

  const TelaCredenciais({
    super.key,
    required this.api,
    required this.usuarioId,
    required this.emailAtual,
    required this.aoVoltar,
    required this.aoAtualizarLogin,
  });

  @override
  State<TelaCredenciais> createState() => _TelaCredenciaisState();
}

class _TelaCredenciaisState extends State<TelaCredenciais> {
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
    if (salvando) return;
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
      widget.aoAtualizarLogin(email.text.trim());
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Credenciais atualizadas com sucesso.')),
        );
      }
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
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          tooltip: 'Voltar',
          onPressed: widget.aoVoltar,
          icon: const Icon(Icons.arrow_back),
        ),
        title: const LogoAtivoTI(),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
        children: [
          const TituloPaginaAtivo(
            sobretitulo: 'PERFIL',
            titulo: 'Minha conta',
            descricao: 'Atualize seu e-mail de login e sua senha.',
          ),
          Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 520),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Form(
                    key: chaveFormulario,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const Text(
                          'Credenciais de acesso',
                          style: TextStyle(
                            color: azulMarinho,
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 14),
                        TextFormField(
                          controller: email,
                          keyboardType: TextInputType.emailAddress,
                          textInputAction: TextInputAction.next,
                          decoration: const InputDecoration(
                            labelText: 'E-mail de login',
                            prefixIcon: Icon(Icons.alternate_email),
                          ),
                          validator: (valor) {
                            final texto = valor?.trim() ?? '';
                            if (texto.isEmpty ||
                                !RegExp(
                                  r'^[^\s@]+@[^\s@]+\.[^\s@]+$',
                                ).hasMatch(texto)) {
                              return 'Informe um e-mail válido.';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 13),
                        TextFormField(
                          controller: novaSenha,
                          obscureText: true,
                          keyboardType: TextInputType.visiblePassword,
                          decoration: const InputDecoration(
                            labelText: 'Nova senha (opcional)',
                            prefixIcon: Icon(Icons.lock_outline),
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
                          'Deixe a senha em branco para manter a atual. Se preencher, use ao menos 8 caracteres e até 72 bytes. A senha atual nunca é exibida.',
                          style: TextStyle(
                            color: Color(0xFF64748B),
                            fontSize: 12,
                          ),
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
                        const SizedBox(height: 18),
                        FilledButton.icon(
                          onPressed: salvando ? null : salvar,
                          icon: salvando
                              ? const SizedBox.square(
                                  dimension: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Icon(Icons.save_outlined),
                          label: Text(
                            salvando ? 'Salvando...' : 'Salvar credenciais',
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
