"""Atividades suspeitas (spec 6.6).

Uma atividade suspeita não alimenta o eFTP, o W′ nem os modelos personalizados até
o atleta confirmar que os dados estão certos. A carga continua a contar.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

import numpy as np

from ww.config import Qualidade
from ww.metrics.power import melhor_media, potencia_normalizada
from ww.stream import Array, Serie, em_movimento

Codigo = Literal["transporte_motorizado", "e_bike", "potencia_inconsistente", "potencia_muito_acima_do_habitual"]


@dataclass(frozen=True)
class Suspeita:
    codigo: Codigo
    detalhe: str


def aplicar_calibracao(potencia: Array, escala: float = 1.0, desvio_w: float = 0.0) -> Array:
    """Correção por potenciómetro (escala e desvio definidos para esse dispositivo)."""
    return potencia * escala + desvio_w


def _maior_sequencia(marca: np.ndarray) -> int:
    melhor = atual = 0
    for m in marca:
        atual = atual + 1 if m else 0
        melhor = max(melhor, atual)
    return melhor


def avaliar(
    serie: Serie,
    cfg: Qualidade,
    *,
    eficiencia_habitual: float | None = None,
    melhores_epoca: Mapping[int, float] | None = None,
) -> list[Suspeita]:
    """`serie` já limpa. `eficiencia_habitual` = mediana de potência ponderada / FC média
    das atividades recentes do atleta com o mesmo potenciómetro."""
    out: list[Suspeita] = []

    if "e_bike" in serie.subdesporto or "e_bike" in serie.desporto:
        out.append(Suspeita("e_bike", "Atividade registada como e-bike."))

    rapido = np.nan_to_num(serie.velocidade, nan=0.0) >= cfg.velocidade_motorizada_ms
    seq = _maior_sequencia(rapido)
    if seq >= cfg.velocidade_motorizada_min_s:
        out.append(Suspeita("transporte_motorizado",
                            f"{seq} s seguidos acima de {cfg.velocidade_motorizada_ms * 3.6:.0f} km/h."))

    npw = potencia_normalizada(serie.potencia, movimento=em_movimento(serie))
    fc_media = float(np.nanmean(serie.fc)) if serie.tem_fc else None
    if eficiencia_habitual and npw and fc_media:
        ef = npw / fc_media
        desvio = (ef / eficiencia_habitual - 1.0) * 100.0
        if abs(desvio) > cfg.eficiencia_desvio_suspeito_pct:
            out.append(Suspeita("potencia_inconsistente",
                                f"Potência/FC {desvio:+.0f}% face ao habitual (potenciómetro ou rolo mal calibrado?)."))

    if melhores_epoca:
        for d, melhor in sorted(melhores_epoca.items()):
            p = melhor_media(serie.potencia, d)
            if p is not None and melhor > 0 and (p / melhor - 1.0) * 100.0 > cfg.curva_salto_suspeito_pct:
                out.append(Suspeita("potencia_muito_acima_do_habitual",
                                    f"Melhor {d} s: {p:.0f} W, {(p / melhor - 1) * 100:.0f}% acima do melhor da época ({melhor:.0f} W)."))
                break
    return out
