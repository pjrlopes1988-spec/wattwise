"""Exportação: cada treino da biblioteca, exportado e lido de volta, tem de ficar igual (D-057)."""
import pytest

from ww.exportar import nome_ficheiro, para_erg, para_mrc, para_zwo
from ww.treinos import carregar
from ww.zwo import importar_ficheiro

LIB = carregar()
TODOS = list(LIB.values())


@pytest.mark.parametrize("t", TODOS, ids=[t.id for t in TODOS])
def test_zwo_ida_e_volta(t, tmp_path):
    f = tmp_path / nome_ficheiro(t, "zwo")
    f.write_text(para_zwo(t), encoding="utf-8")
    volta = importar_ficheiro(f, indoor=t.ambiente == "indoor").treino
    assert volta is not None
    assert len(volta.passos) == len(t.passos)
    for a, b in zip(t.passos, volta.passos):
        assert a.segundos == b.segundos and a.rampa == b.rampa and a.cadencia == b.cadencia
        assert a.pct_min == pytest.approx(b.pct_min, abs=0.01) and a.pct_max == pytest.approx(b.pct_max, abs=0.01)
    assert volta.carga == pytest.approx(t.carga, rel=1e-6)
    assert volta.descricao == t.descricao


def _ler_curso(texto):
    dados = texto.split("[COURSE DATA]")[1].split("[END COURSE DATA]")[0].strip().splitlines()
    return [tuple(float(x) for x in l.split("\t")) for l in dados]


@pytest.mark.parametrize("t", TODOS, ids=[t.id for t in TODOS])
def test_erg_e_mrc(t):
    erg = _ler_curso(para_erg(t, 250))
    mrc = _ler_curso(para_mrc(t))
    assert erg[-1][0] == pytest.approx(t.minutos, abs=0.01)
    assert all(b[0] >= a[0] for a, b in zip(erg, erg[1:]))          # tempo nunca recua
    # potência média do ERG = FTP × média dos alvos (meio do intervalo; rampas lineares)
    media_pct = sum((p.pct_medio if p.rampa else p.pct_fixo) * p.segundos for p in t.passos) / t.segundos
    area = sum((b[0] - a[0]) * (a[1] + b[1]) / 2 for a, b in zip(erg, erg[1:]))
    assert area / t.minutos == pytest.approx(250 * media_pct / 100, abs=1.0)
    assert [m[0] for m in mrc] == [e[0] for e in erg]


def test_erg_a_mao():
    t = LIB["resistencia_indoor"]   # indoor: 10 min a 55%, 40 min a 67%, 10 min a 55% (alvos fixos)
    linhas = _ler_curso(para_erg(t, 200))
    assert linhas == [(0.0, 110.0), (10.0, 110.0), (10.0, 134.0), (50.0, 134.0), (50.0, 110.0), (60.0, 110.0)]
    assert 'Power="0.67"' in para_zwo(t) and "PowerLow" not in para_zwo(t)
    assert "FTP = 200" in para_erg(t, 200)
    with pytest.raises(ValueError):
        para_erg(t, 0)


def test_nome_ficheiro_sem_acentos():
    assert nome_ficheiro(LIB["limiar_2x20"], "zwo") == "Wattwise_Angliru_Limiar_2_20_min.zwo"


def test_outdoor_exporta_intervalos_indoor_exporta_fixos():
    out, ind = para_zwo(LIB["limiar_2x20"]), para_zwo(LIB["limiar_2x20_indoor"])
    assert 'PowerLow="0.95" PowerHigh="1.02"' in out
    assert 'Power="0.98"' in ind
