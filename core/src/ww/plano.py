"""Geração do plano de treino (spec 7.2 e 7.3). Determinístico, sem base de dados.

Passos:
1. Fases por semana: com prova, conta-se para trás a partir da data (afinação → específico
   → construção → base); sem prova, ciclos a partir da base. A cada 3 semanas de carga, 1 de
   recuperação (pelo menos a cada 4 semanas, spec 7.3).
2. Carga-alvo de cada semana de carga: a necessária para subir a Condição `rampa` pontos
   (por nível); recuperação e afinação são frações da última semana de carga.
3. Dias: respeita a disponibilidade e os dias de descanso mínimos; sessões-chave o mais
   espaçadas possível (nunca mais de N dias seguidos de alta intensidade, também entre
   semanas); dia longo em resistência; o resto da carga em resistência/recuperação.
4. Verificação: a Condição prevista nunca sobe mais do que a rampa permitida em quaisquer
   7 dias seguidos (não só de segunda a domingo); se subir, encurtam-se os treinos de
   resistência (D-043).

Cada decisão fica no registo do plano (spec 7.1).
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Literal

from ww.config import Config
from ww.metrics.load import fator
from ww.perfil import Atleta, nivel_regras, precisa_de_teste
from ww.treinos import Passo, Treino

Fase = Literal["base", "construcao", "especifico", "recuperacao", "afinacao"]
FASES_CARGA = ("base", "construcao", "especifico")


@dataclass(frozen=True)
class TreinoPlaneado:
    data: date
    treino: Treino
    papel: str           # sessao_chave, teste, dia_longo, resistencia, recuperacao, prova
    alta_intensidade: bool

    @property
    def minutos(self) -> int:
        return round(self.treino.minutos)

    @property
    def carga(self) -> float:
        return self.treino.carga


@dataclass(frozen=True)
class Semana:
    numero: int
    inicio: date            # segunda-feira
    fase: Fase
    carga_alvo: float
    treinos: tuple[TreinoPlaneado, ...]
    condicao_inicio: float
    condicao_fim: float
    notas: tuple[str, ...]

    @property
    def carga_planeada(self) -> float:
        return sum(t.carga for t in self.treinos)

    @property
    def subida_condicao(self) -> float:
        return self.condicao_fim - self.condicao_inicio


@dataclass(frozen=True)
class Plano:
    inicio: date
    fim: date
    nivel_regras: str
    semanas: tuple[Semana, ...]
    registo: tuple[str, ...]
    versao_config: str

    def treinos(self) -> list[TreinoPlaneado]:
        return [t for s in self.semanas for t in s.treinos]

    def cargas_diarias(self) -> dict[date, float]:
        out: dict[date, float] = {}
        for t in self.treinos():
            out[t.data] = out.get(t.data, 0.0) + t.carga
        return out


class PlanoImpossivel(ValueError):
    pass


# ------------------------------------------------------------------ fases

def fases(n_semanas: int, *, prova: bool, arranque_frio: bool, objetivo: str, cfg: Config) -> list[Fase]:
    c = cfg.plano
    base_frio = c.semanas_base_arranque_frio if arranque_frio else 0
    seq: list[Fase]
    if prova:
        afin = min(n_semanas, c.semanas_afinacao_prova_longe if n_semanas >= c.semanas_prova_longe else 1)
        r = n_semanas - afin
        base = min(base_frio, r)
        esp = min(c.semanas_especifico, r - base)
        cons = min(c.semanas_construcao_max, r - base - esp)
        base += r - base - esp - cons
        seq = ["base"] * base + ["construcao"] * cons + ["especifico"] * esp + ["afinacao"] * afin
    elif objetivo in ("resistencia", "peso"):
        seq = ["base"] * n_semanas
    else:
        base = min(base_frio, n_semanas)
        seq = ["base"] * base + ["construcao"] * (n_semanas - base)

    seguidas = 0
    for i, f in enumerate(seq):
        if f in FASES_CARGA:
            if seguidas == c.semanas_carga_por_ciclo:
                seq[i] = "recuperacao"
                seguidas = 0
            else:
                seguidas += 1
        else:
            seguidas = 0
    return seq


# ------------------------------------------------------------------ auxiliares

def _segunda(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _arredondar_abaixo(minutos: float, passo: int) -> int:
    return int(minutos // passo * passo)


def _treino_prova(atleta: Atleta, cfg: Config) -> Treino:
    # Carga prevista configurável; representada como um esforço a 90% do FTP
    horas = cfg.plano.carga_prova_estimada / (0.9**2 * 100)
    return Treino("prova", f"Prova{': ' + atleta.objetivo.nome_prova if atleta.objetivo.nome_prova else ''}",
                  "prova", 5, (Passo(round(horas * 3600), 85, 95),))


def _escolher_treino(
    lib: dict[str, Treino], tipo: str, minutos: int, dif_alvo: int, dif_max: int, potencia: bool,
    mais_leve: bool = False,
) -> Treino | None:
    cand = [t for t in lib.values()
            if t.tipo == tipo and t.minutos <= minutos and t.dificuldade <= dif_max
            and (not t.so_sem_potencia or not potencia)]
    if not cand:
        return None
    if mais_leve:          # afinação: manter o estímulo com a menor carga possível
        return min(cand, key=lambda t: (t.carga, t.dificuldade))
    ate_alvo = [t for t in cand if t.dificuldade <= dif_alvo]
    if ate_alvo:
        return max(ate_alvo, key=lambda t: (t.dificuldade, t.minutos))
    return min(cand, key=lambda t: (t.dificuldade, t.minutos))


def _sequencias_altas(dias_altos: set[date]) -> int:
    """Maior número de dias seguidos de alta intensidade."""
    melhor = 0
    for d in dias_altos:
        if d - timedelta(days=1) in dias_altos:
            continue
        n = 1
        while d + timedelta(days=n) in dias_altos:
            n += 1
        melhor = max(melhor, n)
    return melhor


def _escolher_dias_chave(
    candidatos: list[date], n: int, altos_antes: set[date], disp: dict[date, int], max_seguidos: int
) -> list[date]:
    """Combinação de dias que respeita o limite de dias seguidos e maximiza o espaçamento."""
    if n <= 0 or not candidatos:
        return []
    n = min(n, len(candidatos))
    melhor: tuple | None = None
    escolha: list[date] = []
    for combo in itertools.combinations(sorted(candidatos), n):
        viol = max(0, _sequencias_altas(altos_antes | set(combo)) - max_seguidos)
        datas = sorted(altos_antes | set(combo))
        gaps = [(b - a).days for a, b in zip(datas, datas[1:]) if b in combo or a in combo]
        min_gap = min(gaps) if gaps else 7
        chave = (viol, -min_gap, -sum(disp[d] for d in combo))
        if melhor is None or chave < melhor:
            melhor, escolha = chave, list(combo)
    if melhor and melhor[0] > 0:
        # não há forma de respeitar o limite com n sessões: tirar sessões até respeitar
        return _escolher_dias_chave(candidatos, n - 1, altos_antes, disp, max_seguidos)
    return escolha


# ------------------------------------------------------------------ geração

def gerar(
    atleta: Atleta,
    lib: dict[str, Treino],
    cfg: Config,
    *,
    inicio: date,
    condicao_inicial: float = 0.0,
    fadiga_inicial: float = 0.0,
) -> Plano:
    c = cfg.plano
    nivel = nivel_regras(atleta, inicio, cfg)
    potencia = atleta.equipamento.potenciometro
    prova = atleta.objetivo.data_prova if atleta.objetivo.tipo == "prova" else None
    arranque_frio = condicao_inicial < 1.0

    seg0 = _segunda(inicio)
    if prova:
        n_sem = (_segunda(prova) - seg0).days // 7 + 1
        fim = prova
    else:
        n_sem = c.horizonte_sem_prova_semanas
        fim = seg0 + timedelta(days=7 * n_sem - 1)
    seq = fases(n_sem, prova=prova is not None, arranque_frio=arranque_frio,
                objetivo=atleta.objetivo.tipo, cfg=cfg)

    f_c = fator(cfg.carga_forma.constante_condicao_dias, cfg.carga_forma.fator_media)
    f_a = fator(cfg.carga_forma.constante_fadiga_dias, cfg.carga_forma.fator_media)
    k7 = 1 - (1 - f_c) ** 7          # fração da diferença (carga − condição) absorvida numa semana
    rampa = c.rampa_condicao_semana[nivel]
    dif_max = int(c.dificuldade_max[nivel])
    resist, recup = lib["resistencia"], lib["recuperacao"]
    carga_min_resist = resist.com_duracao(60).carga / 60   # carga por minuto em Z2

    teste = precisa_de_teste(atleta)
    registo: list[str] = [
        f"nível usado nas regras: {nivel}" + (" (menor de idade)" if nivel != atleta.nivel else ""),
        f"{n_sem} semanas, fases: {', '.join(seq)}",
    ]
    if teste:
        registo.append(f"teste guiado de {'FTP' if teste == 'ftp' else 'FC limiar'} na 1.ª semana (valor estimado)")

    ctl, atl = condicao_inicial, fadiga_inicial
    ultima_carga: float | None = None
    semana_na_fase = 0
    fase_anterior: Fase | None = None
    altos: set[date] = set()
    semanas: list[Semana] = []
    condicao_dia: dict[date, float] = {}   # Condição no fim de cada dia já planeado

    for i, fase in enumerate(seq):
        seg = seg0 + timedelta(days=7 * i)
        semana_na_fase = semana_na_fase + 1 if fase == fase_anterior else 1
        fase_anterior = fase
        notas: list[str] = []

        # --- carga-alvo
        if fase in FASES_CARGA:
            alvo = 7 * (ctl + rampa / k7)
        else:
            ref = ultima_carga if ultima_carga is not None else 7 * (ctl + rampa / k7)
            alvo = ref * (c.fator_semana_recuperacao if fase == "recuperacao" else c.fator_afinacao)

        # --- dias disponíveis nesta semana
        datas = [seg + timedelta(days=d) for d in range(7)]
        datas = [d for d in datas if d >= inicio and (prova is None or d <= prova)]
        disp = {d: atleta.disponibilidade[d.weekday()] for d in datas
                if atleta.disponibilidade[d.weekday()] >= c.duracao_minima_treino_min}
        dia_prova = prova if prova is not None and prova in datas else None
        if dia_prova is not None:
            disp.pop(dia_prova, None)
        max_treino = 7 - int(c.dias_descanso_min[nivel]) - (1 if dia_prova is not None else 0)  # a prova conta
        if len(disp) > max_treino:
            longo_pref = atleta.dia_longo
            ordem = sorted(disp, key=lambda d: (d.weekday() == longo_pref, disp[d]))
            for d in ordem[: len(disp) - max_treino]:
                disp.pop(d)
            notas.append(f"{int(c.dias_descanso_min[nivel])} dia(s) de descanso mínimo")

        treinos: list[TreinoPlaneado] = []
        if dia_prova is not None:
            treinos.append(TreinoPlaneado(dia_prova, _treino_prova(atleta, cfg), "prova", True))

        if not disp:
            notas.append("sem dias disponíveis")
        else:
            longos = [d for d in disp if d.weekday() == atleta.dia_longo]
            if dia_prova is not None:
                longo = None      # semana da prova: sem treino longo
            else:
                longo = longos[0] if longos else max(disp, key=lambda d: (disp[d], d))

            # --- sessões-chave
            n_chave = int(getattr(c.sessoes_chave, fase)[nivel])
            com_teste = teste is not None and i == 0
            if com_teste:
                n_chave = max(n_chave, 1)
            tipos = (getattr(c.tipos_por_fase.especifico, atleta.disciplina) if fase == "especifico"
                     else getattr(c.tipos_por_fase, fase, []))
            # só dias onde cabe pelo menos um treino dos tipos desta fase (ou o teste)
            precisos = set(tipos) | ({"teste"} if com_teste else set())
            curtos = [t.minutos for t in lib.values() if t.tipo in precisos
                      and (t.dificuldade <= dif_max or t.tipo == "teste")
                      and (not t.so_sem_potencia or not potencia)]
            minimo = max(c.duracao_minima_sessao_chave_min, min(curtos) if curtos else 0)
            cand = [d for d in disp if d != longo and disp[d] >= minimo]
            if com_teste and len(cand) > 1:
                # o teste não é o primeiro treino do plano: antes, pelo menos um treino fácil
                cand = [d for d in cand if d != min(disp)]
            if not cand and n_chave and longo is not None and disp[longo] >= minimo:
                cand = [longo]
            if fase == "afinacao" and dia_prova is not None:
                # ativação o mais perto possível da prova (2 dias antes no máximo)
                cand = [d for d in cand if 1 <= (dia_prova - d).days <= 2] or cand
            if dia_prova is not None:
                altos_ref = altos | {dia_prova}
            else:
                altos_ref = set(altos)
            dias_chave = _escolher_dias_chave(cand, n_chave, altos_ref, disp, c.max_dias_alta_intensidade_seguidos)
            if len(dias_chave) < n_chave:
                notas.append(f"só {len(dias_chave)} de {n_chave} sessões-chave (disponibilidade/limite de dias seguidos)")

            for j, d in enumerate(sorted(dias_chave)):
                if com_teste and j == 0:
                    tipo, papel = "teste", "teste"
                else:
                    tipo = tipos[(j + i) % len(tipos)] if tipos else "resistencia"
                    papel = "sessao_chave"
                # progressão dentro da fase, a começar 2 níveis abaixo do máximo do atleta
                dif_alvo = min(dif_max, max(1, dif_max - 2) + semana_na_fase - 1) if fase != "afinacao" else 1
                # o teste não depende do nível (é sempre o mesmo protocolo)
                t = _escolher_treino(lib, tipo, disp[d], 5 if tipo == "teste" else dif_alvo,
                                     5 if tipo == "teste" else dif_max, potencia, mais_leve=fase == "afinacao")
                if t is None:
                    notas.append(f"{d}: nenhum treino '{tipo}' cabe em {disp[d]} min; fica resistência")
                    continue
                alta = t.tipo in c.tipos_alta_intensidade
                treinos.append(TreinoPlaneado(d, t, papel, alta))

            # --- resistência / recuperação com a carga que falta
            usados = {t.data for t in treinos}
            livres = [d for d in disp if d not in usados]
            falta = max(0.0, alvo - sum(t.carga for t in treinos))
            alocar: dict[date, float] = {}
            if livres:
                cap = {d: disp[d] * carga_min_resist for d in livres}
                if longo in livres and len(livres) > 1:
                    alocar[longo] = min(cap[longo], falta * c.fracao_carga_dia_longo)
                resto = falta - sum(alocar.values())
                outros = [d for d in livres if d not in alocar]
                for _ in range(3):   # distribuir e redistribuir o que não coube
                    if resto <= 0.5 or not outros:
                        break
                    parte = resto / len(outros)
                    for d in outros:
                        dar = min(parte, cap[d] - alocar.get(d, 0.0))
                        alocar[d] = alocar.get(d, 0.0) + dar
                        resto -= dar
                    outros = [d for d in outros if cap[d] - alocar[d] > 1]
                if resto > 0.5 and longo in alocar:
                    dar = min(resto, cap[longo] - alocar[longo])
                    alocar[longo] += dar
                    resto -= dar
                if resto > 0.05 * alvo:
                    notas.append(f"carga limitada pela disponibilidade (faltam ~{resto:.0f})")

            for d, carga in sorted(alocar.items()):
                minutos = min(disp[d], _arredondar_abaixo(carga / carga_min_resist, c.arredondar_min))
                if minutos < c.duracao_minima_treino_min:
                    continue
                if d == longo and minutos > 45:
                    treinos.append(TreinoPlaneado(d, resist.com_duracao(minutos), "dia_longo", False))
                elif minutos <= 45:
                    treinos.append(TreinoPlaneado(d, recup.com_duracao(minutos), "recuperacao", False))
                else:
                    treinos.append(TreinoPlaneado(d, resist.com_duracao(minutos), "resistencia", False))

        # --- verificação da rampa (spec 7.3): encurtar resistência se a Condição subir demais
        def simular(ts: list[TreinoPlaneado]) -> tuple[float, float, float, dict[date, float]]:
            """Condição e fadiga no fim da semana e a maior subida em quaisquer 7 dias seguidos."""
            cs, a_ = ctl, atl
            por_dia: dict[date, float] = {}
            for t in ts:
                por_dia[t.data] = por_dia.get(t.data, 0.0) + t.carga
            diaria: dict[date, float] = {}
            subida = 0.0
            for k in range(7):
                d = seg + timedelta(days=k)
                carga_d = por_dia.get(d, 0.0)
                cs += (carga_d - cs) * f_c
                a_ += (carga_d - a_) * f_a
                diaria[d] = cs
                antes = condicao_dia.get(d - timedelta(days=7), diaria.get(d - timedelta(days=7), condicao_inicial))
                subida = max(subida, cs - antes)
            return cs, a_, subida, diaria

        ctl_fim, atl_fim, subida, diaria = simular(treinos)
        while subida > rampa + 1e-9:
            redutiveis = [t for t in treinos if t.papel in ("dia_longo", "resistencia", "recuperacao")
                          and t.minutos - c.arredondar_min >= c.duracao_minima_treino_min]
            if not redutiveis:
                notas.append("ATENÇÃO: rampa acima do limite sem treinos para encurtar")
                break
            mais_longo = max(redutiveis, key=lambda t: t.minutos)
            novo = (resist if mais_longo.treino.id == "resistencia" else recup).com_duracao(mais_longo.minutos - c.arredondar_min)
            treinos[treinos.index(mais_longo)] = replace(mais_longo, treino=novo)
            ctl_fim, atl_fim, subida, diaria = simular(treinos)
            if "rampa: resistência encurtada" not in notas:
                notas.append("rampa: resistência encurtada")

        treinos.sort(key=lambda t: t.data)
        condicao_dia.update(diaria)
        altos |= {t.data for t in treinos if t.alta_intensidade}
        s = Semana(i + 1, seg, fase, alvo, tuple(treinos), ctl, ctl_fim, tuple(notas))
        semanas.append(s)
        registo.append(f"S{s.numero} ({seg}) {fase}: alvo {alvo:.0f}, planeado {s.carga_planeada:.0f}, "
                       f"condição {ctl:.1f} → {ctl_fim:.1f}" + (f" — {'; '.join(notas)}" if notas else ""))
        if fase in FASES_CARGA:
            ultima_carga = s.carga_planeada
        ctl, atl = ctl_fim, atl_fim

    return Plano(inicio, fim, nivel, tuple(semanas), tuple(registo), cfg.versao)
