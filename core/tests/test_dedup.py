from datetime import datetime, timedelta

from ww.dedup import AtividadeRef, e_duplicado, principal, procurar_duplicado

T = datetime(2026, 11, 1, 9, 0)


def ref(id, inicio_s=0, dur=3600, origem="dispositivo", p=True, f=True, q=1.0, recebida_s=0):
    return AtividadeRef(id, T + timedelta(seconds=inicio_s), dur, origem, p, f, q, T + timedelta(hours=2, seconds=recebida_s))


def test_tolerancias(cfg):
    c = cfg.dados
    assert e_duplicado(ref("a"), ref("b", inicio_s=120), c)
    assert not e_duplicado(ref("a"), ref("b", inicio_s=121), c)
    assert e_duplicado(ref("a", dur=3600), ref("b", dur=3240), c)        # −10%
    assert not e_duplicado(ref("a", dur=3600), ref("b", dur=3200), c)    # −11%


def test_principal_prefere_potencia_depois_qualidade_depois_origem():
    assert principal(ref("sem_p", p=False), ref("com_p")).id == "com_p"
    assert principal(ref("q90", q=0.9), ref("q100", q=1.0)).id == "q100"
    assert principal(ref("app", origem="app"), ref("disp")).id == "disp"
    assert principal(ref("segunda", recebida_s=10), ref("primeira")).id == "primeira"


def test_procurar_escolhe_o_mais_proximo(cfg):
    existentes = [ref("longe", inicio_s=100), ref("perto", inicio_s=-20), ref("outra", inicio_s=7200)]
    assert procurar_duplicado(ref("nova"), existentes, cfg.dados).id == "perto"
    assert procurar_duplicado(ref("nova", inicio_s=4000), existentes, cfg.dados) is None
