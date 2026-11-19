"""Deduplicação de atividades que chegam por duas vias (spec 5).

Duplicado = início a ± `dedup_inicio_tolerancia_s` e duração a ± `dedup_duracao_tolerancia_pct`.
Os dois ficheiros originais são guardados; só um é a atividade principal (a que conta
para carga e métricas). Preferência: tem potência → tem FC → melhor qualidade →
dispositivo antes de app, app antes de manual → a que chegou primeiro.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from ww.config import Dados

Origem = Literal["dispositivo", "app", "manual", "estimado"]
_PRIORIDADE_ORIGEM = {"dispositivo": 0, "app": 1, "manual": 2, "estimado": 3}


@dataclass(frozen=True)
class AtividadeRef:
    id: str
    inicio: datetime
    duracao_s: int
    origem: Origem
    tem_potencia: bool
    tem_fc: bool
    qualidade: float
    recebida_em: datetime


def e_duplicado(a: AtividadeRef, b: AtividadeRef, cfg: Dados) -> bool:
    if abs((a.inicio - b.inicio).total_seconds()) > cfg.dedup_inicio_tolerancia_s:
        return False
    maior = max(a.duracao_s, b.duracao_s)
    if maior == 0:
        return True
    return abs(a.duracao_s - b.duracao_s) / maior * 100.0 <= cfg.dedup_duracao_tolerancia_pct


def _chave(a: AtividadeRef) -> tuple:
    return (not a.tem_potencia, not a.tem_fc, -a.qualidade, _PRIORIDADE_ORIGEM[a.origem], a.recebida_em)


def principal(a: AtividadeRef, b: AtividadeRef) -> AtividadeRef:
    return min(a, b, key=_chave)


def procurar_duplicado(nova: AtividadeRef, existentes: Iterable[AtividadeRef], cfg: Dados) -> AtividadeRef | None:
    candidatos = [e for e in existentes if e.id != nova.id and e_duplicado(nova, e, cfg)]
    if not candidatos:
        return None
    return min(candidatos, key=lambda e: abs((e.inicio - nova.inicio).total_seconds()))
