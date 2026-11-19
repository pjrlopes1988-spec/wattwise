import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend"))
sys.path.insert(0, str(RAIZ / "core" / "src"))
sys.path.insert(0, str(RAIZ / "core" / "tests"))

from app.main import criar_app  # noqa: E402


@pytest.fixture
def cliente():
    return TestClient(criar_app("sqlite:///:memory:"))


PERFIL = {
    "nome": "Atleta de Teste", "data_nascimento": "1985-06-02", "sexo": "M", "peso_kg": 74,
    "nivel": "intermedio", "disciplina": "estrada", "objetivo": {"tipo": "ftp"},
    "disponibilidade": [60, 90, 0, 90, 0, 180, 240], "dia_longo": 6,
    "equipamento": {"potenciometro": True, "rolo_inteligente": True, "cinta_fc": True},
    "ftp": {"valor": 250, "fonte": "atleta"}, "fc_limiar": {"valor": 165, "fonte": "atleta"},
    "fc_max": {"valor": 185, "fonte": "atleta"}, "fc_repouso": {"valor": 50, "fonte": "atleta"},
}


@pytest.fixture
def atleta(cliente):
    r = cliente.post("/atletas", json={"perfil": PERFIL, "consentimento_dados_saude": True})
    assert r.status_code == 201, r.text
    return r.json()["id"]
