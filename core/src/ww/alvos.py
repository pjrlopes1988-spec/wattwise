"""Alvos de cada passo para o atleta: watts (com potenciómetro) ou FC (sem potenciómetro).

Sem potenciómetro (spec 2.4), a zona de potência do passo é convertida na zona de FC de
Friel correspondente. Esforços curtos acima do limiar (< 3 min, Z5+) não são guiáveis pela
FC (a FC demora a subir): usa-se o esforço percebido (D-046).
"""

from __future__ import annotations

from ww.config import Config
from ww.metrics.power import zona
from ww.treinos import Passo

# Zona de potência (Coggan 1–7) → intervalo em % da FC limiar (Friel, ciclismo)
FC_POR_ZONA = {1: (65, 80), 2: (81, 89), 3: (90, 93), 4: (94, 100), 5: (100, 106), 6: None, 7: None}
RPE_POR_ZONA = {1: "2/10", 2: "3–4/10", 3: "5–6/10", 4: "7/10", 5: "8/10", 6: "9/10", 7: "10/10"}


def descrever(p: Passo, *, ftp: float | None, fc_limiar: float | None, potencia: bool, cfg: Config) -> str:
    z = zona(p.pct_medio, 100, cfg.potencia.zonas_coggan_limites_pct)
    cad = ""
    if p.cadencia:
        lo_c, hi_c = p.cadencia
        cad = f", cadência {lo_c} rpm" if lo_c == hi_c else f", cadência {lo_c}–{hi_c} rpm"
    if potencia and ftp:
        a, b = round(ftp * p.pct_min / 100), round(ftp * p.pct_max / 100)
        if p.rampa:
            ini, fim = (a, b) if p.rampa == "sobe" else (b, a)
            return f"rampa {ini}→{fim} W{cad}"
        return (f"{a} W" if a == b else f"{a}–{b} W") + f" (Z{z}){cad}"
    faixa = FC_POR_ZONA[z]
    if faixa is None or (z >= 5 and p.segundos < 180) or not fc_limiar:
        return f"esforço percebido {RPE_POR_ZONA[z]} (Z{z}){cad}"
    return f"{round(fc_limiar * faixa[0] / 100)}–{round(fc_limiar * faixa[1] / 100)} bpm (Z{z}){cad}"


def resumir(passos: tuple[Passo, ...], **kw: object) -> list[str]:
    """Agrupa passos repetidos: '3 × [10 min a 220–232 W; 5 min a 125–150 W]'."""
    linhas: list[str] = []
    i = 0
    n = len(passos)
    while i < n:
        for tam in (2, 1):
            bloco = passos[i:i + tam]
            if len(bloco) < tam:
                continue
            rep = 1
            while passos[i + rep * tam:i + (rep + 1) * tam] == bloco:
                rep += 1
            if rep > 1 or tam == 1:
                txt = "; ".join(_frase(p, descrever(p, **kw)) for p in bloco)  # type: ignore[arg-type]
                linhas.append(f"{rep} × [{txt}]" if rep > 1 else txt)
                i += rep * tam
                break
    return linhas


def _frase(p: Passo, alvo: str) -> str:
    return f"{_dur(p.segundos)} em {alvo}" if alvo.startswith("rampa") else f"{_dur(p.segundos)} a {alvo}"


def _dur(seg: int) -> str:
    return f"{seg // 60} min" if seg % 60 == 0 else (f"{seg} s" if seg < 60 else f"{seg // 60} min {seg % 60} s")
