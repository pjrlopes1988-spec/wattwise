import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ww.metrics.power import (
    carga_potencia, curva_potencia, fator_intensidade, melhor_media,
    potencia_normalizada, tempo_em_zonas, zona,
)

LIM = [55, 75, 90, 105, 120, 150]


@pytest.mark.parametrize("w,esperado", [
    (0, 1), (110, 1), (110.01, 2), (150, 2), (150.5, 3), (180, 3), (181, 4),
    (210, 4), (211, 5), (240, 5), (241, 6), (300, 6), (301, 7), (1000, 7),
])
def test_zonas_coggan_ftp_200(w, esperado):
    # FTP 200 W: limites 110 / 150 / 180 / 210 / 240 / 300 W, superiores inclusivos (D-007)
    assert zona(w, 200, LIM) == esperado


def test_tempo_em_zonas_ignora_desconhecidos():
    p = np.array([100, 100, 160, 400, np.nan, 250])
    assert tempo_em_zonas(p, 200, LIM) == [2, 0, 1, 0, 0, 1, 1]


def test_np_constante_e_igual_a_potencia():
    assert potencia_normalizada(np.full(600, 200.0)) == pytest.approx(200.0)


def test_np_curta_demais_nao_existe():
    assert potencia_normalizada(np.full(29, 200.0)) is None


def test_np_blocos_contra_calculo_a_mao():
    # 300 s a 300 W + 300 s a 100 W.
    # 571 janelas: 271 a 300 W, 271 a 100 W, 29 de transição com k s a 300 W (k = 29..1):
    # média = 100 + 200k/30.
    p = np.array([300.0] * 300 + [100.0] * 300)
    soma4 = 271 * 300**4 + 271 * 100**4 + sum((100 + 200 * k / 30) ** 4 for k in range(1, 30))
    esperado = (soma4 / 571) ** 0.25
    assert potencia_normalizada(p) == pytest.approx(esperado, rel=1e-12)
    assert esperado == pytest.approx(251.67, abs=0.01)


def test_np_maior_ou_igual_a_media():
    rng = np.random.default_rng(1)
    p = rng.uniform(0, 500, 3600)
    assert potencia_normalizada(p) >= p.mean()


@settings(max_examples=50)
@given(st.lists(st.floats(0, 1500), min_size=30, max_size=400))
def test_np_entre_minimo_e_maximo(valores):
    p = np.array(valores)
    n = potencia_normalizada(p)
    assert p.min() - 1e-6 <= n <= p.max() + 1e-6


def test_np_ignora_falhas_curtas():
    p = np.full(600, 200.0)
    p[100:105] = np.nan
    assert potencia_normalizada(p) == pytest.approx(200.0)


def test_carga_uma_hora_ao_ftp_vale_100():
    assert carga_potencia(3600, 250, 250) == pytest.approx(100.0)


def test_carga_duas_horas_np200_ftp250():
    # IF = 0,8; carga = 7200 × 200 × 0,8 / (250 × 3600) × 100 = 128
    assert fator_intensidade(200, 250) == pytest.approx(0.8)
    assert carga_potencia(7200, 200, 250) == pytest.approx(128.0)


def test_curva_de_potencia():
    p = np.array([100.0] * 10 + [500.0] * 5 + [100.0] * 10)
    c = curva_potencia(p, [5, 10, 60])
    assert c[5] == pytest.approx(500)
    assert c[10] == pytest.approx(300)  # (5×500 + 5×100) / 10
    assert c[60] is None                 # atividade mais curta do que 60 s


def test_melhor_media_nao_usa_janelas_com_falhas():
    p = np.array([200.0] * 10 + [np.nan] + [400.0] * 4 + [100.0] * 10)
    assert melhor_media(p, 5) == pytest.approx((4 * 400 + 100) / 5)


def test_np_ignora_janelas_paradas():
    # 600 s a 200 W, 300 s parado (0 W), 600 s a 200 W
    p = np.array([200.0] * 600 + [0.0] * 300 + [200.0] * 600)
    mov = np.array([True] * 600 + [False] * 300 + [True] * 600)
    assert potencia_normalizada(p) < 200            # sem informação de movimento, a paragem baixa a NP
    # com movimento: só sobram janelas que terminam a andar; as 29 primeiras após a paragem
    # misturam zeros, por isso a NP fica ligeiramente abaixo de 200
    n = potencia_normalizada(p, movimento=mov)
    assert 195 < n < 200


def test_curva_conta_falhas_como_zero():
    p = np.full(100, 300.0)
    p[50:55] = np.nan                                 # 5% em falta → janela aceite, conta 0 W
    assert melhor_media(p, 100) == pytest.approx(285.0)
    p[50:61] = np.nan                                 # 11% em falta → janela rejeitada
    assert melhor_media(p, 100) is None
