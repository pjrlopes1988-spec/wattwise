"""Modelos de potência crítica, W′ e W′bal (spec 6.1).

Aqui só estão os modelos matemáticos. A escolha dos esforços (qualidade, época,
decaimento, confirmação antes de subir o FTP, proposta ao atleta) é feita noutra
camada e nunca aplica alterações em silêncio.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq, curve_fit

from ww.stream import Array

Esforco = tuple[float, float]  # (duração_s, potência média W)


@dataclass(frozen=True)
class ModeloPC:
    cp: float          # potência crítica (W)
    w_linha: float     # W′ (J)
    pmax: float | None # só no modelo de 3 parâmetros
    metodo: str


def morton_potencia(t: Array | float, cp: float, w: float, pmax: float) -> Array | float:
    """Modelo de 3 parâmetros de Morton: P(t) = CP + W′ / (t + W′/(Pmax − CP))."""
    return cp + w / (np.asarray(t, dtype=float) + w / (pmax - cp))


def monod_2p(esforcos: Sequence[Esforco]) -> ModeloPC:
    """Monod & Scherrer: P = CP + W′/t. Regressão linear de P contra 1/t (≥ 2 esforços)."""
    if len(esforcos) < 2:
        raise ValueError("o modelo de 2 parâmetros precisa de pelo menos 2 esforços")
    t = np.array([e[0] for e in esforcos], dtype=float)
    p = np.array([e[1] for e in esforcos], dtype=float)
    if len(set(t)) < 2:
        raise ValueError("os esforços têm de ter durações diferentes")
    w, cp = np.polyfit(1.0 / t, p, 1)
    if w <= 0 or cp <= 0:
        raise ValueError("ajuste sem significado fisiológico (W′ ou CP ≤ 0)")
    return ModeloPC(float(cp), float(w), None, "monod_2p")


def morton_3p(esforcos: Sequence[Esforco]) -> ModeloPC:
    """Ajuste completo do modelo de Morton (≥ 3 esforços, ex.: 5 s, 3–5 min, 10–30 min)."""
    if len(esforcos) < 3:
        raise ValueError("o modelo de 3 parâmetros precisa de pelo menos 3 esforços")
    t = np.array([e[0] for e in esforcos], dtype=float)
    p = np.array([e[1] for e in esforcos], dtype=float)
    inicial = monod_2p([e for e in esforcos if e[0] >= 120] or esforcos[-2:])
    p0 = [inicial.cp, inicial.w_linha, float(p.max()) * 1.1]
    params, _ = curve_fit(
        morton_potencia, t, p, p0=p0,
        bounds=([1.0, 1.0, float(p.max()) * 0.9], [float(p.max()), 1e6, 5000.0]),
        maxfev=10000,
    )
    cp, w, pmax = (float(v) for v in params)
    return ModeloPC(cp, w, pmax, "morton_3p")


def cp_de_um_esforco(duracao_s: float, potencia: float, w_linha: float, pmax: float) -> ModeloPC:
    """CP a partir de um único esforço máximo, com W′ e Pmax fixos (D-010).

    P(t) cresce com CP, por isso há uma única solução em (0, potência).
    """
    if potencia >= pmax:
        raise ValueError("potência do esforço tem de ser inferior a Pmax")

    def erro(cp: float) -> float:
        return float(morton_potencia(duracao_s, cp, w_linha, pmax)) - potencia

    if erro(1e-6) > 0:
        raise ValueError("W′/Pmax fixos incompatíveis com o esforço (a potência é baixa demais)")
    cp = brentq(erro, 1e-6, potencia - 1e-6)
    return ModeloPC(float(cp), w_linha, pmax, "morton_1_esforco")


def ftp_de_cp(cp: float, fator: float) -> float:
    return cp * fator


def w_linha_da_curva(curva: Mapping[int, float | None], cp: float, duracao_max_s: int = 600) -> float | None:
    """W′ estimado: maior energia acima da CP nos esforços curtos da curva de potência."""
    energias = [(p - cp) * d for d, p in curva.items() if p is not None and d <= duracao_max_s and p > cp]
    return max(energias) if energias else None


def w_bal(potencia: Array, cp: float, w_linha: float) -> Array:
    """Saldo de W′ (J) segundo a segundo, forma diferencial (Skiba et al., 2015).

    Acima da CP: gasta (P − CP) J/s. Abaixo: recupera (W′ − W′bal)·(CP − P)/W′ J/s.
    Amostras desconhecidas mantêm o saldo (não se inventa recuperação).
    """
    saldo = np.empty(len(potencia), dtype=float)
    atual = w_linha
    for i, p in enumerate(potencia):
        if np.isfinite(p):
            if p > cp:
                atual -= p - cp
            else:
                atual += (w_linha - atual) * (cp - p) / w_linha
        saldo[i] = atual
    return saldo
