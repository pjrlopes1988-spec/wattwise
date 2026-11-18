"""Análise completa de uma atividade: qualidade → métricas → carga com fonte registada.

Prioridade da carga (spec 6.2): potência → FC (HRSS) → RPE × duração.
Cada valor sai com a sua origem; as estimativas ficam marcadas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from ww.config import Config
from ww.metrics import hr as m_hr
from ww.metrics import power as m_pot
from ww.quality.clean import Relatorio, limpar
from ww.stream import Serie

FonteCarga = Literal["potencia", "fc", "rpe", "nenhuma"]


@dataclass(frozen=True)
class Fisiologia:
    """Valores do atleta em vigor na data da atividade (com indicação se são estimados)."""
    sexo: Literal["M", "F"]
    ftp: float | None = None
    fc_limiar: float | None = None
    fc_max: float | None = None
    fc_repouso: float | None = None
    estimados: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Resumo:
    duracao_s: int
    qualidade: Relatorio
    potencia_media: float | None
    potencia_ponderada: float | None
    intensidade: float | None
    fc_media: float | None
    carga: float | None
    fonte_carga: FonteCarga
    carga_estimada: bool
    tempo_zonas_potencia: list[int] | None
    tempo_zonas_fc: list[int] | None
    curva: dict[int, float | None] | None
    fator_eficiencia: float | None
    versao_config: str


def analisar(serie: Serie, fis: Fisiologia, cfg: Config, rpe: float | None = None) -> Resumo:
    limpa, rel = limpar(serie, cfg.qualidade, fis.fc_max)
    p, f = limpa.potencia, limpa.fc
    tem_p = bool(np.isfinite(p).any())
    tem_f = bool(np.isfinite(f).any())

    pm = float(np.nanmean(p)) if tem_p else None
    npw = m_pot.potencia_normalizada(p, cfg.potencia.np_janela_s) if tem_p else None
    fcm = float(np.nanmean(f)) if tem_f else None

    carga: float | None = None
    fonte: FonteCarga = "nenhuma"
    estimada = False
    intensidade = None

    if npw is not None and fis.ftp:
        intensidade = m_pot.fator_intensidade(npw, fis.ftp)
        carga = m_pot.carga_potencia(limpa.duracao_s, npw, fis.ftp)
        fonte = "potencia"
        estimada = "ftp" in fis.estimados
    elif tem_f and fis.fc_repouso and fis.fc_limiar and fis.fc_max:
        b = cfg.frequencia_cardiaca.hrss_b_masculino if fis.sexo == "M" else cfg.frequencia_cardiaca.hrss_b_feminino
        carga = m_hr.carga_fc(f, fc_repouso=fis.fc_repouso, fc_limiar=fis.fc_limiar, fc_max=fis.fc_max, b=b)
        fonte = "fc"
        estimada = bool({"fc_limiar", "fc_max", "fc_repouso"} & fis.estimados)
    elif rpe is not None:
        carga = rpe * (limpa.duracao_s / 60.0) * 100.0 / (cfg.carga_forma.rpe_limiar * 60.0)
        fonte = "rpe"
        estimada = True

    return Resumo(
        duracao_s=limpa.duracao_s,
        qualidade=rel,
        potencia_media=pm,
        potencia_ponderada=npw,
        intensidade=intensidade,
        fc_media=fcm,
        carga=carga,
        fonte_carga=fonte,
        carga_estimada=estimada,
        tempo_zonas_potencia=m_pot.tempo_em_zonas(p, fis.ftp, cfg.potencia.zonas_coggan_limites_pct) if tem_p and fis.ftp else None,
        tempo_zonas_fc=m_pot.tempo_em_zonas(f, fis.fc_limiar, cfg.frequencia_cardiaca.zonas_friel_limites_pct) if tem_f and fis.fc_limiar else None,
        curva=m_pot.curva_potencia(p, cfg.potencia.curva_duracoes_s) if tem_p else None,
        fator_eficiencia=m_hr.fator_eficiencia(npw, fcm) if npw is not None and fcm else None,
        versao_config=cfg.versao,
    )
