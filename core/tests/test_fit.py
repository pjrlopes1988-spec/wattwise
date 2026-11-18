import numpy as np
import pytest

from fit_sintetico import INICIO, gerar
from ww.fit.reader import ErroFIT, ler_bytes


def test_le_registos_a_1hz():
    s = ler_bytes(gerar([(i, 200, 140, 90) for i in range(120)]))
    assert s.duracao_s == 120
    assert s.inicio == INICIO
    assert np.all(s.potencia == 200)
    assert np.all(s.fc == 140)


def test_pausa_longa_e_removida():
    regs = [(i, 200, 140, 90) for i in range(60)] + [(i, 250, 150, 90) for i in range(360, 420)]
    s = ler_bytes(gerar(regs))
    assert s.duracao_s == 120  # os 300 s parados não contam


def test_gravacao_inteligente_e_preenchida():
    # um registo a cada 3 s (< pausa mínima de 10 s)
    s = ler_bytes(gerar([(t, 210, 135, 85) for t in range(0, 30, 3)]))
    assert s.duracao_s == 28  # 9 intervalos de 3 s + último registo
    assert np.all(s.potencia == 210)


def test_campos_em_falta_ficam_desconhecidos():
    s = ler_bytes(gerar([(i, None, 140, None) for i in range(10)]))
    assert not s.tem_potencia
    assert s.tem_fc


def test_ficheiro_invalido():
    with pytest.raises(ErroFIT):
        ler_bytes(b"isto nao e um ficheiro fit")
