import numpy as np
import pytest

from ww.metrics.hr import carga_fc, desacoplamento, fator_eficiencia
from ww.metrics.power import zona

FRIEL = [81, 89, 93, 99, 102, 106]
ATLETA = dict(fc_repouso=50, fc_limiar=165, fc_max=190, b=1.92)


@pytest.mark.parametrize("fc,esperado", [
    (130, 1), (133.65, 1), (134, 2), (146.85, 2), (147, 3), (153, 3),
    (154, 4), (163, 4), (164, 5), (168, 5), (169, 6), (174, 6), (175, 7),
])
def test_zonas_friel_lthr_165(fc, esperado):
    # 81% = 133,65; 89% = 146,85; 93% = 153,45; 99% = 163,35; 102% = 168,3; 106% = 174,9
    assert zona(fc, 165, FRIEL) == esperado


def test_hrss_uma_hora_a_fc_limiar_vale_100():
    assert carga_fc(np.full(3600, 165.0), **ATLETA) == pytest.approx(100.0)


def test_hrss_meia_hora_a_fc_limiar_vale_50():
    assert carga_fc(np.full(1800, 165.0), **ATLETA) == pytest.approx(50.0)


def test_hrss_calculo_a_mao_uma_hora_a_120():
    # x = 70/140 = 0,5; xL = 115/140
    # HRSS = (0,5·e^0,96) / (xL·e^(1,92·xL)) × 100
    xl = 115 / 140
    esperado = (0.5 * np.exp(0.96)) / (xl * np.exp(1.92 * xl)) * 100
    assert carga_fc(np.full(3600, 120.0), **ATLETA) == pytest.approx(esperado)
    assert esperado == pytest.approx(32.84, abs=0.01)  # 1,3058 / 3,9767


def test_hrss_abaixo_do_repouso_e_zero_e_ignora_desconhecidos():
    fc = np.array([40.0] * 100 + [np.nan] * 100)
    assert carga_fc(fc, **ATLETA) == 0.0


def test_hrss_valida_entradas():
    with pytest.raises(ValueError):
        carga_fc(np.full(10, 150.0), fc_repouso=50, fc_limiar=200, fc_max=190, b=1.92)


def test_desacoplamento_a_mao():
    # 200 W constantes; FC 140 → 147. (EF1 − EF2)/EF1 = 1 − 140/147 = 4,7619%
    p = np.full(3600, 200.0)
    f = np.array([140.0] * 1800 + [147.0] * 1800)
    assert desacoplamento(p, f) == pytest.approx(100 * 7 / 147)


def test_desacoplamento_zero_quando_estavel():
    assert desacoplamento(np.full(100, 180.0), np.full(100, 130.0)) == pytest.approx(0.0)


def test_fator_eficiencia():
    assert fator_eficiencia(210, 140) == pytest.approx(1.5)
