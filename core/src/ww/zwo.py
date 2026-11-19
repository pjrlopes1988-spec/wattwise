"""Importação de treinos em formato ZWO (Zwift) para a biblioteca da Wattwise (D-048).

    python -m ww.zwo PASTA_OU_FICHEIROS... --saida config/treinos_paulo.yaml

- Lê Warmup, Cooldown, Ramp, SteadyState, IntervalsT, FreeRide e MaxEffort, com cadência.
- Classifica o tipo e a dificuldade (1–5) a partir dos passos; a classificação é uma
  proposta para o treinador confirmar.
- Treinos fora da bicicleta (sportType ≠ bike ou sem passos) não entram na biblioteca do
  plano; são listados à parte.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import yaml

from ww.treinos import Passo, Treino

CADENCIA_BAIXA = 70   # rpm: trabalho com cadência ≤ isto conta como força


@dataclass(frozen=True)
class Importado:
    ficheiro: str
    treino: Treino | None        # None = fora da bicicleta / sem passos
    autor: str
    tags: tuple[str, ...]
    desporto: str
    motivo: str = ""


def _f(el: ET.Element, *nomes: str) -> float | None:
    for n in nomes:
        v = el.get(n)
        if v is not None:
            return float(v)
    return None


def _cad(el: ET.Element, prefixo: str = "") -> tuple[int, int] | None:
    lo = _f(el, f"{prefixo}CadenceLow")
    hi = _f(el, f"{prefixo}CadenceHigh")
    if lo is not None and hi is not None:
        return (round(lo), round(hi))
    c = _f(el, f"{prefixo}Cadence") if prefixo else _f(el, "Cadence")
    return (round(c), round(c)) if c is not None else None


def _passos(workout: ET.Element) -> list[Passo]:
    out: list[Passo] = []
    for el in workout:
        tag = el.tag
        dur = round(_f(el, "Duration") or 0)
        if tag in ("Warmup", "Cooldown", "Ramp"):
            lo, hi = _f(el, "PowerLow") or 0.5, _f(el, "PowerHigh") or 0.5
            rampa = "sobe" if hi >= lo else "desce"
            out.append(Passo(dur, min(lo, hi) * 100, max(lo, hi) * 100, _cad(el), rampa=rampa))
        elif tag == "SteadyState":
            p = _f(el, "Power")
            lo, hi = (p, p) if p is not None else (_f(el, "PowerLow") or 0.5, _f(el, "PowerHigh") or 0.5)
            out.append(Passo(dur, lo * 100, hi * 100, _cad(el)))
        elif tag == "IntervalsT":
            rep = int(_f(el, "Repeat") or 1)
            on_d, off_d = round(_f(el, "OnDuration") or 0), round(_f(el, "OffDuration") or 0)
            on_p = _f(el, "OnPower")
            on = (on_p, on_p) if on_p is not None else (_f(el, "PowerOnLow") or 1.0, _f(el, "PowerOnHigh") or 1.0)
            off_p = _f(el, "OffPower")
            off = (off_p, off_p) if off_p is not None else (_f(el, "PowerOffLow") or 0.5, _f(el, "PowerOffHigh") or 0.5)
            cad_on = _cad(el)
            cad_off = _cad(el, "Resting") if el.get("CadenceResting") else None
            if cad_off is None and el.get("CadenceResting"):
                c = round(float(el.get("CadenceResting")))  # type: ignore[arg-type]
                cad_off = (c, c)
            for _ in range(rep):
                out.append(Passo(on_d, on[0] * 100, on[1] * 100, cad_on))
                if off_d:
                    out.append(Passo(off_d, off[0] * 100, off[1] * 100, cad_off))
        elif tag == "FreeRide":
            out.append(Passo(dur, 50, 65, _cad(el)))      # sem alvo: assume-se Z2 leve
        elif tag == "MaxEffort":
            out.append(Passo(dur, 150, 200, _cad(el)))
    return [p for p in out if p.segundos > 0]


def _ident(nome: str) -> str:
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    return "paulo_" + re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def classificar(passos: list[Passo]) -> tuple[str, int]:
    """Tipo e dificuldade (1–5) a partir do trabalho (passos ≥ 76% do FTP)."""
    trabalho = [p for p in passos if p.pct_medio >= 76 and not p.rampa]
    t_trab = sum(p.segundos for p in trabalho)
    if t_trab < 60:
        media = sum(p.pct_medio * p.segundos for p in passos) / max(1, sum(p.segundos for p in passos))
        return ("resistencia" if media >= 56 else "recuperacao"), 1
    # zona dominante pelo tempo
    faixas = [("anaerobio", 121, 999), ("vo2max", 106, 121), ("limiar", 95, 106), ("sweetspot", 88, 95), ("tempo", 76, 88)]
    tempo_faixa = {n: sum(p.segundos for p in trabalho if lo <= p.pct_medio < hi) for n, lo, hi in faixas}
    # esforços curtos e muito intensos dominam mesmo com pouco tempo
    if tempo_faixa["anaerobio"] >= 60 and tempo_faixa["anaerobio"] >= 0.3 * t_trab:
        tipo = "anaerobio"
    else:
        tipo = max(tempo_faixa, key=lambda n: tempo_faixa[n])
    baixa = sum(p.segundos for p in trabalho if p.cadencia and p.cadencia[1] <= CADENCIA_BAIXA)
    zona_trab = tipo
    if baixa >= 0.5 * t_trab:
        tipo = "forca"
    minutos = tempo_faixa[zona_trab] / 60 if zona_trab != "forca" else t_trab / 60
    escalas = {   # limites de minutos de trabalho para dificuldade 1, 2, 3, 4 (acima: 5)
        "tempo": (20, 30, 40, 60), "sweetspot": (20, 30, 45, 60), "limiar": (15, 24, 32, 40),
        "vo2max": (10, 15, 20, 24), "anaerobio": (2, 4, 6, 8),
    }
    lim = escalas[zona_trab]
    dif = 1 + sum(minutos > x for x in lim)
    return tipo, dif


def importar_ficheiro(caminho: Path) -> Importado:
    texto = caminho.read_bytes()
    if b"<!DOCTYPE" in texto or b"<!ENTITY" in texto:
        raise ValueError(f"{caminho.name}: XML com DOCTYPE/ENTITY não é aceite")
    raiz = ET.fromstring(texto)
    nome = (raiz.findtext("name") or caminho.stem).strip()
    desc = (raiz.findtext("description") or "").strip()
    autor = (raiz.findtext("author") or "").strip()
    desporto = (raiz.findtext("sportType") or "bike").strip()
    tags = tuple(t.get("name", "") for t in raiz.iter("tag"))
    wk = raiz.find("workout")
    passos = _passos(wk) if wk is not None else []
    if desporto != "bike" or not passos:
        motivo = "fora da bicicleta" if desporto != "bike" else "sem passos"
        return Importado(caminho.name, None, autor, tags, desporto, motivo)
    tipo, dif = classificar(passos)
    t = Treino(_ident(nome), nome, tipo, dif, tuple(passos), descricao=desc, origem="paulo")
    return Importado(caminho.name, t, autor, tags, desporto)


def para_yaml(t: Treino) -> dict:
    passos = []
    for p in t.passos:
        d: dict = {"min": round(p.segundos / 60, 3), "pct": [round(p.pct_min, 1), round(p.pct_max, 1)]}
        if p.cadencia:
            d["cadencia"] = list(p.cadencia)
        if p.rampa:
            d["rampa"] = p.rampa
        passos.append(d)
    return {"id": t.id, "nome": t.nome, "tipo": t.tipo, "dificuldade": t.dificuldade,
            "origem": t.origem, "descricao": t.descricao, "passos": passos}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m ww.zwo")
    ap.add_argument("entradas", nargs="+", type=Path)
    ap.add_argument("--saida", type=Path, required=True)
    args = ap.parse_args(argv)
    fich = sorted({f for e in args.entradas for f in ([e] if e.is_file() else e.rglob("*.zwo"))})
    imp = [importar_ficheiro(f) for f in fich]
    bons = [i.treino for i in imp if i.treino]
    ids = [t.id for t in bons]
    if len(ids) != len(set(ids)):
        print("ids repetidos:", sorted({i for i in ids if ids.count(i) > 1}), file=sys.stderr)
        return 1
    cab = ("# Biblioteca do Paulo — importada de ZWO (python -m ww.zwo). Tipo e dificuldade são\n"
           "# propostas automáticas: o Paulo confirma ou corrige aqui (D-048).\n")
    args.saida.write_text(cab + yaml.safe_dump([para_yaml(t) for t in bons], allow_unicode=True, sort_keys=False,
                                               width=120), encoding="utf-8")
    for i in imp:
        if i.treino:
            t = i.treino
            print(f"OK   {t.nome:40s} {t.tipo:11s} dif {t.dificuldade}  {t.minutos:5.0f} min  carga {t.carga:5.1f}")
        else:
            print(f"FORA {i.ficheiro:40s} ({i.motivo})")
    print(f"{len(bons)} treinos → {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
