"""Biblioteca de treinos estruturados (spec 7.2), lida de config/treinos.yaml.

A carga prevista de cada passo usa a mesma escala da carga de potência:
    carga = horas × (intensidade)² × 100, com intensidade = meio do alvo em % do FTP.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import yaml

CAMINHO_OUTDOOR = Path(__file__).resolve().parents[3] / "config" / "treinos_outdoor.yaml"
CAMINHO_INDOOR = Path(__file__).resolve().parents[3] / "config" / "treinos_indoor.yaml"
CAMINHO_POR_DEFEITO = CAMINHO_OUTDOOR
CAMINHO_PAULO = Path(__file__).resolve().parents[3] / "config" / "treinos_paulo.yaml"
CAMINHO_NOMES = Path(__file__).resolve().parents[3] / "config" / "nomes_treinos.yaml"
TIPOS = {"recuperacao", "resistencia", "tempo", "forca", "sweetspot", "limiar", "vo2max", "anaerobio", "teste"}


@dataclass(frozen=True)
class Passo:
    segundos: int
    pct_min: float
    pct_max: float
    cadencia: tuple[int, int] | None = None
    escala: bool = False
    rampa: str | None = None     # "sobe" (pct_min → pct_max) ou "desce" (pct_max → pct_min)
    alvo: float | None = None    # alvo fixo indoor (% do FTP); por defeito o meio do intervalo (D-058)

    @property
    def pct_medio(self) -> float:
        return (self.pct_min + self.pct_max) / 2

    @property
    def pct_fixo(self) -> float:
        """Alvo único para o rolo (modo ERG): sem descidas, vento nem trânsito, não há intervalo."""
        return self.alvo if self.alvo is not None else round(self.pct_medio)

    @property
    def carga(self) -> float:
        a, b = self.pct_min / 100, self.pct_max / 100
        # rampa linear: média de IF² = (a² + ab + b²) / 3; bloco com alvo [a, b]: usa o meio
        if2 = (a * a + a * b + b * b) / 3 if self.rampa else ((a + b) / 2) ** 2
        return self.segundos / 3600 * if2 * 100


@dataclass(frozen=True)
class Treino:
    id: str
    nome: str
    tipo: str
    dificuldade: int
    passos: tuple[Passo, ...]
    escalavel: bool = False
    so_sem_potencia: bool = False
    descricao: str = ""
    origem: str = "wattwise"      # "wattwise" (provisório) ou "paulo" (biblioteca do treinador)
    subtitulo: str = ""           # descrição técnica curta (o `nome` é o nome de marca, D-050)
    ambiente: str = "outdoor"     # "indoor" (alvos fixos, rolo) ou "outdoor" (intervalos) (D-058)
    base: str = ""                # id comum às versões indoor e outdoor do mesmo treino

    @property
    def titulo(self) -> str:
        return f"{self.nome} · {self.subtitulo}" if self.subtitulo else self.nome

    @property
    def segundos(self) -> int:
        return sum(p.segundos for p in self.passos)

    @property
    def minutos(self) -> float:
        return self.segundos / 60

    @property
    def carga(self) -> float:
        return sum(p.carga for p in self.passos)

    def indoor(self) -> "Treino":
        """Versão para o rolo: cada passo (exceto rampas) passa a ter um alvo fixo (D-058)."""
        return replace(self, passos=tuple(
            p if p.rampa else replace(p, pct_min=p.pct_fixo, pct_max=p.pct_fixo) for p in self.passos))

    def com_duracao(self, minutos: int) -> "Treino":
        """Estica/encolhe os passos marcados com `escala` para durar `minutos`."""
        if not self.escalavel:
            raise ValueError(f"o treino {self.id} não é escalável")
        fixo = sum(p.segundos for p in self.passos if not p.escala)
        n_escala = sum(1 for p in self.passos if p.escala)
        livre = minutos * 60 - fixo
        if livre <= 0:
            # pouco tempo: só o passo escalável, com a duração toda
            principal = next(p for p in self.passos if p.escala)
            return replace(self, passos=(replace(principal, segundos=minutos * 60),))
        novos = tuple(replace(p, segundos=livre // n_escala) if p.escala else p for p in self.passos)
        return replace(self, passos=novos)


def _expandir(itens: list[dict[str, Any]]) -> list[Passo]:
    out: list[Passo] = []
    for it in itens:
        if "repetir" in it:
            out += _expandir(it["passos"]) * int(it["repetir"])
            continue
        lo, hi = it["pct"]
        cad = tuple(it["cadencia"]) if "cadencia" in it else None
        alvo = float(it["alvo"]) if "alvo" in it else None
        if alvo is not None and not lo <= alvo <= hi:
            raise ValueError(f"alvo indoor {alvo}% fora do intervalo [{lo}, {hi}]")
        out.append(Passo(round(float(it["min"]) * 60), float(lo), float(hi), cad,  # type: ignore[arg-type]
                         bool(it.get("escala", False)), it.get("rampa"), alvo))
    return out


def carregar(*caminhos: Path | str, nomes: Path | str | None = CAMINHO_NOMES) -> dict[str, Treino]:
    """Lê uma ou mais bibliotecas. Por defeito: a provisória + a do Paulo (se existir).

    Os nomes de marca (`config/nomes_treinos.yaml`) substituem o nome; o nome original
    passa a subtítulo técnico.
    """
    caminhos_explicitos = bool(caminhos)
    if not caminhos:
        caminhos = tuple(c for c in (CAMINHO_OUTDOOR, CAMINHO_INDOOR, CAMINHO_PAULO) if Path(c).exists())
    marca: dict[str, str] = {}
    if nomes is not None and Path(nomes).exists():
        marca = yaml.safe_load(Path(nomes).read_text(encoding="utf-8")) or {}
    dados: list[dict[str, Any]] = []
    for c in caminhos:
        dados += yaml.safe_load(Path(c).read_text(encoding="utf-8")) or []
    out: dict[str, Treino] = {}
    for d in dados:
        t = Treino(
            id=d["id"], nome=d["nome"], tipo=d["tipo"], dificuldade=int(d["dificuldade"]),
            passos=tuple(_expandir(d["passos"])), escalavel=bool(d.get("escalavel", False)),
            so_sem_potencia=bool(d.get("so_sem_potencia", False)),
            descricao=d.get("descricao", ""), origem=d.get("origem", "wattwise"),
            ambiente=d.get("ambiente", "outdoor"), base=d.get("base", d["id"]),
        )
        if t.ambiente not in ("indoor", "outdoor"):
            raise ValueError(f"{t.id}: ambiente '{t.ambiente}' (indoor ou outdoor)")
        if t.ambiente == "indoor" and any(p.pct_min != p.pct_max for p in t.passos if not p.rampa):
            raise ValueError(f"{t.id}: treino indoor com alvo em intervalo (tem de ser fixo)")
        if t.base in marca:
            t = replace(t, nome=str(marca[t.base]), subtitulo=d["nome"])
        if t.id in out:
            raise ValueError(f"treino repetido: {t.id}")
        if t.tipo not in TIPOS:
            raise ValueError(f"{t.id}: tipo desconhecido '{t.tipo}'")
        if not 1 <= t.dificuldade <= 5:
            raise ValueError(f"{t.id}: dificuldade fora de 1–5")
        if any(p.pct_min > p.pct_max or p.segundos <= 0 or p.rampa not in (None, "sobe", "desce") for p in t.passos):
            raise ValueError(f"{t.id}: passo inválido")
        if t.escalavel and not any(p.escala for p in t.passos):
            raise ValueError(f"{t.id}: escalável sem passo com 'escala'")
        out[t.id] = t
    sem_uso = set(marca) - {t.base for t in out.values()}
    if sem_uso and nomes is not None and not caminhos_explicitos:
        raise ValueError(f"nomes de marca para treinos que não existem: {sorted(sem_uso)}")
    repetidos = {n for n in marca.values() if list(marca.values()).count(n) > 1}
    if repetidos:
        raise ValueError(f"nomes de marca repetidos: {sorted(repetidos)}")
    return out


# ------------------------------------------------------------------ dificuldade objetiva (D-055)

# Zona de trabalho de cada tipo (% do FTP, pelo meio do alvo): [mín, máx)
ZONAS_TRABALHO = {
    "tempo": (76, 88), "sweetspot": (88, 95), "limiar": (93, 106), "vo2max": (105, 121), "anaerobio": (121, 999),
}
# Minutos de trabalho efetivo que separam os níveis 1|2|3|4|5
ESCALAS = {
    "tempo": (20, 30, 40, 55), "sweetspot": (20, 30, 40, 55), "limiar": (15, 24, 32, 40),
    "vo2max": (10, 15, 20, 24), "anaerobio": (2, 4, 6, 8),
}
# Recuperação "normal" (descanso ÷ trabalho) de cada tipo; mais curta = mais difícil
DESCANSO_NORMAL = {"tempo": 0.15, "sweetspot": 0.2, "limiar": 0.3, "vo2max": 0.75, "anaerobio": 2.0}
CADENCIA_BAIXA = 70


def zona_de_trabalho(passos: tuple[Passo, ...] | list[Passo]) -> tuple[str | None, list[Passo]]:
    """Tipo de esforço dominante (pelo tempo) e os passos de trabalho (≥ 76% do FTP, sem rampas)."""
    trabalho = [p for p in passos if p.pct_medio >= 76 and not p.rampa]
    if sum(p.segundos for p in trabalho) < 60:
        return None, []
    tempo_zona = {z: sum(p.segundos for p in trabalho if lo <= p.pct_medio < hi) for z, (lo, hi) in ZONAS_TRABALHO.items()}
    total = sum(p.segundos for p in trabalho)
    if tempo_zona["anaerobio"] >= 60 and tempo_zona["anaerobio"] >= 0.3 * total:
        return "anaerobio", trabalho
    return max(tempo_zona, key=lambda z: tempo_zona[z]), trabalho


def dificuldade_objetiva(passos: tuple[Passo, ...] | list[Passo], tipo: str) -> int:
    """Nível 1–5 pela mesma regra para todos os treinos (originais e importados).

    minutos efetivos = minutos de trabalho a partir do início da zona do tipo (a zona dominante, na
    força) × fator de densidade, em que o fator = √(descanso normal do tipo ÷ descanso real entre
    esforços), entre 1 e 1,5 (sem descanso: 1,5). Força: +1 nível (cadência baixa).
    Recuperação, resistência e testes: pela duração (resistência) ou fixos.
    """
    if tipo in ("recuperacao", "teste"):
        return 1 if tipo == "recuperacao" else 3
    zona, trabalho = zona_de_trabalho(passos)
    if tipo == "resistencia" or zona is None:
        horas = sum(p.segundos for p in passos) / 3600
        extra = 1 if zona is not None else 0      # Z2 com blocos de tempo/sweet spot
        return min(5, 1 + sum(horas > h for h in (1.25, 2.25, 3.5, 4.5)) + extra)
    if tipo in ZONAS_TRABALHO:
        zona = tipo          # a zona do tipo declarado (ex.: 15/15 a 125% é VO2máx, não anaeróbio)
    t_zona = sum(p.segundos for p in trabalho if p.pct_medio >= ZONAS_TRABALHO[zona][0])
    t_trab = sum(p.segundos for p in trabalho)
    # recuperação típica entre esforços: mediana dos descansos entre dois esforços ÷ mediana dos
    # esforços (as pausas longas entre séries não diluem recuperações curtas como 40/20)
    lista = list(passos)
    descansos = [lista[i].segundos for i in range(1, len(lista) - 1)
                 if lista[i].pct_medio < 76 and lista[i - 1].pct_medio >= 76 and lista[i + 1].pct_medio >= 76]
    esforcos = [p.segundos for p in trabalho]
    razao = statistics.median(descansos) / statistics.median(esforcos) if descansos else 0.0
    densidade = min(1.5, max(1.0, (DESCANSO_NORMAL[zona] / razao) ** 0.5)) if razao > 0 else 1.5
    minutos = t_zona / 60 * densidade
    nivel = 1 + sum(minutos > x for x in ESCALAS[zona])
    if tipo == "forca":
        nivel += 1
    return min(5, nivel)


def biblioteca(lib: dict[str, Treino], ambiente: str) -> dict[str, Treino]:
    """Só os treinos de um ambiente (indoor ou outdoor)."""
    return {k: t for k, t in lib.items() if t.ambiente == ambiente}


def equivalente(t: Treino, ambiente: str, lib: dict[str, Treino], minutos_max: float | None = None) -> Treino | None:
    """O mesmo treino no outro ambiente; se não existir (ex.: Z2 de 4 h indoor), o mais parecido:
    mesmo tipo, dificuldade mais próxima (sem passar) e duração mais próxima (D-058)."""
    if t.ambiente == ambiente:
        return t
    outra = biblioteca(lib, ambiente)
    limite = minutos_max if minutos_max is not None else float("inf")
    for c in outra.values():
        if c.base == t.base and c.minutos <= limite:
            return c
    cand = [c for c in outra.values() if c.tipo == t.tipo and c.dificuldade <= t.dificuldade and c.minutos <= limite]
    if not cand:
        return None
    return min(cand, key=lambda c: (t.dificuldade - c.dificuldade, abs(c.minutos - t.minutos), c.id))
