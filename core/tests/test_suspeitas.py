from datetime import datetime

import numpy as np
import pytest

from ww.quality.suspeitas import aplicar_calibracao, avaliar
from ww.stream import Serie


def serie(n=600, p=200.0, f=100.0, v=9.0, sub=""):
    return Serie(datetime(2026, 1, 1), np.full(n, p), np.full(n, f), np.full(n, 90.0), np.full(n, v), subdesporto=sub)


def codigos(s):
    return [x.codigo for x in s]


def test_atividade_normal_sem_suspeitas(cfg):
    assert avaliar(serie(), cfg.qualidade, eficiencia_habitual=1.9, melhores_epoca={300: 210}) == []


def test_transporte_motorizado(cfg):
    v = np.full(600, 9.0)
    v[100:161] = 25.0   # 61 s a 90 km/h
    s = serie().com(velocidade=v)
    assert codigos(avaliar(s, cfg.qualidade)) == ["transporte_motorizado"]
    v[160] = 9.0        # só 60 s... ainda conta (mínimo 60 s)
    assert codigos(avaliar(serie().com(velocidade=v), cfg.qualidade)) == ["transporte_motorizado"]
    v[159] = 9.0        # 59 s: descida rápida, não é carro
    assert avaliar(serie().com(velocidade=v), cfg.qualidade) == []


def test_e_bike(cfg):
    assert codigos(avaliar(serie(sub="e_bike_fitness"), cfg.qualidade)) == ["e_bike"]


def test_potencia_inconsistente(cfg):
    # NP 200 / FC 100 = 2,0. Habitual 1,5 → +33% (> 20%)
    s = avaliar(serie(), cfg.qualidade, eficiencia_habitual=1.5)
    assert codigos(s) == ["potencia_inconsistente"]
    assert "+33%" in s[0].detalhe


def test_potencia_muito_acima_do_habitual(cfg):
    assert codigos(avaliar(serie(p=360), cfg.qualidade, melhores_epoca={300: 280})) == ["potencia_muito_acima_do_habitual"]  # +28,6%
    assert avaliar(serie(p=340), cfg.qualidade, melhores_epoca={300: 280}) == []  # +21,4%


def test_calibracao_por_dispositivo():
    assert aplicar_calibracao(np.array([100.0, 200.0]), 1.05, -3).tolist() == pytest.approx([102.0, 207.0])
