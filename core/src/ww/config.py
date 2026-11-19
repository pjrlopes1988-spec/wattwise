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
    perfil_minimo_atividades: int = Field(ge=1)
    decaimento_carencia_dias: int = Field(ge=0)
    decaimento_pct_por_semana: float = Field(ge=0, lt=10)
    subida_sem_confirmacao_max_pct: float = Field(ge=0)
    alteracao_minima_pct: float = Field(ge=0)
    dias_para_resposta: int = Field(ge=1)
    descida_minimo_dias_dados: int = Field(ge=0)
    descida_max_pct: float = Field(gt=0)
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


class Dados(_Base):
    dedup_inicio_tolerancia_s: int = Field(ge=0)
    dedup_duracao_tolerancia_pct: float = Field(ge=0)


class ModeloFCPersonalizado(_Base):
    minimo_atividades: int = Field(ge=5)
    r2_minimo: float = Field(gt=0, le=1)
    janela_dias: int = Field(gt=0)


Nivel = Literal["iniciante", "intermedio", "avancado", "competicao"]
PorNivel = dict[Nivel, float]


def _todos_os_niveis(v: dict) -> dict:
    falta = {"iniciante", "intermedio", "avancado", "competicao"} - set(v)
    if falta:
        raise ValueError(f"faltam níveis: {sorted(falta)}")
    return v


class Perfil(_Base):
    idade_minima: int = Field(ge=10)
    idade_consentimento_proprio: int = Field(ge=13)
    idade_adulto: int = Field(ge=16)
    ftp_w_kg_estimado: PorNivel
    fator_ftp_feminino: float = Field(gt=0.5, le=1.0)
    fc_limiar_fator_fc_max: float = Field(gt=0.7, lt=1.0)
    fc_repouso_estimada: float = Field(gt=30, lt=100)
    idade_ciclo_2_1: int = Field(ge=18)

    _v = field_validator("ftp_w_kg_estimado")(_todos_os_niveis)


class TiposEspecifico(_Base):
    estrada: list[str]
    gravel: list[str]
    btt_xco: list[str]
    btt_maratona: list[str]
    contrarrelogio: list[str]


class TiposPorFase(_Base):
    base: list[str]
    construcao: list[str]
    afinacao: list[str]
    especifico: TiposEspecifico


class SessoesChave(_Base):
    base: PorNivel
    construcao: PorNivel
    especifico: PorNivel
    recuperacao: PorNivel
    afinacao: PorNivel


class Plano(_Base):
    rampa_condicao_semana: PorNivel
    semanas_carga_por_ciclo: int = Field(ge=1, le=3)   # spec 7.3: recuperação pelo menos a cada 4 semanas
    fator_semana_recuperacao: float = Field(gt=0, lt=1)
    fator_afinacao: float = Field(gt=0, lt=1)
    semanas_base_arranque_frio: int = Field(ge=0)
    semanas_especifico: int = Field(ge=0)
    semanas_construcao_max: int = Field(ge=0)
    semanas_afinacao_prova_longe: int = Field(ge=1)
    semanas_prova_longe: int = Field(ge=1)
    horizonte_sem_prova_semanas: int = Field(ge=4)
    carga_prova_estimada: float = Field(gt=0)
    sessoes_chave: SessoesChave
    tipos_por_fase: TiposPorFase
    dificuldade_max: PorNivel
    dias_descanso_min: PorNivel
    max_dias_alta_intensidade_seguidos: int = Field(ge=1)
    tipos_alta_intensidade: list[str]
    alta_intensidade_s_acima_95pct: int = Field(gt=0)
    alta_intensidade_s_acima_120pct: int = Field(gt=0)
    duracao_minima_sessao_chave_min: int = Field(gt=0)
    duracao_minima_treino_min: int = Field(gt=0)
    arredondar_min: int = Field(gt=0)
    fracao_carga_dia_longo: float = Field(gt=0, lt=1)
    duracao_minima_resistencia_min: int = Field(gt=0)

    _v = field_validator("rampa_condicao_semana", "dificuldade_max", "dias_descanso_min")(_todos_os_niveis)


class Indoor(_Base):
    duracao_max_min: int = Field(ge=30, le=600)


class Provas(_Base):
    semanas_recuperacao_apos_A: int = Field(ge=0, le=3)
    fator_carga_semana_B: float = Field(gt=0, le=1)
    dias_sem_intensidade_antes: dict[str, int]
    dias_faceis_depois: dict[str, int]
    duracao_max_antes_min: int = Field(ge=30)
    conta_como_sessao_chave: dict[str, bool]
    ativacao_antes: dict[str, bool]
    etapas_max_dias: int = Field(ge=2, le=60)
    prolongar_recuperacao_max_semanas: int = Field(ge=0, le=3)
    duracao_por_defeito_h: float = Field(gt=0)
    intensidade_por_duracao: list[tuple[float, float]]

    @field_validator("dias_sem_intensidade_antes", "dias_faceis_depois", "conta_como_sessao_chave", "ativacao_antes")
    @classmethod
    def _abcd(cls, v: dict) -> dict:
        if set(v) != {"A", "B", "C", "D"}:
            raise ValueError("é preciso um valor para cada prioridade A, B, C e D")
        return v


class Qualidade(_Base):
    potencia_maxima_plausivel_w: float = Field(gt=0)
    fc_minima_plausivel: float = Field(gt=0)
    fc_folga_acima_fc_max: float = Field(ge=0)
    fc_salto_maximo_bpm_por_s: float = Field(gt=0)
    cadencia_minima_falha_potencia: float = Field(ge=0)
    pausa_minima_s: float = Field(gt=0)
    indice_minimo_para_modelos: float = Field(ge=0, le=1)
    penalizacao_fc_otica: float = Field(ge=0, le=1)
    velocidade_motorizada_ms: float = Field(gt=0)
    velocidade_motorizada_min_s: int = Field(gt=0)
    eficiencia_desvio_suspeito_pct: float = Field(gt=0)
    curva_salto_suspeito_pct: float = Field(gt=0)


class Intervalos(_Base):
    limiar_pct_ftp: float = Field(gt=0)
    limiar_pct_fc_limiar: float = Field(gt=0)
    saida_pct_ftp: float = Field(gt=0)
    saida_pct_fc_limiar: float = Field(gt=0)
    suavizacao_s: int = Field(ge=1)
    duracao_minima_s: int = Field(ge=1)
    juntar_pausas_ate_s: int = Field(ge=0)
    recuperacao_fc_s: int = Field(ge=1)


class Seiler(_Base):
    potencia_ultima_zona: tuple[int, int]
    fc_ultima_zona: tuple[int, int]


class Config(_Base):
    potencia: Potencia
    frequencia_cardiaca: FrequenciaCardiaca
    carga_forma: CargaForma
    modelo_potencia_critica: ModeloPotenciaCritica
    eftp: Eftp
    recuperacao: Recuperacao
    intervalos: Intervalos
    seiler: Seiler
    dados: Dados
    modelo_fc_personalizado: ModeloFCPersonalizado
    perfil: Perfil
    plano: Plano
    indoor: Indoor
    provas: Provas
    qualidade: Qualidade
    versao: str = ""


def carregar(caminho: Path | str = CAMINHO_POR_DEFEITO) -> Config:
    texto = Path(caminho).read_bytes()
    dados = yaml.safe_load(texto)
    versao = hashlib.sha256(texto).hexdigest()[:12]
    return Config(**dados, versao=versao)
