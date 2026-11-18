import math
from datetime import date, timedelta

import pytest

from ww.metrics.load import faixa_frescura, fator, serie_forma

D0 = date(2026, 1, 1)


def test_um_treino_a_partir_de_zero(cfg):
    dias = serie_forma({D0: 100.0}, cfg.carga_forma, fim=D0 + timedelta(days=1))
    assert dias[0].condicao == pytest.approx(100 / 42)
    assert dias[0].fadiga == pytest.approx(100 / 7)
    assert dias[0].frescura == 0.0
    # Frescura de hoje = condição de ontem − fadiga de ontem
    assert dias[1].frescura == pytest.approx(100 / 42 - 100 / 7)  # −11,905


def test_carga_constante_converge(cfg):
    cargas = {D0 + timedelta(days=i): 80.0 for i in range(400)}
    ultimo = serie_forma(cargas, cfg.carga_forma)[-1]
    assert ultimo.condicao == pytest.approx(80.0, abs=0.01)
    assert ultimo.fadiga == pytest.approx(80.0, abs=1e-6)


def test_forma_em_percentagem(cfg):
    dias = serie_forma({}, cfg.carga_forma, inicio=D0, fim=D0, condicao_inicial=50, fadiga_inicial=60)
    assert dias[0].frescura == -10
    assert dias[0].frescura_pct == pytest.approx(-20.0)


def test_forma_em_percentagem_a_calibrar_com_condicao_baixa(cfg):
    dias = serie_forma({}, cfg.carga_forma, inicio=D0, fim=D0, condicao_inicial=3, fadiga_inicial=9)
    assert dias[0].frescura == -6
    assert dias[0].frescura_pct is None


def test_subida_semanal(cfg):
    dias = serie_forma({}, cfg.carga_forma, inicio=D0, fim=D0 + timedelta(days=7), condicao_inicial=50)
    assert dias[6].subida_7d is None
    # dia 7 face ao dia 0: 50·(41/42)^8 − 50·(41/42)
    assert dias[7].subida_7d == pytest.approx(50 * (41 / 42) ** 8 - 50 * (41 / 42))


def test_fator_exponencial():
    assert fator(42, "exponencial") == pytest.approx(1 - math.exp(-1 / 42))
    assert fator(42, "linear") == pytest.approx(1 / 42)


def test_constante_por_atleta_sobrepoe_config(cfg):
    dias = serie_forma({D0: 100.0}, cfg.carga_forma, constante_condicao=50)
    assert dias[0].condicao == pytest.approx(2.0)


@pytest.mark.parametrize("pct,faixa", [
    (None, "a_calibrar"), (30, "transicao"), (10, "fresco"), (0, "neutra"),
    (-10, "otima"), (-20, "otima"), (-30, "otima"), (-31, "risco"),
])
def test_faixas(cfg, pct, faixa):
    assert faixa_frescura(pct, cfg.carga_forma) == faixa
