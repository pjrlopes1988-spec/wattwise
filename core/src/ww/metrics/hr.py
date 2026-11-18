"""Métricas de frequência cardíaca (spec 6.2 e 6.5)."""

from __future__ import annotations

from typing import Literal

import numpy as np

from ww.stream import Array

Sexo = Literal["M", "F"]


def carga_fc(
    fc: Array,
    *,
    fc_repouso: float,
    fc_limiar: float,
    fc_max: float,
    b: float,
) -> float:
    """Carga por FC (HRSS, D-011): TRIMP de Banister normalizado (1 h à FC limiar = 100).

    TRIMP por segundo = (1/60) · x · e^(b·x), com x = (FC − FCrep) / (FCmax − FCrep) em [0, 1].
    O fator multiplicativo 'a' do TRIMP anula-se na normalização.
    Amostras desconhecidas (NaN) não somam carga.
    """
    if not (0 < fc_repouso < fc_limiar < fc_max):
        raise ValueError("é preciso FC repouso < FC limiar < FC máxima")
    reserva = fc_max - fc_repouso
    x = np.clip((fc[np.isfinite(fc)] - fc_repouso) / reserva, 0.0, 1.0)
    trimp = float(np.sum(x * np.exp(b * x))) / 60.0
    x_l = (fc_limiar - fc_repouso) / reserva
    trimp_hora_limiar = 60.0 * x_l * np.exp(b * x_l)
    return trimp / trimp_hora_limiar * 100.0


def desacoplamento(potencia: Array, fc: Array) -> float | None:
    """Desacoplamento aeróbio Pa:Hr em %: (EF1 − EF2) / EF1 × 100, EF = potência média / FC média.

    Deve ser aplicado a um esforço contínuo (ex.: bloco em Z2); a escolha do troço é feita fora.
    Positivo = a FC subiu em relação à potência na 2.ª metade.
    """
    n = len(potencia)
    if n < 2 or len(fc) != n:
        return None
    meio = n // 2
    ef1 = _ef(potencia[:meio], fc[:meio])
    ef2 = _ef(potencia[meio:], fc[meio:])
    if ef1 is None or ef2 is None or ef1 == 0:
        return None
    return (ef1 - ef2) / ef1 * 100.0


def _ef(p: Array, f: Array) -> float | None:
    ok = np.isfinite(p) & np.isfinite(f)
    if not ok.any():
        return None
    fc_media = float(np.mean(f[ok]))
    return float(np.mean(p[ok])) / fc_media if fc_media > 0 else None


def fator_eficiencia(potencia_ponderada: float, fc_media: float) -> float:
    """Potência ponderada ÷ FC média."""
    if fc_media <= 0:
        raise ValueError("FC média tem de ser positiva")
    return potencia_ponderada / fc_media
