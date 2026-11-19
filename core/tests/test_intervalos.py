from datetime import datetime

import numpy as np
import pytest

from ww.metrics.intervalos import detetar, media_centrada
from ww.stream import Serie


def serie(p, f):
    n = len(p)
    return Serie(datetime(2026, 1, 1), np.array(p, float), np.array(f, float), np.full(n, 90.0), np.full(n, 9.0))


def blocos(*partes):
    p, f = [], []
    for dur, pot, fc in partes:
        p += [pot] * dur
        f += [fc] * dur
    return p, f


def test_media_centrada():
    m = media_centrada(np.array([0, 0, 10, 0, 0], float), 3)
    assert m.tolist() == pytest.approx([0, 10 / 3, 10 / 3, 10 / 3, 0])


def test_cinco_intervalos_de_4_min(cfg):
    # 10 min a 150 W, depois 5 × (4 min a 300 W + 2 min a 150 W). FTP 250 → limiar 220 W.
    partes = [(600, 150, 120)] + [(240, 300, 160), (120, 150, 120)] * 5
    p, f = blocos(*partes)
    iv = detetar(serie(p, f), cfg.intervalos, ftp=250)
    assert len(iv) == 5
    for k, i in enumerate(iv):
        assert i.inicio_s == 600 + k * 360
        assert i.fim_s == 600 + k * 360 + 240
        assert i.duracao_s == 240
        assert i.potencia_media == pytest.approx(300)
        assert i.fc_media == pytest.approx(160)
        assert i.sinal == "potencia"
    # HRRc: FC no último segundo (160) − FC 60 s depois (120)
    assert iv[0].hrrc == pytest.approx(40)


def test_queda_curta_junta_o_mesmo_intervalo(cfg):
    p, f = blocos((300, 150, 120), (120, 300, 160), (5, 100, 155), (120, 300, 160), (300, 150, 120))
    iv = detetar(serie(p, f), cfg.intervalos, ftp=250)
    assert len(iv) == 1
    assert iv[0].duracao_s == 245


def test_esforco_curto_demais_e_ignorado(cfg):
    p, f = blocos((300, 150, 120), (20, 400, 150), (300, 150, 120))
    assert detetar(serie(p, f), cfg.intervalos, ftp=250) == []


def test_sem_potencia_usa_fc(cfg):
    # FC limiar 165 → limiar 92% = 151,8 bpm
    p, f = blocos((600, np.nan, 120), (300, np.nan, 160), (600, np.nan, 120))
    iv = detetar(serie(p, f), cfg.intervalos, fc_limiar=165)
    assert len(iv) == 1 and iv[0].sinal == "fc"
    assert (iv[0].inicio_s, iv[0].fim_s) == (600, 900)
    assert iv[0].potencia_media is None


def test_sem_referencias_nao_deteta(cfg):
    p, f = blocos((600, 300, 160))
    assert detetar(serie(p, f), cfg.intervalos) == []


def test_intervalos_com_ruido_realista(cfg):
    # Mesmos 5 × 4 min, com ruído de ±20 W (desvio-padrão) e falhas de 1 s
    rng = np.random.default_rng(7)
    partes = [(600, 150, 120)] + [(240, 300, 160), (120, 150, 120)] * 5
    p, f = blocos(*partes)
    p = np.array(p) + rng.normal(0, 20, len(p))
    p[rng.choice(len(p), 30, replace=False)] = np.nan
    iv = detetar(serie(p, f), cfg.intervalos, ftp=250)
    assert len(iv) == 5
    for k, i in enumerate(iv):
        assert abs(i.inicio_s - (600 + k * 360)) <= 3
        assert abs(i.duracao_s - 240) <= 6
        assert i.potencia_media == pytest.approx(300, abs=10)
