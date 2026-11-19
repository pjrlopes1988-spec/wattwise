import math
from datetime import date, timedelta

import pytest

from ww.recuperacao import MedicaoVFC, fc_repouso, linha_base, sono_curto, vfc

D0 = date(2026, 1, 1)


def dia(i):
    return D0 + timedelta(days=i)


# ------------------------------------------------------------ cálculo à mão

def test_linha_base_a_mao():
    # 6 dias: 10, 12, 10, 12, 10, 12. Média 3 dias, faixa de 6 dias, ±1 DP, calibração 4 dias.
    # Dia 6: faixa: média 11, DP = √(6/5) = 1,0954 → [9,9046; 12,0954]
    #        média 3 dias = (12+10+12)/3 = 11,333 → normal
    v = {dia(i): x for i, x in enumerate([10, 12, 10, 12, 10, 12])}
    lb = linha_base(v, dia(0), dia(5), janela_media=3, minimo_na_media=2,
                    janela_faixa=6, largura_dp=1.0, dias_calibracao=4)
    assert [x.estado for x in lb[:3]] == ["a_calibrar"] * 3
    u = lb[-1]
    assert u.media7 == pytest.approx(34 / 3)
    assert u.faixa_inf == pytest.approx(11 - math.sqrt(1.2))
    assert u.faixa_sup == pytest.approx(11 + math.sqrt(1.2))
    assert u.estado == "normal"
    assert u.dias_com_dados == 6


def test_sem_dados_recentes():
    v = {dia(i): 50.0 + (i % 2) for i in range(20)}
    lb = linha_base(v, dia(0), dia(30), janela_media=7, minimo_na_media=4,
                    janela_faixa=60, largura_dp=1.0, dias_calibracao=14)
    assert lb[22].estado == "normal"           # dias 16–19 ainda na semana (4 valores)
    assert lb[30].estado == "sem_dados_recentes"


# ------------------------------------------------------------ VFC

def _base(dias=60, fonte="garmin", metrica="rmssd"):
    # alterna 55 e 66 ms (ln ≈ 4,007 e 4,190)
    return [MedicaoVFC(dia(i), fonte, metrica, 55.0 if i % 2 else 66.0) for i in range(dias)]


def test_vfc_calibracao_14_dias(cfg):
    lb = vfc(_base(20), dia(0), dia(19), cfg.recuperacao)
    assert lb[12].estado == "a_calibrar"   # 13 dias de dados
    assert lb[13].estado == "normal"       # 14.º dia
    assert lb[13].fonte == "garmin" and lb[13].metrica == "rmssd"


def test_vfc_usa_ln(cfg):
    lb = vfc(_base(20), dia(0), dia(19), cfg.recuperacao)
    assert lb[19].valor_dia == pytest.approx(math.log(55.0))
    assert lb[19].em_ms(lb[19].valor_dia) == pytest.approx(55.0)


def test_vfc_abaixo_varios_dias_seguidos(cfg):
    meds = _base(60) + [MedicaoVFC(dia(60 + i), "garmin", "rmssd", 35.0) for i in range(6)]
    lb = vfc(meds, dia(59), dia(65), cfg.recuperacao)
    estados = [x.estado for x in lb]
    assert estados[0] == "normal"
    assert "abaixo" in estados
    ultimo = lb[-1]
    assert ultimo.estado == "abaixo"
    primeiro_abaixo = estados.index("abaixo")
    assert ultimo.dias_seguidos_fora == len(estados) - primeiro_abaixo


def test_vfc_mudanca_de_fonte_recalibra(cfg):
    # 30 dias de Garmin (rMSSD) e depois Apple Health (SDNN): não se misturam
    meds = _base(30) + [MedicaoVFC(dia(30 + i), "apple_health", "sdnn", 45.0 + i % 3) for i in range(20)]
    lb = vfc(meds, dia(29), dia(49), cfg.recuperacao)
    assert lb[0].fonte == "garmin" and lb[0].estado == "normal"
    assert lb[1].fonte == "apple_health" and lb[1].estado == "a_calibrar"
    assert lb[14].estado == "normal" and lb[14].metrica == "sdnn"   # 14.º dia de Apple


def test_vfc_varias_medicoes_no_dia_fazem_media_em_ln(cfg):
    meds = [MedicaoVFC(dia(0), "g", "rmssd", 40.0), MedicaoVFC(dia(0), "g", "rmssd", 90.0)]
    lb = vfc(meds, dia(0), dia(0), cfg.recuperacao)
    assert lb[0].valor_dia == pytest.approx((math.log(40) + math.log(90)) / 2)


def test_vfc_sem_medicoes(cfg):
    assert vfc([], dia(0), dia(2), cfg.recuperacao)[0].estado == "a_calibrar"


# ------------------------------------------------------------ FC repouso e sono

def test_fc_repouso_alerta_apos_3_dias_elevada(cfg):
    v = {dia(i): 48.0 + (i % 3) for i in range(60)}
    v.update({dia(60 + i): 60.0 for i in range(8)})
    estados = fc_repouso(v, dia(59), dia(67), cfg.recuperacao)
    assert not estados[0].alerta
    acima = [e for e in estados if e.linha_base.estado == "acima"]
    assert acima, "a média de 7 dias devia sair da faixa"
    assert [e.alerta for e in acima][:3] == [False, False, True]


def test_sono_curto(cfg):
    assert sono_curto(5.5, cfg.recuperacao) is True
    assert sono_curto(7.0, cfg.recuperacao) is False
    assert sono_curto(None, cfg.recuperacao) is None
