"""Conversão do perfil do atleta (dataclasses do motor) de e para JSON."""

from __future__ import annotations

from datetime import date
from typing import Any

from ww.perfil import Atleta, Equipamento, Etapa, Objetivo, Prova, RegistoFTP, Valor


def _d(x: str | None) -> date | None:
    return date.fromisoformat(x) if x else None


def _valor(v: dict | None) -> Valor | None:
    return Valor(float(v["valor"]), v["fonte"]) if v else None


def atleta_de_json(j: dict[str, Any]) -> Atleta:
    o = j.get("objetivo") or {"tipo": "ftp"}
    provas = tuple(
        Prova(p["nome"], date.fromisoformat(p["data"]), p["prioridade"], p.get("duracao_h"),
              tuple(Etapa(date.fromisoformat(e["data"]), e.get("duracao_h"), e.get("descricao", "")) for e in p.get("etapas", [])))
        for p in j.get("provas", []))
    return Atleta(
        nome=j["nome"], data_nascimento=date.fromisoformat(j["data_nascimento"]), sexo=j["sexo"],
        peso_kg=float(j["peso_kg"]), nivel=j["nivel"], disciplina=j["disciplina"],
        objetivo=Objetivo(o["tipo"], _d(o.get("data_prova")), o.get("nome_prova", "")),
        disponibilidade=tuple(int(m) for m in j["disponibilidade"]),  # type: ignore[arg-type]
        dia_longo=j.get("dia_longo"),
        equipamento=Equipamento(**(j.get("equipamento") or {})),
        ftp=_valor(j.get("ftp")), fc_limiar=_valor(j.get("fc_limiar")), fc_max=_valor(j.get("fc_max")),
        fc_repouso=_valor(j.get("fc_repouso")), altura_cm=j.get("altura_cm"),
        anos_treino_estruturado=j.get("anos_treino_estruturado"),
        consentimento_responsavel=bool(j.get("consentimento_responsavel", False)),
        onde_treina=j.get("onde_treina"), provas=provas, ciclo=j.get("ciclo"), agressividade=j.get("agressividade"),
        historico_ftp=tuple(RegistoFTP(date.fromisoformat(r["data"]), float(r["valor"]), r["fonte"])
                            for r in j.get("historico_ftp", [])),
        ftp_modo=j.get("ftp_modo", "automatico"),
    )


def atleta_para_json(a: Atleta) -> dict[str, Any]:
    def v(x: Valor | None) -> dict | None:
        return {"valor": x.valor, "fonte": x.fonte} if x else None
    return {
        "nome": a.nome, "data_nascimento": a.data_nascimento.isoformat(), "sexo": a.sexo, "peso_kg": a.peso_kg,
        "nivel": a.nivel, "disciplina": a.disciplina,
        "objetivo": {"tipo": a.objetivo.tipo, "data_prova": a.objetivo.data_prova.isoformat() if a.objetivo.data_prova else None,
                     "nome_prova": a.objetivo.nome_prova},
        "disponibilidade": list(a.disponibilidade), "dia_longo": a.dia_longo,
        "equipamento": {"potenciometro": a.equipamento.potenciometro, "rolo_inteligente": a.equipamento.rolo_inteligente,
                        "cinta_fc": a.equipamento.cinta_fc},
        "ftp": v(a.ftp), "fc_limiar": v(a.fc_limiar), "fc_max": v(a.fc_max), "fc_repouso": v(a.fc_repouso),
        "altura_cm": a.altura_cm, "anos_treino_estruturado": a.anos_treino_estruturado,
        "consentimento_responsavel": a.consentimento_responsavel, "onde_treina": a.onde_treina,
        "provas": [{"nome": p.nome, "data": p.data.isoformat(), "prioridade": p.prioridade, "duracao_h": p.duracao_h,
                    "etapas": [{"data": e.data.isoformat(), "duracao_h": e.duracao_h, "descricao": e.descricao} for e in p.etapas]}
                   for p in a.provas],
        "ciclo": a.ciclo, "agressividade": a.agressividade,
        "historico_ftp": [{"data": r.data.isoformat(), "valor": r.valor, "fonte": r.fonte} for r in a.historico_ftp],
        "ftp_modo": a.ftp_modo,
    }
