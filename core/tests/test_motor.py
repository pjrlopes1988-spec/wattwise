"""Motor de adaptação diária: cada regra da spec 7.3/7.4 com um caso construído à mão."""
import json
import math
from datetime import date, timedelta

import pytest

from ww.motor import EstadoAtleta, Feito, Questionario, SinaisDia, avaliar, decidir, reorganizar_semana
from ww.plano import TreinoPlaneado, alta_intensidade, trocar_ambiente
from ww.recuperacao import EstadoFCR, LinhaBase
from ww.treinos import carregar

LIB = carregar()
D = date(2027, 1, 12)          # terça


def vfc(estado="normal", seguidos=0):
    return LinhaBase(D, estado, math.log(55), math.log(60), math.log(80), math.log(55), seguidos, 30)


def fcr(estado="normal", alerta=False):
    return EstadoFCR(LinhaBase(D, estado, 52, 45, 50, 52, 1 if estado == "acima" else 0, 30), alerta)


def bom(**kw):
    base = dict(vfc=vfc(), fc_repouso=fcr(), sono_h=7.5, questionario=Questionario(cansaco=2, dores=2, stress=2, humor=4),
                frescura_pct=-15)
    base.update(kw)
    return SinaisDia(D, **base)


def tp(id_, papel="sessao_chave", data=D, cfg=None):
    t = LIB[id_]
    from ww.config import carregar as c
    return TreinoPlaneado(data, t, papel, alta_intensidade(t, cfg or c()), t.ambiente)


# ------------------------------------------------------------------ prontidão

def test_tudo_normal_verde(cfg):
    p, _ = avaliar(bom(), EstadoAtleta(), cfg)
    assert p.estado == "verde" and p.sinais == () and p.em_falta == ()


@pytest.mark.parametrize("alteracao,codigo", [
    (dict(sono_h=5.0), "sono_curto"),
    (dict(vfc=vfc("abaixo", 1)), "vfc_abaixo"),
    (dict(fc_repouso=fcr("acima")), "fc_repouso_alta"),
    (dict(questionario=Questionario(cansaco=4)), "cansaco"),
    (dict(questionario=Questionario(humor=2)), "humor"),
    (dict(frescura_pct=-35), "frescura_negativa"),
])
def test_um_sinal_amarelo(cfg, alteracao, codigo):
    p, _ = avaliar(bom(**alteracao), EstadoAtleta(), cfg)
    assert p.estado == "amarelo" and [s.codigo for s in p.sinais] == [codigo]


def test_dois_sinais_vermelho(cfg):
    p, _ = avaliar(bom(sono_h=5.0, questionario=Questionario(cansaco=5)), EstadoAtleta(), cfg)
    assert p.estado == "vermelho"


@pytest.mark.parametrize("alteracao", [
    dict(vfc=vfc("abaixo", 3)),                 # 3 dias seguidos abaixo da faixa
    dict(fc_repouso=fcr("acima", alerta=True)),  # elevação sustentada
    dict(frescura_pct=-50),                     # frescura muito negativa
])
def test_sinal_forte_vermelho_direto(cfg, alteracao):
    p, _ = avaliar(bom(**alteracao), EstadoAtleta(), cfg)
    assert p.estado == "vermelho" and any(s.forte for s in p.sinais)


def test_dados_em_falta_decide_com_o_que_ha(cfg):
    p, _ = avaliar(SinaisDia(D, sono_h=7.0), EstadoAtleta(), cfg)
    assert p.estado == "verde"
    assert set(p.em_falta) == {"vfc", "fc_repouso", "questionario", "frescura"}
    p2, _ = avaliar(bom(vfc=vfc("a_calibrar")), EstadoAtleta(), cfg)
    assert "vfc_a_calibrar" in p2.em_falta


def test_doenca_persiste_ate_melhorar(cfg):
    p1, e1 = avaliar(bom(questionario=Questionario(doenca=True, febre=True)), EstadoAtleta(), cfg)
    assert p1.estado == "vermelho" and p1.doente and e1.doente_desde == D
    p2, e2 = avaliar(bom(questionario=None), e1, cfg)                     # não respondeu: continua doente
    assert p2.doente and p2.estado == "vermelho"
    p3, e3 = avaliar(bom(questionario=Questionario(melhorou=True)), e2, cfg)
    assert not p3.doente and e3.doente_desde is None and p3.estado == "verde"


def test_alarme_bloqueia(cfg):
    p, _ = avaliar(bom(questionario=Questionario(alarmes=frozenset({"dor_peito"}))), EstadoAtleta(), cfg)
    assert p.estado == "bloqueado"
    d = decidir(tp("limiar_2x20"), p, LIB, cfg)
    assert d.treino_final is None and d.procurar_medico and "alarme_bloqueia_treino" in d.regras


# ------------------------------------------------------------------ decisão

def _p(cfg, **kw):
    return avaliar(bom(**kw), EstadoAtleta(), cfg)[0]


def test_verde_mantem(cfg):
    t = tp("limiar_2x20")
    d = decidir(t, _p(cfg), LIB, cfg)
    assert d.treino_final == t and d.regras == ("verde_mantem_treino",)


def test_amarelo_sessao_chave_versao_mais_facil(cfg):
    t = tp("limiar_2x20")
    d = decidir(t, _p(cfg, sono_h=5.0), LIB, cfg)
    f = d.treino_final.treino
    assert d.regras == ("amarelo_versao_mais_facil",)
    assert f.tipo == "limiar" and f.dificuldade < t.treino.dificuldade
    assert f.carga <= cfg.motor.amarelo_fator_carga * t.treino.carga


def test_amarelo_resistencia_mais_curta(cfg):
    t = TreinoPlaneado(D, LIB["resistencia"].com_duracao(120), "dia_longo", False)
    d = decidir(t, _p(cfg, sono_h=5.0), LIB, cfg)
    assert d.treino_final.minutos == 90      # 75% de 120


def test_amarelo_adia_teste(cfg):
    d = decidir(tp("teste_20min", "teste"), _p(cfg, sono_h=5.0), LIB, cfg)
    assert d.regras == ("amarelo_teste_adiado",) and d.treino_final.papel == "resistencia"


def test_vermelho_recuperacao_ativa(cfg):
    d = decidir(tp("vo2_5x4"), _p(cfg, frescura_pct=-50), LIB, cfg)
    assert d.estado == "vermelho" and d.treino_final.papel == "recuperacao"
    assert d.treino_final.minutos == cfg.motor.vermelho_recuperacao_min and not d.treino_final.alta_intensidade


def test_doenca_com_febre_descanso_sem_febre_recuperacao(cfg):
    p1, _ = avaliar(bom(questionario=Questionario(doenca=True, febre=True)), EstadoAtleta(), cfg)
    assert decidir(tp("limiar_2x20"), p1, LIB, cfg).treino_final is None
    p2, _ = avaliar(bom(questionario=Questionario(doenca=True)), EstadoAtleta(), cfg)
    d2 = decidir(tp("limiar_2x20"), p2, LIB, cfg)
    assert d2.treino_final.papel == "recuperacao" and not d2.treino_final.alta_intensidade


def test_prova_desaconselhada_com_doenca_mantida_com_alerta(cfg):
    prova = TreinoPlaneado(D, LIB["limiar_30"], "prova", True, prioridade="A")
    p1, _ = avaliar(bom(questionario=Questionario(doenca=True)), EstadoAtleta(), cfg)
    assert decidir(prova, p1, LIB, cfg).regras == ("doenca_prova_desaconselhada",)
    assert decidir(prova, _p(cfg, sono_h=5.0), LIB, cfg).regras == ("prova_mantida_com_alerta",)
    d = decidir(prova, _p(cfg, frescura_pct=-50), LIB, cfg)
    assert d.regras == ("vermelho_prova_desaconselhada",) and d.treino_final is None


def test_alteracao_aplica_as_duas_versoes(cfg):
    t = trocar_ambiente(tp("limiar_2x20"), "outdoor", LIB, cfg)
    t = TreinoPlaneado(D, LIB["limiar_2x20"], "sessao_chave", True, "outdoor", alternativa=LIB["limiar_2x20_indoor"])
    d = decidir(t, _p(cfg, frescura_pct=-50), LIB, cfg)
    op = d.treino_final.opcoes()
    assert op["outdoor"].ambiente == "outdoor" and op["indoor"].ambiente == "indoor"
    assert op["outdoor"].tipo == op["indoor"].tipo == "recuperacao"


def test_prontidao_apos_prova_A(cfg):
    d = decidir(tp("limiar_2x20"), _p(cfg, sono_h=5.0), LIB, cfg, verificar_prontidao=True)
    assert "prontidao_apos_prova_A_prolonga_recuperacao" in d.regras and d.treino_final.papel == "recuperacao"
    assert decidir(tp("limiar_2x20"), _p(cfg), LIB, cfg, verificar_prontidao=True).regras == ("verde_mantem_treino",)


def test_registo_completo_e_sem_dados_pessoais(cfg):
    d = decidir(tp("limiar_2x20"), _p(cfg, sono_h=5.0), LIB, cfg)
    r = d.registo()
    json.dumps(r)                                          # serializável para a auditoria
    assert set(r) >= {"data", "estado", "regras", "sinais", "dados_em_falta", "treino_original", "treino_final",
                      "versao_config", "versao_motor"}
    assert r["sinais"][0] == {"codigo": "sono_curto", "valor": 5.0, "limiar": 6.0, "forte": False}


# ------------------------------------------------------------------ semana

def _semana(cfg):
    seg = date(2027, 1, 11)
    return [
        tp("limiar_3x10", "sessao_chave", seg + timedelta(days=1), cfg),                     # ter
        TreinoPlaneado(seg + timedelta(days=2), LIB["resistencia"].com_duracao(90), "resistencia", False),  # qua
        TreinoPlaneado(seg + timedelta(days=3), LIB["resistencia"].com_duracao(90), "resistencia", False),  # qui
        tp("vo2_5x4", "sessao_chave", seg + timedelta(days=5), cfg),                          # sáb
        TreinoPlaneado(seg + timedelta(days=6), LIB["resistencia"].com_duracao(180), "dia_longo", False),   # dom
    ]


def test_treino_chave_falhado_e_movido_sem_acumular(cfg):
    sem = _semana(cfg)
    r = reorganizar_semana(sem, {}, date(2027, 1, 13), LIB, cfg)        # quarta; terça falhou
    por_dia = {t.data: t for t in r.treinos}
    assert por_dia[date(2027, 1, 13)].treino.id == "limiar_3x10"       # passou para hoje (quarta), o 1.º dia possível
    assert sum(1 for t in r.treinos if t.treino.id == "limiar_3x10" and t.papel == "sessao_chave") == 1
    assert por_dia[date(2027, 1, 12)].papel == "falhado"
    assert any(x.startswith("treino_falhado_movido") for x in r.regras)


def test_volta_de_grupo_nao_planeada_protege_o_dia_seguinte(cfg):
    sem = _semana(cfg)
    # sexta: volta de grupo intensa não planeada; sábado tinha VO2máx; sexta+sábado+... ok (2),
    # mas com quinta também intensa (feita acima do previsto) seriam 3 seguidos
    feitos = {date(2027, 1, 12): Feito(date(2027, 1, 12), 70, 0.9), date(2027, 1, 14): Feito(date(2027, 1, 14), 90, 0.9),
              date(2027, 1, 15): Feito(date(2027, 1, 15), 120, 0.92, planeado=False)}
    r = reorganizar_semana(sem, feitos, date(2027, 1, 16), LIB, cfg)
    sab = {t.data: t for t in r.treinos}[date(2027, 1, 16)]
    assert not sab.alta_intensidade
    assert any(x.startswith("intensidade_a_mais") for x in r.regras)


def test_carga_acima_do_previsto_encurta_resistencia(cfg):
    sem = _semana(cfg)
    feitos = {date(2027, 1, 12): Feito(date(2027, 1, 12), 150), date(2027, 1, 13): Feito(date(2027, 1, 13), 140),
              date(2027, 1, 14): Feito(date(2027, 1, 14), 140)}
    r = reorganizar_semana(sem, feitos, date(2027, 1, 15), LIB, cfg)
    dom = {t.data: t for t in r.treinos}[date(2027, 1, 17)]
    assert dom.minutos < 180
    assert any(x.startswith("carga_acima_do_previsto") for x in r.regras)


def test_frescura_com_condicao_baixa_usa_valor_absoluto(cfg):
    # Condição 16, frescura −16 → −100% (instável): com Condição < 30 usa-se a absoluta (−16 ≥ −25 → sem sinal)
    p, _ = avaliar(bom(frescura_pct=-100, frescura=-16, condicao=16), EstadoAtleta(), cfg)
    assert p.estado == "verde"
    p2, _ = avaliar(bom(frescura_pct=-200, frescura=-42, condicao=21), EstadoAtleta(), cfg)
    assert p2.estado == "vermelho" and p2.sinais[0].codigo == "frescura_muito_negativa" and p2.sinais[0].valor == -42
    # com Condição suficiente usa-se a %
    p3, _ = avaliar(bom(frescura_pct=-35, frescura=-21, condicao=60), EstadoAtleta(), cfg)
    assert p3.estado == "amarelo" and p3.sinais[0].codigo == "frescura_negativa"
