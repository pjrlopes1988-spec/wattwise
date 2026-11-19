"""Atletas fictícios para testar o plano (spec 10.3). Sem dados de pessoas reais."""
from datetime import date

from ww.perfil import Atleta, Equipamento, Objetivo, Valor

HOJE = date(2026, 11, 19)
INICIO = date(2026, 11, 23)   # segunda-feira

CENARIOS = {
    "iniciante_sem_potenciometro": Atleta(
        "Ana (fictícia)", date(1990, 3, 10), "F", 61, "iniciante", "estrada", Objetivo("resistencia"),
        (0, 60, 0, 60, 0, 120, 0), dia_longo=5, equipamento=Equipamento(cinta_fc=True)),
    "intermedio_prova_16_semanas": Atleta(
        "Bruno (fictício)", date(1985, 6, 2), "M", 74, "intermedio", "estrada",
        Objetivo("prova", date(2027, 3, 14), "Granfondo"), (60, 90, 0, 90, 0, 180, 240), dia_longo=6,
        equipamento=Equipamento(potenciometro=True, cinta_fc=True), ftp=Valor(250, "atleta"),
        fc_limiar=Valor(165, "atleta"), fc_max=Valor(185, "atleta"), fc_repouso=Valor(50, "atleta")),
    "avancado_com_tudo_ftp": Atleta(
        "Carlos (fictício)", date(1980, 1, 20), "M", 70, "avancado", "contrarrelogio", Objetivo("ftp"),
        (90, 90, 60, 90, 0, 210, 180), dia_longo=5,
        equipamento=Equipamento(potenciometro=True, rolo_inteligente=True, cinta_fc=True),
        ftp=Valor(310, "atleta"), fc_limiar=Valor(170, "atleta"), fc_max=Valor(188, "atleta"),
        fc_repouso=Valor(45, "atleta")),
    "competicao_xco_prova_8_semanas": Atleta(
        "Diana (fictícia)", date(1998, 9, 9), "F", 55, "competicao", "btt_xco",
        Objetivo("prova", date(2027, 1, 17), "Taça XCO"), (90, 120, 60, 120, 60, 180, 150), dia_longo=6,
        equipamento=Equipamento(potenciometro=True, cinta_fc=True), ftp=Valor(240, "atleta")),
    "pouca_disponibilidade": Atleta(
        "Eduardo (fictício)", date(1975, 11, 30), "M", 82, "intermedio", "gravel", Objetivo("ftp"),
        (0, 0, 45, 0, 0, 90, 0), equipamento=Equipamento(potenciometro=True), ftp=Valor(230, "atleta")),
    "juvenil_14_anos": Atleta(
        "Filipe (fictício)", date(2012, 5, 1), "M", 50, "competicao", "estrada", Objetivo("ftp"),
        (0, 75, 0, 75, 0, 150, 120), dia_longo=5, equipamento=Equipamento(potenciometro=True),
        ftp=Valor(190, "atleta")),
}
