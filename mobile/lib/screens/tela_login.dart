import 'package:flutter/material.dart';

import '../brand.dart';
import '../services/api_service.dart';

class TelaLogin extends StatefulWidget {
  final ApiService api;
  final ValueChanged<Map<String, dynamic>> aoEntrar;

  const TelaLogin({super.key, required this.api, required this.aoEntrar});

  @override
  State<TelaLogin> createState() => _TelaLoginState();
}

class _TelaLoginState extends State<TelaLogin> {
  final chaveFormulario = GlobalKey<FormState>();
  final emailController = TextEditingController();
  final senhaController = TextEditingController();
  bool entrando = false;
  String? erro;

  @override
  void dispose() {
    emailController.dispose();
    senhaController.dispose();
    super.dispose();
  }

  Future<void> entrar() async {
    if (!(chaveFormulario.currentState?.validate() ?? false)) return;
    setState(() {
      entrando = true;
      erro = null;
    });
    try {
      final usuario = await widget.api.entrar(
        emailController.text.trim(),
        senhaController.text,
      );
      if (mounted) widget.aoEntrar(usuario);
    } catch (falha) {
      if (mounted) {
        setState(() => erro = falha.toString().replaceFirst('Exception: ', ''));
      }
    } finally {
      if (mounted) setState(() => entrando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: true,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final compacta = constraints.maxHeight < 600;
            final muitoCompacta = constraints.maxHeight < 400;

            return Center(
              child: Padding(
                padding: EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: muitoCompacta
                      ? 4
                      : compacta
                      ? 8
                      : 24,
                ),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 420),
                  child: Card(
                    color: Colors.white,
                    margin: EdgeInsets.zero,
                    child: Padding(
                      padding: EdgeInsets.all(
                        muitoCompacta
                            ? 14
                            : compacta
                            ? 18
                            : 24,
                      ),
                      child: AutofillGroup(
                        child: Form(
                          key: chaveFormulario,
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              if (!muitoCompacta) ...[
                                const Center(
                                  child: LogoAtivoTI(sobreFundoEscuro: false),
                                ),
                                SizedBox(height: compacta ? 8 : 12),
                              ],
                              if (!compacta) ...[
                                const Text(
                                  'Equipamentos organizados. Gestão sem complicação.',
                                  textAlign: TextAlign.center,
                                  style: TextStyle(color: Color(0xFF64748B)),
                                ),
                                const SizedBox(height: 8),
                              ],
                              Text(
                                'Entrar no AtivoTI',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  color: azulMarinho,
                                  fontSize: compacta ? 20 : 24,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              if (!compacta) ...[
                                const SizedBox(height: 8),
                                const Text(
                                  'Entre com o e-mail e a senha cadastrados pelo administrador.',
                                  textAlign: TextAlign.center,
                                ),
                              ],
                              SizedBox(height: compacta ? 12 : 24),
                              TextFormField(
                                controller: emailController,
                                keyboardType: TextInputType.emailAddress,
                                textCapitalization: TextCapitalization.none,
                                textInputAction: TextInputAction.next,
                                autocorrect: false,
                                autofillHints: const [
                                  AutofillHints.username,
                                  AutofillHints.email,
                                ],
                                decoration: InputDecoration(
                                  labelText: 'E-mail',
                                  border: const OutlineInputBorder(),
                                  isDense: compacta,
                                ),
                                validator: (valor) =>
                                    valor == null || !valor.contains('@')
                                    ? 'Informe um e-mail válido.'
                                    : null,
                                onFieldSubmitted: (_) =>
                                    FocusScope.of(context).nextFocus(),
                              ),
                              SizedBox(height: compacta ? 8 : 14),
                              TextFormField(
                                controller: senhaController,
                                obscureText: true,
                                keyboardType: TextInputType.visiblePassword,
                                textInputAction: TextInputAction.done,
                                autofillHints: const [AutofillHints.password],
                                decoration: InputDecoration(
                                  labelText: 'Senha',
                                  border: const OutlineInputBorder(),
                                  isDense: compacta,
                                ),
                                validator: (valor) =>
                                    valor == null || valor.isEmpty
                                    ? 'Informe sua senha.'
                                    : null,
                                onFieldSubmitted: (_) => entrar(),
                              ),
                              if (erro != null) ...[
                                SizedBox(height: compacta ? 8 : 12),
                                Text(
                                  erro!,
                                  maxLines: compacta ? 2 : 4,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    color: Theme.of(context).colorScheme.error,
                                  ),
                                ),
                              ],
                              SizedBox(height: compacta ? 12 : 20),
                              SizedBox(
                                height: compacta ? 44 : null,
                                child: FilledButton(
                                  onPressed: entrando ? null : entrar,
                                  child: Text(
                                    entrando ? 'Entrando...' : 'Entrar',
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
