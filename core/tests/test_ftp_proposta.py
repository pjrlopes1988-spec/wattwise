from datetime import date, timedelta

import pytest

from ww.eftp import EsforcoMax, Estimativa, PerfilAnaerobio
from ww.ftp_proposta import Proposta, avaliar, estado_sem_resposta

HOJE = date(2026, 11, 1)
PERFIL = PerfilAnaerobio(15000, 980, "populacao")


def est(ftp, aid="a1", dias_atras=2):
    e = EsforcoMax(aid, HOJE - timedelta(days=dias_atras), 1200, ftp + 12, True)
    return Estimativa(ftp, ftp, "morton_1_esforco", PERFIL, (e,))


def av(atual, e, por_atividade=None, confirmado=False, cfg=None):
    return avaliar(atual, e, por_atividade=por_atividade or {}, confirmado_por_treinos_limiar=confirmado, hoje=HOJE, cfg=cfg)


def test_sem_estimativa_nao_propoe(cfg):
    assert av(250, None, cfg=cfg) is None


def test_variacao_pequena_nao_incomoda(cfg):
    assert av(250, est(252), cfg=cfg) is None   # +0,8% < 1%


def test_descida(cfg):
    p = av(250, est(240), cfg=cfg)
    assert p.tipo == "descida" and p.ftp_proposto == 240 and p.motivo == "novo_esforco"
    assert p.variacao_pct == pytest.approx(-4.0)


def test_descida_por_decaimento(cfg):
    p = av(250, est(240, dias_atras=60), cfg=cfg)
    assert p.motivo == "sem_esforcos_recentes"


def test_subida_pequena_proposta_por_inteiro(cfg):
    p = av(250, est(257), cfg=cfg)   # +2,8%
    assert p.tipo == "subida" and p.ftp_proposto == 257


def test_subida_grande_com_um_esforco_fica_limitada_a_3pct(cfg):
    p = av(250, est(270), por_atividade={"a1": 270}, cfg=cfg)   # +8%
    assert p.motivo == "subida_limitada_aguarda_confirmacao"
    assert p.ftp_proposto == pytest.approx(257.5)
    assert p.estimativa == 270


def test_subida_grande_confirmada_por_segundo_esforco(cfg):
    p = av(250, est(270), por_atividade={"a1": 270, "a2": 262, "a3": 255}, cfg=cfg)
    assert p.motivo == "subida_confirmada" and p.ftp_proposto == 270
    assert p.atividades == ("a1", "a2")   # a3 (255) não chega a +3%


def test_subida_grande_confirmada_por_treinos_de_limiar(cfg):
    p = av(250, est(270), por_atividade={"a1": 270}, confirmado=True, cfg=cfg)
    assert p.ftp_proposto == 270


@pytest.mark.parametrize("tipo,dias,esperado", [
    ("descida", 2, "pendente"), ("descida", 3, "aplicada_automaticamente"),
    ("subida", 2, "pendente"), ("subida", 3, "expirada"), ("subida", 30, "expirada"),
])
def test_sem_resposta(cfg, tipo, dias, esperado):
    p = Proposta(HOJE, 250, 240 if tipo == "descida" else 257, 0, tipo, "novo_esforco", ())
    assert estado_sem_resposta(p, HOJE + timedelta(days=dias), cfg) == esperado
