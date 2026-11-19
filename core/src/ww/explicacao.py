"""Explicações ao atleta a partir do registo de decisão (spec 7.5).

Textos-modelo pré-escritos (PT-PT): são a explicação por defeito e a reserva quando o LLM falha
na validação. Usam só números que estão no registo; nunca conselhos médicos além de "procura um
médico" nos sinais de alarme.
"""

from __future__ import annotations

from typing import Any

SINAIS = {
    "sono_curto": "dormiste {valor} h (abaixo de {limiar} h)",
    "vfc_abaixo": "a tua VFC está abaixo do teu normal ({valor} ms)",
    "fc_repouso_alta": "a tua FC de repouso está acima do normal ({valor})",
    "cansaco": "indicaste cansaço {valor}/5",
    "dores": "indicaste dores musculares {valor}/5",
    "stress": "indicaste stress {valor}/5",
    "humor": "indicaste humor/motivação {valor}/5",
    "frescura_negativa": "acumulaste fadiga (frescura {valor})",
    "frescura_muito_negativa": "acumulaste muita fadiga (frescura {valor})",
    "doenca": "estás doente",
    "alarme": "indicaste um sinal de alarme",
}

REGRAS = {
    "verde_mantem_treino": "Está tudo dentro do teu normal: fazemos o treino planeado.",
    "amarelo_versao_mais_facil": "Mantemos o tipo de treino numa versão mais leve.",
    "amarelo_troca_por_resistencia": "Trocámos a sessão intensa por resistência mais curta.",
    "amarelo_resistencia_mais_curta": "Encurtámos o treino de resistência.",
    "amarelo_teste_adiado": "Adiámos o teste: um teste só é fiável quando estás fresco.",
    "amarelo_mantem_recuperacao": "O treino de hoje já é leve: mantém-se.",
    "vermelho_recuperacao_ativa": "Hoje é para recuperar: pedalada leve e curta.",
    "vermelho_mantem_recuperacao": "Hoje é para recuperar: mantemos a recuperação.",
    "doenca_febre_descanso": "Com febre, descansa. Sem treino até te sentires melhor.",
    "doenca_sem_intensidade": "Enquanto estiveres doente, nada de intensidade: só pedalada leve, se te sentires bem.",
    "doenca_prova_desaconselhada": "Doente, não recomendamos fazer a prova. A decisão é tua.",
    "vermelho_prova_desaconselhada": "Os teus sinais estão fora do normal: não recomendamos fazer a prova. A decisão é tua.",
    "prova_mantida": "Dia de prova. Boa sorte!",
    "prova_mantida_com_alerta": "Dia de prova, com um sinal a vigiar: começa com calma.",
    "alarme_bloqueia_treino": "Não treines hoje e procura um médico. Se for agora e for forte, liga 112.",
    "rampa_limite_reduz_treino": "Reduzimos o treino para a carga não subir depressa demais.",
    "prontidao_apos_prova_A_prolonga_recuperacao": "Depois da prova, ainda não estás pronto para voltar à carga: mais uns dias leves.",
    "dia_de_descanso": "Hoje é dia de descanso.",
}


def _fmt(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:g}".replace(".", ",")
    return str(v)


def explicar(registo: dict[str, Any]) -> str:
    """Uma ou duas frases, com os números do registo."""
    sinais = [SINAIS[s["codigo"]].format(valor=_fmt(s["valor"]), limiar=_fmt(s["limiar"]))
              for s in registo.get("sinais", []) if s["codigo"] in SINAIS]
    regra = next((REGRAS[r.split(":")[0]] for r in registo.get("regras", []) if r.split(":")[0] in REGRAS), "")
    if "alarme_bloqueia_treino" in registo.get("regras", []):
        return REGRAS["alarme_bloqueia_treino"]
    if sinais:
        frase = sinais[0][0].upper() + sinais[0][1:]
        if len(sinais) > 1:
            frase += " e " + " e ".join(sinais[1:])
        texto = f"{frase}. {regra}".strip()
    else:
        texto = regra
    if registo.get("dados_em_falta") and registo.get("estado") != "bloqueado":
        falta = [d for d in registo["dados_em_falta"] if d in ("vfc", "questionario")]
        if falta:
            texto += " (Decidido sem " + " nem ".join("VFC" if d == "vfc" else "questionário" for d in falta) + ".)"
    return texto
