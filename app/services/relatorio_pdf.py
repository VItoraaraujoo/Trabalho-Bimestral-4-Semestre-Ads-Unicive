from datetime import datetime
import textwrap

from ..schemas.relatorio import RelatorioEquipamentos


LINHAS_POR_PAGINA = 50


def _linhas_relatorio(relatorio: RelatorioEquipamentos) -> list[str]:
    linhas = [f"Total de equipamentos: {relatorio.total_equipamentos}", ""]
    for titulo, grupos in (
        ("Por status", relatorio.por_status),
        ("Por tipo", relatorio.por_tipo),
        ("Por setor", relatorio.por_setor),
    ):
        linhas.append(titulo)
        linhas.extend(
            f"- {grupo.nome}: {grupo.quantidade}"
            for grupo in grupos
        )
        linhas.append("")

    linhas.append("Inventário detalhado")
    if not relatorio.equipamentos:
        linhas.append("Nenhum equipamento cadastrado.")
    for item in relatorio.equipamentos:
        linhas.append(
            f"{item.patrimonio or 'Sem patrimônio'} - {item.nome} ({item.tipo})"
        )
        linhas.append(
            f"  Marca: {item.marca or 'Não informada'} | "
            f"Modelo: {item.modelo or 'Não informado'}"
        )
        linhas.append(f"  Número de série: {item.numero_serie or 'Não informado'}")
        linhas.append(
            f"  Status: {item.status} | Condição: {item.condicao} | "
            f"Setor: {item.setor or 'Sem setor'}"
        )
        linhas.append(
            f"  Responsável: {item.nome_funcionario or 'Sem responsável'}"
            + (
                f" | Matrícula: {item.matricula_funcionario}"
                if item.matricula_funcionario
                else ""
            )
        )

    linhas_formatadas = []
    for linha in linhas:
        if not linha:
            linhas_formatadas.append("")
            continue
        linhas_formatadas.extend(
            textwrap.wrap(
                linha,
                width=100,
                break_long_words=True,
                break_on_hyphens=False,
            )
        )
    return linhas_formatadas


def _texto_pdf(texto: str) -> bytes:
    codificado = texto.encode("cp1252", errors="replace").hex().upper()
    return f"<{codificado}> Tj".encode("ascii")


def _conteudo_pagina(
    linhas: list[str], gerado_em: datetime, numero: int, total_paginas: int
) -> bytes:
    competencia = gerado_em.strftime("%m/%Y")
    data_geracao = gerado_em.strftime("%d/%m/%Y %H:%M")
    comandos = [
        b"BT",
        b"/F1 15 Tf",
        b"50 790 Td",
        _texto_pdf("AtivoTI - Relatório mensal de equipamentos"),
        b"/F1 9 Tf",
        b"0 -22 Td",
        _texto_pdf(f"Competência: {competencia} | Gerado em: {data_geracao}"),
    ]
    for linha in linhas:
        comandos.extend([b"0 -14 Td", _texto_pdf(linha)])
    comandos.extend(
        [
            b"ET",
            b"BT",
            b"/F1 8 Tf",
            b"50 35 Td",
            _texto_pdf(f"Página {numero} de {total_paginas}"),
            b"ET",
        ]
    )
    return b"\n".join(comandos) + b"\n"


def gerar_pdf(relatorio: RelatorioEquipamentos, gerado_em: datetime) -> bytes:
    linhas = _linhas_relatorio(relatorio)
    paginas = [
        linhas[inicio : inicio + LINHAS_POR_PAGINA]
        for inicio in range(0, len(linhas), LINHAS_POR_PAGINA)
    ] or [[]]

    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"",
    ]
    ids_paginas = [3 + 2 * indice for indice in range(len(paginas))]
    id_fonte = 3 + 2 * len(paginas)
    filhos = " ".join(f"{identificador} 0 R" for identificador in ids_paginas)
    objetos[1] = (
        f"<< /Type /Pages /Kids [{filhos}] /Count {len(paginas)} >>".encode(
            "ascii"
        )
    )

    for indice, linhas_pagina in enumerate(paginas):
        id_pagina = ids_paginas[indice]
        id_conteudo = id_pagina + 1
        conteudo = _conteudo_pagina(
            linhas_pagina, gerado_em, indice + 1, len(paginas)
        )
        objetos.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /Font << /F1 {id_fonte} 0 R >> >> "
                f"/Contents {id_conteudo} 0 R >>"
            ).encode("ascii")
        )
        objetos.append(
            f"<< /Length {len(conteudo)} >>\nstream\n".encode("ascii")
            + conteudo
            + b"endstream"
        )
    objetos.append(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
        b"/Encoding /WinAnsiEncoding >>"
    )

    pdf = bytearray(b"%PDF-1.4\n")
    deslocamentos = [0]
    for indice, objeto in enumerate(objetos, start=1):
        deslocamentos.append(len(pdf))
        pdf.extend(f"{indice} 0 obj\n".encode("ascii"))
        pdf.extend(objeto)
        pdf.extend(b"\nendobj\n")

    inicio_referencias = len(pdf)
    pdf.extend(f"xref\n0 {len(objetos) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for deslocamento in deslocamentos[1:]:
        pdf.extend(f"{deslocamento:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\n"
        f"startxref\n{inicio_referencias}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)
