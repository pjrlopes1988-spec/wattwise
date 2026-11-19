"""Simulação de temporada (spec 10.4): 6 meses por cenário, nenhum limite de segurança ultrapassado."""
import pytest

from cenarios import CENARIOS, HOJE, INICIO
from ww.perfil import completar
from ww.simulacao import Comportamento, simular
from ww.treinos import carregar

LIB = carregar()

CASOS = {
    "iniciante_sem_potenciometro": ("iniciante_sem_potenciometro", Comportamento(semente=11, com_vfc=False)),
    "avancado_com_tudo": ("avancado_com_tudo_ftp", Comportamento(semente=12, doencas=((60, 5, 2),), alarme_dia=100)),
    "falha_treinos": ("intermedio_prova_16_semanas", Comportamento(semente=13, cumprimento=0.6)),
    "doente_10_dias": ("competicao_xco_prova_8_semanas", Comportamento(semente=14, doencas=((30, 10, 3),))),
    "sem_vfc": ("pouca_disponibilidade", Comportamento(semente=15, com_vfc=False, responde_questionario=0.3)),
    "epoca_com_provas_e_etapas": ("epoca_provas_abcd", Comportamento(semente=16, excesso_prob=0.25, volta_grupo_prob=0.4)),
    "juvenil": ("juvenil_14_anos", Comportamento(semente=17, doencas=((90, 4, 0),))),
    "mais_agressivo_5": ("avancado_com_tudo_ftp", Comportamento(semente=18, excesso_prob=0.2, volta_grupo_prob=0.3)),
}
AGRESSIVIDADE = {"mais_agressivo_5": 5}


@pytest.fixture(scope="module", params=list(CASOS))
def sim(request, cfg):
    from dataclasses import replace
    cenario, comp = CASOS[request.param]
    a = completar(replace(CENARIOS[cenario], agressividade=AGRESSIVIDADE.get(request.param)), HOJE, cfg)
    return request.param, comp, simular(a, LIB, cfg, inicio=INICIO, dias=182, comportamento=comp)


def test_nenhum_limite_de_seguranca_ultrapassado(sim):
    nome, _, r = sim
    assert r.violacoes == [], f"{nome}: " + "; ".join(r.violacoes[:10])


def test_doenca_sempre_vermelho_e_sem_intensidade(sim):
    _, comp, r = sim
    dias_doente = {ini + k for ini, dur, _ in comp.doencas for k in range(dur)}
    for i in dias_doente:
        d = r.dias[i]
        assert d.prontidao.doente and d.decisao.estado == "vermelho"
        assert d.decisao.treino_final is None or not d.decisao.treino_final.alta_intensidade


def test_alarme_bloqueia_e_manda_ao_medico(sim):
    _, comp, r = sim
    if comp.alarme_dia is not None:
        d = r.dias[comp.alarme_dia]
        assert d.decisao.estado == "bloqueado" and d.decisao.procurar_medico and d.decisao.treino_final is None


def test_cada_dia_tem_registo_de_decisao(sim):
    _, _, r = sim
    assert len(r.dias) == 182
    for d in r.dias:
        reg = d.decisao.registo()
        assert reg["regras"] and reg["versao_motor"] and reg["versao_config"]


def test_o_atleta_progride(sim):
    nome, comp, r = sim
    # quem cumpre a maior parte do plano tem a Condição a subir ao longo da época
    if comp.cumprimento >= 0.8 and nome != "sem_vfc":
        assert r.dias[-1].condicao > r.dias[27].condicao + 5, (nome, r.dias[27].condicao, r.dias[-1].condicao)
