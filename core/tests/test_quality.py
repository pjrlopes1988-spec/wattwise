from datetime import datetime

import numpy as np
import pytest

from ww.quality.clean import limpar
from ww.stream import Serie


def serie(p, f, c, fonte="desconhecida"):
    a = lambda x: np.array(x, dtype=float)
    return Serie(datetime(2026, 1, 1), a(p), a(f), a(c), np.full(len(p), np.nan), fonte_fc=fonte)


def test_sem_problemas_indice_1(cfg):
    _, r = limpar(serie([200] * 100, [140] * 100, [90] * 100), cfg.qualidade, fc_max=190)
    assert r.indice == 1.0
    assert r.motivos == ()


def test_pico_de_potencia_removido(cfg):
    s, r = limpar(serie([200, 3000, 200, 200], [140] * 4, [90] * 4), cfg.qualidade)
    assert np.isnan(s.potencia[1])
    assert r.potencia_picos == 1
    assert r.indice == pytest.approx(0.75)


def test_falha_de_sinal_vs_parar_de_pedalar(cfg):
    # 0 W com cadência 90 = falha; 0 W com cadência 0 = parou de pedalar (válido)
    s, r = limpar(serie([0, 0, 200], [140] * 3, [90, 0, 90]), cfg.qualidade)
    assert np.isnan(s.potencia[0])
    assert s.potencia[1] == 0
    assert r.potencia_falhas_sinal == 1


def test_fc_acima_da_maxima_e_pico_isolado(cfg):
    s, r = limpar(serie([200] * 5, [140, 141, 180, 142, 260], [90] * 5), cfg.qualidade, fc_max=190)
    assert np.isnan(s.fc[2])   # pico isolado (+39 e −38 bpm), abaixo da FC máx.
    assert np.isnan(s.fc[4])   # acima de FC máx. + 5
    assert r.fc_picos == 1 and r.fc_fora_limites == 1


def test_fc_otica_baixa_indice(cfg):
    _, r = limpar(serie([200] * 10, [140] * 10, [90] * 10, "otica"), cfg.qualidade)
    assert r.indice == pytest.approx(0.9)
    assert "FC ótica de pulso" in r.motivos


def test_original_nao_e_alterado(cfg):
    original = serie([3000, 200], [140, 140], [90, 90])
    limpar(original, cfg.qualidade)
    assert original.potencia[0] == 3000
