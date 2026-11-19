from datetime import datetime

import numpy as np

from ww.stream import Serie, em_movimento


def s(p, c, v):
    a = lambda x: np.array(x, float)
    return Serie(datetime(2026, 1, 1), a(p), np.full(len(p), np.nan), a(c), a(v))


def test_parado_pela_velocidade():
    m = em_movimento(s([0, 0, 200], [0, 0, 90], [0, 8, 9]))
    assert m.tolist() == [False, True, True]   # 2.º: roda livre a andar conta como movimento


def test_sem_velocidade_usa_potencia_e_cadencia():
    m = em_movimento(s([0, 0, 150, np.nan], [0, 60, 0, np.nan], [np.nan] * 4))
    assert m.tolist() == [False, True, True, False]
