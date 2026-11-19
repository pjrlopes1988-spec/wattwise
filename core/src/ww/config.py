"""Carregamento e validação de config/motor.yaml.

Um ficheiro inválido levanta exceção no arranque: nunca chega aos atletas.
A versão (hash do conteúdo) é registada em cada cálculo/decisão.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

CAMINHO_POR_DEFEITO = Path(__file__).resolve().parents[3] / "config" / "motor.yaml"


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _crescente(v: list[float]) -> list[float]:
    if any(b <= a for a, b in zip(v, v[1:])):
        raise ValueError("os limites das zonas têm de ser estritamente crescentes")
    return v


class Potencia(_Base):
    zonas_coggan_limites_pct: list[float] = Field(min_length=6, max_length=6)
    np_janela_s: int = Field(ge=1)
    curva_duracoes_s: list[int]

    _v = field_validator("zonas_coggan_limites_pct")(_crescente)


class FrequenciaCardiaca(_Base):
    zonas_friel_limites_pct: list[float]
    zonas_friel_nomes: list[str]
    hrss_b_masculino: float = Field(gt=0)
    hrss_b_feminino: float = Field(gt=0)
    desacoplamento_bom_pct: float

    _v = field_validator("zonas_friel_limites_pct")(_crescente)

    def model_post_init(self, __context: object) -> None:
        if len(self.zonas_friel_nomes) != len(self.zonas_friel_limites_pct) + 1:
            raise ValueError("zonas_friel_nomes tem de ter mais um elemento do que os limites")


class FaixasFrescura(_Base):
    transicao_acima: float
    fresco_acima: float
    neutra_acima: float
    otima_acima: float


class CargaForma(_Base):
    constante_condicao_dias: float = Field(gt=0)
    constante_fadiga_dias: float = Field(gt=0)
    fator_media: Literal["linear", "exponencial"]
    condicao_minima_para_pct: float = Field(ge=0)
    rpe_limiar: float = Field(gt=0, le=10)
    faixas_frescura_pct: FaixasFrescura


class Populacao(_Base):
    w_linha_j: float = Field(gt=0)
    pmax_w_por_kg: float = Field(gt=0)


class ModeloPotenciaCritica(_Base):
    duracao_minima_esforco_s: int = Field(gt=0)
    duracao_maxima_esforco_s: int = Field(gt=0)
    ftp_fator_cp: float = Field(gt=0.5, le=1.2)
    populacao: Populacao


class Eftp(_Base):
    metodo: Literal["morton_1_esforco", "morton_3p", "monod_2p"]
    duracoes_curva_s: list[int]
    janela_perfil_dias: int = Field(gt=0)
    w_linha_plausivel_j: tuple[float, float]
    decaimento_carencia_dias: int = Field(ge=0)
    decaimento_pct_por_semana: float = Field(ge=0, lt=10)
    subida_sem_confirmacao_max_pct: float = Field(ge=0)
    alteracao_minima_pct: float = Field(ge=0)
    dias_para_resposta: int = Field(ge=1)
    fator_teste_20min: float = Field(gt=0.8, le=1.0)


class Recuperacao(_Base):
    vfc_janela_media_dias: int = Field(ge=1)
    vfc_minimo_valores_na_media: int = Field(ge=1)
    vfc_janela_faixa_dias: int = Field(ge=14)
    vfc_largura_faixa_dp: float = Field(gt=0)
    vfc_dias_calibracao: int = Field(ge=7)
    fcr_largura_faixa_dp: float = Field(gt=0)
    fcr_dias_elevada_alerta: int = Field(ge=1)
    sono_curto_h: float = Field(gt=0)


class Qualidade(_Base):
    potencia_maxima_plausivel_w: float = Field(gt=0)
    fc_minima_plausivel: float = Field(gt=0)
    fc_folga_acima_fc_max: float = Field(ge=0)
    fc_salto_maximo_bpm_por_s: float = Field(gt=0)
    cadencia_minima_falha_potencia: float = Field(ge=0)
    pausa_minima_s: float = Field(gt=0)
    indice_minimo_para_modelos: float = Field(ge=0, le=1)
    penalizacao_fc_otica: float = Field(ge=0, le=1)


class Config(_Base):
    potencia: Potencia
    frequencia_cardiaca: FrequenciaCardiaca
    carga_forma: CargaForma
    modelo_potencia_critica: ModeloPotenciaCritica
    eftp: Eftp
    recuperacao: Recuperacao
    qualidade: Qualidade
    versao: str = ""


def carregar(caminho: Path | str = CAMINHO_POR_DEFEITO) -> Config:
    texto = Path(caminho).read_bytes()
    dados = yaml.safe_load(texto)
    versao = hashlib.sha256(texto).hexdigest()[:12]
    return Config(**dados, versao=versao)
