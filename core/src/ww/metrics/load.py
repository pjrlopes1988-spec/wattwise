"""Condição, Fadiga e Frescura (internamente CTL/ATL/TSB; spec 6.3).

Na interface nunca se usam as siglas CTL/ATL/TSB (marcas da TrainingPeaks).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta

from ww.config import CargaForma


@dataclass(frozen=True)
class Dia:
    data: date
    carga: float
    condicao: float        # CTL no fim do dia
    fadiga: float          # ATL no fim do dia
    frescura: float        # TSB = CTL de ontem − ATL de ontem
    frescura_pct: float | None  # frescura ÷ condição de ontem × 100 (None = "a calibrar")
    subida_7d: float | None     # variação da condição face a 7 dias antes


def fator(constante_dias: float, tipo: str) -> float:
    if tipo == "linear":
        return 1.0 / constante_dias
    if tipo == "exponencial":
        return 1.0 - math.exp(-1.0 / constante_dias)
    raise ValueError(f"fator_media desconhecido: {tipo}")


def serie_forma(
    cargas: Mapping[date, float],
    cfg: CargaForma,
    *,
    inicio: date | None = None,
    fim: date | None = None,
    condicao_inicial: float = 0.0,
    fadiga_inicial: float = 0.0,
    constante_condicao: float | None = None,
    constante_fadiga: float | None = None,
) -> list[Dia]:
    """Calcula dia a dia. Dias sem atividade têm carga 0.

    As constantes por atleta (fase futura) sobrepõem-se às da configuração.
    """
    if not cargas and (inicio is None or fim is None):
        return []
    inicio = inicio or min(cargas)
    fim = fim or max(cargas)
    k_c = fator(constante_condicao or cfg.constante_condicao_dias, cfg.fator_media)
    k_f = fator(constante_fadiga or cfg.constante_fadiga_dias, cfg.fator_media)

    dias: list[Dia] = []
    ctl, atl = condicao_inicial, fadiga_inicial
    d = inicio
    while d <= fim:
        carga = float(cargas.get(d, 0.0))
        tsb = ctl - atl
        pct = (tsb / ctl * 100.0) if ctl >= cfg.condicao_minima_para_pct and ctl > 0 else None
        ctl = ctl + (carga - ctl) * k_c
        atl = atl + (carga - atl) * k_f
        subida = ctl - dias[-7].condicao if len(dias) >= 7 else None
        dias.append(Dia(d, carga, ctl, atl, tsb, pct, subida))
        d += timedelta(days=1)
    return dias


def faixa_frescura(pct: float | None, cfg: CargaForma) -> str:
    """Faixa da frescura em % (gráfico 2 da spec). None → 'a_calibrar'."""
    if pct is None:
        return "a_calibrar"
    f = cfg.faixas_frescura_pct
    if pct > f.transicao_acima:
        return "transicao"
    if pct > f.fresco_acima:
        return "fresco"
    if pct > f.neutra_acima:
        return "neutra"
    if pct >= f.otima_acima:
        return "otima"
    return "risco"
