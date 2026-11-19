import pytest

from ww.config import carregar as carregar_cfg
from ww.plano import alta_intensidade
from ww.zwo import classificar, importar_ficheiro

ZWO = """<?xml version="1.0" encoding="UTF-8"?>
<workout_file><author>Teste</author><name>Teste 3x5</name><description>d</description><sportType>bike</sportType>
<tags><tag name="Extra"/></tags>
<workout>
  <Ramp PowerLow="0.45" PowerHigh="0.75" Duration="600"/>
  <IntervalsT Repeat="3" OnDuration="300" OffDuration="120" OnPower="1.0" OffPower="0.5" Cadence="55" CadenceResting="90"/>
  <SteadyState Power="0.6" Duration="300"/>
</workout></workout_file>"""


def test_importa_e_calcula_carga_a_mao(tmp_path):
    f = tmp_path / "t.zwo"
    f.write_text(ZWO, encoding="utf-8")
    t = importar_ficheiro(f).treino
    assert t.id == "paulo_teste_3x5" and t.origem == "paulo"
    assert len(t.passos) == 1 + 3 * 2 + 1
    assert t.passos[0].rampa == "sobe" and t.passos[1].cadencia == (55, 55) and t.passos[2].cadencia == (90, 90)
    # rampa 45→75%: 10 min × (0,45² + 0,45·0,75 + 0,75²)/3 = (1/6) × 0,3675 × 100 = 6,125
    # 3 × 5 min a 100% = 25; 3 × 2 min a 50% = 2,5; 5 min a 60% = 3
    assert t.carga == pytest.approx(6.125 + 25 + 2.5 + 3)
    # 15 min ao limiar em cadência baixa → força, mas conta como alta intensidade
    assert t.tipo == "forca"
    assert alta_intensidade(t, carregar_cfg())


def test_fora_da_bicicleta(tmp_path):
    f = tmp_path / "m.zwo"
    f.write_text("<workout_file><name>Core</name><sportType>run</sportType><workout/></workout_file>")
    r = importar_ficheiro(f)
    assert r.treino is None and r.motivo == "fora da bicicleta"


def test_recusa_xml_com_entidades(tmp_path):
    f = tmp_path / "x.zwo"
    f.write_text('<!DOCTYPE a [<!ENTITY x "y">]><workout_file/>')
    with pytest.raises(ValueError):
        importar_ficheiro(f)


@pytest.mark.parametrize("min_trab,pct,tipo,dif", [
    (20, 80, "tempo", 1), (35, 80, "tempo", 3), (30, 90, "sweetspot", 2), (40, 100, "limiar", 4),
    (12, 110, "vo2max", 2), (3, 130, "anaerobio", 2), (0, 65, "resistencia", 1), (0, 50, "recuperacao", 1),
])
def test_classificacao(min_trab, pct, tipo, dif):
    from ww.treinos import Passo
    passos = [Passo(600, 55, 65)] + ([Passo(min_trab * 60, pct, pct)] if min_trab else [Passo(1800, pct, pct)])
    assert classificar(passos) == (tipo, dif)
