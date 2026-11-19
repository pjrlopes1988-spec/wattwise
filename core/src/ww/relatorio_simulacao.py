"""Relatório da simulação de temporada (Fase 3, spec 10.4) para validação pelo treinador.

    python -m ww.relatorio_simulacao SAIDA.md
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from ww.config import carregar
from ww.perfil import completar
from ww.simulacao import simular
from ww.treinos import carregar as carregar_lib

NOMES_REGRAS = {
    "verde_mantem_treino": "verde: treino mantido",
    "amarelo_versao_mais_facil": "amarelo: versão mais fácil",
    "amarelo_resistencia_mais_curta": "amarelo: resistência mais curta",
    "amarelo_troca_por_resistencia": "amarelo: troca por resistência",
    "amarelo_teste_adiado": "amarelo: teste adiado",
    "amarelo_mantem_recuperacao": "amarelo: recuperação mantida",
    "vermelho_recuperacao_ativa": "vermelho: recuperação ativa",
    "vermelho_mantem_recuperacao": "vermelho: recuperação mantida",
    "doenca_febre_descanso": "doença com febre: descanso",
    "doenca_sem_intensidade": "doença: recuperação, sem intensidade",
    "doenca_prova_desaconselhada": "doença: prova desaconselhada",
    "vermelho_prova_desaconselhada": "vermelho: prova desaconselhada",
    "prova_mantida": "prova mantida",
    "prova_mantida_com_alerta": "prova mantida com alerta",
    "alarme_bloqueia_treino": "ALARME: treino bloqueado, procurar médico",
    "rampa_limite_reduz_treino": "guarda da rampa: treino reduzido",
    "prontidao_apos_prova_A_prolonga_recuperacao": "após prova A: recuperação prolongada",
    "dia_de_descanso": "dia de descanso",
}
NOMES_SINAIS = {
    "frescura_negativa": "frescura negativa", "frescura_muito_negativa": "frescura muito negativa",
    "sono_curto": "sono curto", "cansaco": "cansaço", "dores": "dores musculares", "stress": "stress",
    "humor": "humor baixo", "vfc_abaixo": "VFC abaixo do normal", "fc_repouso_alta": "FC de repouso alta",
    "doenca": "doença", "alarme": "sinal de alarme",
}


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
    from cenarios import CENARIOS, HOJE, INICIO  # type: ignore[import-not-found]
    from test_simulacao import CASOS  # type: ignore[import-not-found]

    cfg = carregar()
    lib = carregar_lib()
    saida = Path(sys.argv[1] if len(sys.argv) > 1 else "simulacao_fase3.md")
    out = ["# Wattwise — Simulação de temporada (Fase 3)", "",
           f"Motor v{cfg.motor.versao}, configuração `{cfg.versao}`. Cada cenário: 182 dias (6 meses) dia a dia. "
           "O atleta simulado falha treinos, às vezes faz mais do que o previsto, vai a voltas de grupo, dorme mal "
           "e fica doente; a VFC, a FC de repouso e o cansaço reagem à fadiga. O motor decide cada manhã.", "",
           "**Critério da Fase 3 (spec 11):** nenhuma violação dos limites de segurança (spec 7.3), verificados dia a "
           "dia sobre as prescrições do motor: nada com sinal de alarme; sem intensidade com doença; dias vermelhos "
           "só com recuperação/descanso; nunca mais de 2 dias seguidos de alta intensidade (contando o que o atleta "
           "fez de facto, incluindo voltas de grupo); a Condição nunca sobe mais do que a rampa do nível em 7 dias "
           "(com a carga real); recuperação pelo menos a cada 4 semanas.", "",
           "| Cenário | Violações | Verde | Amarelo | Vermelho | Bloqueado | Condição semana 4 → 26 | Treinos feitos |",
           "|---|---|---|---|---|---|---|---|"]
    detalhes = []
    for nome, (cenario, comp) in CASOS.items():
        a = completar(CENARIOS[cenario], HOJE, cfg)
        r = simular(a, lib, cfg, inicio=INICIO, dias=182, comportamento=comp)
        e = r.contagem_estados()
        n = len(r.dias)
        pct = lambda k: f"{100 * e.get(k, 0) / n:.0f}%"  # noqa: E731
        feitos = sum(1 for d in r.dias if d.feito is not None)
        out.append(f"| {nome.replace('_', ' ')} | **{len(r.violacoes)}** | {pct('verde')} | {pct('amarelo')} | "
                   f"{pct('vermelho')} | {e.get('bloqueado', 0)} | {r.dias[27].condicao:.0f} → {r.dias[-1].condicao:.0f} | {feitos} |")
        sinais = Counter(s.codigo for d in r.dias for s in d.prontidao.sinais)
        regras = Counter(x.split(":")[0] for d in r.dias for x in d.decisao.regras)
        comport = (f"cumprimento {comp.cumprimento:.0%}, faz mais {comp.excesso_prob:.0%} das vezes, volta de grupo "
                   f"{comp.volta_grupo_prob:.0%} dos sábados livres" + (", sem VFC" if not comp.com_vfc else "")
                   + (f", doença {comp.doencas}" if comp.doencas else "") + (f", alarme no dia {comp.alarme_dia}" if comp.alarme_dia else ""))
        detalhes += ["", f"## {nome.replace('_', ' ').capitalize()}", "", f"Atleta: {a.nome} ({a.nivel}). Comportamento: {comport}.", "",
                     "**Sinais mais frequentes:** " + ", ".join(f"{NOMES_SINAIS.get(k, k)} ({v})" for k, v in sinais.most_common(6)), "",
                     "**Decisões:** " + ", ".join(f"{NOMES_REGRAS.get(k, k)} ({v})" for k, v in regras.most_common(10))]
        exemplo = next((d for d in r.dias if d.decisao.estado in ("amarelo", "vermelho") and d.decisao.treino_original), None)
        if exemplo:
            reg = exemplo.decisao.registo()
            orig = reg["treino_original"]["opcoes"]
            final = reg["treino_final"]["opcoes"] if reg["treino_final"] else None
            detalhes += ["", f"Exemplo ({exemplo.data:%d/%m}): estado **{reg['estado']}**; sinais: "
                         + ", ".join(f"{NOMES_SINAIS.get(s['codigo'], s['codigo'])} = {s['valor']} (limiar {s['limiar']})" for s in reg["sinais"])
                         + f"; planeado: {', '.join(x['nome'] + ' ' + str(x['minutos']) + ' min' for x in orig.values())}"
                         + f" → final: {', '.join(x['nome'] + ' ' + str(x['minutos']) + ' min' for x in final.values()) if final else 'descanso'}"
                         + (f"; dados em falta: {', '.join(reg['dados_em_falta'])}" if reg["dados_em_falta"] else "")]
    out += detalhes
    out += ["", "---", "", "## Perguntas para o Paulo", "",
            "1. A proporção de dias amarelos/vermelhos parece-te realista? (limiares em `config/motor.yaml` → `motor`)",
            "2. Frescura: sinal abaixo de −30% e vermelho abaixo de −45% (ou −25/−40 absolutos com Condição < 30). "
            "É o sinal que mais dispara — os limiares estão bem?",
            "3. Amarelo numa sessão-chave: versão mais fácil do mesmo tipo (até 75% da carga). Preferes menos repetições?",
            "4. Dia de prova vermelho: a app desaconselha a prova, mas o atleta pode fazê-la. Para provas A, outro comportamento?",
            "5. VFC: vermelho direto ao 3.º dia seguido abaixo da faixa. Concordas?", ""]
    saida.write_text("\n".join(out), encoding="utf-8")
    print(f"relatório → {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
