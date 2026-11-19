"""Propostas de alteração do FTP ao atleta (spec 6.1 e 7.6).

Regras:
- Nenhuma alteração é aplicada em silêncio: tudo é proposto, com explicação.
- Alterações abaixo de `alteracao_minima_pct` não geram proposta.
- Subidas acima de `subida_sem_confirmacao_max_pct` exigem um 2.º esforço (outra atividade)
  ou treinos de limiar cumpridos. Sem isso, propõe-se só a subida até esse limite (D-024).
- Sem resposta em `dias_para_resposta` dias: descidas aplicam-se; subidas expiram.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Literal

from ww.config import Config
from ww.eftp import Estimativa

Tipo = Literal["subida", "descida"]
Estado = Literal["pendente", "aplicada_automaticamente", "expirada"]
Motivo = Literal["novo_esforco", "subida_confirmada", "subida_limitada_aguarda_confirmacao", "sem_esforcos_recentes"]


@dataclass(frozen=True)
class Proposta:
    criada_em: date
    ftp_atual: float
    ftp_proposto: float
    estimativa: float          # eFTP calculado, antes de qualquer limite
    tipo: Tipo
    motivo: Motivo
    atividades: tuple[str, ...]  # atividades que justificam a proposta

    @property
    def variacao_pct(self) -> float:
        return (self.ftp_proposto - self.ftp_atual) / self.ftp_atual * 100.0


def avaliar(
    ftp_atual: float,
    estimativa: Estimativa | None,
    *,
    por_atividade: Mapping[str, float],
    confirmado_por_treinos_limiar: bool,
    hoje: date,
    cfg: Config,
) -> Proposta | None:
    if estimativa is None or ftp_atual <= 0:
        return None
    c = cfg.eftp
    est = estimativa.ftp
    variacao = (est - ftp_atual) / ftp_atual * 100.0
    if abs(variacao) < c.alteracao_minima_pct:
        return None

    atividades = tuple(sorted({e.atividade_id for e in estimativa.esforcos}))

    if variacao < 0:
        # Esforços antigos (com decaimento) ou novos mais fracos → proposta de descida
        recentes = any((hoje - e.data).days <= cfg.eftp.decaimento_carencia_dias for e in estimativa.esforcos)
        motivo: Motivo = "novo_esforco" if recentes else "sem_esforcos_recentes"
        return Proposta(hoje, ftp_atual, est, est, "descida", motivo, atividades)

    limite = ftp_atual * (1.0 + c.subida_sem_confirmacao_max_pct / 100.0)
    if est <= limite:
        return Proposta(hoje, ftp_atual, est, est, "subida", "novo_esforco", atividades)

    apoio = sorted(a for a, v in por_atividade.items() if v >= limite)
    if len(apoio) >= 2 or confirmado_por_treinos_limiar:
        return Proposta(hoje, ftp_atual, est, est, "subida", "subida_confirmada", tuple(apoio) or atividades)

    return Proposta(hoje, ftp_atual, limite, est, "subida", "subida_limitada_aguarda_confirmacao", atividades)


def estado_sem_resposta(proposta: Proposta, hoje: date, cfg: Config) -> Estado:
    """O que acontece a uma proposta que o atleta ainda não aceitou nem recusou."""
    if (hoje - proposta.criada_em).days < cfg.eftp.dias_para_resposta:
        return "pendente"
    return "aplicada_automaticamente" if proposta.tipo == "descida" else "expirada"
