"""Gera config/treinos.yaml: biblioteca ORIGINAL da Wattwise (D-053, D-054).

Estruturas genéricas de treino (conhecimento comum), escritas de raiz; nada copiado de
outras plataformas (D-052). O Paulo revê e ajusta o YAML gerado; este script serve para
recriar a biblioteca de forma consistente se se quiser mudar o padrão de aquecimento, etc.

    python tools/gerar_biblioteca.py > ../config/treinos.yaml
"""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ww.treinos import _expandir, dificuldade_objetiva  # noqa: E402

AQ = [{"min": 12, "pct": [45, 70], "rampa": "sobe"}]           # aquecimento progressivo
AQ_LONGO = [{"min": 15, "pct": [45, 70], "rampa": "sobe"}]
ARR = [{"min": 8, "pct": [45, 60], "rampa": "desce"}]          # arrefecimento
AQ_CURTO = [{"min": 10, "pct": [45, 72], "rampa": "sobe"}]     # versões até 60 min
ARR_CURTO = [{"min": 5, "pct": [45, 60], "rampa": "desce"}]


def rep(n, *passos):
    return {"repetir": n, "passos": list(passos)}


def p(minutos, lo, hi, cad=None):
    d = {"min": minutos, "pct": [lo, hi]}
    if cad:
        d["cadencia"] = list(cad)
    return d


T = []


SENSACAO = {
    "recuperacao": "Sensação: 1–2/10, muito fácil.",
    "resistencia": "Sensação: 3–4/10, consegues conversar.",
    "tempo": "Sensação nos blocos: 5–6/10, só frases curtas.",
    "sweetspot": "Sensação nos blocos: 6–7/10, exigente mas controlado.",
    "limiar": "Sensação nos blocos: 7–8/10, difícil, só palavras soltas.",
    "vo2max": "Sensação nos esforços: 9/10, respiração no máximo.",
    "anaerobio": "Sensação nos esforços: 10/10, tudo o que tens.",
    "forca": "Sentado, tronco estável, força em todo o círculo da pedalada. Parar se houver dor nos joelhos.",
    "teste": "Fazer descansado, depois de 1–2 dias leves.",
}


def treino(id, nome, tipo, dif, passos, descricao, **extra):
    """`dif` é ignorado: a dificuldade é calculada pela regra única (D-055)."""
    dificuldade = dificuldade_objetiva(_expandir(passos), tipo)
    T.append({"id": id, "nome": nome, "tipo": tipo, "dificuldade": dificuldade, **extra,
              "descricao": f"{descricao} {SENSACAO[tipo]}", "passos": passos})


# ---------------------------------------------------------------- recuperação e resistência
treino("recuperacao", "Recuperação ativa", "recuperacao", 1, [{"min": 30, "pct": [45, 55], "escala": True}],
       "Pedalar muito leve, cadência solta. Ajuda a recuperar sem acrescentar cansaço.", escalavel=True)
treino("recuperacao_cadencia", "Recuperação com cadência 45 min", "recuperacao", 1,
       [p(15, 45, 55), rep(5, p(1, 50, 55, (100, 110)), p(3, 45, 55)), p(10, 45, 55)],
       "Recuperação leve com 5 minutos soltos a cadência alta, para manter a pedalada fluida.")
treino("resistencia", "Resistência Z2", "resistencia", 1,
       [p(10, 50, 60), {"min": 40, "pct": [62, 72], "escala": True}, p(10, 50, 60)],
       "Ritmo de conversa, constante. A base de tudo: mais capacidade aeróbia e melhor uso das gorduras.",
       escalavel=True)
treino("z2_cadencia_90", "Z2 com cadência 90 min", "resistencia", 2,
       AQ + [rep(6, p(9, 62, 72), p(1, 62, 70, (105, 115))), p(12, 60, 70)] + ARR,
       "Z2 com um minuto de cadência alta a cada 10, para trabalhar a eficiência da pedalada sem cansar.")
treino("z2_progressivo_90", "Z2 progressivo 90 min", "resistencia", 2,
       AQ + [p(25, 60, 65), p(25, 65, 70), p(20, 70, 75)] + ARR,
       "Começa calmo e vai subindo dentro da Z2. Ensina a gerir o esforço numa volta longa.")
treino("z2_longo_tempo", "Z2 longo 3 h com tempo no fim", "resistencia", 3,
       AQ_LONGO + [p(120, 62, 72), rep(3, p(10, 76, 85), p(5, 60, 65)), p(5, 55, 65)] + ARR,
       "Três horas em Z2 com três blocos de tempo já cansado, como no final de uma prova longa.")
treino("z2_longo_sweetspot", "Z2 longo 4 h com sweet spot", "resistencia", 4,
       AQ_LONGO + [p(60, 62, 72), rep(2, p(15, 88, 92), p(10, 60, 68)), p(90, 62, 72), p(12, 55, 65)] + ARR,
       "Volta longa com dois blocos de sweet spot a meio. Para provas longas (gran fondo, maratona BTT).")

# ---------------------------------------------------------------- tempo
for id_, nome, dif, n, m, r in [
    ("tempo_2x15", "Tempo 2 × 15 min", 1, 2, 15, 5), ("tempo_3x10", "Tempo 3 × 10 min", 2, 3, 10, 5),
    ("tempo_3x12", "Tempo 3 × 12 min", 2, 3, 12, 4), ("tempo_2x20", "Tempo 2 × 20 min", 3, 2, 20, 5),
    ("tempo_3x15", "Tempo 3 × 15 min", 3, 3, 15, 5), ("tempo_2x30", "Tempo 2 × 30 min", 4, 2, 30, 5),
]:
    treino(id_, nome, "tempo", dif, AQ + [rep(n, p(m, 76, 85), p(r, 50, 60))] + ARR,
           f"{n} blocos de {m} min a ritmo de tempo (76–85% do FTP): esforço firme mas sustentável, "
           "respiração controlada. Melhora a resistência a ritmos médios.")
treino("tempo_60", "Tempo contínuo 60 min", "tempo", 5, AQ_LONGO + [p(60, 76, 85)] + ARR,
       "Uma hora seguida a tempo. Exige concentração e boa alimentação durante o treino.")

# ---------------------------------------------------------------- sweet spot
for id_, nome, dif, n, m, r in [
    ("sweetspot_2x12", "Sweet spot 2 × 12 min", 1, 2, 12, 4), ("sweetspot_3x10", "Sweet spot 3 × 10 min", 2, 3, 10, 5),
    ("sweetspot_4x10", "Sweet spot 4 × 10 min", 2, 4, 10, 4), ("sweetspot_3x12", "Sweet spot 3 × 12 min", 3, 3, 12, 4),
    ("sweetspot_3x15", "Sweet spot 3 × 15 min", 3, 3, 15, 5), ("sweetspot_2x20", "Sweet spot 2 × 20 min", 4, 2, 20, 5),
    ("sweetspot_4x15", "Sweet spot 4 × 15 min", 4, 4, 15, 5), ("sweetspot_2x30", "Sweet spot 2 × 30 min", 5, 2, 30, 5),
]:
    treino(id_, nome, "sweetspot", dif, AQ + [rep(n, p(m, 88, 93), p(r, 50, 60))] + ARR,
           f"{n} blocos de {m} min a sweet spot (88–93% do FTP), logo abaixo do limiar. Muito estímulo "
           "para pouco cansaço: sobe o FTP de forma eficiente.")

# ---------------------------------------------------------------- limiar
for id_, nome, dif, n, m, r in [
    ("limiar_3x8", "Limiar 3 × 8 min", 1, 3, 8, 4), ("limiar_4x6", "Limiar 4 × 6 min", 1, 4, 6, 4),
    ("limiar_4x8", "Limiar 4 × 8 min", 2, 4, 8, 4), ("limiar_3x10", "Limiar 3 × 10 min", 2, 3, 10, 5),
    ("limiar_3x12", "Limiar 3 × 12 min", 3, 3, 12, 5), ("limiar_2x15", "Limiar 2 × 15 min", 3, 2, 15, 6),
    ("limiar_4x10", "Limiar 4 × 10 min", 4, 4, 10, 5), ("limiar_2x20", "Limiar 2 × 20 min", 5, 2, 20, 8),
]:
    treino(id_, nome, "limiar", dif, AQ + [rep(n, p(m, 95, 102), p(r, 50, 60))] + ARR,
           f"{n} blocos de {m} min ao limiar (95–102% do FTP): o ritmo que aguentas cerca de uma hora. "
           "Treino-chave para subir o FTP.")
treino("limiar_sobe_desce", "Limiar sobe e desce 3 × 9 min", "limiar", 4,
       AQ + [rep(3, p(1.5, 95, 97), p(1.5, 103, 106), p(1.5, 95, 97), p(1.5, 103, 106), p(1.5, 95, 97),
                 p(1.5, 103, 106), p(5, 50, 60))] + ARR,
       "Blocos de 9 min a alternar entre ligeiramente abaixo e acima do limiar. Ensina o corpo a "
       "recuperar em esforço, como nas mudanças de ritmo de uma prova.")

# ---------------------------------------------------------------- VO2máx
for id_, nome, dif, n, m, lo, hi in [
    ("vo2_4x3", "VO2máx 4 × 3 min", 1, 4, 3, 106, 115), ("vo2_5x3", "VO2máx 5 × 3 min", 2, 5, 3, 106, 115),
    ("vo2_6x3", "VO2máx 6 × 3 min", 2, 6, 3, 106, 115), ("vo2_5x4", "VO2máx 5 × 4 min", 3, 5, 4, 106, 118),
    ("vo2_6x4", "VO2máx 6 × 4 min", 4, 6, 4, 108, 120), ("vo2_5x5", "VO2máx 5 × 5 min", 5, 5, 5, 106, 115),
]:
    treino(id_, nome, "vo2max", dif, AQ + [rep(n, p(m, lo, hi), p(m, 45, 55))] + ARR,
           f"{n} esforços de {m} min a {lo}–{hi}% do FTP, com recuperação igual. Duro: a respiração fica "
           "no máximo. Aumenta a potência aeróbia máxima.")
treino("vo2_piramide", "VO2máx pirâmide 2-3-4-3-2", "vo2max", 3,
       AQ + [p(2, 110, 120), p(2, 45, 55), p(3, 108, 115), p(3, 45, 55), p(4, 106, 112), p(4, 45, 55),
             p(3, 108, 115), p(3, 45, 55), p(2, 110, 120), p(5, 45, 55)] + ARR,
       "Esforços de 2, 3, 4, 3 e 2 min acima do limiar. Variedade mental com o mesmo estímulo de VO2máx.")
treino("vo2_30_30", "VO2máx 3 × 8 × 30/30 s", "vo2max", 3,
       AQ + [rep(3, rep(8, p(0.5, 115, 125), p(0.5, 45, 55)), p(5, 45, 55))] + ARR,
       "Três séries de 8 × (30 s forte / 30 s leve). Acumula muito tempo perto do VO2máx com esforços curtos.")
treino("vo2_40_20", "VO2máx 2 × 10 × 40/20 s", "vo2max", 4,
       AQ + [rep(2, rep(10, p(40 / 60, 118, 125), p(20 / 60, 45, 55)), p(6, 45, 55))] + ARR,
       "Duas séries de 10 × (40 s forte / 20 s leve). Recuperação curta: muito exigente.")
treino("vo2_ativacao", "Ativação pré-prova 3 × 1 min", "vo2max", 1,
       [p(20, 55, 70), rep(3, p(1, 110, 120), p(3, 45, 55)), p(10, 50, 60)],
       "Treino curto para a véspera da prova: acorda as pernas sem cansar.")

# ---------------------------------------------------------------- anaeróbio
treino("sprints_6x15s", "Sprints 6 × 15 s", "anaerobio", 1,
       AQ + [rep(6, p(0.25, 150, 200), p(4.75, 45, 55))] + ARR,
       "Seis sprints de 15 s com recuperação longa. Potência e explosão, sem acumular cansaço.")
treino("anaerobio_8x30s", "Anaeróbio 8 × 30 s", "anaerobio", 2,
       AQ + [rep(8, p(0.5, 130, 150), p(4.5, 45, 55))] + ARR,
       "Oito esforços de 30 s muito fortes. Treina a capacidade de ataque e de responder a mudanças de ritmo.")
treino("anaerobio_6x45s", "Anaeróbio 6 × 45 s", "anaerobio", 3,
       AQ + [rep(6, p(0.75, 125, 140), p(4.25, 45, 55))] + ARR,
       "Seis esforços de 45 s. Para provas com subidas curtas e muitas acelerações (XCO, critérios).")
treino("anaerobio_2x5x1", "Anaeróbio 2 × 5 × 1 min", "anaerobio", 4,
       AQ + [rep(2, rep(5, p(1, 120, 130), p(2, 45, 55)), p(6, 45, 55))] + ARR,
       "Duas séries de 5 × 1 min muito forte. Muito exigente: só com boa base.")

# ---------------------------------------------------------------- força
treino("forca_5x5", "Força 5 × 5 min em cadência baixa", "forca", 2,
       AQ + [rep(5, p(5, 78, 82, (50, 60)), p(3, 50, 60))] + ARR,
       "Cinco blocos de 5 min a tempo com cadência de 50–60 rpm, sentado. Força específica para subir.")
treino("forca_3x10", "Força 3 × 10 min a 60 rpm", "forca", 3,
       AQ + [rep(3, p(10, 80, 85, (55, 65)), p(5, 50, 60))] + ARR,
       "Três blocos de 10 min a cadência baixa. Tronco estável, força em todo o círculo da pedalada.")
treino("forca_subida_6x4", "Força em subida 6 × 4 min", "forca", 4,
       AQ + [rep(6, p(4, 88, 92, (50, 60)), p(3, 50, 60))] + ARR,
       "Seis blocos de 4 min a sweet spot e cadência muito baixa, como numa subida inclinada.")

# ---------------------------------------------------------------- testes
treino("teste_20min", "Teste de FTP (20 min)", "teste", 3,
       [p(20, 55, 70), p(5, 105, 115), p(10, 50, 60), p(20, 100, 110), p(10, 45, 55)],
       "Teste de 20 min ao máximo sustentável. O FTP estimado é 95% da potência média dos 20 min.")
treino("teste_fc_limiar_30min", "Teste de FC limiar (30 min, sem potenciómetro)", "teste", 3,
       [p(15, 55, 70), p(30, 95, 105), p(10, 45, 55)],
       "30 min ao máximo sustentável. A FC limiar é a FC média dos últimos 20 min.", so_sem_potencia=True)

# ================================================================ alargamento (D-054)
# ---- recuperação e resistência
treino("recuperacao_60", "Recuperação 60 min", "recuperacao", 1, [p(60, 45, 55)],
       "Uma hora muito leve. Para o dia seguinte a uma prova ou a um bloco duro.")
treino("recuperacao_pernas_soltas", "Pernas soltas 40 min", "recuperacao", 1,
       [p(10, 45, 55), rep(4, p(0.5, 50, 55, (110, 120)), p(4.5, 45, 55)), p(10, 45, 55)],
       "Recuperação com quatro acelerações de cadência sem força. Solta as pernas depois de esforços duros.")
treino("z2_2h", "Z2 2 h", "resistencia", 2, AQ_LONGO + [p(97, 62, 72)] + ARR,
       "Duas horas a ritmo de conversa. O treino de base mais importante da semana.")
treino("z2_2h30_sprints", "Z2 2 h 30 com sprints", "resistencia", 3,
       AQ_LONGO + [rep(6, p(20, 62, 72), p(10 / 60, 150, 200), p(50 / 60, 55, 65)), p(9, 62, 72)] + ARR,
       "Duas horas e meia em Z2 com um sprint de 10 s a cada 20 min, para não perder a explosão.")
treino("z2_cadencia_baixa", "Z2 com força 90 min", "resistencia", 2,
       AQ + [rep(4, p(10, 62, 72), p(5, 65, 72, (60, 65))), p(10, 62, 72)] + ARR,
       "Z2 com quatro blocos de 5 min a cadência baixa, ainda em Z2. Força sem intensidade.")
treino("z2_longo_5h", "Z2 longo 5 h", "resistencia", 5,
       AQ_LONGO + [p(270, 60, 70)] + ARR,
       "Cinco horas em Z2. Só para quem prepara provas de mais de 5 h (maratona BTT, ultra). Comer e beber sempre.")

# ---- tempo
treino("tempo_4x10", "Tempo 4 × 10 min", "tempo", 2, AQ + [rep(4, p(10, 76, 85), p(4, 50, 60))] + ARR,
       "Quatro blocos de 10 min a tempo com recuperações curtas.")
treino("tempo_progressivo_3x15", "Tempo progressivo 3 × 15 min", "tempo", 3,
       AQ + [rep(3, p(5, 76, 79), p(5, 80, 83), p(5, 84, 87), p(5, 50, 60))] + ARR,
       "Cada bloco de 15 min sobe de ritmo de 5 em 5 min, do tempo baixo ao alto. Ensina a acabar forte.")
treino("tempo_45", "Tempo contínuo 45 min", "tempo", 4, AQ_LONGO + [p(45, 76, 85)] + ARR,
       "45 minutos seguidos a tempo. Concentração e ritmo constante.")

# ---- sweet spot
treino("sweetspot_5x8", "Sweet spot 5 × 8 min", "sweetspot", 2, AQ + [rep(5, p(8, 88, 93), p(3, 50, 60))] + ARR,
       "Cinco blocos de 8 min a sweet spot. Boa porta de entrada para blocos mais longos.")
treino("sweetspot_com_picos", "Sweet spot com acelerações 3 × 12 min", "sweetspot", 3,
       AQ + [rep(3, rep(6, p(110 / 60, 88, 92), p(10 / 60, 130, 150)), p(5, 50, 60))] + ARR,
       "Blocos de sweet spot com uma aceleração de 10 s a cada 2 min. Simula mudanças de ritmo no pelotão.")
treino("sweetspot_progressivo_2x20", "Sweet spot progressivo 2 × 20 min", "sweetspot", 4,
       AQ + [rep(2, p(10, 88, 90), p(10, 92, 94), p(5, 50, 60))] + ARR,
       "Dois blocos de 20 min: os primeiros 10 no sweet spot baixo, os últimos 10 no alto.")
treino("sweetspot_3x20", "Sweet spot 3 × 20 min", "sweetspot", 5, AQ + [rep(3, p(20, 88, 93), p(5, 50, 60))] + ARR,
       "Uma hora de sweet spot em três blocos. Muito exigente: só com boa base.")

# ---- limiar
treino("limiar_5x5", "Limiar 5 × 5 min", "limiar", 1, AQ + [rep(5, p(5, 95, 100), p(3, 50, 60))] + ARR,
       "Cinco blocos curtos ao limiar. Primeiro contacto com o ritmo de limiar.")
treino("limiar_2x12", "Limiar 2 × 12 min", "limiar", 2, AQ + [rep(2, p(12, 95, 102), p(6, 50, 60))] + ARR,
       "Dois blocos de 12 min ao limiar.")
treino("limiar_3x15", "Limiar 3 × 15 min", "limiar", 4, AQ + [rep(3, p(15, 95, 100), p(6, 50, 60))] + ARR,
       "45 minutos ao limiar em três blocos. Treino-chave de fim de construção.")
treino("limiar_sobe_desce_2x12", "Limiar sobe e desce 2 × 12 min", "limiar", 5,
       AQ + [rep(2, rep(4, p(2, 95, 97), p(1, 108, 112)), p(6, 50, 60))] + ARR,
       "Blocos de 12 min com 1 min acima do limiar a cada 3. Duro: treina a recuperação sob esforço.")
treino("limiar_30", "Limiar contínuo 30 min", "limiar", 5, AQ_LONGO + [p(30, 95, 100)] + ARR,
       "Meia hora seguida ao limiar. Ensaio de contrarrelógio.")

# ---- VO2máx
treino("vo2_8x2", "VO2máx 8 × 2 min", "vo2max", 1, AQ + [rep(8, p(2, 110, 120), p(2, 45, 55))] + ARR,
       "Oito esforços de 2 min com recuperação igual. Introdução ao trabalho de VO2máx.")
treino("vo2_4x4", "VO2máx 4 × 4 min", "vo2max", 2, AQ + [rep(4, p(4, 106, 115), p(4, 45, 55))] + ARR,
       "Quatro esforços de 4 min: o formato clássico para subir a potência aeróbia máxima.")
treino("vo2_15_15", "VO2máx 2 × 12 × 15/15 s", "vo2max", 2,
       AQ + [rep(2, rep(12, p(0.25, 120, 130), p(0.25, 45, 55)), p(6, 45, 55))] + ARR,
       "Duas séries de 12 × (15 s forte / 15 s leve). Muito tempo perto do VO2máx com pouca acidez.")
treino("vo2_arranque_5x4", "VO2máx com arranque 5 × 4 min", "vo2max", 4,
       AQ + [rep(5, p(0.5, 130, 140), p(3.5, 106, 112), p(4, 45, 55))] + ARR,
       "Cada esforço começa com 30 s muito fortes e depois estabiliza acima do limiar. Leva o coração ao máximo mais cedo.")
treino("vo2_3x6", "VO2máx 3 × 6 min", "vo2max", 5, AQ + [rep(3, p(6, 105, 110), p(5, 45, 55))] + ARR,
       "Três esforços longos acima do limiar. Muito exigente física e mentalmente.")

# ---- anaeróbio
treino("sprints_10x10s", "Sprints 10 × 10 s", "anaerobio", 1, AQ + [rep(10, p(10 / 60, 170, 220), p(170 / 60, 45, 55))] + ARR,
       "Dez sprints curtíssimos, sentado e de pé, com recuperação completa. Velocidade pura.")
treino("anaerobio_6x1", "Anaeróbio 6 × 1 min", "anaerobio", 3, AQ + [rep(6, p(1, 120, 130), p(4, 45, 55))] + ARR,
       "Seis esforços de 1 min muito fortes com recuperação longa.")
treino("anaerobio_10x30s", "Anaeróbio 10 × 30 s", "anaerobio", 3, AQ + [rep(10, p(0.5, 130, 150), p(2.5, 45, 55))] + ARR,
       "Dez esforços de 30 s com recuperação curta. Repetir ataques.")
treino("anaerobio_20_10", "Anaeróbio 2 × 8 × 20/10 s", "anaerobio", 4,
       AQ + [rep(2, rep(8, p(20 / 60, 140, 160), p(10 / 60, 40, 50)), p(8, 45, 55))] + ARR,
       "Duas séries de 8 × (20 s máximo / 10 s parado). Muito curto e muito duro.")
treino("anaerobio_5x2", "Anaeróbio 5 × 2 min", "anaerobio", 5, AQ + [rep(5, p(2, 118, 125), p(4, 45, 55))] + ARR,
       "Cinco esforços de 2 min bem acima do VO2máx. Para provas com subidas curtas e duras.")

# ---- força
treino("forca_arranques_8x20s", "Arranques 8 × 20 s em cadência baixa", "forca", 2,
       AQ + [rep(8, p(20 / 60, 140, 160, (40, 60)), p(160 / 60, 45, 55))] + ARR,
       "Oito arranques de 20 s a partir de cadência muito baixa, sentado. Força explosiva.")
treino("forca_tempo_2x20", "Força a tempo 2 × 20 min", "forca", 3,
       AQ + [rep(2, p(20, 78, 85, (55, 65)), p(5, 50, 60))] + ARR,
       "Dois blocos longos a tempo e cadência baixa. Resistência de força para subidas longas.")
treino("forca_limiar_4x5", "Força ao limiar 4 × 5 min", "forca", 4,
       AQ + [rep(4, p(5, 95, 100, (50, 60)), p(5, 50, 60))] + ARR,
       "Quatro blocos ao limiar com cadência de 50–60 rpm. Exigente para os joelhos: só com boa base de força.")

# ================================================================ cobertura completa (D-056)
# Versões até 60 min (dias de semana) nos níveis em que faltavam, e níveis com menos de 2 treinos.
treino("tempo_2x18_curto", "Tempo 2 × 18 min (55 min)", "tempo", 0, AQ_CURTO + [rep(2, p(18, 76, 85), p(3, 50, 60))] + ARR_CURTO,
       "Dois blocos de 18 min a tempo, em menos de uma hora.")
treino("tempo_40_curto", "Tempo contínuo 40 min (55 min)", "tempo", 0, AQ_CURTO + [p(40, 76, 85)] + ARR_CURTO,
       "Quarenta minutos seguidos a tempo, com aquecimento curto.")
treino("tempo_3x13_curto", "Tempo 3 × 13 min (59 min)", "tempo", 0, AQ_CURTO + [rep(3, p(13, 76, 85), p(2, 50, 60))] + ARR_CURTO,
       "Três blocos de 13 min a tempo com recuperações curtas.")
treino("tempo_3x25", "Tempo 3 × 25 min", "tempo", 0, AQ_LONGO + [rep(3, p(25, 76, 85), p(5, 50, 60))] + ARR,
       "Setenta e cinco minutos de tempo em três blocos. Para provas longas.")
treino("sweetspot_2x14_curto", "Sweet spot 2 × 14 min (48 min)", "sweetspot", 0,
       AQ_CURTO + [rep(2, p(14, 88, 93), p(3, 50, 60))] + ARR_CURTO,
       "Dois blocos de 14 min a sweet spot em menos de uma hora.")
treino("sweetspot_3x11_curto", "Sweet spot 3 × 11 min (55 min)", "sweetspot", 0,
       AQ_CURTO + [rep(3, p(11, 88, 93), p(3, 50, 60))] + ARR_CURTO,
       "Três blocos de 11 min a sweet spot com recuperações curtas.")
treino("sweetspot_2x20_curto", "Sweet spot 2 × 20 min (59 min)", "sweetspot", 0,
       AQ_CURTO + [p(20, 88, 93), p(4, 50, 60), p(20, 88, 93)] + ARR_CURTO,
       "Dois blocos de 20 min a sweet spot, com aquecimento curto, numa hora.")
treino("sweetspot_45_curto", "Sweet spot contínuo 45 min (58 min)", "sweetspot", 0,
       [{"min": 8, "pct": [45, 75], "rampa": "sobe"}, p(45, 88, 92)] + ARR_CURTO,
       "Quarenta e cinco minutos seguidos a sweet spot. Muito exigente para uma hora de treino.")
treino("limiar_3x9_curto", "Limiar 3 × 9 min (51 min)", "limiar", 0, AQ_CURTO + [rep(3, p(9, 95, 102), p(3, 50, 60))] + ARR_CURTO,
       "Três blocos de 9 min ao limiar, em menos de uma hora.")
treino("limiar_2x15_curto", "Limiar 2 × 15 min (50 min)", "limiar", 0, AQ_CURTO + [p(15, 95, 100), p(5, 50, 60), p(15, 95, 100)] + ARR_CURTO,
       "Dois blocos de 15 min ao limiar com aquecimento curto.")
treino("limiar_4x9_curto", "Limiar 4 × 9 min (57 min)", "limiar", 0,
       [{"min": 8, "pct": [45, 75], "rampa": "sobe"}, rep(4, p(9, 95, 100), p(2, 50, 60))] + ARR_CURTO,
       "Quatro blocos de 9 min ao limiar com recuperações curtas. Duro para uma hora.")
treino("vo2_4x6", "VO2máx 4 × 6 min", "vo2max", 0, AQ + [rep(4, p(6, 105, 110), p(5, 45, 55))] + ARR,
       "Quatro esforços longos de VO2máx. Muito exigente.")
treino("vo2_2x8x2", "VO2máx 2 × 8 × 2 min", "vo2max", 0,
       AQ + [rep(2, rep(8, p(2, 112, 118), p(1, 45, 55)), p(6, 45, 55))] + ARR,
       "Duas séries de 8 × 2 min com 1 min de recuperação. Recuperações curtas: muito duro.")
treino("anaerobio_6x30s_curto", "Anaeróbio 6 × 30 s (40 min)", "anaerobio", 0,
       AQ_CURTO + [rep(6, p(0.5, 130, 150), p(3.5, 45, 55))] + ARR_CURTO,
       "Seis esforços de 30 s muito fortes, em 40 minutos.")
treino("anaerobio_4x1", "Anaeróbio 4 × 1 min", "anaerobio", 0, AQ + [rep(4, p(1, 120, 130), p(4, 45, 55))] + ARR,
       "Quatro esforços de 1 min muito fortes, recuperação completa.")
treino("anaerobio_8x1", "Anaeróbio 8 × 1 min", "anaerobio", 0, AQ + [rep(8, p(1, 120, 130), p(3, 45, 55))] + ARR,
       "Oito esforços de 1 min muito fortes. Muito exigente: só com boa base.")
treino("forca_arranques_5x15s", "Arranques 5 × 15 s em cadência baixa", "forca", 0,
       AQ + [rep(5, p(0.25, 140, 160, (40, 60)), p(4.75, 45, 55))] + ARR,
       "Cinco arranques curtos a partir de cadência muito baixa. Introdução à força explosiva.")
treino("forca_z3_3x8", "Força 3 × 8 min a 60 rpm", "forca", 0, AQ + [rep(3, p(8, 76, 80, (55, 65)), p(4, 50, 60))] + ARR,
       "Três blocos de 8 min a tempo baixo e cadência baixa. Primeiro contacto com o trabalho de força.")
treino("forca_limiar_5x6", "Força ao limiar 5 × 6 min", "forca", 0, AQ + [rep(5, p(6, 95, 100, (50, 60)), p(5, 50, 60))] + ARR,
       "Cinco blocos ao limiar em cadência baixa. Muito exigente para os joelhos: só com boa base de força.")
treino("z2_75", "Z2 75 min", "resistencia", 0, AQ + [p(55, 62, 72)] + ARR,
       "Setenta e cinco minutos a ritmo de conversa.")

treino("z2_3h", "Z2 3 h", "resistencia", 0, AQ_LONGO + [p(157, 62, 72)] + ARR,
       "Três horas a ritmo de conversa. Comer e beber desde o início.")
treino("z2_2h_tempo", "Z2 2 h 20 com tempo", "resistencia", 0,
       AQ_LONGO + [p(60, 62, 72), rep(2, p(10, 76, 82), p(10, 62, 70)), p(17, 62, 72)] + ARR,
       "Z2 com dois blocos de 10 min a tempo a meio. Prepara mudanças de ritmo em voltas longas.")
treino("tempo_2x10_curto", "Tempo 2 × 10 min (40 min)", "tempo", 0, AQ_CURTO + [rep(2, p(10, 76, 82), p(3, 50, 60))] + ARR_CURTO,
       "Dois blocos de 10 min a tempo. Introdução ao ritmo de tempo.")
treino("tempo_3x8_curto", "Tempo 3 × 8 min (48 min)", "tempo", 0, AQ_CURTO + [rep(3, p(8, 76, 82), p(3, 50, 60))] + ARR_CURTO,
       "Três blocos de 8 min a tempo, em menos de uma hora.")
treino("sweetspot_3x13_curto", "Sweet spot 3 × 13 min (58 min)", "sweetspot", 0,
       [{"min": 8, "pct": [45, 75], "rampa": "sobe"}, rep(3, p(13, 88, 93), p(2, 50, 60))] + ARR_CURTO,
       "Três blocos de 13 min a sweet spot com recuperações curtas.")
treino("sweetspot_2x22", "Sweet spot 2 × 22 min", "sweetspot", 0, AQ + [rep(2, p(22, 88, 93), p(5, 50, 60))] + ARR,
       "Dois blocos longos de sweet spot.")
treino("limiar_3x5_curto", "Limiar 3 × 5 min (42 min)", "limiar", 0, AQ_CURTO + [rep(3, p(5, 95, 100), p(4, 50, 60))] + ARR_CURTO,
       "Três blocos curtos ao limiar. Primeiro contacto com o ritmo de limiar.")
treino("limiar_3x4_curto", "Limiar 3 × 4 min (39 min)", "limiar", 0, AQ_CURTO + [rep(3, p(4, 95, 100), p(4, 50, 60))] + ARR_CURTO,
       "Três blocos de 4 min ao limiar. O treino de limiar mais acessível.")
treino("limiar_3x11_curto", "Limiar 3 × 11 min (55 min)", "limiar", 0,
       [{"min": 8, "pct": [45, 75], "rampa": "sobe"}, rep(3, p(11, 95, 100), p(3, 50, 60))] + ARR_CURTO,
       "Três blocos de 11 min ao limiar, numa hora.")
treino("vo2_4x5_curto", "VO2máx 4 × 5 min (44 min)", "vo2max", 0, AQ_CURTO + [rep(4, p(5, 106, 112), p(3, 45, 55))] + ARR_CURTO,
       "Quatro esforços de 5 min com recuperações curtas.")
treino("vo2_5x5_curto", "VO2máx 5 × 5 min (50 min)", "vo2max", 0,
       [{"min": 8, "pct": [45, 75], "rampa": "sobe"}, rep(5, p(5, 106, 112), p(2.5, 45, 55))] + ARR_CURTO,
       "Cinco esforços de 5 min com pouca recuperação. Muito exigente.")
treino("forca_ss_4x8_curto", "Força 4 × 8 min a sweet spot (56 min)", "forca", 0,
       AQ_CURTO + [rep(4, p(8, 88, 92, (55, 62)), p(3, 50, 60))] + ARR_CURTO,
       "Quatro blocos a sweet spot em cadência baixa, numa hora.")
treino("forca_limiar_6x6", "Força ao limiar 6 × 6 min", "forca", 0, AQ + [rep(6, p(6, 95, 100, (50, 60)), p(4, 50, 60))] + ARR,
       "Seis blocos ao limiar em cadência baixa. O treino de força mais exigente da biblioteca.")
treino("forca_ss_3x15", "Força 3 × 15 min a sweet spot", "forca", 0, AQ + [rep(3, p(15, 88, 92, (55, 62)), p(5, 50, 60))] + ARR,
       "Três blocos longos a sweet spot em cadência baixa. Para subidas longas.")

treino("z2_2h45", "Z2 2 h 45", "resistencia", 0, AQ_LONGO + [p(142, 62, 72)] + ARR,
       "Duas horas e três quartos a ritmo de conversa.")
treino("sweetspot_2x10_curto", "Sweet spot 2 × 10 min (40 min)", "sweetspot", 0,
       AQ_CURTO + [rep(2, p(10, 88, 92), p(3, 50, 60))] + ARR_CURTO,
       "Dois blocos de 10 min a sweet spot. Introdução ao sweet spot.")
treino("tempo_3x14_curto", "Tempo 3 × 14 min (60 min)", "tempo", 0,
       [{"min": 8, "pct": [45, 75], "rampa": "sobe"}, rep(3, p(14, 76, 85), p(1.5, 50, 60))] + ARR_CURTO,
       "Três blocos de 14 min a tempo com recuperações curtas, numa hora.")

cab = ("# Biblioteca ORIGINAL da Wattwise (D-053) — gerada por core/tools/gerar_biblioteca.py.\n"
       "# Estruturas genéricas de treino escritas de raiz; nada copiado de outras plataformas (D-052).\n"
       "# O Paulo revê e ajusta. Nomes de marca em config/nomes_treinos.yaml.\n"
       "# Passo: {min, pct: [mín, máx] em % do FTP, cadencia, rampa: sobe|desce, escala}\n")
print(cab + yaml.safe_dump(T, allow_unicode=True, sort_keys=False, width=120))
