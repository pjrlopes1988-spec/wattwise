from datetime import datetime

import numpy as np
import pytest

from ww.analise import Fisiologia, analisar
from ww.metrics.fc_personalizado import AmostraTreino, ModeloFC, ajustar
from ww.stream import Serie

COEF = np.array([20.0, 50.0, 70.0, 85.0, 100.0, 115.0, 130.0])   # carga por hora em cada zona


def amostras(n, ruido=0.0, seed=1):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        seg = rng.integers(0, 1800, 7) * (rng.random(7) < 0.8)
        carga = float(seg / 3600 @ COEF) * (1 + rng.normal(0, ruido))
        out.append(AmostraTreino(seg.tolist(), carga))
    return out


def test_recupera_coeficientes(cfg):
    r = ajustar(amostras(40), cfg.modelo_fc_personalizado)
    assert r.motivo == "ok"
    assert r.modelo.carga_por_hora == pytest.approx(COEF.tolist(), rel=1e-6)
    assert r.modelo.r2 == pytest.approx(1.0)


def test_calculo_a_mao():
    m = ModeloFC(tuple(COEF), 0.95, 30)
    # 30 min em Z2 + 15 min em Z4 = 0,5×50 + 0,25×85 = 46,25
    assert m.carga([0, 1800, 0, 900, 0, 0, 0]) == pytest.approx(46.25)


def test_poucas_atividades(cfg):
    assert ajustar(amostras(10), cfg.modelo_fc_personalizado).motivo == "poucas_atividades"


def test_ajuste_fraco_volta_ao_hrss(cfg):
    assert ajustar(amostras(40, ruido=0.6), cfg.modelo_fc_personalizado).motivo == "ajuste_fraco"


def test_coeficientes_incoerentes_sao_rejeitados(cfg):
    rng = np.random.default_rng(3)
    errado = np.array([20.0, 90.0, 40.0, 85.0, 100.0, 115.0, 130.0])  # Z3 vale menos do que Z2
    a = []
    for _ in range(40):
        seg = rng.integers(0, 1800, 7)
        a.append(AmostraTreino(seg.tolist(), float(seg / 3600 @ errado)))
    assert ajustar(a, cfg.modelo_fc_personalizado).motivo == "incoerente"


def test_analise_usa_modelo_personalizado_sem_potencia(cfg):
    n = 3600
    s = Serie(datetime(2026, 1, 1), np.full(n, np.nan), np.full(n, 140.0), np.full(n, 90.0), np.full(n, np.nan))
    # FC 140 com limiar 165 = 84,8% → Z2 de Friel → 1 h × 50
    fis = Fisiologia("M", fc_limiar=165, fc_max=190, fc_repouso=50, modelo_fc=ModeloFC(tuple(COEF), 0.9, 30))
    r = analisar(s, fis, cfg)
    assert r.fonte_carga == "fc_personalizado"
    assert r.carga == pytest.approx(50.0)
