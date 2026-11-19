"""Importação de dados de bem-estar (VFC, FC repouso, sono) a partir de CSV.

Serve enquanto não há integrações automáticas (Fase 5): o atleta exporta da sua app
(Garmin Connect, HRV4Training, Elite HRV, Intervals.icu…) e carrega o ficheiro.

Formato base (uma linha por dia; colunas opcionais exceto `data`):
    data;fonte;rmssd;sdnn;fc_repouso;sono_h
Outros formatos: passar `mapa` com {nome_da_coluna_no_ficheiro: nome_interno}.
Aceita separador ';' ou ',', vírgula decimal e datas AAAA-MM-DD ou DD/MM/AAAA.
Valores fora de limites plausíveis são rejeitados e reportados, nunca corrigidos.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import date, datetime

from ww.recuperacao import MedicaoVFC

LIMITES = {"rmssd": (3.0, 300.0), "sdnn": (3.0, 400.0), "fc_repouso": (25.0, 120.0), "sono_h": (0.0, 16.0)}
INTERNOS = {"data", "fonte", *LIMITES}


@dataclass
class BemEstar:
    vfc: list[MedicaoVFC] = field(default_factory=list)
    fc_repouso: dict[date, float] = field(default_factory=dict)
    sono_h: dict[date, float] = field(default_factory=dict)
    erros: list[str] = field(default_factory=list)


def _data(txt: str) -> date:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(txt.strip()[:10], fmt).date()
        except ValueError:
            continue
    raise ValueError(f"data inválida: '{txt}'")


def _num(txt: str) -> float | None:
    txt = txt.strip().replace(",", ".")
    return float(txt) if txt else None


def ler(texto: str, *, mapa: dict[str, str] | None = None, fonte: str = "csv") -> BemEstar:
    amostra = texto[:2048]
    sep = ";" if amostra.count(";") >= amostra.count(",") else ","
    leitor = csv.DictReader(io.StringIO(texto), delimiter=sep)
    mapa = {k.strip().lower(): v for k, v in (mapa or {}).items()}

    def nome(col: str) -> str | None:
        c = col.strip().lower()
        n = mapa.get(c, c)
        return n if n in INTERNOS else None

    r = BemEstar()
    if not leitor.fieldnames or "data" not in {nome(c) for c in leitor.fieldnames}:
        r.erros.append("falta a coluna 'data' (use `mapa` para indicar o nome da coluna)")
        return r

    for i, linha in enumerate(leitor, start=2):
        campos = {nome(k): v for k, v in linha.items() if k is not None and nome(k) and v is not None}
        try:
            d = _data(campos["data"])
        except (KeyError, ValueError) as e:
            r.erros.append(f"linha {i}: {e}")
            continue
        f = (campos.get("fonte") or "").strip() or fonte
        for chave, (lo, hi) in LIMITES.items():
            if chave not in campos:
                continue
            try:
                v = _num(campos[chave])
            except ValueError:
                r.erros.append(f"linha {i}: {chave} não é um número ('{campos[chave]}')")
                continue
            if v is None:
                continue
            if not lo <= v <= hi:
                r.erros.append(f"linha {i}: {chave} = {v} fora dos limites plausíveis ({lo}–{hi}); ignorado")
                continue
            if chave in ("rmssd", "sdnn"):
                r.vfc.append(MedicaoVFC(d, f, chave, v))  # type: ignore[arg-type]
            elif chave == "fc_repouso":
                r.fc_repouso[d] = v
            else:
                r.sono_h[d] = v
    return r
