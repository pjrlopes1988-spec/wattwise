"""Modelo interno de uma atividade: séries a 1 Hz, sem pausas.

Convenções (D-020):
- Uma amostra por segundo de tempo em movimento; as pausas (intervalos sem registo
  maiores do que `pausa_minima_s`) são removidas.
- Valor desconhecido = NaN. Zero é um valor real (ex.: parar de pedalar).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Literal

import numpy as np
from numpy.typing import NDArray

FonteFC = Literal["cinta", "otica", "desconhecida"]
Array = NDArray[np.float64]


@dataclass(frozen=True)
class Serie:
    inicio: datetime
    potencia: Array
    fc: Array
    cadencia: Array
    velocidade: Array  # m/s
    fonte_fc: FonteFC = "desconhecida"
    desporto: str = "cycling"
    subdesporto: str = ""
    avisos: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        n = len(self.potencia)
        for nome in ("fc", "cadencia", "velocidade"):
            if len(getattr(self, nome)) != n:
                raise ValueError(f"série '{nome}' com comprimento diferente da potência")

    @property
    def duracao_s(self) -> int:
        return len(self.potencia)

    @property
    def tem_potencia(self) -> bool:
        return bool(np.any(np.isfinite(self.potencia)))

    @property
    def tem_fc(self) -> bool:
        return bool(np.any(np.isfinite(self.fc)))

    def com(self, **alteracoes: object) -> "Serie":
        return replace(self, **alteracoes)  # type: ignore[arg-type]


def em_movimento(serie: "Serie") -> np.ndarray:
    """Segundos em movimento (D-037). Parado = velocidade 0; sem dados de velocidade,
    parado = potência 0 e cadência 0 (ou desconhecidas). Roda livre a andar conta como movimento."""
    vel = serie.velocidade
    tem_vel = np.isfinite(vel)
    parado_vel = tem_vel & (vel <= 0)
    pot0 = np.nan_to_num(serie.potencia, nan=0.0) <= 0
    cad0 = np.nan_to_num(serie.cadencia, nan=0.0) <= 0
    parado_sem_vel = ~tem_vel & pot0 & cad0
    return ~(parado_vel | parado_sem_vel)


def vazia(n: int) -> Array:
    return np.full(n, np.nan, dtype=np.float64)
