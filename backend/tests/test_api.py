"""API: cada caminho que a app vai usar, de ponta a ponta."""
from datetime import date, timedelta

from conftest import PERFIL
from fit_sintetico import gerar


def _dia_com_treino(cliente, aid, papel=("sessao_chave",)):
    p = cliente.get(f"/atletas/{aid}/plano").json()
    for s in p["semanas"]:
        for t in s["treinos"]:
            if t["papel"] in papel:
                return t["data"], t
    raise AssertionError("sem treino")


def test_registo_exige_consentimento_e_perfil_valido(cliente):
    assert cliente.post("/atletas", json={"perfil": PERFIL, "consentimento_dados_saude": False}).status_code == 400
    mau = {**PERFIL, "data_nascimento": "2020-01-01"}
    assert cliente.post("/atletas", json={"perfil": mau, "consentimento_dados_saude": True}).status_code == 422
    r = cliente.post("/atletas", json={"perfil": PERFIL, "consentimento_dados_saude": True})
    assert r.status_code == 201
    assert r.json()["sugestoes"] == {"onde_treina": "ambos", "ciclo": "3+1", "intensidade": 3}


def test_plano_com_duas_versoes_e_alvos(cliente, atleta):
    _, t = _dia_com_treino(cliente, atleta)
    amb = {o["ambiente"]: o for o in t["opcoes"]}
    assert set(amb) == {"outdoor", "indoor"}            # tem rolo inteligente → as duas versões
    trab = [x for x in amb["indoor"]["passos"] if x["pct_min"] >= 76 and not x["rampa"]][0]
    assert " W" in trab["alvo"] and "–" not in trab["alvo"].split(" W")[0]    # indoor: valor fixo
    trab_o = [x for x in amb["outdoor"]["passos"] if x["pct_min"] >= 76 and not x["rampa"]][0]
    assert "–" in trab_o["alvo"]                                              # outdoor: intervalo


def test_hoje_sem_dados_verde_e_auditoria(cliente, atleta):
    d, _ = _dia_com_treino(cliente, atleta)
    h = cliente.get(f"/atletas/{atleta}/hoje", params={"data": d}).json()
    assert h["estado"] == "verde" and "questionario" in h["dados_em_falta"]
    assert h["explicacao"].startswith("Está tudo dentro do teu normal")
    assert h["treino"]["opcoes"]
    dados = cliente.get(f"/atletas/{atleta}/exportar").json()
    assert dados["decisoes"][0]["data"] == d and dados["decisoes"][0]["registo"]["regras"]


def test_sono_curto_dia_amarelo_com_explicacao(cliente, atleta):
    d, _ = _dia_com_treino(cliente, atleta)
    assert cliente.post(f"/atletas/{atleta}/manha", json={"data": d, "sono_h": 5.5, "cansaco": 2}).status_code == 201
    h = cliente.get(f"/atletas/{atleta}/hoje", params={"data": d}).json()
    assert h["estado"] == "amarelo"
    assert h["explicacao"].startswith("Dormiste 5,5 h (abaixo de 6 h).")
    assert h["treino"]["opcoes"][0]["carga"] < h["treino_original"]["opcoes"][0]["carga"]


def test_alarme_bloqueia(cliente, atleta):
    d, _ = _dia_com_treino(cliente, atleta)
    r = cliente.post(f"/atletas/{atleta}/manha", json={"data": d, "alarmes": ["dor_peito"]})
    assert r.json()["alarme"] is True
    h = cliente.get(f"/atletas/{atleta}/hoje", params={"data": d}).json()
    assert h["estado"] == "bloqueado" and h["procurar_medico"] and h["treino"] is None
    assert "médico" in h["explicacao"]


def test_escolha_da_versao(cliente, atleta):
    d, _ = _dia_com_treino(cliente, atleta)
    assert cliente.post(f"/atletas/{atleta}/hoje/escolha", json={"data": d, "ambiente": "indoor"}).status_code == 409
    cliente.get(f"/atletas/{atleta}/hoje", params={"data": d})
    r = cliente.post(f"/atletas/{atleta}/hoje/escolha", json={"data": d, "ambiente": "indoor"})
    assert r.status_code == 200 and r.json()["treino"]["id"].endswith("_indoor")
    assert cliente.post(f"/atletas/{atleta}/hoje/escolha", json={"data": d, "ambiente": "lua"}).status_code == 422


def test_upload_fit_e_duplicado(cliente, atleta):
    fit = gerar([(i, 250, 160, 90) for i in range(3600)])          # 1 h ao FTP (250) → carga 100
    r = cliente.post(f"/atletas/{atleta}/atividades", files={"ficheiro": ("a.fit", fit)})
    assert r.status_code == 201, r.text
    j = r.json()
    assert round(j["carga"]) == 100 and j["fonte_carga"] == "potencia" and j["duplicado_de"] is None
    r2 = cliente.post(f"/atletas/{atleta}/atividades", files={"ficheiro": ("b.fit", fit)})
    assert r2.json()["duplicado_de"] == j["id"]
    assert cliente.post(f"/atletas/{atleta}/atividades", files={"ficheiro": ("x.fit", b"lixo")}).status_code == 422


def test_ftp_manual(cliente, atleta):
    assert cliente.put(f"/atletas/{atleta}/ftp", json={"valor": 40}).status_code == 422          # 0,5 W/kg
    fit = gerar([(i, 250, 160, 90) for i in range(1200)])
    cliente.post(f"/atletas/{atleta}/atividades", files={"ficheiro": ("a.fit", fit)})            # eFTP ~ 240
    r = cliente.put(f"/atletas/{atleta}/ftp", json={"valor": 320})
    assert r.json()["guardado"] is False and r.json()["avisos"][0].startswith("diferenca_grande_eftp")
    r = cliente.put(f"/atletas/{atleta}/ftp", json={"valor": 320, "confirmar": True})
    assert r.json()["guardado"] is True
    assert cliente.get(f"/atletas/{atleta}").json()["perfil"]["ftp"] == {"valor": 320.0, "fonte": "atleta"}


def test_prova_A_muda_o_plano(cliente, atleta):
    data_prova = (date.today() + timedelta(days=70)).isoformat()
    r = cliente.post(f"/atletas/{atleta}/provas", json={"nome": "Granfondo", "prioridade": "A", "data": data_prova, "duracao_h": 4})
    assert r.status_code == 201
    p = cliente.get(f"/atletas/{atleta}/plano").json()
    assert p["fim"] == data_prova and p["semanas"][-1]["fase"] == "afinacao"
    assert cliente.post(f"/atletas/{atleta}/provas", json={"nome": "X", "prioridade": "E", "data": data_prova}).status_code == 422


def test_exportar_zwo(cliente, atleta):
    d, _ = _dia_com_treino(cliente, atleta)
    r = cliente.get(f"/atletas/{atleta}/treinos/{d}/exportar", params={"formato": "zwo", "ambiente": "indoor"})
    assert r.status_code == 200 and "<workout_file>" in r.text and "Wattwise_" in r.headers["content-disposition"]
    erg = cliente.get(f"/atletas/{atleta}/treinos/{d}/exportar", params={"formato": "erg"})
    assert "FTP = 250" in erg.text


def test_rgpd_exportar_e_apagar(cliente, atleta):
    cliente.post(f"/atletas/{atleta}/manha", json={"sono_h": 7})
    dados = cliente.get(f"/atletas/{atleta}/exportar").json()
    assert dados["consentimentos"][0]["tipo"] == "dados_saude" and dados["bem_estar"]
    assert cliente.delete(f"/atletas/{atleta}").status_code == 204
    assert cliente.get(f"/atletas/{atleta}").status_code == 404
    assert cliente.get(f"/atletas/{atleta}/exportar").status_code == 404
