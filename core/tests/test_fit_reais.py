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
FICHEIRO_ESTRADA = PASTA / "wahoo_roam_estrada_2026-11-14.fit"
FICHEIRO_Z3 = PASTA / "wahoo_roam_rolo_z3_2026-11-09.fit"

# Os ficheiros reais são dados pessoais e não estão no repositório (D-036): sem eles, salta.
precisa_rolo = pytest.mark.skipif(not FICHEIRO_ROLO.exists(), reason="ficheiro FIT real não disponível (D-036)")
precisa_z3 = pytest.mark.skipif(not FICHEIRO_Z3.exists(), reason="ficheiro FIT real não disponível (D-036)")
precisa_estrada = pytest.mark.skipif(not FICHEIRO_ESTRADA.exists(), reason="ficheiro FIT real não disponível (D-036)")


@pytest.fixture(scope="module")
def rolo():
    # Wahoo ELEMNT ROAM, rolo, 17/11/2026, 75 min, potência sem FC.
    # Treino planeado: 15 min aquecimento, 12 min 297–310 W, 4 min 185 W, 12 min 297–310 W
    # (interrompido por paragens), 4 min 185 W, 12 min 209–243 W, 5 min 169 W.
    return ler_ficheiro(FICHEIRO_ROLO)


@precisa_rolo
def test_leitura(rolo):
    assert rolo.subdesporto == "indoor_cycling"
    assert rolo.tem_potencia and not rolo.tem_fc
    assert abs(rolo.duracao_s - 4492) <= 5   # tempo de timer do Wahoo


@precisa_rolo
def test_metricas_contra_o_intervals(rolo, cfg):
    # Valores do Intervals.icu (19/11/2026), com o FTP definido lá: 338 W (o Wahoo tem 334).
    # O Intervals usa o tempo em movimento (~4215 s); o Wahoo usa o tempo total (NP 240, TSS 63,9).
    r = analisar(rolo, Fisiologia("M", ftp=338), cfg)
    assert r.potencia_media == pytest.approx(211, rel=0.01)
    assert r.potencia_ponderada == pytest.approx(242, rel=0.01)
    assert r.intensidade == pytest.approx(0.716, rel=0.01)
    assert r.carga == pytest.approx(60, rel=0.02)
    assert r.fonte_carga == "potencia"
    assert abs(r.tempo_movimento_s - 4215) <= 10
    for d, iv in {5: 413, 60: 318, 300: 303, 1200: 278, 3600: 223}.items():
        assert r.curva[d] == pytest.approx(iv, rel=0.01), d


@precisa_rolo
def test_qualidade_e_sem_suspeitas(rolo, cfg):
    limpa, rel = limpar(rolo, cfg.qualidade)
    assert rel.indice > 0.99
    assert avaliar(limpa, cfg.qualidade) == []


@precisa_rolo
def test_primeiro_bloco_de_12_min_e_um_so_intervalo(rolo, cfg):
    limpa, _ = limpar(rolo, cfg.qualidade)
    iv = detetar(limpa, cfg.intervalos, ftp=334)
    primeiro = iv[0]
    assert abs(primeiro.duracao_s - 720) <= 15
    assert 297 <= primeiro.potencia_media <= 310
    # o 2.º bloco foi interrompido por paragens: começa ~16 min depois do 1.º
    assert abs(iv[1].inicio_s - (primeiro.inicio_s + 960)) <= 30


@pytest.fixture(scope="module")
def estrada():
    # Wahoo ELEMNT ROAM, estrada, 14/11/2026, 2 h 48 min, 54,6 km, Quarq + cinta de FC.
    return ler_ficheiro(FICHEIRO_ESTRADA)


@precisa_estrada
def test_estrada_contra_o_intervals(estrada, cfg):
    # Intervals.icu: IF 0,659 com NP 224 → FTP ≈ 340 W nesse dia.
    assert estrada.fonte_fc == "cinta"
    r = analisar(estrada, Fisiologia("M", ftp=224 / 0.659), cfg)
    assert r.potencia_media == pytest.approx(175, rel=0.01)
    assert r.potencia_ponderada == pytest.approx(224, rel=0.01)
    assert r.carga == pytest.approx(121, rel=0.02)
    assert r.fc_media == pytest.approx(128, rel=0.01)
    for d, iv in {5: 544, 60: 352, 300: 283, 1200: 229, 3600: 192}.items():
        assert r.curva[d] == pytest.approx(iv, rel=0.01), d


@precisa_estrada
def test_estrada_qualidade(estrada, cfg):
    limpa, rel = limpar(estrada, cfg.qualidade)
    assert rel.indice > 0.99
    assert avaliar(limpa, cfg.qualidade) == []


@pytest.fixture(scope="module")
def z3():
    # Wahoo ELEMNT ROAM, rolo, 09/11/2026, 57 min, cinta de FC.
    # 10 min a ~205 W, 5 × (5 min a ~270 W em cadência baixa + 3 min a ~190 W), arrefecimento.
    return ler_ficheiro(FICHEIRO_Z3)


@precisa_z3
def test_z3_contra_o_intervals(z3, cfg):
    r = analisar(z3, Fisiologia("M", ftp=338), cfg)
    assert r.potencia_media == pytest.approx(226, rel=0.01)
    assert r.potencia_ponderada == pytest.approx(237, rel=0.01)
    assert r.intensidade == pytest.approx(0.701, rel=0.01)
    assert r.carga == pytest.approx(47, rel=0.02)
    assert r.fc_media == pytest.approx(138, rel=0.01)
    for d, iv in {5: 657, 60: 305, 300: 277, 1200: 247}.items():
        assert r.curva[d] == pytest.approx(iv, rel=0.01), d
    assert r.curva[3600] is None   # atividade com menos de 60 min


@precisa_z3
def test_z3_desacoplamento(z3, cfg):
    # Intervals.icu: 10,9%. Método clássico (média ÷ média por metade) dá 11,8% (D-040).
    from ww.metrics.hr import desacoplamento
    limpa, _ = limpar(z3, cfg.qualidade)
    assert desacoplamento(limpa.potencia, limpa.fc) == pytest.approx(10.9, abs=1.5)


@precisa_z3
def test_z3_cinco_intervalos_como_no_intervals(z3, cfg):
    # Tabela de intervalos do Intervals.icu: (duração s, potência média W)
    intervals = [(301, 272), (293, 271), (301, 269), (295, 270), (294, 270)]
    limpa, _ = limpar(z3, cfg.qualidade)
    iv = detetar(limpa, cfg.intervalos, ftp=338)
    assert len(iv) == 5
    for meu, (dur, pot) in zip(iv, intervals):
        assert abs(meu.duracao_s - dur) <= 10
        assert meu.potencia_media == pytest.approx(pot, rel=0.03)


@precisa_z3
@precisa_estrada
def test_carga_fc_contra_o_intervals(z3, estrada, cfg):
    # Intervals.icu (HRSS): 09/11 → 50; 14/11 → 118. Perfil: FC limiar 168, FC máx. 180.
    # A FC de repouso configurada no Intervals (168) é impossível; um único valor real de
    # ~42 bpm explica os dois treinos a ≤ 1,1% (D-041).
    from ww.metrics.hr import carga_fc
    b = cfg.frequencia_cardiaca.hrss_b_masculino
    for serie, iv in ((z3, 50), (estrada, 118)):
        limpa, _ = limpar(serie, cfg.qualidade, fc_max=180)
        v = carga_fc(limpa.fc, fc_repouso=42, fc_limiar=168, fc_max=180, b=b)
        assert v == pytest.approx(iv, rel=0.02)
