"""Métricas de potência (spec 6.1). Funções puras sobre séries a 1 Hz (NaN = desconhecido)."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from ww.stream import Array


def zona(valor: float, referencia: float, limites_pct: Sequence[float]) -> int:
    """Zona (1..n+1) com limites superiores inclusivos (D-007). Ex.: 55% do FTP → Z1."""
    limiares = np.asarray(limites_pct, dtype=float) * referencia / 100.0
    return int(np.searchsorted(limiares, valor, side="left")) + 1


def tempo_em_zonas(serie: Array, referencia: float, limites_pct: Sequence[float]) -> list[int]:
    """Segundos em cada zona. Amostras desconhecidas (NaN) não contam."""
    limiares = np.asarray(limites_pct, dtype=float) * referencia / 100.0
    validos = serie[np.isfinite(serie)]
    idx = np.searchsorted(limiares, validos, side="left")
    return np.bincount(idx, minlength=len(limiares) + 1).astype(int).tolist()


def _medias_moveis(x: Array, janela: int, min_validos: int) -> Array:
    """Médias de todas as janelas de `janela` s; NaN onde há menos de `min_validos` amostras válidas."""
    if len(x) < janela:
        return np.array([], dtype=float)
    validos = np.isfinite(x)
    soma = np.concatenate(([0.0], np.cumsum(np.where(validos, x, 0.0))))
    conta = np.concatenate(([0], np.cumsum(validos)))
    s = soma[janela:] - soma[:-janela]
    c = conta[janela:] - conta[:-janela]
    with np.errstate(invalid="ignore", divide="ignore"):
        medias = s / c
    medias[c < min_validos] = np.nan
    return medias


def potencia_normalizada(
    potencia: Array, janela_s: int = 30, movimento: np.ndarray | None = None
) -> float | None:
    """NP: média móvel de 30 s → 4.ª potência → média → raiz 4.ª.

    - Janelas com menos de metade das amostras válidas são ignoradas (falhas de sinal).
    - Com `movimento`, só contam as janelas que terminam num segundo em movimento
      (as paragens não baixam a NP), como no Intervals.icu (D-037).
    Atividades mais curtas do que a janela não têm NP.
    """
    medias = _medias_moveis(potencia, janela_s, min_validos=max(1, janela_s // 2))
    if movimento is not None and medias.size:
        medias = medias[movimento[janela_s - 1:]]
    medias = medias[np.isfinite(medias)]
    if medias.size == 0:
        return None
    return float(np.mean(medias**4) ** 0.25)


def fator_intensidade(np_w: float, ftp: float) -> float:
    if ftp <= 0:
        raise ValueError("FTP tem de ser positivo")
    return np_w / ftp


def carga_potencia(duracao_s: float, np_w: float, ftp: float) -> float:
    """TSS = (duração_s × NP × IF) / (FTP × 3600) × 100."""
    fi = fator_intensidade(np_w, ftp)
    return duracao_s * np_w * fi / (ftp * 3600.0) * 100.0


def melhor_media(potencia: Array, duracao_s: int) -> float | None:
    """Melhor média em `duracao_s` segundos (D-037).

    Segundos desconhecidos contam como 0 W (conservador: nunca aumentam a curva);
    janelas com menos de 90% de amostras válidas são ignoradas.
    """
    if len(potencia) < duracao_s:
        return None
    validos = np.isfinite(potencia)
    soma = np.concatenate(([0.0], np.cumsum(np.where(validos, potencia, 0.0))))
    conta = np.concatenate(([0], np.cumsum(validos)))
    medias = (soma[duracao_s:] - soma[:-duracao_s]) / duracao_s
    ok = (conta[duracao_s:] - conta[:-duracao_s]) >= 0.9 * duracao_s
    medias = medias[ok]
    return float(medias.max()) if medias.size else None


def curva_potencia(potencia: Array, duracoes_s: Sequence[int]) -> dict[int, float | None]:
    return {d: melhor_media(potencia, d) for d in duracoes_s}
