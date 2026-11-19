from dataclasses import replace
from datetime import date

import pytest

from cenarios import CENARIOS, HOJE
from ww.perfil import Atleta, Equipamento, Objetivo, PerfilInvalido, Valor, completar, nivel_regras, precisa_de_teste, validar
from ww.treinos import carregar as carregar_lib

BASE = CENARIOS["intermedio_prova_16_semanas"]


def test_cenarios_validos(cfg):
    for a in CENARIOS.values():
        validar(a, HOJE, cfg)


@pytest.mark.parametrize("alteracao,erro", [
    (dict(data_nascimento=date(2017, 1, 1)), "idade mínima"),
    (dict(peso_kg=10), "peso"),
    (dict(disponibilidade=(0, 0, 0, 0, 0, 0, 20)), "pelo menos um dia"),
    (dict(dia_longo=2), "dia longo"),
    (dict(objetivo=Objetivo("prova")), "sem data"),
    (dict(objetivo=Objetivo("prova", date(2026, 1, 1))), "já passou"),
    (dict(fc_repouso=Valor(168, "atleta"), fc_limiar=Valor(168, "atleta")), "FC de repouso"),
])
def test_perfil_invalido(cfg, alteracao, erro):
    with pytest.raises(PerfilInvalido, match=erro):
        validar(replace(BASE, **alteracao), HOJE, cfg)


def test_menor_de_14_precisa_de_consentimento(cfg):
    crianca = replace(BASE, data_nascimento=date(2014, 1, 1))     # 12 anos
    with pytest.raises(PerfilInvalido, match="responsável"):
        validar(crianca, HOJE, cfg)
    validar(replace(crianca, consentimento_responsavel=True), HOJE, cfg)


def test_menor_usa_regras_de_iniciante(cfg):
    assert nivel_regras(CENARIOS["juvenil_14_anos"], HOJE, cfg) == "iniciante"
    assert nivel_regras(BASE, HOJE, cfg) == "intermedio"


def test_estimativas_conservadoras_e_marcadas(cfg):
    a = completar(CENARIOS["iniciante_sem_potenciometro"], HOJE, cfg)
    # FTP: 2,0 W/kg × 0,88 (feminino) × 61 kg = 107 W; FC máx. Tanaka: 208 − 0,7 × 36 = 182,8 → 183
    assert a.ftp == Valor(107, "estimado")
    assert a.fc_max == Valor(183, "estimado")
    assert a.fc_limiar == Valor(165, "estimado")   # 0,90 × 183 = 164,7
    assert a.fc_repouso.estimado
    assert precisa_de_teste(a) == "fc_limiar"      # sem potenciómetro


def test_estimativas_nunca_substituem_valores_do_atleta(cfg):
    a = completar(BASE, HOJE, cfg)
    assert a.ftp == Valor(250, "atleta") and a.fc_max == Valor(185, "atleta")
    assert precisa_de_teste(a) is None


def test_biblioteca_carga_a_mao():
    lib = carregar_lib()
    # Resistência 60 min: 10 min a 55% + 40 min a 67% + 10 min a 55%
    # = (10/60)·0,3025·100 × 2 + (40/60)·0,4489·100 = 10,083 + 29,927 = 40,01
    assert lib["resistencia"].carga == pytest.approx(10 / 60 * 30.25 * 2 + 40 / 60 * 44.89)
    # Escalar para 120 min: passo central passa a 100 min
    r = lib["resistencia"].com_duracao(120)
    assert r.minutos == 120
    assert r.passos[1].segundos == 100 * 60
    # Repetições expandidas: sweet spot 3 × 10 tem 1 + 3×2 + 1 = 8 passos
    assert len(lib["sweetspot_3x10"].passos) == 8


def test_biblioteca_sem_erros():
    lib = carregar_lib()
    assert {"resistencia", "recuperacao", "teste_20min", "teste_fc_limiar_30min"} <= set(lib)


def test_todos_os_treinos_tem_nome_de_marca():
    lib = carregar_lib()
    sem = [t.id for t in lib.values() if not t.subtitulo]
    assert sem == [], f"treinos sem nome de marca em config/nomes_treinos.yaml: {sem}"
    assert lib["limiar_2x20"].titulo == "Angliru · Limiar 2 × 20 min"
    assert lib["paulo_torque_ao_limiar_10x1"].titulo == "Guimarães · Torque ao Limiar 10x1"
    assert len({t.nome for t in lib.values()}) == len({t.base for t in lib.values()})   # um nome por treino-base
    assert lib["limiar_2x20_indoor"].titulo == "Angliru · Limiar 2 × 20 min"
