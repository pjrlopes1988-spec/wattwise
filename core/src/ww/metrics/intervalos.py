"""Deteção automática de intervalos (spec 6.5), sem depender do botão de volta.

Trabalho = sinal suavizado (média centrada) sobe acima do limiar de entrada e só acaba
quando desce abaixo do limiar de saída (histerese); quedas curtas dentro do mesmo esforço
são juntadas; esforços mais curtos do que a duração mínima são ignorados.
Para cada intervalo calcula-se também a recuperação da FC (HRRc).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ww.config import Intervalos
from ww.stream import Array, Serie


@dataclass(frozen=True)
class Intervalo:
    inicio_s: int
    fim_s: int                 # exclusivo
    sinal: str                 # "potencia" ou "fc"
    potencia_media: float | None
    fc_media: float | None
    fc_max: float | None
    hrrc: float | None         # descida da FC (bpm) nos N s após o fim

    @property
    def duracao_s(self) -> int:
        return self.fim_s - self.inicio_s


def media_centrada(x: Array, janela: int) -> Array:
    """Média móvel centrada, ignorando desconhecidos; NaN se a janela não tiver dados."""
    n = len(x)
    validos = np.isfinite(x)
    soma = np.concatenate(([0.0], np.cumsum(np.where(validos, x, 0.0))))
    conta = np.concatenate(([0], np.cumsum(validos)))
    i = np.arange(n)
    a = np.clip(i - janela // 2, 0, n)
    b = np.clip(i - janela // 2 + janela, 0, n)   # nas pontas a janela encolhe, não se desloca
    c = conta[b] - conta[a]
    with np.errstate(invalid="ignore", divide="ignore"):
        m = (soma[b] - soma[a]) / c
    m[c == 0] = np.nan
    return m


def _sequencias(marca: np.ndarray) -> list[tuple[int, int]]:
    d = np.diff(np.concatenate(([0], marca.astype(int), [0])))
    return list(zip(np.flatnonzero(d == 1).tolist(), np.flatnonzero(d == -1).tolist()))


def _histerese(suave: Array, entrada: float, saida: float) -> list[tuple[int, int]]:
    """Começa quando o sinal sobe acima de `entrada`; só acaba quando desce abaixo de `saida`."""
    seqs: list[tuple[int, int]] = []
    inicio = -1
    for i, v in enumerate(suave):
        if inicio < 0 and v >= entrada:
            inicio = i
        elif inicio >= 0 and v < saida:
            seqs.append((inicio, i))
            inicio = -1
    if inicio >= 0:
        seqs.append((inicio, len(suave)))
    return seqs


def _media(x: Array) -> float | None:
    return float(np.nanmean(x)) if np.isfinite(x).any() else None


def detetar(serie: Serie, cfg: Intervalos, *, ftp: float | None = None, fc_limiar: float | None = None) -> list[Intervalo]:
    if ftp and serie.tem_potencia:
        sinal, x = "potencia", serie.potencia
        limiar, saida = ftp * cfg.limiar_pct_ftp / 100.0, ftp * cfg.saida_pct_ftp / 100.0
    elif fc_limiar and serie.tem_fc:
        sinal, x = "fc", serie.fc
        limiar, saida = fc_limiar * cfg.limiar_pct_fc_limiar / 100.0, fc_limiar * cfg.saida_pct_fc_limiar / 100.0
    else:
        return []

    suave = np.nan_to_num(media_centrada(x, cfg.suavizacao_s), nan=-1.0)
    seqs = _histerese(suave, limiar, saida)

    juntas: list[list[int]] = []
    for a, b in seqs:
        if juntas and a - juntas[-1][1] <= cfg.juntar_pausas_ate_s:
            juntas[-1][1] = b
        else:
            juntas.append([a, b])

    fc = serie.fc
    out = []
    for a, b in juntas:
        # A suavização desloca as pontas (para fora ou para dentro): acerta-as no sinal original
        while a > 0 and np.isfinite(x[a - 1]) and x[a - 1] >= limiar:
            a -= 1
        while b < len(x) and np.isfinite(x[b]) and x[b] >= limiar:
            b += 1
        while a < b and not (np.isfinite(x[a]) and x[a] >= limiar):
            a += 1
        while b > a and not (np.isfinite(x[b - 1]) and x[b - 1] >= limiar):
            b -= 1
        if b - a < cfg.duracao_minima_s:
            continue
        hrrc = None
        fim = b - 1 + cfg.recuperacao_fc_s
        if fim < len(fc) and np.isfinite(fc[b - 1]) and np.isfinite(fc[fim]):
            hrrc = float(fc[b - 1] - fc[fim])
        seg_fc = fc[a:b]
        out.append(Intervalo(
            a, b, sinal,
            _media(serie.potencia[a:b]),
            _media(seg_fc),
            float(np.nanmax(seg_fc)) if np.isfinite(seg_fc).any() else None,
            hrrc,
        ))
    return out
