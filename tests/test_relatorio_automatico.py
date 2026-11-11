from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import Equipamento
from app.schemas.relatorio import (
    EquipamentoRelatorio,
    GrupoRelatorio,
    RelatorioEquipamentos,
)
from app.services.relatorio_automatico import (
    gerar_relatorio_mensal,
    proxima_execucao,
)
from app.services.relatorio_pdf import gerar_pdf


def criar_relatorio(tamanho: int = 1) -> RelatorioEquipamentos:
    equipamentos = [
        EquipamentoRelatorio(
            id=indice,
            patrimonio=f"ATI-{indice:06}",
            nome="Notebook de demonstração",
            tipo="Notebook",
            numero_serie=None,
            marca="Exemplo",
            modelo="Modelo A",
            condicao="Usado",
            status="Em estoque",
            setor="Laboratório",
        )
        for indice in range(1, tamanho + 1)
    ]
    return RelatorioEquipamentos(
        total_equipamentos=tamanho,
        por_status=[GrupoRelatorio(nome="Em estoque", quantidade=tamanho)],
        por_tipo=[GrupoRelatorio(nome="Notebook", quantidade=tamanho)],
        por_setor=[GrupoRelatorio(nome="Laboratório", quantidade=tamanho)],
        equipamentos=equipamentos,
    )


def test_pdf_tem_cabecalho_em_portugues_e_mais_de_uma_pagina() -> None:
    relatorio = criar_relatorio(tamanho=10)
    pdf = gerar_pdf(
        relatorio,
        datetime(2026, 10, 1, 8, 0, tzinfo=ZoneInfo("America/Sao_Paulo")),
    )

    assert pdf.startswith(b"%PDF-1.4")
    assert b"/Count 2" in pdf
    assert b"%%EOF" in pdf
    assert "Laboratório".encode("cp1252").hex().upper().encode() in pdf


def test_referencias_do_pdf_apontam_para_objetos_validos() -> None:
    pdf = gerar_pdf(
        criar_relatorio(),
        datetime(2026, 10, 1, 8, 0, tzinfo=ZoneInfo("America/Sao_Paulo")),
    )
    inicio_referencias = pdf.rfind(b"\nxref\n") + 1
    linhas = pdf[inicio_referencias:].splitlines()
    quantidade_objetos = int(linhas[1].split()[1])

    assert int(linhas[-2]) == inicio_referencias
    for numero_objeto in range(1, quantidade_objetos):
        deslocamento = int(linhas[numero_objeto + 2][:10])
        assert pdf[deslocamento:].startswith(f"{numero_objeto} 0 obj".encode())


def test_proxima_execucao_usa_primeiro_dia_as_oito() -> None:
    zona = ZoneInfo("America/Sao_Paulo")
    antes_do_horario = datetime(2026, 10, 1, 7, 59, tzinfo=zona)
    depois_do_horario = datetime(2026, 10, 1, 8, 1, tzinfo=zona)

    assert proxima_execucao(antes_do_horario) == datetime(
        2026, 10, 1, 8, 0, tzinfo=zona
    )
    assert proxima_execucao(depois_do_horario) == datetime(
        2026, 11, 1, 8, 0, tzinfo=zona
    )


def test_gera_um_pdf_por_mes(tmp_path: Path) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    fabrica_sessoes = sessionmaker(bind=engine, expire_on_commit=False)
    with fabrica_sessoes() as db:
        db.add(
            Equipamento(
                nome="Notebook de teste",
                tipo="Notebook",
                patrimonio="ATI-000001",
                condicao="Usado",
                status="Em estoque",
                setor="TI",
            )
        )
        db.commit()

    fuso = ZoneInfo("America/Sao_Paulo")
    primeira_data = datetime(2026, 10, 1, 8, 0, tzinfo=fuso)
    caminho = gerar_relatorio_mensal(
        primeira_data,
        session_factory=fabrica_sessoes,
        diretorio=tmp_path,
    )
    conteudo_original = caminho.read_bytes()
    caminho_repetido = gerar_relatorio_mensal(
        datetime(2026, 10, 20, 12, 0, tzinfo=fuso),
        session_factory=fabrica_sessoes,
        diretorio=tmp_path,
    )

    assert caminho == tmp_path / "relatorio_equipamentos_2026-10.pdf"
    assert caminho_repetido == caminho
    assert caminho.read_bytes() == conteudo_original
    engine.dispose()
