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
    # bloco contínuo (sem recuperação) → densidade 1,5 (D-055):
    (20, 80, "tempo", 2),        # 20 × 1,5 = 30 → escala tempo (20, 30, 40, 55) → nível 2
    (35, 80, "tempo", 4),        # 52,5 → nível 4
    (30, 90, "sweetspot", 4),    # 45 → escala (20, 30, 40, 55) → nível 4
    (40, 100, "limiar", 5),      # 60 → escala (15, 24, 32, 40) → nível 5
    (12, 110, "vo2max", 3),      # 18 → escala (10, 15, 20, 24) → nível 3
    (3, 130, "anaerobio", 3),    # 4,5 → escala (2, 4, 6, 8) → nível 3
    (0, 65, "resistencia", 1), (0, 50, "recuperacao", 1),
])
def test_classificacao(min_trab, pct, tipo, dif):
    from ww.treinos import Passo
    passos = [Passo(600, 55, 65)] + ([Passo(min_trab * 60, pct, pct)] if min_trab else [Passo(1800, pct, pct)])
    assert classificar(passos) == (tipo, dif)


def _intervalos(n, trab_s, pct, desc_s, cad=None):
    from ww.treinos import Passo
    out = [Passo(600, 45, 70, rampa="sobe")]
    for k in range(n):
        out.append(Passo(trab_s, pct, pct, cad))
        if k < n - 1:
            out.append(Passo(desc_s, 50, 50))
    return out + [Passo(480, 45, 60, rampa="desce")]


def test_dificuldade_com_recuperacoes_a_mao():
    from ww.treinos import dificuldade_objetiva
    # Limiar 3 × 8 min, 4 min de recuperação: razão 0,5 ≥ normal 0,3 → densidade 1 → 24 min → nível 2
    assert dificuldade_objetiva(_intervalos(3, 480, 98, 240), "limiar") == 2
    # 10 × 40/20 s: razão 0,5 < normal 0,75 → √1,5 = 1,2247 → 6,67 min × 1,2247 = 8,2 → nível 1;
    # 20 × 40/20 s (duas séries seguidas): 13,3 × 1,2247 = 16,3 → nível 3
    assert dificuldade_objetiva(_intervalos(10, 40, 120, 20), "vo2max") == 1
    assert dificuldade_objetiva(_intervalos(20, 40, 120, 20), "vo2max") == 3
    # Força: o mesmo treino (tempo 3 × 8, 4 min) em cadência baixa sobe 1 nível
    assert dificuldade_objetiva(_intervalos(3, 480, 80, 240), "tempo") == 2
    assert dificuldade_objetiva(_intervalos(3, 480, 80, 240, (55, 65)), "forca") == 3
