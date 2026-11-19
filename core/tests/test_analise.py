from datetime import datetime

import numpy as np
import pytest

from ww.analise import Fisiologia, analisar
from ww.stream import Serie


def serie(p, f):
    n = len(p)
    return Serie(datetime(2026, 1, 1), np.array(p, float), np.array(f, float), np.full(n, 90.0), np.full(n, np.nan))


def test_prioridade_potencia(cfg):
    r = analisar(serie([250] * 3600, [165] * 3600), Fisiologia("M", ftp=250, fc_limiar=165, fc_max=190, fc_repouso=50), cfg)
    assert r.fonte_carga == "potencia"
    assert r.carga == pytest.approx(100)
    assert not r.carga_estimada
    assert r.versao_config == cfg.versao


def test_sem_potencia_usa_fc(cfg):
    r = analisar(serie([np.nan] * 3600, [165] * 3600), Fisiologia("F", fc_limiar=165, fc_max=190, fc_repouso=50), cfg)
    assert r.fonte_carga == "fc"
    assert r.carga == pytest.approx(100)


def test_sem_dados_usa_rpe_marcado_estimado(cfg):
    r = analisar(serie([np.nan] * 3600, [np.nan] * 3600), Fisiologia("M"), cfg, rpe=7)
    assert r.fonte_carga == "rpe"
    assert r.carga == pytest.approx(100)
    assert r.carga_estimada


def test_ftp_estimado_marca_carga_estimada(cfg):
    r = analisar(serie([200] * 600, [140] * 600), Fisiologia("M", ftp=200, estimados=frozenset({"ftp"})), cfg)
    assert r.carga_estimada


def test_perfil_fc_impossivel_avisa_e_nao_rebenta(cfg):
    # Caso real: FC de repouso configurada igual à FC limiar (168 / 168 / 180)
    r = analisar(serie([np.nan] * 3600, [150] * 3600), Fisiologia("M", fc_limiar=168, fc_max=180, fc_repouso=168), cfg, rpe=6)
    assert "perfil_fc_invalido" in r.avisos
    assert r.fonte_carga == "rpe" and r.carga_estimada
