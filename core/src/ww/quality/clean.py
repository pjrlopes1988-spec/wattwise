"""Qualidade dos dados (spec 6.6): limpeza de picos e falhas de sinal + índice de qualidade.

Os valores rejeitados passam a NaN (desconhecido); nunca são inventados.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ww.config import Qualidade
from ww.stream import Array, Serie


@dataclass(frozen=True)
class Relatorio:
    indice: float                      # 0–1
    potencia_picos: int
    potencia_falhas_sinal: int
    fc_fora_limites: int
    fc_picos: int
    fracao_potencia_valida: float | None
    fracao_fc_valida: float | None
    motivos: tuple[str, ...]

    def serve_para_modelos(self, cfg: Qualidade) -> bool:
        return self.indice >= cfg.indice_minimo_para_modelos


def limpar(serie: Serie, cfg: Qualidade, fc_max: float | None = None) -> tuple[Serie, Relatorio]:
    pot = serie.potencia.copy()
    fc = serie.fc.copy()
    motivos: list[str] = []
    tinha_pot = serie.tem_potencia
    tinha_fc = serie.tem_fc

    # Potência: valores impossíveis
    picos_pot = (pot > cfg.potencia_maxima_plausivel_w) | (pot < 0)
    pot[picos_pot] = np.nan

    # Potência a zero enquanto se pedala = falha de sinal, não esforço
    falhas = (pot == 0) & (serie.cadencia > cfg.cadencia_minima_falha_potencia)
    pot[falhas] = np.nan

    # FC fora de limites fisiológicos
    limite_sup = (fc_max + cfg.fc_folga_acima_fc_max) if fc_max else 230.0
    fora = (fc < cfg.fc_minima_plausivel) | (fc > limite_sup)
    fc[fora] = np.nan

    # FC: picos isolados (salto grande para cima/baixo e regresso logo a seguir)
    picos_fc = _picos_isolados(fc, cfg.fc_salto_maximo_bpm_por_s)
    fc[picos_fc] = np.nan

    frac_pot = _fracao_valida(pot, serie.duracao_s) if tinha_pot else None
    frac_fc = _fracao_valida(fc, serie.duracao_s) if tinha_fc else None

    fracoes = [f for f in (frac_pot, frac_fc) if f is not None]
    indice = min(fracoes) if fracoes else 0.0
    if not fracoes:
        motivos.append("sem potência nem FC")
    if serie.fonte_fc == "otica" and tinha_fc:
        indice -= cfg.penalizacao_fc_otica
        motivos.append("FC ótica de pulso")
    if int(picos_pot.sum()):
        motivos.append(f"{int(picos_pot.sum())} s de potência impossível removidos")
    if int(falhas.sum()):
        motivos.append(f"{int(falhas.sum())} s de falha de sinal de potência")
    if int(fora.sum()) + int(picos_fc.sum()):
        motivos.append(f"{int(fora.sum()) + int(picos_fc.sum())} s de FC inválida removidos")

    relatorio = Relatorio(
        indice=float(np.clip(indice, 0.0, 1.0)),
        potencia_picos=int(picos_pot.sum()),
        potencia_falhas_sinal=int(falhas.sum()),
        fc_fora_limites=int(fora.sum()),
        fc_picos=int(picos_fc.sum()),
        fracao_potencia_valida=frac_pot,
        fracao_fc_valida=frac_fc,
        motivos=tuple(motivos),
    )
    return serie.com(potencia=pot, fc=fc), relatorio


def _fracao_valida(x: Array, n: int) -> float:
    return float(np.isfinite(x).sum() / n) if n else 0.0


def _picos_isolados(x: Array, salto: float) -> np.ndarray:
    marca = np.zeros(len(x), dtype=bool)
    if len(x) < 3:
        return marca
    antes = x[1:-1] - x[:-2]
    depois = x[1:-1] - x[2:]
    # mesmo sinal dos dois lados e ambos acima do salto máximo
    marca[1:-1] = (np.abs(antes) > salto) & (np.abs(depois) > salto) & (np.sign(antes) == np.sign(depois))
    return marca
