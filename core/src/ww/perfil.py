"""Perfil do atleta (spec 4).

- Campos obrigatórios validados; idade mínima configurável (10 anos, D-045).
- Abaixo da idade de consentimento próprio é obrigatório o consentimento de um responsável legal.
- Menores de idade usam sempre as regras de treino de iniciante (`nivel_regras`).
- Valores fisiológicos em falta são estimados de forma conservadora e marcados como
  "estimado"; nunca substituem um valor indicado pelo atleta (spec 5).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date
from typing import Literal

from ww.config import Config

Sexo = Literal["M", "F"]
Nivel = Literal["iniciante", "intermedio", "avancado", "competicao"]
Disciplina = Literal["estrada", "gravel", "btt_xco", "btt_maratona", "contrarrelogio"]
TipoObjetivo = Literal["prova", "ftp", "peso", "resistencia"]
Fonte = Literal["atleta", "dispositivo", "teste", "estimado"]
Ambiente = Literal["indoor", "outdoor"]
OndeTreina = Literal["outdoor", "indoor", "ambos"]

DIAS = ("segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo")


class PerfilInvalido(ValueError):
    pass


@dataclass(frozen=True)
class Valor:
    valor: float
    fonte: Fonte

    @property
    def estimado(self) -> bool:
        return self.fonte == "estimado"


@dataclass(frozen=True)
class Objetivo:
    tipo: TipoObjetivo
    data_prova: date | None = None
    nome_prova: str = ""


@dataclass(frozen=True)
class Equipamento:
    potenciometro: bool = False
    rolo_inteligente: bool = False
    cinta_fc: bool = False


@dataclass(frozen=True)
class Atleta:
    nome: str
    data_nascimento: date
    sexo: Sexo
    peso_kg: float
    nivel: Nivel
    disciplina: Disciplina
    objetivo: Objetivo
    # minutos disponíveis por dia da semana (0 = segunda … 6 = domingo); 0 = não treina
    disponibilidade: tuple[int, int, int, int, int, int, int]
    dia_longo: int | None = None
    equipamento: Equipamento = field(default_factory=Equipamento)
    ftp: Valor | None = None
    fc_limiar: Valor | None = None
    fc_max: Valor | None = None
    fc_repouso: Valor | None = None
    altura_cm: float | None = None
    anos_treino_estruturado: int | None = None
    consentimento_responsavel: bool = False   # obrigatório abaixo da idade de consentimento próprio
    # "Onde vais treinar?" — pergunta da configuração inicial (D-059); None = sugestão pelo equipamento
    onde_treina: OndeTreina | None = None

    def idade(self, em: date) -> int:
        d = self.data_nascimento
        return em.year - d.year - ((em.month, em.day) < (d.month, d.day))


def validar(a: Atleta, hoje: date, cfg: Config) -> None:
    erros = []
    if not a.nome.strip():
        erros.append("nome em falta")
    idade = a.idade(hoje)
    if idade < cfg.perfil.idade_minima:
        erros.append(f"idade mínima {cfg.perfil.idade_minima} anos")
    elif idade < cfg.perfil.idade_consentimento_proprio and not a.consentimento_responsavel:
        erros.append("menor de idade: falta o consentimento de um responsável legal")
    if not 30 <= a.peso_kg <= 200:
        erros.append("peso fora do intervalo 30–200 kg")
    if len(a.disponibilidade) != 7 or any(not 0 <= m <= 720 for m in a.disponibilidade):
        erros.append("disponibilidade: 7 valores entre 0 e 720 minutos")
    elif not any(m >= cfg.plano.duracao_minima_treino_min for m in a.disponibilidade):
        erros.append(f"é preciso pelo menos um dia com {cfg.plano.duracao_minima_treino_min} min")
    if a.dia_longo is not None and (not 0 <= a.dia_longo <= 6 or a.disponibilidade[a.dia_longo] == 0):
        erros.append("o dia longo tem de ser um dia com disponibilidade")
    if a.objetivo.tipo == "prova":
        if a.objetivo.data_prova is None:
            erros.append("objetivo 'prova' sem data")
        elif a.objetivo.data_prova <= hoje:
            erros.append("a data da prova já passou")
    fl, fm, fr = a.fc_limiar, a.fc_max, a.fc_repouso
    if fl and fm and fl.valor >= fm.valor:
        erros.append("FC limiar tem de ser inferior à FC máxima")
    if fr and fl and fr.valor >= fl.valor:
        erros.append("FC de repouso tem de ser inferior à FC limiar")
    if erros:
        raise PerfilInvalido("; ".join(erros))


def completar(a: Atleta, hoje: date, cfg: Config) -> Atleta:
    """Preenche valores em falta com estimativas conservadoras (fonte = "estimado")."""
    p = cfg.perfil
    alt: dict[str, Valor] = {}
    if a.ftp is None:
        wkg = p.ftp_w_kg_estimado[a.nivel] * (p.fator_ftp_feminino if a.sexo == "F" else 1.0)
        alt["ftp"] = Valor(round(wkg * a.peso_kg), "estimado")
    fc_max = a.fc_max
    if fc_max is None:
        # Tanaka et al. (2001): 208 − 0,7 × idade
        fc_max = Valor(round(208 - 0.7 * a.idade(hoje)), "estimado")
        alt["fc_max"] = fc_max
    if a.fc_limiar is None:
        alt["fc_limiar"] = Valor(round(fc_max.valor * p.fc_limiar_fator_fc_max), "estimado")
    if a.fc_repouso is None:
        alt["fc_repouso"] = Valor(p.fc_repouso_estimada, "estimado")
    return replace(a, **alt)


def precisa_de_teste(a: Atleta) -> Literal["ftp", "fc_limiar"] | None:
    """Teste guiado na 1.ª semana se o valor de referência for estimado (spec 4)."""
    if a.equipamento.potenciometro:
        return "ftp" if a.ftp is None or a.ftp.estimado else None
    return "fc_limiar" if a.fc_limiar is None or a.fc_limiar.estimado else None


def nivel_regras(a: Atleta, hoje: date, cfg: Config) -> Nivel:
    """Nível usado nas regras de treino: menores de idade usam sempre as de iniciante (D-045)."""
    return "iniciante" if a.idade(hoje) < cfg.perfil.idade_adulto else a.nivel


def onde_treina(a: Atleta) -> OndeTreina:
    """Resposta do atleta ou, sem resposta, a sugestão pelo equipamento: com rolo inteligente
    "ambos", sem rolo "outdoor" (D-059)."""
    if a.onde_treina is not None:
        return a.onde_treina
    return "ambos" if a.equipamento.rolo_inteligente else "outdoor"


def ambientes(a: Atleta) -> tuple[Ambiente, ...]:
    """Versões a mostrar no calendário: a principal primeiro."""
    return {"outdoor": ("outdoor",), "indoor": ("indoor",), "ambos": ("outdoor", "indoor")}[onde_treina(a)]  # type: ignore[return-value]


def tem_potencia(a: Atleta, ambiente: Ambiente) -> bool:
    """Alvos em watts: com potenciómetro, ou no rolo inteligente (que mede a potência)."""
    return a.equipamento.potenciometro or (ambiente == "indoor" and a.equipamento.rolo_inteligente)
