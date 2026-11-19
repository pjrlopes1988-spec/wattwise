import numpy as np
import pytest

from ww.metrics.aerobio import Distribuicao3Zonas, eficiencia_z2, seiler

LIM = [55, 75, 90, 105, 120, 150]


def test_seiler_a_mao():
    d = seiler([100, 200, 300, 400, 500, 600, 700], (2, 4))
    assert (d.baixa_s, d.limiar_s, d.alta_s) == (300, 700, 1800)
    b, l, a = d.percentagens()
    assert b == pytest.approx(300 / 28)      # 10,71%
    assert l == pytest.approx(700 / 28)
    assert a == pytest.approx(1800 / 28)


def test_seiler_soma_semanas_e_vazio():
    assert (Distribuicao3Zonas(10, 0, 0) + Distribuicao3Zonas(0, 5, 1)) == Distribuicao3Zonas(10, 5, 1)
    assert Distribuicao3Zonas(0, 0, 0).percentagens() is None


def test_eficiencia_z2():
    # FTP 200 → Z2 = ]110, 150] W. 700 s a 140 W / 125 bpm + 300 s a 250 W / 160 bpm
    p = np.array([140.0] * 700 + [250.0] * 300)
    f = np.array([125.0] * 700 + [160.0] * 300)
    assert eficiencia_z2(p, f, 200, LIM) == pytest.approx(140 / 125)


def test_eficiencia_z2_precisa_de_10_min():
    p = np.array([140.0] * 599)
    assert eficiencia_z2(p, np.full(599, 125.0), 200, LIM) is None
