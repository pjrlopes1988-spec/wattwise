import pytest
import yaml

from ww.config import CAMINHO_POR_DEFEITO, carregar


def test_carrega_e_tem_versao(cfg):
    assert len(cfg.versao) == 12
    assert cfg.carga_forma.constante_condicao_dias == 42
    assert cfg.carga_forma.constante_fadiga_dias == 7


def test_versao_muda_quando_o_ficheiro_muda(tmp_path):
    original = CAMINHO_POR_DEFEITO.read_text()
    alterado = tmp_path / "m.yaml"
    alterado.write_text(original.replace("constante_fadiga_dias: 7", "constante_fadiga_dias: 8"))
    assert carregar(alterado).versao != carregar().versao


def test_zonas_nao_crescentes_sao_rejeitadas(tmp_path):
    dados = yaml.safe_load(CAMINHO_POR_DEFEITO.read_text())
    dados["potencia"]["zonas_coggan_limites_pct"] = [55, 75, 70, 105, 120, 150]
    f = tmp_path / "m.yaml"
    f.write_text(yaml.safe_dump(dados))
    with pytest.raises(ValueError):
        carregar(f)


def test_campo_desconhecido_e_rejeitado(tmp_path):
    dados = yaml.safe_load(CAMINHO_POR_DEFEITO.read_text())
    dados["potencia"]["campo_inventado"] = 1
    f = tmp_path / "m.yaml"
    f.write_text(yaml.safe_dump(dados))
    with pytest.raises(ValueError):
        carregar(f)
