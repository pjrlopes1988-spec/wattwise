"""Explicações (spec 7.5): só números do registo; alarme manda ao médico; dados em falta ditos."""
import re

import pytest

from ww.explicacao import REGRAS, explicar


def reg(sinais=(), regras=("verde_mantem_treino",), falta=(), estado="verde"):
    return {"sinais": [{"codigo": c, "valor": v, "limiar": l, "forte": False} for c, v, l in sinais],
            "regras": list(regras), "dados_em_falta": list(falta), "estado": estado}


def test_verde():
    assert explicar(reg()) == "Está tudo dentro do teu normal: fazemos o treino planeado."


def test_amarelo_com_numeros_do_registo():
    t = explicar(reg([("sono_curto", 5.7, 6.0)], ["amarelo_versao_mais_facil"], estado="amarelo"))
    assert t == "Dormiste 5,7 h (abaixo de 6 h). Mantemos o tipo de treino numa versão mais leve."


def test_dois_sinais():
    t = explicar(reg([("sono_curto", 5.0, 6.0), ("cansaco", 4, 4)], ["vermelho_recuperacao_ativa"], estado="vermelho"))
    assert t.startswith("Dormiste 5 h (abaixo de 6 h) e indicaste cansaço 4/5.")


def test_alarme_so_manda_ao_medico():
    t = explicar(reg([("alarme", "dor_peito", None)], ["alarme_bloqueia_treino"], estado="bloqueado"))
    assert t == REGRAS["alarme_bloqueia_treino"] and "112" in t


def test_dados_em_falta():
    assert explicar(reg(falta=("vfc", "questionario"))).endswith("(Decidido sem VFC nem questionário.)")


@pytest.mark.parametrize("regra", list(REGRAS))
def test_numeros_so_do_registo(regra):
    # nenhum texto-modelo inventa números (exceto o 112 do alarme)
    assert not re.findall(r"\d", REGRAS[regra].replace("112", ""))
