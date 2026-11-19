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
    n_out = sum(t.ambiente == "outdoor" for t in lib.values())
    n_in = sum(t.ambiente == "indoor" for t in lib.values())
    n_paulo = sum(t.origem == "paulo" for t in lib.values())
    bases_com_indoor = {t.base for t in lib.values() if t.ambiente == "indoor"}
    bases_com_outdoor = {t.base for t in lib.values() if t.ambiente == "outdoor"}
    out = ["# Wattwise — Biblioteca de treinos", "",
           f"**{n_out} treinos outdoor** (alvos em intervalo: terreno, vento, trânsito) e **{n_in} indoor** "
           f"(alvos fixos para o rolo em modo ERG; até {cfg.indoor.duracao_max_min} min), dos quais {n_paulo} "
           "do Paulo (🅿). O atleta escolhe onde treina; o plano usa a biblioteca desse ambiente (D-058).", "",
           "Cada linha é um treino; a coluna *Onde* diz se existe em 🌳 outdoor, 🏠 indoor ou ambos. A estrutura "
           "mostrada é a outdoor (a indoor usa o alvo fixo do meio do intervalo). Alvos em % do FTP.", "",
           "Editar: `config/treinos_outdoor.yaml`, `config/treinos_indoor.yaml` (geradas por "
           "`core/tools/gerar_biblioteca.py`), `config/treinos_paulo.yaml`, `config/nomes_treinos.yaml`.", ""]
    # um treino por base: a versão outdoor, ou a indoor se só existir indoor (ex.: os do Paulo)
    por_base: dict[str, object] = {}
    for t in lib.values():
        if t.base not in por_base or t.ambiente == "outdoor":
            por_base[t.base] = t
    for titulo, tipos in FAMILIAS:
        ts = sorted((t for t in por_base.values() if t.tipo in tipos), key=lambda t: (t.dificuldade, t.minutos))  # type: ignore[attr-defined]
        out += [f"## {titulo}", "", "| Nome | Treino | Dif. | Min | Carga | Onde | Alta int. | Estrutura |",
                "|---|---|---|---|---|---|---|---|"]
        for t in ts:  # type: ignore[assignment]
            estrutura = " → ".join(resumir(t.passos, ftp=100, fc_limiar=None, potencia=True, cfg=cfg))
            estrutura = estrutura.replace(" W", "%")
            onde = " ".join(x for x, b in (("🌳", t.base in bases_com_outdoor), ("🏠", t.base in bases_com_indoor)) if b)
            out.append(f"| **{t.nome}**{' 🅿' if t.origem == 'paulo' else ''} | {t.subtitulo} | {t.dificuldade} | "
                       f"{t.minutos:.0f} | {t.carga:.0f} | {onde} | {'sim' if alta_intensidade(t, cfg) else ''} | {estrutura} |")
        out.append("")
    saida.write_text("\n".join(out), encoding="utf-8")
    print(f"{len(lib)} treinos → {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
