"""Inspeção automática da biblioteca de treinos (D-056). Corre sobre TODOS os treinos.

Se acrescentares um treino e um destes testes falhar, a mensagem diz qual e porquê.
"""
import re
import statistics

import pytest

from ww.treinos import ZONAS_TRABALHO, carregar, dificuldade_objetiva, zona_de_trabalho

LIB = carregar()
TODOS = list(LIB.values())
ORIGINAIS = [t for t in TODOS if t.origem == "wattwise"]
COM_INTERVALOS = [t for t in TODOS if t.tipo not in ("recuperacao", "resistencia")]
PRINCIPAIS = ("tempo", "sweetspot", "limiar", "vo2max", "anaerobio")
ids = lambda ts: [t.id for t in ts]  # noqa: E731


@pytest.mark.parametrize("t", TODOS, ids=ids(TODOS))
def test_duracao_e_carga_plausiveis(t):
    assert 20 <= t.minutos <= 330, f"{t.id}: {t.minutos:.0f} min"
    carga_hora = t.carga / (t.minutos / 60)
    assert 20 <= carga_hora <= 100, f"{t.id}: carga/hora {carga_hora:.0f}"


@pytest.mark.parametrize("t", COM_INTERVALOS, ids=ids(COM_INTERVALOS))
def test_aquecimento_e_arrefecimento(t):
    primeiro, ultimo = t.passos[0], t.passos[-1]
    assert primeiro.rampa == "sobe" or primeiro.pct_max <= 75, f"{t.id}: sem aquecimento"
    assert primeiro.segundos >= 240, f"{t.id}: aquecimento com menos de 4 min"
    assert ultimo.pct_max <= 65, f"{t.id}: sem arrefecimento"


@pytest.mark.parametrize("t", [t for t in ORIGINAIS if t.tipo in PRINCIPAIS], ids=ids([t for t in ORIGINAIS if t.tipo in PRINCIPAIS]))
def test_trabalho_na_zona_do_tipo(t):
    zona, _ = zona_de_trabalho(t.passos)
    permitido = {t.tipo} | ({"anaerobio"} if t.tipo == "vo2max" else set()) | ({"vo2max"} if t.tipo == "limiar" else set())
    assert zona in permitido, f"{t.id}: trabalho dominante em {zona}, tipo {t.tipo}"
    lo = ZONAS_TRABALHO[t.tipo][0]
    trabalho = [p for p in t.passos if p.pct_medio >= 76 and not p.rampa and p.segundos > 15]
    assert all(p.pct_medio >= lo - 3 for p in trabalho if p.pct_medio >= 76), f"{t.id}: blocos abaixo da zona"


@pytest.mark.parametrize("t", [t for t in TODOS if t.tipo in ("vo2max", "anaerobio")],
                         ids=ids([t for t in TODOS if t.tipo in ("vo2max", "anaerobio")]))
def test_recuperacao_entre_esforcos_intensos(t):
    lista = list(t.passos)
    descansos = [lista[i].segundos for i in range(1, len(lista) - 1)
                 if lista[i].pct_medio < 76 and lista[i - 1].pct_medio >= 76 and lista[i + 1].pct_medio >= 76]
    esforcos = [p.segundos for p in lista if p.pct_medio >= 105 and not p.rampa]
    assert descansos, f"{t.id}: esforços intensos sem recuperação entre eles"
    assert statistics.median(descansos) / statistics.median(esforcos) >= 0.25, f"{t.id}: recuperação curta demais"


@pytest.mark.parametrize("t", ORIGINAIS, ids=ids(ORIGINAIS))
def test_dificuldade_pela_regra_unica(t):
    assert t.dificuldade == dificuldade_objetiva(t.passos, t.tipo), \
        f"{t.id}: dificuldade {t.dificuldade} ≠ regra {dificuldade_objetiva(t.passos, t.tipo)}"


@pytest.mark.parametrize("t", TODOS, ids=ids(TODOS))
def test_descricao_e_nome(t):
    assert t.subtitulo, f"{t.id}: sem nome de marca"
    assert len(t.descricao) >= 40, f"{t.id}: descrição curta demais"
    assert not re.search(r"trainerroad|zwift|sufferfest|wahoo systm|xert|trainingpeaks", t.descricao, re.I), \
        f"{t.id}: a descrição refere outra plataforma"


def test_nomes_unicos():
    # o mesmo nome nas versões indoor e outdoor do mesmo treino; nunca em treinos diferentes
    por_nome: dict[str, set[str]] = {}
    for t in TODOS:
        por_nome.setdefault(t.nome, set()).add(t.base)
    assert {n: b for n, b in por_nome.items() if len(b) > 1} == {}


@pytest.mark.parametrize("t", [t for t in TODOS if t.ambiente == "indoor"],
                         ids=[t.id for t in TODOS if t.ambiente == "indoor"])
def test_indoor_com_alvos_fixos_e_duracao_maxima(t):
    from ww.config import carregar as cfg
    assert all(p.pct_min == p.pct_max for p in t.passos if not p.rampa), f"{t.id}: alvo em intervalo"
    assert t.minutos <= cfg().indoor.duracao_max_min, f"{t.id}: {t.minutos:.0f} min indoor"


def test_versoes_indoor_correspondem_as_outdoor():
    for t in TODOS:
        if t.ambiente == "indoor" and t.origem == "wattwise":
            o = LIB[t.base]
            assert o.ambiente == "outdoor" and o.tipo == t.tipo and o.dificuldade == t.dificuldade
            assert [p.segundos for p in o.passos] == [p.segundos for p in t.passos]
            for po, pi in zip(o.passos, t.passos):
                assert pi.rampa or po.pct_min <= pi.pct_min <= po.pct_max


@pytest.mark.parametrize("tipo", PRINCIPAIS)
def test_cobertura_por_nivel(tipo):
    for n in range(1, 6):
        ts = [t for t in TODOS if t.tipo == tipo and t.dificuldade == n]
        assert len(ts) >= 2, f"{tipo} nível {n}: só {len(ts)} treino(s)"
        if n <= 4 and tipo != "anaerobio":
            assert any(t.minutos <= 60 for t in ts), f"{tipo} nível {n}: nenhum treino até 60 min"


def test_cobertura_forca_e_resistencia():
    for n in range(2, 6):     # a força começa no nível 2 (cadência baixa soma 1 nível)
        assert sum(t.tipo == "forca" and t.dificuldade == n for t in TODOS) >= 2, f"força nível {n}"
    for n in range(1, 6):
        assert sum(t.tipo == "resistencia" and t.dificuldade == n for t in TODOS) >= 2, f"resistência nível {n}"
