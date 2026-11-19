"""Ficheiros FIT reais de referência (spec 10.2).

Valores de referência: os que o próprio dispositivo gravou na sessão. Tolerância de 1%
(arredondamentos e pequenas diferenças de método); a validação contra o Intervals.icu
é feita à parte com `python -m ww.relatorio`.
"""

from pathlib import Path

import pytest

from ww.analise import Fisiologia, analisar
from ww.fit.reader import ler_ficheiro
from ww.metrics.intervalos import detetar
from ww.quality.clean import limpar
from ww.quality.suspeitas import avaliar

PASTA = Path(__file__).parent / "fixtures" / "fit"


FICHEIRO_ROLO = PASTA / "wahoo_roam_rolo_2026-11-17.fit"

# Os ficheiros reais são dados pessoais e não estão no repositório (D-036): sem eles, salta.
pytestmark = pytest.mark.skipif(not FICHEIRO_ROLO.exists(), reason="ficheiro FIT real não disponível (D-036)")


@pytest.fixture(scope="module")
def rolo():
    # Wahoo ELEMNT ROAM, rolo, 17/11/2026, 75 min, potência sem FC.
    # Treino planeado: 15 min aquecimento, 12 min 297–310 W, 4 min 185 W, 12 min 297–310 W
    # (interrompido por paragens), 4 min 185 W, 12 min 209–243 W, 5 min 169 W.
    # Valores do Wahoo: FTP 334, média 211 W, NP 240 W, IF 0,717, TSS 63,9.
    return ler_ficheiro(FICHEIRO_ROLO)


def test_leitura(rolo):
    assert rolo.subdesporto == "indoor_cycling"
    assert rolo.tem_potencia and not rolo.tem_fc
    assert abs(rolo.duracao_s - 4492) <= 5   # tempo de timer do Wahoo


def test_metricas_contra_o_wahoo(rolo, cfg):
    r = analisar(rolo, Fisiologia("M", ftp=334), cfg)
    assert r.potencia_ponderada == pytest.approx(240, rel=0.01)
    assert r.potencia_media == pytest.approx(211, rel=0.01)
    assert r.intensidade == pytest.approx(0.717, rel=0.01)
    assert r.carga == pytest.approx(63.9, rel=0.01)
    assert r.fonte_carga == "potencia"


def test_qualidade_e_sem_suspeitas(rolo, cfg):
    limpa, rel = limpar(rolo, cfg.qualidade)
    assert rel.indice > 0.99
    assert avaliar(limpa, cfg.qualidade) == []


def test_primeiro_bloco_de_12_min_e_um_so_intervalo(rolo, cfg):
    limpa, _ = limpar(rolo, cfg.qualidade)
    iv = detetar(limpa, cfg.intervalos, ftp=334)
    primeiro = iv[0]
    assert abs(primeiro.duracao_s - 720) <= 15
    assert 297 <= primeiro.potencia_media <= 310
    # o 2.º bloco foi interrompido por paragens: começa ~16 min depois do 1.º
    assert abs(iv[1].inicio_s - (primeiro.inicio_s + 960)) <= 30
