import numpy as np
import pytest

from ww.metrics.cp import (
    cp_de_um_esforco, ftp_de_cp, monod_2p, morton_3p, morton_potencia, w_bal, w_linha_da_curva,
)

CP, W, PMAX = 250.0, 20000.0, 1000.0


def test_monod_dois_esforcos_a_mao():
    # P = 250 + 20000/t → 180 s: 361,11 W; 720 s: 277,78 W
    m = monod_2p([(180, 250 + 20000 / 180), (720, 250 + 20000 / 720)])
    assert m.cp == pytest.approx(250)
    assert m.w_linha == pytest.approx(20000)


def test_monod_rejeita_um_esforco():
    with pytest.raises(ValueError):
        monod_2p([(300, 300)])


def test_morton_recupera_parametros():
    t = np.array([5, 60, 180, 300, 720, 1200])
    p = morton_potencia(t, CP, W, PMAX)
    m = morton_3p(list(zip(t.tolist(), p.tolist())))
    assert m.cp == pytest.approx(CP, rel=1e-3)
    assert m.w_linha == pytest.approx(W, rel=1e-2)
    assert m.pmax == pytest.approx(PMAX, rel=1e-2)


def test_um_esforco_com_w_e_pmax_corretos_recupera_cp():
    p20 = float(morton_potencia(1200, CP, W, PMAX))
    assert cp_de_um_esforco(1200, p20, W, PMAX).cp == pytest.approx(CP, rel=1e-6)


def test_um_esforco_sensibilidade_a_w():
    # W′ maior → CP menor para o mesmo esforço (documenta a sensibilidade referida na spec)
    p20 = float(morton_potencia(1200, CP, W, PMAX))
    assert cp_de_um_esforco(1200, p20, W * 1.5, PMAX).cp < CP


def test_ftp_de_cp():
    assert ftp_de_cp(250, 0.95) == pytest.approx(237.5)


def test_w_linha_da_curva():
    curva = {5: 900.0, 60: 500.0, 300: 300.0, 1200: 260.0}
    # (900−250)·5 = 3250; (500−250)·60 = 15000; (300−250)·300 = 15000; 1200 s fora
    assert w_linha_da_curva(curva, 250) == pytest.approx(15000)


def test_wbal_a_mao():
    p = np.array([350.0] * 60 + [150.0])
    s = w_bal(p, CP, W)
    assert s[59] == pytest.approx(20000 - 60 * 100)          # 14000 J
    assert s[60] == pytest.approx(14000 + 6000 * 100 / 20000)  # recupera 30 J


def test_wbal_desconhecido_mantem_saldo():
    s = w_bal(np.array([450.0, np.nan, np.nan]), CP, W)
    assert s.tolist() == [19800.0, 19800.0, 19800.0]


def test_wbal_nunca_passa_de_w():
    s = w_bal(np.full(1000, 0.0), CP, W)
    assert s.max() <= W
