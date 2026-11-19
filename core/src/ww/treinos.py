"""Biblioteca de treinos estruturados (spec 7.2), lida de config/treinos.yaml.

A carga prevista de cada passo usa a mesma escala da carga de potência:
    carga = horas × (intensidade)² × 100, com intensidade = meio do alvo em % do FTP.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import yaml

CAMINHO_POR_DEFEITO = Path(__file__).resolve().parents[3] / "config" / "treinos.yaml"
TIPOS = {"recuperacao", "resistencia", "tempo", "forca", "sweetspot", "limiar", "vo2max", "anaerobio", "teste"}


@dataclass(frozen=True)
class Passo:
    segundos: int
    pct_min: float
    pct_max: float
    cadencia: tuple[int, int] | None = None
    escala: bool = False

    @property
    def pct_medio(self) -> float:
        return (self.pct_min + self.pct_max) / 2

    @property
    def carga(self) -> float:
        return self.segundos / 3600 * (self.pct_medio / 100) ** 2 * 100


@dataclass(frozen=True)
class Treino:
    id: str
    nome: str
    tipo: str
    dificuldade: int
    passos: tuple[Passo, ...]
    escalavel: bool = False
    so_sem_potencia: bool = False

    @property
    def segundos(self) -> int:
        return sum(p.segundos for p in self.passos)

    @property
    def minutos(self) -> float:
        return self.segundos / 60

    @property
    def carga(self) -> float:
        return sum(p.carga for p in self.passos)

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
        out.append(Passo(round(float(it["min"]) * 60), float(lo), float(hi), cad, bool(it.get("escala", False))))  # type: ignore[arg-type]
    return out


def carregar(caminho: Path | str = CAMINHO_POR_DEFEITO) -> dict[str, Treino]:
    dados = yaml.safe_load(Path(caminho).read_text(encoding="utf-8"))
    out: dict[str, Treino] = {}
    for d in dados:
        t = Treino(
            id=d["id"], nome=d["nome"], tipo=d["tipo"], dificuldade=int(d["dificuldade"]),
            passos=tuple(_expandir(d["passos"])), escalavel=bool(d.get("escalavel", False)),
            so_sem_potencia=bool(d.get("so_sem_potencia", False)),
        )
        if t.id in out:
            raise ValueError(f"treino repetido: {t.id}")
        if t.tipo not in TIPOS:
            raise ValueError(f"{t.id}: tipo desconhecido '{t.tipo}'")
        if not 1 <= t.dificuldade <= 5:
            raise ValueError(f"{t.id}: dificuldade fora de 1–5")
        if any(p.pct_min > p.pct_max or p.segundos <= 0 for p in t.passos):
            raise ValueError(f"{t.id}: passo inválido")
        if t.escalavel and not any(p.escala for p in t.passos):
            raise ValueError(f"{t.id}: escalável sem passo com 'escala'")
        out[t.id] = t
    return out
