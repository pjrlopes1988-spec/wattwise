import csv

import pytest

from fit_sintetico import gerar
from ww.relatorio import comparar, main


@pytest.fixture
def pasta(tmp_path):
    d = tmp_path / "fit"
    d.mkdir()
    # 1 h a 250 W / 165 bpm (= FTP e FC limiar) e uma de 30 min a 200 W
    (d / "a.fit").write_bytes(gerar([(i, 250, 165, 90) for i in range(3600)]))
    (d / "b.fit").write_bytes(gerar([(i, 200, 150, 90) for i in range(1800)]))
    (d / "estragado.fit").write_bytes(b"lixo")
    return d


def ler(p):
    with p.open(encoding="utf-8-sig") as fh:
        return {r["ficheiro"]: r for r in csv.DictReader(fh, delimiter=";")}


def test_analisar_gera_csv(pasta, tmp_path, capsys):
    saida = tmp_path / "v.csv"
    rc = main(["analisar", str(pasta), "--ftp", "250", "--lthr", "165", "--fcmax", "190",
               "--fcrep", "50", "--sexo", "M", "--peso", "70", "--saida", str(saida)])
    assert rc == 0
    r = ler(saida)
    assert r["a.fit"]["ww_carga"] == "100,0"
    assert r["a.fit"]["ww_carga_fc"] == "100,0"
    assert r["a.fit"]["ww_intensidade"] == "1,000"
    assert r["a.fit"]["ww_melhor_60min"] == "250,0"
    assert r["a.fit"]["fonte_carga"] == "potencia"
    assert r["a.fit"]["iv_carga"] == ""
    assert r["b.fit"]["ww_melhor_60min"] == ""
    assert r["estragado.fit"]["erro"]
    assert "eFTP" in capsys.readouterr().out


def test_comparar(pasta, tmp_path):
    saida = tmp_path / "v.csv"
    main(["analisar", str(pasta), "--ftp", "250", "--sexo", "M", "--peso", "70", "--saida", str(saida)])
    linhas = list(ler(saida).values())
    linhas[0]["iv_carga"] = "102"      # a.fit: 100 vs 102 → −2%
    linhas[1]["iv_carga"] = "40"       # b.fit: 32 vs 40 → −20%
    with saida.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0]), delimiter=";")
        w.writeheader()
        w.writerows(linhas)
    texto, acima = comparar(saida, 5)
    assert acima == 1
    assert any("b.fit" in t and "-20,0%".replace(",", ".") in t for t in texto)
