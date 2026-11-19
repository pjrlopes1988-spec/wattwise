"""Relatório dos planos dos cenários de teste, para validação pelo treinador (spec 10.3, Fase 2).

    python -m ww.relatorio_plano SAIDA.md
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from ww.alvos import resumir
from ww.config import Config, carregar
from ww.perfil import DIAS, Atleta, completar
from ww.plano import Plano, gerar
from ww.treinos import carregar as carregar_lib

NOMES_FASE = {"base": "Base", "construcao": "Construção", "especifico": "Específico",
              "recuperacao": "Recuperação", "afinacao": "Afinação"}


def _perfil_md(a: Atleta, idade: int) -> list[str]:
    def v(x):
        return "—" if x is None else f"{x.valor:.0f}" + (" (estimado)" if x.estimado else "")
    disp = ", ".join(f"{DIAS[i][:3]} {m} min" for i, m in enumerate(a.disponibilidade) if m)
    obj = a.objetivo.tipo + (f" — {a.objetivo.nome_prova} em {a.objetivo.data_prova:%d/%m/%Y}" if a.objetivo.data_prova else "")
    eq = ", ".join(k for k, on in (("potenciómetro", a.equipamento.potenciometro), ("cinta FC", a.equipamento.cinta_fc),
                                   ("rolo inteligente", a.equipamento.rolo_inteligente)) if on) or "nenhum"
    return [
        f"- **{a.nome}**, {idade} anos, {a.sexo}, {a.peso_kg:.0f} kg — nível **{a.nivel}**, {a.disciplina}",
        f"- Objetivo: {obj}",
        f"- Disponibilidade: {disp}" + (f"; dia longo: {DIAS[a.dia_longo]}" if a.dia_longo is not None else ""),
        f"- Equipamento: {eq}",
        f"- FTP {v(a.ftp)} W · FC limiar {v(a.fc_limiar)} · FC máx. {v(a.fc_max)} · FC repouso {v(a.fc_repouso)}",
    ] + ([f"- Provas: " + "; ".join(f"**{p.prioridade}** {p.nome} ({p.data:%d/%m/%Y}"
                                    + (f", {p.duracao_h:g} h" if p.duracao_h else "") + ")" for p in a.provas)]
         if a.provas else [])


def plano_md(a: Atleta, p: Plano, cfg: Config, *, detalhe_semanas: tuple[int, ...]) -> list[str]:
    out = ["", "| Sem. | Início | Fase | Carga alvo | Planeada | Condição | Subida | Treinos | Notas |",
           "|---|---|---|---|---|---|---|---|---|"]
    for s in p.semanas:
        tipos = Counter(t.treino.tipo if t.papel != "prova" else f"prova {t.prioridade}" for t in s.treinos)
        resumo = ", ".join(f"{n}× {t}" for t, n in tipos.most_common())
        horas = sum(t.minutos for t in s.treinos) / 60
        out.append(f"| {s.numero} | {s.inicio:%d/%m} | {NOMES_FASE[s.fase]} | {s.carga_alvo:.0f} | "
                   f"{s.carga_planeada:.0f} ({horas:.1f} h) | {s.condicao_fim:.1f} | {s.subida_condicao:+.1f} | "
                   f"{resumo} | {'; '.join(s.notas)} |")
    from ww.perfil import tem_potencia
    base_kw = dict(ftp=a.ftp.valor if a.ftp else None, fc_limiar=a.fc_limiar.valor if a.fc_limiar else None, cfg=cfg)
    for n in detalhe_semanas:
        s = p.semanas[n - 1]
        out += ["", f"**Semana {s.numero} — {NOMES_FASE[s.fase]}** (a partir de {s.inicio:%d/%m/%Y})", ""]
        for t in s.treinos:
            out.append(f"- **{DIAS[t.data.weekday()]} {t.data:%d/%m}**{' · ALTA INTENSIDADE' if t.alta_intensidade else ''}")
            for amb_, tr in t.opcoes().items():
                kw = dict(base_kw, potencia=tem_potencia(a, amb_))  # type: ignore[arg-type]
                alvo = " → ".join(resumir(tr.passos, **kw)) if t.papel != "prova" else "prova"
                local = "🏠 indoor" if amb_ == "indoor" else "🌳 outdoor"
                out.append(f"  - {local} · {tr.titulo} · {round(tr.minutos)} min · carga {tr.carga:.0f}  \n    {alvo}")
    return out


def gerar_relatorio(cenarios: dict[str, Atleta], hoje, inicio, cfg: Config) -> str:
    lib = carregar_lib()
    out = [
        "# Wattwise — Planos dos cenários de teste (Fase 2)",
        "",
        f"Gerado com a configuração `{cfg.versao}` e a biblioteca provisória de {len(lib)} treinos. "
        "Atletas **fictícios**. Para o Paulo validar como treinador (spec 10.3).",
        "",
        "**Como ler:** *Carga alvo* = a necessária para subir a Condição o máximo permitido para o nível; "
        "*Planeada* = o que cabe na disponibilidade; *Subida* = variação da Condição na semana "
        f"(limite: {', '.join(f'{k} {v:g}' for k, v in cfg.plano.rampa_condicao_semana.items())}). "
        "Em todos os cenários, verificado por testes automáticos: disponibilidade respeitada, dias de descanso "
        "mínimos, nunca mais de 2 dias seguidos de alta intensidade, recuperação pelo menos a cada 4 semanas, "
        "subida da Condição dentro do limite em quaisquer 7 dias seguidos.",
        "",
        "**Perguntas para o Paulo** estão no fim.",
    ]
    for nome, a0 in cenarios.items():
        a = completar(a0, hoje, cfg)
        p = gerar(a, lib, cfg, inicio=inicio)
        from ww.perfil import semanas_de_carga
        ciclo_txt = f"{semanas_de_carga(a, hoje, cfg)}+1" + (" (automático)" if a.ciclo == "auto" else " (escolha do atleta)")
        semanas_prova = tuple(s.numero for s in p.semanas if any(t.papel == "prova" for t in s.treinos))
        detalhe = (1, 5) + semanas_prova
        out += ["", "---", "", f"## {nome.replace('_', ' ').capitalize()}", ""] + _perfil_md(a, a.idade(hoje))
        out.append(f"- Ciclos: {ciclo_txt}")
        if p.nivel_regras != a.nivel:
            out.append(f"- Regras de treino usadas: **{p.nivel_regras}** (menor de idade)")
        out += plano_md(a, p, cfg, detalhe_semanas=tuple(sorted(set(detalhe))))
    out += ["", "---", "", "## Perguntas para o Paulo", "",
            "1. As fases e a duração de cada uma (base / construção / específico / afinação) fazem sentido?",
            "2. A distribuição das sessões-chave por fase e nível (`sessoes_chave` em `config/motor.yaml`)?",
            "3. A biblioteca de treinos (`config/treinos.yaml`): o que tirar, mudar ou acrescentar?",
            "4. Afinação: a última semana fica com recuperação + ativação na véspera. Preferes manter mais intensidade?",
            "5. Quando a disponibilidade não chega para a carga alvo, o plano fica abaixo do alvo (nunca acima). Concordas?",
            "6. Atletas sem potenciómetro: alvos em FC (zonas de Friel) e esforço percebido nos esforços curtos. Concordas?",
            "7. Atletas com muito pouco tempo (ex.: Eduardo, 2 dias): o plano põe 1 sessão-chave e o resto em "
            "resistência/recuperação. Preferes mais intensidade quando há pouco tempo?",
            "8. Menores (a partir de 10 anos): usam sempre as regras de iniciante. Chega, ou queres regras próprias "
            "para jovens (ex.: sem treinos de limiar/VO2máx abaixo de certa idade)?",
            ""]
    return "\n".join(out)


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
    from cenarios import CENARIOS, HOJE, INICIO  # type: ignore[import-not-found]
    saida = Path(sys.argv[1] if len(sys.argv) > 1 else "cenarios_fase2.md")
    saida.write_text(gerar_relatorio(CENARIOS, HOJE, INICIO, carregar()), encoding="utf-8")
    print(f"relatório → {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
