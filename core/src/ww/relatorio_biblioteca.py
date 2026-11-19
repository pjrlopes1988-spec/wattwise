"""Página da biblioteca de treinos para revisão pelo treinador.

    python -m ww.relatorio_biblioteca SAIDA.md
"""

from __future__ import annotations

import sys
from pathlib import Path

from ww.alvos import resumir
from ww.config import carregar as carregar_cfg
from ww.plano import alta_intensidade
from ww.treinos import carregar

FAMILIAS = [
    ("Rios — recuperação e resistência", ("recuperacao", "resistencia")),
    ("Serras — tempo", ("tempo",)),
    ("Serras — sweet spot", ("sweetspot",)),
    ("Subidas míticas — limiar", ("limiar",)),
    ("Ventos — VO2máx", ("vo2max",)),
    ("Ventos — anaeróbio", ("anaerobio",)),
    ("Castelos — força", ("forca",)),
    ("Faróis — testes", ("teste",)),
]


def main() -> int:
    cfg = carregar_cfg()
    lib = carregar()
    saida = Path(sys.argv[1] if len(sys.argv) > 1 else "biblioteca.md")
    n_paulo = sum(t.origem == "paulo" for t in lib.values())
    out = ["# Wattwise — Biblioteca de treinos", "",
           f"{len(lib)} treinos: {len(lib) - n_paulo} originais Wattwise (estruturas genéricas, escritas de raiz) "
           f"e {n_paulo} do Paulo (🅿). Alvos em % do FTP. Para o Paulo rever: tipo, dificuldade (1–5), "
           "estrutura e descrição. Editar em `config/treinos.yaml`, `config/treinos_paulo.yaml` e "
           "`config/nomes_treinos.yaml`.", ""]
    for titulo, tipos in FAMILIAS:
        ts = sorted((t for t in lib.values() if t.tipo in tipos), key=lambda t: (t.dificuldade, t.minutos))
        out += [f"## {titulo}", "", "| Nome | Treino | Dif. | Min | Carga | Alta int. | Estrutura |",
                "|---|---|---|---|---|---|---|"]
        for t in ts:
            estrutura = " → ".join(resumir(t.passos, ftp=100, fc_limiar=None, potencia=True, cfg=cfg))
            estrutura = estrutura.replace(" W", "%")
            out.append(f"| **{t.nome}**{' 🅿' if t.origem == 'paulo' else ''} | {t.subtitulo} | {t.dificuldade} | "
                       f"{t.minutos:.0f} | {t.carga:.0f} | {'sim' if alta_intensidade(t, cfg) else ''} | {estrutura} |")
        out.append("")
    saida.write_text("\n".join(out), encoding="utf-8")
    print(f"{len(lib)} treinos → {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
