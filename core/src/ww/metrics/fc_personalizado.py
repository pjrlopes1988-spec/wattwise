"""Modelo de carga por FC personalizado (spec 6.2).

Aprende, com as atividades do próprio atleta que têm potência e FC, quanta carga
(na escala da potência) vale cada hora em cada zona de FC:
    carga ≈ Σ horas_na_zona_i × coeficiente_i     (coeficientes ≥ 0, sem constante)
Só é usado se houver atividades suficientes, o ajuste for bom (R²) e os coeficientes
subirem com a zona (fisiologicamente coerente). Caso contrário usa-se o HRSS.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from scipy.optimize import nnls

from ww.config import ModeloFCPersonalizado


@dataclass(frozen=True)
class AmostraTreino:
    segundos_zonas_fc: Sequence[int]   # tempo em cada zona de FC (7 zonas de Friel)
    carga_potencia: float


@dataclass(frozen=True)
class ModeloFC:
    carga_por_hora: tuple[float, ...]
    r2: float
    n_atividades: int

    def carga(self, segundos_zonas_fc: Sequence[int]) -> float:
        h = np.asarray(segundos_zonas_fc, dtype=float) / 3600.0
        return float(h @ np.asarray(self.carga_por_hora))


@dataclass(frozen=True)
class ResultadoAjuste:
    modelo: ModeloFC | None
    motivo: str   # "ok", "poucas_atividades", "ajuste_fraco", "incoerente"


def ajustar(amostras: Sequence[AmostraTreino], cfg: ModeloFCPersonalizado) -> ResultadoAjuste:
    if len(amostras) < cfg.minimo_atividades:
        return ResultadoAjuste(None, "poucas_atividades")
    x = np.array([a.segundos_zonas_fc for a in amostras], dtype=float) / 3600.0
    y = np.array([a.carga_potencia for a in amostras], dtype=float)
    coef, _ = nnls(x, y)
    prev = x @ coef
    ss_res = float(np.sum((y - prev) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    modelo = ModeloFC(tuple(float(c) for c in coef), r2, len(amostras))
    if r2 < cfg.r2_minimo:
        return ResultadoAjuste(None, "ajuste_fraco")
    # Zonas com tempo suficiente têm de ter carga/hora crescente
    usadas = [i for i in range(x.shape[1]) if x[:, i].sum() >= 1.0]   # ≥ 1 h no total
    valores = [coef[i] for i in usadas]
    if any(b < a * 0.95 for a, b in zip(valores, valores[1:])):
        return ResultadoAjuste(None, "incoerente")
    return ResultadoAjuste(modelo, "ok")
