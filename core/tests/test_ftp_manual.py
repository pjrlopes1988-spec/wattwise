"""FTP definido manualmente pelo atleta (D-071)."""
from dataclasses import replace
from datetime import date

import pytest

from cenarios import CENARIOS, HOJE
from ww.eftp import EsforcoMax, Estimativa, PerfilAnaerobio
from ww.ftp_proposta import avaliar
from ww.perfil import FTPInvalido, RegistoFTP, completar, definir_ftp_manual, ftp_em_vigor
from ww.plano import gerar
from ww.treinos import carregar

LIB = carregar()
BASE = CENARIOS["intermedio_prova_16_semanas"]          # 74 kg, FTP 250 (atleta)


def test_definir_ftp_vale_a_partir_da_data(cfg):
    a, avisos = definir_ftp_manual(BASE, 265, date(2026, 12, 1), cfg)
    assert a.ftp.valor == 265 and a.ftp.fonte == "atleta" and avisos == ()
    assert a.historico_ftp == (RegistoFTP(date(2026, 12, 1), 265.0, "atleta"),)
    assert ftp_em_vigor(a, date(2026, 12, 1)) == 265
    # antes da data vale o FTP anterior (histórico não muda)
    a2 = replace(a, historico_ftp=(RegistoFTP(date(2026, 9, 1), 250.0, "teste"),) + a.historico_ftp)
    assert ftp_em_vigor(a2, date(2026, 11, 15)) == 250
    assert ftp_em_vigor(a2, date(2027, 1, 10)) == 265


@pytest.mark.parametrize("valor", [60, 600])   # 0,8 e 8,1 W/kg para 74 kg
def test_valores_impossiveis_recusados(cfg, valor):
    with pytest.raises(FTPInvalido, match="W/kg"):
        definir_ftp_manual(BASE, valor, date(2026, 12, 1), cfg)


def test_aviso_quando_longe_do_eftp(cfg):
    _, avisos = definir_ftp_manual(BASE, 300, date(2026, 12, 1), cfg, eftp=250)     # +20%
    assert avisos == ("diferenca_grande_eftp:+20%",)
    _, avisos2 = definir_ftp_manual(BASE, 260, date(2026, 12, 1), cfg, eftp=250)    # +4%
    assert avisos2 == ()


def test_mesmo_dia_substitui(cfg):
    a, _ = definir_ftp_manual(BASE, 260, date(2026, 12, 1), cfg)
    a, _ = definir_ftp_manual(a, 262, date(2026, 12, 1), cfg)
    assert [r.valor for r in a.historico_ftp] == [262.0]


def test_modo_manual_sem_propostas(cfg):
    e = Estimativa(270, 270, "morton_1_esforco", PerfilAnaerobio(15000, 1000, "populacao"),
                   (EsforcoMax("x", HOJE, 1200, 282, True),))
    args = dict(por_atividade={"x": 270, "y": 268}, confirmado_por_treinos_limiar=False, hoje=HOJE, cfg=cfg,
                dias_com_dados_potencia=100)
    assert avaliar(250, e, **args) is not None                      # automático: propõe
    assert avaliar(250, e, **args, modo="manual") is None          # manual: nunca propõe


def test_plano_usa_o_ftp_manual(cfg):
    from ww.alvos import descrever
    a, _ = definir_ftp_manual(completar(BASE, HOJE, cfg), 300, HOJE, cfg)
    p = gerar(a, LIB, cfg, inicio=date(2026, 11, 23))
    chave = next(t for t in p.treinos() if t.papel == "sessao_chave")
    passo = next(x for x in chave.treino.passos if x.pct_medio >= 76 and not x.rampa)
    txt = descrever(passo, ftp=a.ftp.valor, fc_limiar=None, potencia=True, cfg=cfg)
    assert str(round(300 * passo.pct_min / 100)) in txt
