"""Análise completa de uma atividade: qualidade → métricas → carga com fonte registada.

Prioridade da carga (spec 6.2): potência → FC (modelo personalizado, se aceite; senão HRSS)
→ RPE × duração.
Cada valor sai com a sua origem; as estimativas ficam marcadas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from ww.config import Config
from ww.metrics import hr as m_hr
from ww.metrics import power as m_pot
from ww.metrics.fc_personalizado import ModeloFC
from ww.quality.clean import Relatorio, limpar
from ww.stream import Serie, em_movimento

FonteCarga = Literal["potencia", "fc_personalizado", "fc", "rpe", "nenhuma"]


@dataclass(frozen=True)
class Fisiologia:
    """Valores do atleta em vigor na data da atividade (com indicação se são estimados)."""
    sexo: Literal["M", "F"]
    ftp: float | None = None
    fc_limiar: float | None = None
    fc_max: float | None = None
    fc_repouso: float | None = None
    estimados: frozenset[str] = frozenset()
    modelo_fc: ModeloFC | None = None   # só se o ajuste foi aceite (ww.metrics.fc_personalizado)


@dataclass(frozen=True)
class Resumo:
    duracao_s: int
    tempo_movimento_s: int
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
    avisos: tuple[str, ...] = ()


def analisar(serie: Serie, fis: Fisiologia, cfg: Config, rpe: float | None = None) -> Resumo:
    limpa, rel = limpar(serie, cfg.qualidade, fis.fc_max)
    p, f = limpa.potencia, limpa.fc
    tem_p = bool(np.isfinite(p).any())
    tem_f = bool(np.isfinite(f).any())

    mov = em_movimento(limpa)
    t_mov = int(mov.sum())
    # Média sobre o tempo total, com segundos sem dados a 0 W (como o Intervals.icu) (D-039)
    pm = float(np.nansum(p)) / len(p) if tem_p else None
    npw = m_pot.potencia_normalizada(p, cfg.potencia.np_janela_s, mov) if tem_p else None
    fcm = float(np.nanmean(f)) if tem_f else None

    avisos: list[str] = []
    fc_ok = bool(fis.fc_repouso and fis.fc_limiar and fis.fc_max)
    if fc_ok and not (fis.fc_repouso < fis.fc_limiar < fis.fc_max):  # type: ignore[operator]
        # Ex. real: FC de repouso configurada igual à FC limiar (168). Não se calcula HRSS
        # com valores impossíveis; avisa-se o atleta para corrigir o perfil (D-041).
        fc_ok = False
        avisos.append("perfil_fc_invalido")

    carga: float | None = None
    fonte: FonteCarga = "nenhuma"
    estimada = False
    intensidade = None

    if npw is not None and fis.ftp:
        intensidade = m_pot.fator_intensidade(npw, fis.ftp)
        carga = m_pot.carga_potencia(t_mov, npw, fis.ftp)
        fonte = "potencia"
        estimada = "ftp" in fis.estimados
    elif tem_f and fis.modelo_fc is not None and fis.fc_limiar:
        zonas = m_pot.tempo_em_zonas(f, fis.fc_limiar, cfg.frequencia_cardiaca.zonas_friel_limites_pct)
        carga = fis.modelo_fc.carga(zonas)
        fonte = "fc_personalizado"
        estimada = "fc_limiar" in fis.estimados
    elif tem_f and fc_ok:
        b = cfg.frequencia_cardiaca.hrss_b_masculino if fis.sexo == "M" else cfg.frequencia_cardiaca.hrss_b_feminino
        carga = m_hr.carga_fc(f, fc_repouso=fis.fc_repouso, fc_limiar=fis.fc_limiar, fc_max=fis.fc_max, b=b)
        fonte = "fc"
        estimada = bool({"fc_limiar", "fc_max", "fc_repouso"} & fis.estimados)
    elif rpe is not None:
        carga = rpe * (t_mov / 60.0) * 100.0 / (cfg.carga_forma.rpe_limiar * 60.0)
        fonte = "rpe"
        estimada = True

    return Resumo(
        duracao_s=limpa.duracao_s,
        tempo_movimento_s=t_mov,
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
        avisos=tuple(avisos),
    )
