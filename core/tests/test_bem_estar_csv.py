from datetime import date

from ww.bem_estar_csv import ler


def test_formato_base_com_ponto_e_virgula_e_virgula_decimal():
    r = ler("data;fonte;rmssd;fc_repouso;sono_h\n2026-11-01;garmin;62,5;48;7,5\n02/11/2026;;58;;\n", fonte="manual")
    assert r.erros == []
    assert [(m.data, m.fonte, m.metrica, m.valor_ms) for m in r.vfc] == [
        (date(2026, 11, 1), "garmin", "rmssd", 62.5),
        (date(2026, 11, 2), "manual", "rmssd", 58.0),
    ]
    assert r.fc_repouso == {date(2026, 11, 1): 48.0}
    assert r.sono_h == {date(2026, 11, 1): 7.5}


def test_mapa_de_colunas_de_outra_app():
    r = ler("Date,HRV,Resting HR\n2026-11-01,70,50\n", mapa={"Date": "data", "HRV": "sdnn", "Resting HR": "fc_repouso"},
            fonte="apple_health")
    assert r.vfc[0].metrica == "sdnn" and r.vfc[0].fonte == "apple_health"
    assert r.fc_repouso[date(2026, 11, 1)] == 50.0


def test_valores_impossiveis_sao_rejeitados_e_reportados():
    r = ler("data;rmssd;fc_repouso\n2026-11-01;900;10\n2026-11-02;abc;50\nontem;50;50\n")
    assert r.vfc == []
    assert r.fc_repouso == {date(2026, 11, 2): 50.0}
    assert len(r.erros) == 4
    assert any("linha 4" in e and "data inválida" in e for e in r.erros)


def test_sem_coluna_data():
    r = ler("dia;rmssd\n1;50\n")
    assert r.erros and "data" in r.erros[0]
