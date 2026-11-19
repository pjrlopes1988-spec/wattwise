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


# ------------------------------------------------------------------ indoor / outdoor (D-058, D-059)
from dataclasses import replace as _replace  # noqa: E402
from datetime import date  # noqa: E402

from ww.perfil import Equipamento, ambientes, onde_treina  # noqa: E402
from ww.plano import escolher, trocar_ambiente  # noqa: E402


def test_onde_treina_sugerido_pelo_equipamento():
    assert onde_treina(CENARIOS["avancado_com_tudo_ftp"]) == "ambos"            # tem rolo inteligente
    assert onde_treina(CENARIOS["intermedio_prova_16_semanas"]) == "outdoor"     # sem rolo
    a = _replace(CENARIOS["avancado_com_tudo_ftp"], onde_treina="indoor")
    assert ambientes(a) == ("indoor",)


def test_ambos_dois_treinos_lado_a_lado(cfg):
    a = completar(CENARIOS["avancado_com_tudo_ftp"], HOJE, cfg)
    p = gerar(a, LIB, cfg, inicio=INICIO)
    for t in p.treinos():
        assert t.papel == "prova" or set(t.opcoes()) == {"outdoor", "indoor"}, t
        o, i = t.opcoes()["outdoor"], t.opcoes().get("indoor")
        assert o.ambiente == "outdoor" and i.ambiente == "indoor"
        assert all(x.pct_min == x.pct_max for x in i.passos if not x.rampa), i.id
        assert i.minutos <= cfg.indoor.duracao_max_min
        assert i.tipo == o.tipo
        # antes da escolha conta a versão mais pesada (segurança)
        assert t.carga == pytest.approx(max(o.carga, i.carga))


def test_so_outdoor_sem_alternativa(cfg):
    a = completar(CENARIOS["intermedio_prova_16_semanas"], HOJE, cfg)
    p = gerar(a, LIB, cfg, inicio=INICIO)
    assert all(t.alternativa is None and t.ambiente == "outdoor" for t in p.treinos())


def test_so_indoor(cfg):
    a = completar(_replace(CENARIOS["avancado_com_tudo_ftp"], onde_treina="indoor"), HOJE, cfg)
    p = gerar(a, LIB, cfg, inicio=INICIO)
    for t in p.treinos():
        assert t.alternativa is None and t.ambiente == "indoor" and t.treino.ambiente == "indoor"
        assert t.minutos <= cfg.indoor.duracao_max_min


def test_escolher_uma_versao(cfg):
    a = completar(CENARIOS["avancado_com_tudo_ftp"], HOJE, cfg)
    p = gerar(a, LIB, cfg, inicio=INICIO)
    t = next(t for t in p.treinos() if t.papel == "dia_longo")
    ind = escolher(t, "indoor", cfg)
    assert ind.escolhido and ind.ambiente == "indoor" and ind.alternativa is None
    assert ind.carga == pytest.approx(t.opcoes()["indoor"].carga)
    assert escolher(t, "outdoor", cfg).treino == t.opcoes()["outdoor"]
    with pytest.raises(ValueError):
        escolher(ind, "outdoor", cfg)      # depois de escolhido, só fica essa versão


def test_rolo_sem_potenciometro_da_watts_indoor(cfg):
    from ww.perfil import tem_potencia
    a = _replace(CENARIOS["iniciante_sem_potenciometro"], equipamento=Equipamento(rolo_inteligente=True))
    assert tem_potencia(a, "indoor") and not tem_potencia(a, "outdoor")


def test_trocar_treino_para_indoor_e_outdoor(cfg):
    from datetime import date
    from ww.plano import TreinoPlaneado
    d = date(2026, 12, 1)
    tp = TreinoPlaneado(d, LIB["limiar_2x20"], "sessao_chave", True, "outdoor")
    ind = trocar_ambiente(tp, "indoor", LIB, cfg)
    assert ind.treino.id == "limiar_2x20_indoor" and ind.ambiente == "indoor"
    assert trocar_ambiente(ind, "outdoor", LIB, cfg).treino.id == "limiar_2x20"
    # Z2 de 4 h escalável → indoor fica no máximo do rolo
    longo = TreinoPlaneado(d, LIB["resistencia"].com_duracao(240), "dia_longo", False, "outdoor")
    assert trocar_ambiente(longo, "indoor", LIB, cfg).minutos == cfg.indoor.duracao_max_min
    # Z2 longo de 5 h (não existe indoor) → o resistência indoor mais parecido, dentro do limite
    z5 = TreinoPlaneado(d, LIB["z2_longo_5h"], "dia_longo", False, "outdoor")
    alt = trocar_ambiente(z5, "indoor", LIB, cfg)
    assert alt.treino.ambiente == "indoor" and alt.treino.tipo == "resistencia"
    assert alt.minutos <= cfg.indoor.duracao_max_min
    # treinos do Paulo (só existem indoor) → outdoor: o mais parecido do mesmo tipo
    torque = TreinoPlaneado(d, LIB["paulo_torque_ao_limiar_10x1"], "sessao_chave", True, "indoor")
    out = trocar_ambiente(torque, "outdoor", LIB, cfg)
    assert out.treino.ambiente == "outdoor" and out.treino.tipo == "forca"


# ------------------------------------------------------------------ provas A–D (D-060)
from ww.perfil import Prova, PerfilInvalido, validar  # noqa: E402


@pytest.fixture(scope="module")
def epoca(cfg):
    a = completar(CENARIOS["epoca_provas_abcd"], HOJE, cfg)
    return a, gerar(a, LIB, cfg, inicio=INICIO)


def test_todas_as_provas_no_plano_com_prioridade(epoca):
    a, p = epoca
    provas = {t.data: t for t in p.treinos() if t.papel == "prova"}
    assert {d: t.prioridade for d, t in provas.items()} == {x.data: x.prioridade for x in a.provas}
    assert p.fim == max(x.data for x in a.provas)


def test_prova_A_com_afinacao_e_recuperacao_depois(epoca):
    a, p = epoca
    for x in a.provas:
        if x.prioridade != "A":
            continue
        s = next(s for s in p.semanas if s.inicio <= x.data < s.inicio + timedelta(days=7))
        assert s.fase == "afinacao"
        seguinte = [t for t in p.semanas if t.numero == s.numero + 1]
        if seguinte:
            assert seguinte[0].fase == "recuperacao"


def test_sem_intensidade_antes_e_dias_faceis_depois(epoca, cfg):
    a, p = epoca
    cp = cfg.provas
    por_dia = {t.data: t for t in p.treinos()}
    for x in a.provas:
        for k in range(1, cp.dias_sem_intensidade_antes[x.prioridade] + 1):
            t = por_dia.get(x.data - timedelta(days=k))
            if t is not None:
                assert t.papel in ("resistencia", "recuperacao", "ativacao"), (x.nome, t)
                assert t.minutos <= cp.duracao_max_antes_min, (x.nome, t)
        for k in range(1, cp.dias_faceis_depois[x.prioridade] + 1):
            t = por_dia.get(x.data + timedelta(days=k))
            if t is not None:
                assert t.minutos <= 45 and not t.alta_intensidade, (x.nome, t)


def test_ativacao_antes_da_prova_B(epoca):
    a, p = epoca
    por_dia = {t.data: t for t in p.treinos()}
    for x in a.provas:
        if x.prioridade == "B":
            ativ = [por_dia.get(x.data - timedelta(days=k)) for k in (1, 2)]
            assert any(t is not None and t.papel == "ativacao" for t in ativ), x.nome


def test_provas_B_C_D_contam_como_sessao_chave(epoca, cfg):
    a, p = epoca
    for s in p.semanas:
        provas = [t for t in s.treinos if t.papel == "prova" and t.prioridade in "BCD"]
        if not provas or s.fase not in ("base", "construcao", "especifico"):
            continue
        normal = int(getattr(cfg.plano.sessoes_chave, s.fase)[p.nivel_regras])
        chaves = [t for t in s.treinos if t.papel == "sessao_chave"]
        assert len(chaves) <= max(0, normal - len(provas)), s.numero


def test_semana_B_com_menos_carga(epoca, cfg):
    a, p = epoca
    for s in p.semanas:
        if s.fase in ("base", "construcao", "especifico") and any(t.prioridade == "B" for t in s.treinos):
            assert "mini-afinação para prova B" in s.notas


def test_sem_provas_A_plano_segue_objetivo_e_encaixa_as_outras(cfg):
    a = completar(_replace(CENARIOS["avancado_com_tudo_ftp"], provas=(
        Prova("Granfondo B", date(2027, 1, 24), "B"), Prova("Prova C", date(2027, 3, 21), "C"))), HOJE, cfg)
    p = gerar(a, LIB, cfg, inicio=INICIO)
    assert "afinacao" not in [s.fase for s in p.semanas]
    assert {t.prioridade for t in p.treinos() if t.papel == "prova"} == {"B", "C"}
    assert p.fim >= date(2027, 3, 21)


def test_validacao_das_provas(cfg):
    base = CENARIOS["epoca_provas_abcd"]
    with pytest.raises(PerfilInvalido, match="prioridade"):
        validar(_replace(base, provas=(Prova("X", date(2027, 5, 1), "E"),)), HOJE, cfg)   # type: ignore[arg-type]
    with pytest.raises(PerfilInvalido, match="mesmo dia"):
        validar(_replace(base, provas=(Prova("X", date(2027, 5, 1), "A"), Prova("Y", date(2027, 5, 1), "C"))), HOJE, cfg)
    with pytest.raises(PerfilInvalido, match="já passou"):
        validar(_replace(base, provas=(Prova("X", date(2026, 1, 1), "A"),)), HOJE, cfg)


def test_carga_da_prova_pela_duracao(cfg):
    from ww.plano import _treino_prova
    # 1 h → intensidade 0,95 → carga 1 × 0,95² × 100 = 90,25; 4 h → 0,76 → 4 × 0,5776 × 100 = 231
    assert _treino_prova(Prova("CR", date(2027, 1, 1), "B", 1.0), cfg).carga == pytest.approx(90.25)
    assert _treino_prova(Prova("GF", date(2027, 1, 1), "A", 4.0), cfg).carga == pytest.approx(231.04)
