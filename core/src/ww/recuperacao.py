"""Recuperação: VFC, FC de repouso e sono (spec 6.4).

VFC:
- Cada fonte e cada métrica tem a sua própria linha de base (rMSSD ≠ SDNN; o Apple
  Health guarda SDNN). Não se misturam (spec 5, D-015).
- Valores transformados em ln (D-026).
- Estado do dia: média dos últimos 7 dias comparada com a faixa normal
  (média ± k·desvio-padrão dos últimos 60 dias), como em Plews et al. e HRV4Training.
- Com menos de 14 dias de dados da fonte em uso: "a calibrar" (o motor não usa a VFC).

A "prontidão" calculada por cada marca não entra aqui (spec 6.4).
"""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from ww.config import Recuperacao

MetricaVFC = Literal["rmssd", "sdnn"]
Estado = Literal["a_calibrar", "sem_dados_recentes", "abaixo", "normal", "acima"]


@dataclass(frozen=True)
class MedicaoVFC:
    data: date
    fonte: str          # ex.: "garmin", "apple_health", "hrv4training", "manual"
    metrica: MetricaVFC
    valor_ms: float


@dataclass(frozen=True)
class LinhaBase:
    data: date
    estado: Estado
    media7: float | None        # na escala usada (ln para a VFC, bpm para a FC repouso)
    faixa_inf: float | None
    faixa_sup: float | None
    valor_dia: float | None
    dias_seguidos_fora: int     # dias seguidos no mesmo estado fora da faixa
    dias_com_dados: int         # dias com medição até esta data (calibração)
    fonte: str | None = None
    metrica: str | None = None

    def em_ms(self, v: float | None) -> float | None:
        """Converte de ln para ms (só para a VFC), para mostrar ao atleta."""
        return math.exp(v) if v is not None else None


def _dias(inicio: date, fim: date) -> list[date]:
    return [inicio + timedelta(days=i) for i in range((fim - inicio).days + 1)]


def linha_base(
    valores: Mapping[date, float],
    inicio: date,
    fim: date,
    *,
    janela_media: int,
    minimo_na_media: int,
    janela_faixa: int,
    largura_dp: float,
    dias_calibracao: int,
) -> list[LinhaBase]:
    """Cálculo genérico (um valor por dia) usado para a VFC e para a FC de repouso."""
    datas = sorted(valores)
    out: list[LinhaBase] = []
    anterior: LinhaBase | None = None
    for d in _dias(inicio, fim):
        n_total = sum(1 for x in datas if x <= d)
        semana = [valores[x] for x in datas if d - timedelta(days=janela_media) < x <= d]
        hist = [valores[x] for x in datas if d - timedelta(days=janela_faixa) < x <= d]
        valor_dia = valores.get(d)

        media7 = inf = sup = None
        estado: Estado
        if n_total < dias_calibracao:
            estado = "a_calibrar"
        elif len(semana) < minimo_na_media:
            estado = "sem_dados_recentes"
        else:
            media7 = statistics.fmean(semana)
            mu = statistics.fmean(hist)
            dp = statistics.stdev(hist) if len(hist) > 1 else 0.0
            inf, sup = mu - largura_dp * dp, mu + largura_dp * dp
            estado = "abaixo" if media7 < inf else "acima" if media7 > sup else "normal"

        seguidos = 0
        if estado in ("abaixo", "acima"):
            seguidos = anterior.dias_seguidos_fora + 1 if anterior and anterior.estado == estado else 1
        lb = LinhaBase(d, estado, media7, inf, sup, valor_dia, seguidos, n_total)
        out.append(lb)
        anterior = lb
    return out


def _por_dia(medicoes: Iterable[tuple[date, float]], transformar: Callable[[float], float]) -> dict[date, float]:
    """Várias medições no mesmo dia → média (já transformada)."""
    acc: dict[date, list[float]] = defaultdict(list)
    for d, v in medicoes:
        acc[d].append(transformar(v))
    return {d: statistics.fmean(v) for d, v in acc.items()}


def vfc(medicoes: Iterable[MedicaoVFC], inicio: date, fim: date, cfg: Recuperacao) -> list[LinhaBase]:
    """Estado diário da VFC. Em cada dia usa a fonte/métrica da medição mais recente."""
    meds = [m for m in medicoes if m.valor_ms > 0]
    series: dict[tuple[str, str], dict[date, float]] = {}
    for chave in {(m.fonte, m.metrica) for m in meds}:
        series[chave] = _por_dia(((m.data, m.valor_ms) for m in meds if (m.fonte, m.metrica) == chave), math.log)

    calculadas = {
        chave: {lb.data: lb for lb in linha_base(
            s, inicio, fim,
            janela_media=cfg.vfc_janela_media_dias,
            minimo_na_media=cfg.vfc_minimo_valores_na_media,
            janela_faixa=cfg.vfc_janela_faixa_dias,
            largura_dp=cfg.vfc_largura_faixa_dp,
            dias_calibracao=cfg.vfc_dias_calibracao,
        )}
        for chave, s in series.items()
    }

    ordenadas = sorted(meds, key=lambda m: m.data)
    out: list[LinhaBase] = []
    for d in _dias(inicio, fim):
        ate_hoje = [m for m in ordenadas if m.data <= d]
        if not ate_hoje:
            out.append(LinhaBase(d, "a_calibrar", None, None, None, None, 0, 0))
            continue
        ativa = (ate_hoje[-1].fonte, ate_hoje[-1].metrica)
        lb = calculadas[ativa][d]
        out.append(LinhaBase(**{**lb.__dict__, "fonte": ativa[0], "metrica": ativa[1]}))
    return out


@dataclass(frozen=True)
class EstadoFCR:
    linha_base: LinhaBase
    alerta: bool   # elevação sustentada acima da linha de base pessoal


def fc_repouso(valores: Mapping[date, float], inicio: date, fim: date, cfg: Recuperacao) -> list[EstadoFCR]:
    lbs = linha_base(
        _por_dia(valores.items(), float), inicio, fim,
        janela_media=cfg.vfc_janela_media_dias,
        minimo_na_media=cfg.vfc_minimo_valores_na_media,
        janela_faixa=cfg.vfc_janela_faixa_dias,
        largura_dp=cfg.fcr_largura_faixa_dp,
        dias_calibracao=cfg.vfc_dias_calibracao,
    )
    return [EstadoFCR(lb, lb.estado == "acima" and lb.dias_seguidos_fora >= cfg.fcr_dias_elevada_alerta) for lb in lbs]


def sono_curto(horas: float | None, cfg: Recuperacao) -> bool | None:
    return None if horas is None else horas < cfg.sono_curto_h
