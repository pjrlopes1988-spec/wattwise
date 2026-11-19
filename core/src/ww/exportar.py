"""Exportação de treinos para o dispositivo do atleta (spec 3: .ZWO/.ERG/.MRC no MVP; D-057).

- ZWO: alvos em % do FTP (o dispositivo/app aplica o FTP do atleta).
- ERG: alvos em watts (precisa do FTP); MRC: alvos em % do FTP.
Passos com alvo em intervalo usam o meio do intervalo no ERG/MRC (o formato só aceita um valor).
O envio automático para o dispositivo fica para uma fase posterior (spec 3).
"""

from __future__ import annotations

import re
import unicodedata
import xml.etree.ElementTree as ET

from ww.treinos import Passo, Treino


def nome_ficheiro(t: Treino, extensao: str) -> str:
    base = unicodedata.normalize("NFKD", t.titulo).encode("ascii", "ignore").decode()
    base = re.sub(r"[^A-Za-z0-9]+", "_", base).strip("_")
    return f"Wattwise_{base}.{extensao}"


def _f(x: float) -> str:
    return f"{x / 100:.4f}".rstrip("0").rstrip(".")


def _cadencia(el: ET.Element, p: Passo) -> None:
    if p.cadencia:
        lo, hi = p.cadencia
        if lo == hi:
            el.set("Cadence", str(lo))
        else:
            el.set("CadenceLow", str(lo))
            el.set("CadenceHigh", str(hi))


def para_zwo(t: Treino) -> str:
    raiz = ET.Element("workout_file")
    ET.SubElement(raiz, "author").text = "Wattwise"
    ET.SubElement(raiz, "name").text = t.titulo
    ET.SubElement(raiz, "description").text = t.descricao
    ET.SubElement(raiz, "sportType").text = "bike"
    tags = ET.SubElement(raiz, "tags")
    ET.SubElement(tags, "tag", name="Wattwise")
    ET.SubElement(tags, "tag", name=t.tipo)
    wk = ET.SubElement(raiz, "workout")
    for p in t.passos:
        if p.rampa:
            ini, fim = (p.pct_min, p.pct_max) if p.rampa == "sobe" else (p.pct_max, p.pct_min)
            el = ET.SubElement(wk, "Ramp", Duration=str(p.segundos), PowerLow=_f(ini), PowerHigh=_f(fim))
        elif p.pct_min == p.pct_max:
            el = ET.SubElement(wk, "SteadyState", Duration=str(p.segundos), Power=_f(p.pct_min))
        else:
            el = ET.SubElement(wk, "SteadyState", Duration=str(p.segundos), PowerLow=_f(p.pct_min), PowerHigh=_f(p.pct_max))
        _cadencia(el, p)
    ET.indent(raiz)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(raiz, encoding="unicode") + "\n"


def _curso(t: Treino, unidade: str, valor) -> str:  # type: ignore[no-untyped-def]
    linhas = []
    tempo = 0.0
    for p in t.passos:
        if p.rampa:
            ini, fim = (p.pct_min, p.pct_max) if p.rampa == "sobe" else (p.pct_max, p.pct_min)
        else:
            ini = fim = p.pct_medio
        linhas.append(f"{tempo:.2f}\t{valor(ini)}")
        tempo += p.segundos / 60
        linhas.append(f"{tempo:.2f}\t{valor(fim)}")
    desc = t.descricao.replace("\n", " ")
    return "\n".join([
        "[COURSE HEADER]", "VERSION = 2", "UNITS = ENGLISH", f"DESCRIPTION = {t.titulo}. {desc}",
        f"FILE NAME = {nome_ficheiro(t, unidade)}", *([f"FTP = {round(valor.ftp)}"] if hasattr(valor, "ftp") else []),
        f"MINUTES {'WATTS' if unidade == 'erg' else 'PERCENT'}", "[END COURSE HEADER]", "[COURSE DATA]",
        *linhas, "[END COURSE DATA]", "",
    ])


class _Watts:
    def __init__(self, ftp: float) -> None:
        self.ftp = ftp

    def __call__(self, pct: float) -> str:
        return str(round(self.ftp * pct / 100))


def para_erg(t: Treino, ftp: float) -> str:
    if ftp <= 0:
        raise ValueError("o ERG precisa de um FTP positivo")
    return _curso(t, "erg", _Watts(ftp))


def para_mrc(t: Treino) -> str:
    return _curso(t, "mrc", lambda pct: f"{pct:.1f}")
