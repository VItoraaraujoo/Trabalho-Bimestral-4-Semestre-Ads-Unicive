import asyncio
from collections.abc import Callable
from contextlib import suppress
from datetime import datetime, time
import logging
import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from ..core.config import RELATORIO_TIMEZONE, RELATORIOS_DIR
from ..core.database import SessionLocal
from .relatorio_pdf import gerar_pdf
from .relatorio_service import montar_relatorio


logger = logging.getLogger(__name__)
HORA_GERACAO = time(hour=8)


def proxima_execucao(agora: datetime) -> datetime:
    fuso = ZoneInfo(RELATORIO_TIMEZONE)
    agora_local = (
        agora.replace(tzinfo=fuso)
        if agora.tzinfo is None
        else agora.astimezone(fuso)
    )
    proxima = datetime.combine(
        agora_local.date().replace(day=1), HORA_GERACAO, tzinfo=fuso
    )
    if proxima <= agora_local:
        ano = agora_local.year + (1 if agora_local.month == 12 else 0)
        mes = 1 if agora_local.month == 12 else agora_local.month + 1
        proxima = datetime(ano, mes, 1, HORA_GERACAO.hour, tzinfo=fuso)
    return proxima


def gerar_relatorio_mensal(
    agora: datetime | None = None,
    *,
    session_factory: Callable[[], Session] | None = None,
    diretorio: Path | None = None,
) -> Path:
    fuso = ZoneInfo(RELATORIO_TIMEZONE)
    gerado_em = agora or datetime.now(fuso)
    if gerado_em.tzinfo is None:
        gerado_em = gerado_em.replace(tzinfo=fuso)
    else:
        gerado_em = gerado_em.astimezone(fuso)

    pasta = diretorio or RELATORIOS_DIR
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"relatorio_equipamentos_{gerado_em:%Y-%m}.pdf"
    if caminho.exists():
        logger.info("Relatório mensal já existe: %s", caminho)
        return caminho

    criar_sessao = session_factory or SessionLocal
    with criar_sessao() as db:
        relatorio = montar_relatorio(db)

    conteudo = gerar_pdf(relatorio, gerado_em)
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=pasta,
            prefix=f".{caminho.stem}-",
            suffix=".tmp",
            delete=False,
        ) as arquivo:
            temporario = Path(arquivo.name)
            arquivo.write(conteudo)
        temporario.replace(caminho)
    finally:
        if temporario is not None:
            temporario.unlink(missing_ok=True)

    logger.info("Relatório mensal gerado: %s", caminho)
    return caminho


async def executar_agendamento_relatorios() -> None:
    fuso = ZoneInfo(RELATORIO_TIMEZONE)
    logger.info(
        "Agendamento mensal ativo: dia 1 às 08:00 (%s).",
        RELATORIO_TIMEZONE,
    )
    while True:
        agora = datetime.now(fuso)
        proxima = proxima_execucao(agora)
        await asyncio.sleep((proxima - agora).total_seconds())
        try:
            await asyncio.to_thread(gerar_relatorio_mensal)
        except Exception:
            logger.exception("Falha ao gerar o relatório mensal de equipamentos.")


async def parar_agendamento_relatorios(tarefa: asyncio.Task) -> None:
    tarefa.cancel()
    with suppress(asyncio.CancelledError):
        await tarefa


if __name__ == "__main__":
    print(f"Relatório salvo em: {gerar_relatorio_mensal()}")
