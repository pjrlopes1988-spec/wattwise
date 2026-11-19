from datetime import date, timedelta

import pytest

from ww.eftp import EsforcoMax, estimar, fator_decaimento, ftp_teste_20min, perfil_anaerobio
from ww.metrics.cp import morton_potencia

HOJE = date(2026, 11, 1)
EPOCA = date(2026, 1, 1)
PESO = 70.0
W_POP, PMAX_POP = 15000.0, 14.0 * PESO  # valores de população da configuração


def esf(aid, dias_atras, dur, pot, ok=True):
    return EsforcoMax(aid, HOJE - timedelta(days=dias_atras), dur, pot, ok)


def p_modelo(t, cp=250.0, w=W_POP, pmax=PMAX_POP):
    return float(morton_potencia(t, cp, w, pmax))


def test_p20_a_mao():
    # 250 + 15000 / (1200 + 15000/730) = 262,29 W
    assert p_modelo(1200) == pytest.approx(262.29, abs=0.01)


# ------------------------------------------------------------- decaimento

def test_decaimento(cfg):
    assert fator_decaimento(HOJE - timedelta(days=28), HOJE, cfg) == 1.0
    assert fator_decaimento(HOJE - timedelta(days=35), HOJE, cfg) == pytest.approx(0.995)
    assert fator_decaimento(HOJE - timedelta(days=98), HOJE, cfg) == pytest.approx(0.995**10)


# ------------------------------------------------------------- 1 esforço

def test_um_esforco_com_populacao_recupera_cp(cfg):
    r = estimar([esf("a1", 3, 1200, p_modelo(1200))], hoje=HOJE, inicio_epoca=EPOCA, peso_kg=PESO, cfg=cfg)
    assert r.epoca.perfil.origem == "populacao"
    assert r.epoca.ftp == pytest.approx(250.0, rel=1e-6)
    assert r.historico.ftp == pytest.approx(250.0, rel=1e-6)
    assert r.epoca.esforcos[0].atividade_id == "a1"


def test_usa_o_esforco_mais_forte(cfg):
    e = [esf("fraco", 3, 1200, p_modelo(1200, cp=230)), esf("forte", 10, 600, p_modelo(600, cp=255))]
    r = estimar(e, hoje=HOJE, inicio_epoca=EPOCA, peso_kg=PESO, cfg=cfg)
    assert r.epoca.ftp == pytest.approx(255.0, rel=1e-6)
    assert r.epoca.esforcos[0].atividade_id == "forte"


def test_ignora_atividades_sem_qualidade(cfg):
    e = [esf("mau", 3, 1200, 400.0, ok=False), esf("bom", 3, 1200, p_modelo(1200))]
    r = estimar(e, hoje=HOJE, inicio_epoca=EPOCA, peso_kg=PESO, cfg=cfg)
    assert r.epoca.ftp == pytest.approx(250.0, rel=1e-6)
    assert "mau" not in r.por_atividade


def test_ignora_duracoes_fora_de_5_a_30_min(cfg):
    e = [esf("a", 3, 60, 500.0), esf("b", 3, 3600, 240.0)]
    r = estimar(e, hoje=HOJE, inicio_epoca=EPOCA, peso_kg=PESO, cfg=cfg)
    assert r.epoca is None and r.historico is None


def test_ignora_esforcos_futuros(cfg):
    e = [EsforcoMax("futuro", HOJE + timedelta(days=1), 1200, 400.0, True)]
    assert estimar(e, hoje=HOJE, inicio_epoca=EPOCA, peso_kg=PESO, cfg=cfg).epoca is None


def test_epoca_vs_historico(cfg):
    # Esforço forte do ano passado (cp 280) e esforço desta época (cp 250)
    antigo = esf("2025", 400, 1200, p_modelo(1200, cp=280))
    novo = esf("2026", 5, 1200, p_modelo(1200, cp=250))
    r = estimar([antigo, novo], hoje=HOJE, inicio_epoca=EPOCA, peso_kg=PESO, cfg=cfg)
    assert r.epoca.ftp == pytest.approx(250.0, rel=1e-6)
    # Histórico: o antigo vale 280-ish × decaimento (372 dias após a carência ≈ 0,995^53) → < 250
    assert r.historico.esforcos[0].atividade_id == "2026"
    assert r.historico.ftp == pytest.approx(250.0, rel=1e-6)


def test_historico_decai_sem_esforcos_novos(cfg):
    e = [esf("velho", 98, 1200, p_modelo(1200))]
    r = estimar(e, hoje=HOJE, inicio_epoca=HOJE - timedelta(days=30), peso_kg=PESO, cfg=cfg)
    assert r.epoca is None
    assert r.historico.ftp < 250.0
    assert r.historico.ftp == pytest.approx(
        250.0 * 0.95, rel=0.02)  # 0,995^10 ≈ 0,951 aplicado à potência do esforço


# ------------------------------------------------------------- perfil do atleta

def _curva_completa(cp, w, pmax, dias_atras=5, aid="c"):
    # esforços curtos, médios e longos em 3 atividades diferentes
    duracoes = (5, 15, 60, 180, 300, 600, 1200, 1800)
    return [esf(f"{aid}{i % 3}", dias_atras, d, p_modelo(d, cp, w, pmax)) for i, d in enumerate(duracoes)]


def test_perfil_de_uma_so_atividade_usa_populacao(cfg):
    duracoes = (5, 15, 60, 180, 300, 600, 1200, 1800)
    uma = [esf("so_uma", 5, d, p_modelo(d, 260, 22000, 1150)) for d in duracoes]
    assert perfil_anaerobio(uma, HOJE, PESO, cfg).origem == "populacao"


def test_perfil_do_atleta_quando_ha_curva_completa(cfg):
    p = perfil_anaerobio(_curva_completa(260, 22000, 1150), HOJE, PESO, cfg)
    assert p.origem == "atleta"
    assert p.w_linha == pytest.approx(22000, rel=0.01)
    assert p.pmax == pytest.approx(1150, rel=0.01)


def test_perfil_usa_populacao_se_curva_antiga(cfg):
    p = perfil_anaerobio(_curva_completa(260, 22000, 1150, dias_atras=200), HOJE, PESO, cfg)
    assert p.origem == "populacao"


def test_com_perfil_proprio_um_esforco_recupera_cp(cfg):
    r = estimar(_curva_completa(260, 22000, 1150), hoje=HOJE, inicio_epoca=EPOCA, peso_kg=PESO, cfg=cfg)
    assert r.epoca.ftp == pytest.approx(260, rel=1e-3)


# ------------------------------------------------------------- métodos alternativos

def _cfg_metodo(cfg, metodo):
    return cfg.model_copy(update={"eftp": cfg.eftp.model_copy(update={"metodo": metodo})})


def test_morton_3p(cfg):
    c = _cfg_metodo(cfg, "morton_3p")
    r = estimar(_curva_completa(260, 22000, 1150), hoje=HOJE, inicio_epoca=EPOCA, peso_kg=PESO, cfg=c)
    assert r.epoca.metodo == "morton_3p"
    assert r.epoca.ftp == pytest.approx(260, rel=1e-3)


def test_monod_2p(cfg):
    c = _cfg_metodo(cfg, "monod_2p")
    e = [esf("a", 3, 240, 250 + 20000 / 240), esf("b", 4, 1200, 250 + 20000 / 1200)]
    r = estimar(e, hoje=HOJE, inicio_epoca=EPOCA, peso_kg=PESO, cfg=c)
    assert r.epoca.ftp == pytest.approx(250)
    assert r.epoca.perfil.w_linha == pytest.approx(20000)
    assert {x.atividade_id for x in r.epoca.esforcos} == {"a", "b"}


def test_teste_20min(cfg):
    assert ftp_teste_20min(280, cfg) == pytest.approx(266)


def test_esforcos_da_atividade_ate_estimativa(cfg):
    import numpy as np

    from ww.eftp import esforcos_da_atividade

    # 10 min a 100 W + 20 min a 262,29 W (P20 do modelo com CP 250) + 10 min a 100 W
    p = np.array([100.0] * 600 + [p_modelo(1200)] * 1200 + [100.0] * 600)
    e = esforcos_da_atividade(p, "volta", HOJE, True, cfg)
    vinte = [x for x in e if x.duracao_s == 1200][0]
    assert vinte.potencia == pytest.approx(p_modelo(1200))
    r = estimar(e, hoje=HOJE, inicio_epoca=EPOCA, peso_kg=PESO, cfg=cfg)
    # O melhor esforço é o de 20 min (os mais longos misturam os 100 W)
    assert r.epoca.ftp == pytest.approx(250.0, rel=1e-6)
