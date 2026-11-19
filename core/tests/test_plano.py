"""Regras de segurança e de estrutura do plano, verificadas em todos os cenários (spec 7.2, 7.3)."""
from datetime import timedelta

import pytest

from cenarios import CENARIOS, HOJE, INICIO
from ww.metrics.load import serie_forma
from ww.perfil import completar, nivel_regras
from ww.plano import fases, gerar, _sequencias_altas
from ww.treinos import carregar as carregar_lib

LIB = carregar_lib()


@pytest.fixture(scope="module", params=list(CENARIOS))
def caso(request, cfg):
    a = completar(CENARIOS[request.param], HOJE, cfg)
    return request.param, a, gerar(a, LIB, cfg, inicio=INICIO)


def test_respeita_disponibilidade(caso):
    _, a, p = caso
    for t in p.treinos():
        if t.papel == "prova":
            continue
        assert a.disponibilidade[t.data.weekday()] > 0, t
        assert t.minutos <= a.disponibilidade[t.data.weekday()], t


def test_um_treino_por_dia_e_nada_antes_do_inicio(caso):
    _, _, p = caso
    datas = [t.data for t in p.treinos()]
    assert len(datas) == len(set(datas))
    assert min(datas) >= INICIO


def test_dias_de_descanso_minimos(caso, cfg):
    _, a, p = caso
    minimo = int(cfg.plano.dias_descanso_min[nivel_regras(a, INICIO, cfg)])
    for s in p.semanas:
        if len([d for d in range(7) if s.inicio + timedelta(days=d) >= INICIO]) == 7:
            assert 7 - len(s.treinos) >= minimo, s.numero


def test_nunca_mais_de_2_dias_seguidos_de_alta_intensidade(caso, cfg):
    _, _, p = caso
    altos = {t.data for t in p.treinos() if t.alta_intensidade}
    assert _sequencias_altas(altos) <= cfg.plano.max_dias_alta_intensidade_seguidos


def test_recuperacao_pelo_menos_a_cada_4_semanas(caso):
    _, _, p = caso
    seguidas = 0
    for s in p.semanas:
        seguidas = seguidas + 1 if s.fase in ("base", "construcao", "especifico") else 0
        assert seguidas <= 3, s.numero


def test_rampa_da_condicao_nunca_ultrapassada(caso, cfg):
    _, a, p = caso
    rampa = cfg.plano.rampa_condicao_semana[nivel_regras(a, INICIO, cfg)]
    for s in p.semanas:
        assert s.subida_condicao <= rampa + 1e-6, (s.numero, s.subida_condicao)
    # verificação independente com o módulo de carga/forma
    dias = serie_forma(p.cargas_diarias(), cfg.carga_forma, inicio=INICIO, fim=p.fim)
    for i in range(7, len(dias)):
        assert dias[i].condicao - dias[i - 7].condicao <= rampa + 1e-6, dias[i].data


def test_teste_guiado_na_primeira_semana_so_se_estimado(caso):
    nome, a, p = caso
    testes = [t for t in p.treinos() if t.papel == "teste"]
    if nome in ("iniciante_sem_potenciometro",):
        assert len(testes) == 1 and testes[0].treino.id == "teste_fc_limiar_30min"
        assert testes[0].data < INICIO + timedelta(days=7)
        # não é o primeiro treino do plano
        assert testes[0].data > min(t.data for t in p.treinos())
    elif CENARIOS[nome].ftp is not None:
        assert testes == []


def test_menor_de_idade_com_regras_de_iniciante(cfg):
    a = completar(CENARIOS["juvenil_14_anos"], HOJE, cfg)
    p = gerar(a, LIB, cfg, inicio=INICIO)
    assert p.nivel_regras == "iniciante"
    assert max(t.treino.dificuldade for t in p.treinos()) <= cfg.plano.dificuldade_max["iniciante"]


def test_prova_no_ultimo_dia_com_afinacao(cfg):
    a = completar(CENARIOS["intermedio_prova_16_semanas"], HOJE, cfg)
    p = gerar(a, LIB, cfg, inicio=INICIO)
    ultimo = p.treinos()[-1]
    assert ultimo.papel == "prova" and ultimo.data == a.objetivo.data_prova
    assert p.semanas[-1].fase == "afinacao"
    carga_max = max(s.carga_planeada for s in p.semanas if s.fase in ("construcao", "especifico"))
    assert p.semanas[-1].carga_planeada < 0.6 * carga_max
    # ativação na véspera ou 2 dias antes, com o treino mais leve do tipo
    ativ = [t for t in p.semanas[-1].treinos if t.papel == "sessao_chave"]
    assert ativ and 1 <= (ultimo.data - ativ[-1].data).days <= 2
    assert ativ[-1].treino.id == "vo2_ativacao"


def test_fases_com_prova_a_mao(cfg):
    # 16 semanas, arranque a frio: 2 afinação, 4 específico, 7 construção, 3 base; recuperação a cada 4.ª
    f = fases(16, prova=True, arranque_frio=True, objetivo="prova", cfg=cfg)
    assert f == ["base"] * 3 + ["recuperacao"] + ["construcao"] * 3 + ["recuperacao"] + \
        ["construcao"] * 2 + ["especifico", "recuperacao", "especifico", "especifico"] + ["afinacao"] * 2


def test_fases_sem_prova(cfg):
    assert fases(8, prova=False, arranque_frio=False, objetivo="resistencia", cfg=cfg) == \
        ["base"] * 3 + ["recuperacao"] + ["base"] * 3 + ["recuperacao"]


def test_deterministico(cfg):
    a = completar(CENARIOS["avancado_com_tudo_ftp"], HOJE, cfg)
    p1, p2 = gerar(a, LIB, cfg, inicio=INICIO), gerar(a, LIB, cfg, inicio=INICIO)
    assert p1 == p2


def test_progressao_comeca_pelo_nivel(cfg):
    # avançado (máx. 4): 1.ª semana de construção com dificuldade 2; iniciante (máx. 2): 1
    a = completar(CENARIOS["avancado_com_tudo_ftp"], HOJE, cfg)
    p = gerar(a, LIB, cfg, inicio=INICIO)
    s = next(s for s in p.semanas if s.fase == "construcao")
    assert min(t.treino.dificuldade for t in s.treinos if t.papel == "sessao_chave") >= 2
