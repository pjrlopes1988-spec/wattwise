"""Relatório de validação cruzada com o Intervals.icu (spec 10.2).

    python -m ww.relatorio analisar PASTA_FIT --ftp 250 --lthr 165 --fcmax 190 --fcrep 50 \
        --sexo M --peso 70 --saida validacao.csv
    (preencher as colunas iv_* com os valores do Intervals.icu)
    python -m ww.relatorio comparar validacao.csv [--limiar 5]

O CSV usa ';' e vírgula decimal para abrir diretamente no Excel em português.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

import numpy as np

from ww.analise import Fisiologia, analisar
from ww.config import Config, carregar
from ww.eftp import esforcos_da_atividade, estimar
from ww.fit.reader import ErroFIT, ler_ficheiro
from ww.metrics.hr import carga_fc, desacoplamento
from ww.metrics.intervalos import detetar
from ww.quality.clean import limpar
from ww.quality.suspeitas import avaliar as avaliar_suspeitas

# (coluna Wattwise, coluna Intervals.icu, descrição)
METRICAS = [
    ("ww_potencia_media", "iv_potencia_media", "Potência média (W)"),
    ("ww_potencia_ponderada", "iv_potencia_ponderada", "Potência ponderada / NP (W)"),
    ("ww_intensidade", "iv_intensidade", "Intensidade / IF"),
    ("ww_carga", "iv_carga", "Carga / Load"),
    ("ww_carga_fc", "iv_carga_fc", "Carga por FC / HRSS"),
    ("ww_fc_media", "iv_fc_media", "FC média"),
    ("ww_desacoplamento_pct", "iv_desacoplamento_pct", "Desacoplamento Pa:Hr (%)"),
    ("ww_melhor_5s", "iv_melhor_5s", "Melhor 5 s (W)"),
    ("ww_melhor_1min", "iv_melhor_1min", "Melhor 1 min (W)"),
    ("ww_melhor_5min", "iv_melhor_5min", "Melhor 5 min (W)"),
    ("ww_melhor_20min", "iv_melhor_20min", "Melhor 20 min (W)"),
    ("ww_melhor_60min", "iv_melhor_60min", "Melhor 60 min (W)"),
]
INFO = ["ficheiro", "data", "duracao_min", "fonte_carga", "qualidade", "suspeitas", "n_intervalos", "erro"]


def _fmt(v: float | None, casas: int = 1) -> str:
    return "" if v is None else f"{v:.{casas}f}".replace(".", ",")


def _num(txt: str | None) -> float | None:
    if txt is None or not txt.strip():
        return None
    return float(txt.strip().replace(",", "."))


def analisar_pasta(ficheiros: Sequence[Path], fis: Fisiologia, peso_kg: float, cfg: Config) -> tuple[list[dict[str, str]], str]:
    linhas: list[dict[str, str]] = []
    esforcos = []
    datas: list[date] = []
    for f in sorted(ficheiros):
        linha = {k: "" for k in INFO} | {c: "" for m in METRICAS for c in m[:2]}
        linha["ficheiro"] = f.name
        try:
            serie = ler_ficheiro(f, cfg.qualidade.pausa_minima_s)
        except (ErroFIT, OSError) as e:
            linha["erro"] = str(e)
            linhas.append(linha)
            continue
        r = analisar(serie, fis, cfg)
        limpa, rel = limpar(serie, cfg.qualidade, fis.fc_max)
        susp = avaliar_suspeitas(limpa, cfg.qualidade)
        d = serie.inicio.date()
        datas.append(d)
        ok = rel.serve_para_modelos(cfg.qualidade) and not susp
        esforcos += esforcos_da_atividade(limpa.potencia, f.name, d, ok, cfg)

        hrss = None
        if limpa.tem_fc and fis.fc_repouso and fis.fc_limiar and fis.fc_max:
            b = cfg.frequencia_cardiaca.hrss_b_masculino if fis.sexo == "M" else cfg.frequencia_cardiaca.hrss_b_feminino
            hrss = carga_fc(limpa.fc, fc_repouso=fis.fc_repouso, fc_limiar=fis.fc_limiar, fc_max=fis.fc_max, b=b)
        curva = r.curva or {}
        linha.update({
            "data": d.isoformat(),
            "duracao_min": _fmt(r.duracao_s / 60),
            "fonte_carga": r.fonte_carga,
            "qualidade": _fmt(rel.indice, 2),
            "suspeitas": " | ".join(s.detalhe for s in susp),
            "n_intervalos": str(len(detetar(limpa, cfg.intervalos, ftp=fis.ftp, fc_limiar=fis.fc_limiar))),
            "ww_potencia_media": _fmt(r.potencia_media),
            "ww_potencia_ponderada": _fmt(r.potencia_ponderada),
            "ww_intensidade": _fmt(r.intensidade, 3),
            "ww_carga": _fmt(r.carga),
            "ww_carga_fc": _fmt(hrss),
            "ww_fc_media": _fmt(r.fc_media),
            "ww_desacoplamento_pct": _fmt(desacoplamento(limpa.potencia, limpa.fc)) if limpa.tem_potencia and limpa.tem_fc else "",
            "ww_melhor_5s": _fmt(curva.get(5)),
            "ww_melhor_1min": _fmt(curva.get(60)),
            "ww_melhor_5min": _fmt(curva.get(300)),
            "ww_melhor_20min": _fmt(curva.get(1200)),
            "ww_melhor_60min": _fmt(curva.get(3600)),
        })
        linhas.append(linha)

    resumo = "Sem esforços válidos para estimar o eFTP."
    if datas:
        hoje = max(datas)
        e = estimar(esforcos, hoje=hoje, inicio_epoca=date(hoje.year, 1, 1), peso_kg=peso_kg, cfg=cfg)
        if e.historico:
            ef = e.historico
            resumo = (f"eFTP (com histórico) a {hoje}: {ef.ftp:.0f} W — método {ef.metodo}, "
                      f"W′ {ef.perfil.w_linha:.0f} J ({ef.perfil.origem}), "
                      f"esforço: {', '.join(f'{x.atividade_id} {x.duracao_s // 60} min {x.potencia:.0f} W' for x in ef.esforcos)}")
    return linhas, resumo


def escrever_csv(linhas: list[dict[str, str]], caminho: Path) -> None:
    colunas = INFO + [c for m in METRICAS for c in m[:2]]
    with caminho.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=colunas, delimiter=";")
        w.writeheader()
        w.writerows(linhas)


def comparar(caminho: Path, limiar_pct: float = 5.0) -> tuple[list[str], int]:
    """Devolve as linhas do relatório e o número de diferenças acima do limiar."""
    with caminho.open(encoding="utf-8-sig") as fh:
        linhas = list(csv.DictReader(fh, delimiter=";"))
    out = [f"Comparação Wattwise vs. Intervals.icu (limiar {limiar_pct:g}%)", ""]
    acima = 0
    for m_ww, m_iv, desc in METRICAS:
        difs = []
        for ln in linhas:
            a, b = _num(ln.get(m_ww)), _num(ln.get(m_iv))
            if a is None or b is None or b == 0:
                continue
            difs.append((ln["ficheiro"], a, b, (a - b) / abs(b) * 100.0))
        if not difs:
            continue
        pct = np.array([d[3] for d in difs])
        maus = [d for d in difs if abs(d[3]) > limiar_pct]
        acima += len(maus)
        estado = "OK" if not maus else f"{len(maus)} ACIMA DO LIMIAR"
        out.append(f"{desc}: n={len(difs)}, diferença média {pct.mean():+.1f}%, máx. {np.abs(pct).max():.1f}% → {estado}")
        for f, a, b, p in maus:
            out.append(f"    {f}: Wattwise {a:g} vs. Intervals {b:g} ({p:+.1f}%)")
    if len(out) == 2:
        out.append("Nenhuma coluna iv_* preenchida.")
    return out, acima


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m ww.relatorio")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analisar")
    a.add_argument("entrada", type=Path, help="pasta com ficheiros .fit (ou um ficheiro)")
    a.add_argument("--ftp", type=float)
    a.add_argument("--lthr", type=float)
    a.add_argument("--fcmax", type=float)
    a.add_argument("--fcrep", type=float)
    a.add_argument("--sexo", choices=["M", "F"], required=True)
    a.add_argument("--peso", type=float, required=True)
    a.add_argument("--saida", type=Path, default=Path("validacao.csv"))
    c = sub.add_parser("comparar")
    c.add_argument("csv", type=Path)
    c.add_argument("--limiar", type=float, default=5.0)
    args = ap.parse_args(argv)

    if args.cmd == "analisar":
        cfg = carregar()
        ent: Path = args.entrada
        fichs = [ent] if ent.is_file() else [p for p in ent.iterdir() if p.suffix.lower() == ".fit"]
        if not fichs:
            print(f"Nenhum ficheiro .fit em {ent}", file=sys.stderr)
            return 1
        fis = Fisiologia(args.sexo, ftp=args.ftp, fc_limiar=args.lthr, fc_max=args.fcmax, fc_repouso=args.fcrep)
        linhas, resumo = analisar_pasta(fichs, fis, args.peso, cfg)
        escrever_csv(linhas, args.saida)
        print(f"{len(linhas)} atividades → {args.saida} (configuração {cfg.versao})")
        print(resumo)
        return 0

    texto, acima = comparar(args.csv, args.limiar)
    print("\n".join(texto))
    return 1 if acima else 0


if __name__ == "__main__":
    raise SystemExit(main())
