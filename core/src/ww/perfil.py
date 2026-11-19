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
Fonte = Literal["atleta", "dispositivo", "teste", "estimado", "eftp"]
ModoFTP = Literal["automatico", "manual"]
Ambiente = Literal["indoor", "outdoor"]
OndeTreina = Literal["outdoor", "indoor", "ambos"]
Prioridade = Literal["A", "B", "C", "D"]
Ciclo = Literal["3+1", "2+1"]

PRIORIDADES = {
    "A": "objetivo principal da época",
    "B": "importante",
    "C": "preparação",
    "D": "prova-treino",
}

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
class RegistoFTP:
    """Um valor de FTP e a data a partir da qual vale (D-071)."""
    data: date
    valor: float
    fonte: Fonte                       # "atleta" (manual), "teste", "eftp" (proposta aceite), "estimado"


@dataclass(frozen=True)
class Etapa:
    """Um dia de uma prova por etapas (D-062)."""
    data: date
    duracao_h: float | None = None
    descricao: str = ""                # ex.: "CR 20 km", "montanha"


@dataclass(frozen=True)
class Prova:
    """Prova do calendário do atleta, com prioridade A (mais importante) a D (D-060).

    Prova de um dia: `data` (+ `duracao_h`). Prova por etapas: `etapas` (≥ 2, cada uma com a sua
    data e duração; os dias entre etapas são de descanso) — `data` é a da 1.ª etapa (D-062).
    """
    nome: str
    data: date
    prioridade: Prioridade
    duracao_h: float | None = None     # estimada pelo atleta; sem ela usa-se o valor por defeito
    etapas: tuple[Etapa, ...] = ()

    @classmethod
    def por_etapas(cls, nome: str, prioridade: Prioridade, etapas: tuple[Etapa, ...]) -> "Prova":
        ordenadas = tuple(sorted(etapas, key=lambda e: e.data))
        return cls(nome, ordenadas[0].data, prioridade, etapas=ordenadas)

    def dias(self) -> tuple[Etapa, ...]:
        """Os dias de prova (uma etapa por dia; prova de um dia = uma etapa)."""
        return self.etapas or (Etapa(self.data, self.duracao_h),)

    @property
    def ultima_data(self) -> date:
        return self.dias()[-1].data


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
    provas: tuple[Prova, ...] = ()     # calendário de provas A–D (D-060)
    ciclo: Ciclo | None = None         # escolha do atleta; None = ainda não escolheu → sugestão (D-061)
    agressividade: int | None = None   # 1 (menos agressivo) a 5 (mais agressivo); None = sugestão 3 (D-069)
    # FTP: histórico com data e origem; modo automático (propostas pelo eFTP) ou manual (D-071)
    historico_ftp: tuple["RegistoFTP", ...] = ()
    ftp_modo: ModoFTP = "automatico"

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
    if a.objetivo.tipo == "prova" and not a.provas:
        if a.objetivo.data_prova is None:
            erros.append("objetivo 'prova' sem data")
        elif a.objetivo.data_prova <= hoje:
            erros.append("a data da prova já passou")
    datas_provas = [e.data for p in a.provas for e in p.dias()]
    for p in a.provas:
        if p.prioridade not in PRIORIDADES:
            erros.append(f"prova '{p.nome}': prioridade tem de ser A, B, C ou D")
        if p.data <= hoje:
            erros.append(f"prova '{p.nome}': a data já passou")
        if not p.nome.strip():
            erros.append("prova sem nome")
        if p.duracao_h is not None and not 0.25 <= p.duracao_h <= 24:
            erros.append(f"prova '{p.nome}': duração entre 15 min e 24 h")
        if p.etapas:
            datas_e = [e.data for e in p.etapas]
            if len(p.etapas) < 2:
                erros.append(f"prova '{p.nome}': uma prova por etapas tem pelo menos 2 etapas")
            if datas_e != sorted(datas_e) or len(set(datas_e)) != len(datas_e):
                erros.append(f"prova '{p.nome}': etapas em dias diferentes e por ordem")
            if p.data != datas_e[0]:
                erros.append(f"prova '{p.nome}': a data da prova é a da 1.ª etapa")
            if (datas_e[-1] - datas_e[0]).days + 1 > cfg.provas.etapas_max_dias:
                erros.append(f"prova '{p.nome}': mais de {cfg.provas.etapas_max_dias} dias entre a 1.ª e a última etapa")
            if any(e.duracao_h is not None and not 0.25 <= e.duracao_h <= 24 for e in p.etapas):
                erros.append(f"prova '{p.nome}': duração de cada etapa entre 15 min e 24 h")
    if len(set(datas_provas)) != len(datas_provas):
        erros.append("duas provas (ou etapas) no mesmo dia")
    if a.ciclo is not None and a.ciclo not in ("3+1", "2+1"):
        erros.append("ciclo tem de ser 3+1 ou 2+1")
    if a.agressividade is not None and a.agressividade not in (1, 2, 3, 4, 5):
        erros.append("intensidade preferida tem de ser de 1 a 5")
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


def calendario_provas(a: Atleta) -> tuple[Prova, ...]:
    """Provas por data. Compatibilidade: um objetivo 'prova' sem calendário vira uma prova A."""
    if a.provas:
        return tuple(sorted(a.provas, key=lambda p: p.data))
    if a.objetivo.tipo == "prova" and a.objetivo.data_prova:
        return (Prova(a.objetivo.nome_prova or "Prova", a.objetivo.data_prova, "A"),)
    return ()


def ciclo_sugerido(a: Atleta, hoje: date, cfg: Config) -> Ciclo:
    """Opção que aparece já selecionada na configuração: 2+1 a partir da idade configurada
    (recuperação mais lenta), 3+1 abaixo. O atleta pode sempre escolher a outra (D-061)."""
    return "2+1" if a.idade(hoje) >= cfg.perfil.idade_ciclo_2_1 else "3+1"


def semanas_de_carga(a: Atleta, hoje: date, cfg: Config) -> int:
    """Semanas de carga antes de cada recuperação: a escolha do atleta (ou a sugestão, se ainda
    não escolheu)."""
    return 2 if (a.ciclo or ciclo_sugerido(a, hoje, cfg)) == "2+1" else 3


def agressividade(a: Atleta, hoje: date, cfg: Config) -> int:
    """Intensidade preferida (1–5): a escolha do atleta ou a sugestão 3; menores limitados (D-069)."""
    v = a.agressividade if a.agressividade is not None else 3
    if a.idade(hoje) < cfg.perfil.idade_adulto:
        v = min(v, cfg.plano.agressividade_max_menores)
    return v


# ------------------------------------------------------------------ FTP manual (D-071)

class FTPInvalido(ValueError):
    pass


def ftp_em_vigor(a: Atleta, data: date) -> float | None:
    """FTP válido numa data: o último registo até essa data. Atividades antigas usam o FTP da sua época."""
    anteriores = [r for r in a.historico_ftp if r.data <= data]
    if anteriores:
        return max(anteriores, key=lambda r: r.data).valor
    return a.ftp.valor if a.ftp is not None else None


def definir_ftp_manual(a: Atleta, valor: float, data: date, cfg: Config,
                       eftp: float | None = None) -> tuple[Atleta, tuple[str, ...]]:
    """O atleta escreve o seu FTP. Vale a partir de `data`; o histórico anterior não muda.

    Recusa valores fora de 1–7 W/kg (erro de escrita); avisa (e pede confirmação na app) se ficar
    longe do eFTP. Devolve o atleta atualizado e os avisos.
    """
    e = cfg.eftp
    wkg = valor / a.peso_kg
    if not e.ftp_manual_w_kg_min <= wkg <= e.ftp_manual_w_kg_max:
        raise FTPInvalido(f"{valor:.0f} W = {wkg:.1f} W/kg: fora de {e.ftp_manual_w_kg_min:g}–{e.ftp_manual_w_kg_max:g} W/kg")
    avisos: list[str] = []
    if eftp:
        dif = (valor - eftp) / eftp * 100
        if abs(dif) > e.ftp_manual_aviso_diferenca_pct:
            avisos.append(f"diferenca_grande_eftp:{dif:+.0f}%")
    hist = tuple(r for r in a.historico_ftp if r.data != data) + (RegistoFTP(data, float(valor), "atleta"),)
    return replace(a, ftp=Valor(float(valor), "atleta"), historico_ftp=tuple(sorted(hist, key=lambda r: r.data))), tuple(avisos)
