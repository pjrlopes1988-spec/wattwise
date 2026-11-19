"""Distribuição da intensidade (3 zonas de Seiler) e potência/FC em Z2 (spec 6.5)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from ww.stream import Array


@dataclass(frozen=True)
class Distribuicao3Zonas:
    baixa_s: int
    limiar_s: int
    alta_s: int

    @property
    def total_s(self) -> int:
        return self.baixa_s + self.limiar_s + self.alta_s

    def percentagens(self) -> tuple[float, float, float] | None:
        t = self.total_s
        if t == 0:
            return None
        return (100 * self.baixa_s / t, 100 * self.limiar_s / t, 100 * self.alta_s / t)

    def __add__(self, o: "Distribuicao3Zonas") -> "Distribuicao3Zonas":
        return Distribuicao3Zonas(self.baixa_s + o.baixa_s, self.limiar_s + o.limiar_s, self.alta_s + o.alta_s)


def seiler(tempo_zonas: Sequence[int], ultima_zona: tuple[int, int]) -> Distribuicao3Zonas:
    """Agrupa o tempo nas 7 zonas em 3. `ultima_zona` = (última zona de "baixa", última de "limiar")."""
    b, l = ultima_zona
    return Distribuicao3Zonas(sum(tempo_zonas[:b]), sum(tempo_zonas[b:l]), sum(tempo_zonas[l:]))


def eficiencia_z2(
    potencia: Array, fc: Array, ftp: float, limites_pct: Sequence[float], minimo_s: int = 600
) -> float | None:
    """Potência média ÷ FC média só nos segundos em Z2 de potência (mín. 10 min)."""
    z2_inf = limites_pct[0] * ftp / 100.0
    z2_sup = limites_pct[1] * ftp / 100.0
    ok = np.isfinite(potencia) & np.isfinite(fc) & (potencia > z2_inf) & (potencia <= z2_sup)
    if ok.sum() < minimo_s:
        return None
    return float(np.mean(potencia[ok]) / np.mean(fc[ok]))
