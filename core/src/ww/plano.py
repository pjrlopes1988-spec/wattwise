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
from ww.perfil import (Ambiente, Atleta, Etapa, Prova, agressividade, ambientes, calendario_provas, nivel_regras,
                       precisa_de_teste, semanas_de_carga, tem_potencia)
from ww.treinos import Passo, Treino, biblioteca

Fase = Literal["base", "construcao", "especifico", "recuperacao", "afinacao"]
FASES_CARGA = ("base", "construcao", "especifico")


@dataclass(frozen=True)
class TreinoPlaneado:
    data: date
    treino: Treino
    papel: str           # sessao_chave, teste, dia_longo, resistencia, recuperacao, prova
    alta_intensidade: bool           # se QUALQUER das versões for de alta intensidade (D-059)
    ambiente: Ambiente = "outdoor"   # da versão principal; indoor = alvos fixos (D-058)
    alternativa: Treino | None = None   # a versão no outro ambiente, lado a lado no calendário (D-059)
    escolhido: bool = False             # o atleta já tocou numa das versões
    prioridade: str | None = None       # só nas provas: A, B, C ou D (D-060)

    @property
    def minutos(self) -> int:
        return round(self.treino.minutos)

    @property
    def carga(self) -> float:
        """Antes da escolha: a versão mais pesada (opção mais conservadora, spec 7.1)."""
        if self.alternativa is not None and not self.escolhido:
            return max(self.treino.carga, self.alternativa.carga)
        return self.treino.carga

    def opcoes(self) -> dict[str, Treino]:
        out = {self.ambiente: self.treino}
        if self.alternativa is not None:
            out[self.alternativa.ambiente] = self.alternativa
        return out


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
    # 1.ª semana depois da recuperação de uma prova A: o motor diário (Fase 3) avalia a prontidão
    # antes de retomar a carga e, se preciso, prolonga a recuperação (D-063)
    verificar_prontidao: bool = False

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

def fases(n_semanas: int, *, prova: bool, arranque_frio: bool, objetivo: str, cfg: Config,
          semanas_carga: int | None = None) -> list[Fase]:
    c = cfg.plano
    por_ciclo = semanas_carga if semanas_carga is not None else c.semanas_carga_por_ciclo
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
            if seguidas == por_ciclo:
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


def _treino_prova(p: Prova, cfg: Config, etapa: "Etapa | None" = None, n: int = 1, total: int = 1) -> Treino:
    """A prova (ou uma etapa) como um esforço com a intensidade típica para a sua duração (D-060, D-062)."""
    cp = cfg.provas
    dur = etapa.duracao_h if etapa is not None and etapa.duracao_h is not None else p.duracao_h
    horas = dur if dur is not None else cp.duracao_por_defeito_h
    data = etapa.data if etapa is not None else p.data
    nome = f"Prova {p.prioridade}: {p.nome}"
    if total > 1:
        nome += f" — etapa {n}/{total}" + (f" ({etapa.descricao})" if etapa is not None and etapa.descricao else "")
    fi = next(i for h, i in cp.intensidade_por_duracao if horas <= h) if horas <= cp.intensidade_por_duracao[-1][0] \
        else cp.intensidade_por_duracao[-1][1]
    pct = fi * 100
    return Treino(f"prova_{data.isoformat()}", nome, "prova", 5, (Passo(round(horas * 3600), pct - 5, pct + 5),))


def fases_por_provas(n_sem: int, semanas_A: list[int] | list[tuple[int, int]], *, arranque_frio: bool, objetivo: str,
                     cfg: Config, semanas_carga: int | None = None) -> list[Fase]:
    """Um ciclo completo para cada prova A (base/construção/específico/afinação); depois de cada A,
    semana(s) de recuperação; depois da última A, ciclos do objetivo geral (D-060)."""
    seq: list[Fase] = []
    ini = 0
    intervalos = sorted({(w, w) if isinstance(w, int) else w for w in semanas_A})
    for k, (wa, wf) in enumerate(intervalos):
        if wa < ini:                       # A logo a seguir a outra A: só afinação nessa semana
            seq[wa] = "afinacao"
            continue
        seq += fases(wa - ini + 1, prova=True, arranque_frio=arranque_frio and k == 0, objetivo="prova", cfg=cfg,
                     semanas_carga=semanas_carga)
        # prova por etapas que continua nas semanas seguintes: semanas leves (só etapas e recuperação)
        seq += ["recuperacao"] * (min(wf, n_sem - 1) - wa)
        ini = wf + 1
        r = min(cfg.provas.semanas_recuperacao_apos_A, n_sem - ini)
        seq += ["recuperacao"] * r
        ini += r
    if n_sem > ini:
        seq += fases(n_sem - ini, prova=False, arranque_frio=arranque_frio and not semanas_A,
                     objetivo=objetivo if objetivo != "prova" else "ftp", cfg=cfg, semanas_carga=semanas_carga)
    return seq[:n_sem]


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

    def aproveita(t: Treino) -> bool:
        # treinos curtos (ex.: Express) só quando o dia é curto (D-051)
        return t.minutos >= min(45, 0.75 * minutos)

    # a biblioteca do treinador tem prioridade sobre a provisória (D-048)
    if ate_alvo:
        return max(ate_alvo, key=lambda t: (t.dificuldade, aproveita(t), t.origem == "paulo", t.minutos, t.id))
    return min(cand, key=lambda t: (t.dificuldade, not aproveita(t), t.origem != "paulo", t.minutos, t.id))


def alta_intensidade(t: Treino, cfg: Config) -> bool:
    """Pelo tipo ou pelo conteúdo: ≥ 5 min a ≥ 95% do FTP ou ≥ 1 min a ≥ 120% (D-049)."""
    c = cfg.plano
    if t.tipo in c.tipos_alta_intensidade or t.tipo == "prova":
        return True
    acima95 = sum(p.segundos for p in t.passos if p.pct_medio >= 95 and not p.rampa)
    acima120 = sum(p.segundos for p in t.passos if p.pct_medio >= 120 and not p.rampa)
    return acima95 >= c.alta_intensidade_s_acima_95pct or acima120 >= c.alta_intensidade_s_acima_120pct


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


def _excesso(altos: set[date], max_seguidos: int, dias_de_prova: set[date] = frozenset()) -> int:  # type: ignore[assignment]
    """Quanto se passa do limite de dias seguidos de alta intensidade. Sequências feitas só de
    dias de prova (ex.: etapas seguidas) não contam: a prova é a prova (D-062)."""
    pior = 0
    for d in altos:
        if d - timedelta(days=1) in altos:
            continue
        seq = [d]
        while seq[-1] + timedelta(days=1) in altos:
            seq.append(seq[-1] + timedelta(days=1))
        if all(x in dias_de_prova for x in seq):
            continue
        pior = max(pior, len(seq) - max_seguidos)
    return pior


def _escolher_dias_chave(
    candidatos: list[date], n: int, altos_antes: set[date], disp: dict[date, int], max_seguidos: int,
    dias_de_prova: set[date] = frozenset(),  # type: ignore[assignment]
) -> list[date]:
    """Combinação de dias que respeita o limite de dias seguidos e maximiza o espaçamento."""
    if n <= 0 or not candidatos:
        return []
    n = min(n, len(candidatos))
    melhor: tuple | None = None
    escolha: list[date] = []
    for combo in itertools.combinations(sorted(candidatos), n):
        viol = _excesso(altos_antes | set(combo), max_seguidos, dias_de_prova)
        datas = sorted(altos_antes | set(combo))
        gaps = [(b - a).days for a, b in zip(datas, datas[1:]) if b in combo or a in combo]
        min_gap = min(gaps) if gaps else 7
        chave = (viol, -min_gap, -sum(disp[d] for d in combo))
        if melhor is None or chave < melhor:
            melhor, escolha = chave, list(combo)
    if melhor and melhor[0] > 0:
        # não há forma de respeitar o limite com n sessões: tirar sessões até respeitar
        return _escolher_dias_chave(candidatos, n - 1, altos_antes, disp, max_seguidos, dias_de_prova)
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
    cp = cfg.provas
    provas = tuple(p for p in calendario_provas(atleta) if p.data >= inicio)
    arranque_frio = condicao_inicial < 1.0

    seg0 = _segunda(inicio)

    def semana_de(d: date) -> int:
        return (_segunda(d) - seg0).days // 7

    semanas_A = [(semana_de(p.data), semana_de(p.ultima_data)) for p in provas if p.prioridade == "A"]
    if provas:
        ultima = max(p.ultima_data for p in provas)
        ate_ultima = semana_de(ultima) + 1
        # com prova A o plano termina na última prova; sem A, pelo menos o horizonte normal
        n_sem = ate_ultima if semanas_A else max(ate_ultima, c.horizonte_sem_prova_semanas)
        fim = ultima if n_sem == ate_ultima else seg0 + timedelta(days=7 * n_sem - 1)
    else:
        n_sem = c.horizonte_sem_prova_semanas
        fim = seg0 + timedelta(days=7 * n_sem - 1)
    carga_por_ciclo = semanas_de_carga(atleta, inicio, cfg)
    seq = fases_por_provas(n_sem, semanas_A, arranque_frio=arranque_frio, objetivo=atleta.objetivo.tipo, cfg=cfg,
                           semanas_carga=carga_por_ciclo)

    # dias sem intensidade antes das provas e dias fáceis depois (B e C; a A tem a afinação)
    sem_intensidade: set[date] = set()
    faceis: set[date] = set()
    dias_de_prova: set[date] = {e.data for p in provas for e in p.dias()}
    for p in provas:
        sem_intensidade |= {p.data - timedelta(days=k) for k in range(1, cp.dias_sem_intensidade_antes[p.prioridade] + 1)}
        faceis |= {p.ultima_data + timedelta(days=k) for k in range(1, cp.dias_faceis_depois[p.prioridade] + 1)}
        # dias de descanso entre etapas: só recuperação curta (D-062)
        faceis |= {p.data + timedelta(days=k) for k in range((p.ultima_data - p.data).days)} - dias_de_prova
    sem_intensidade -= dias_de_prova
    faceis -= dias_de_prova

    f_c = fator(cfg.carga_forma.constante_condicao_dias, cfg.carga_forma.fator_media)
    f_a = fator(cfg.carga_forma.constante_fadiga_dias, cfg.carga_forma.fator_media)
    k7 = 1 - (1 - f_c) ** 7          # fração da diferença (carga − condição) absorvida numa semana
    agr_n = agressividade(atleta, inicio, cfg)
    agr = c.agressividade[agr_n]
    rampa = c.rampa_condicao_semana[nivel] * agr.rampa_fator      # nunca acima do máximo do nível
    dif_max = int(c.dificuldade_max[nivel])
    libs = {"outdoor": biblioteca(lib, "outdoor"), "indoor": biblioteca(lib, "indoor")}

    def tem_pot(d: date) -> bool:
        return tem_potencia(atleta, amb(d))

    versoes = ambientes(atleta)
    principal: Ambiente = versoes[0]
    outro: Ambiente | None = versoes[1] if len(versoes) > 1 else None

    def amb(d: date) -> Ambiente:
        return principal

    def com_alternativa(tp: TreinoPlaneado) -> TreinoPlaneado:
        """Junta a versão do outro ambiente (exceto na prova)."""
        if outro is None or tp.papel == "prova":
            return tp
        sem = replace(tp, alternativa=None)
        alt = trocar_ambiente(sem, outro, lib, cfg).treino
        return replace(tp, alternativa=alt, alta_intensidade=tp.alta_intensidade or alta_intensidade(alt, cfg))

    def resist(d: date) -> Treino:
        return lib["resistencia_indoor" if amb(d) == "indoor" else "resistencia"]

    def recup(d: date) -> Treino:
        return lib["recuperacao_indoor" if amb(d) == "indoor" else "recuperacao"]

    carga_min_resist = lib["resistencia"].com_duracao(60).carga / 60   # carga por minuto em Z2

    teste = precisa_de_teste(atleta)
    registo: list[str] = [
        f"nível usado nas regras: {nivel}" + (" (menor de idade)" if nivel != atleta.nivel else ""),
        f"ciclos {carga_por_ciclo}+1" + (" (escolha do atleta)" if atleta.ciclo else " (sugestão pela idade)"),
        f"intensidade preferida {agr_n}/5" + ("" if atleta.agressividade is not None else " (sugestão)"),
        f"{n_sem} semanas, fases: {', '.join(seq)}",
    ]
    if teste:
        registo.append(f"teste guiado de {'FTP' if teste == 'ftp' else 'FC limiar'} na 1.ª semana (valor estimado)")
    for p in provas:
        registo.append(f"prova {p.prioridade} ({p.data}): {p.nome}")

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
        datas_semana = [seg + timedelta(days=d) for d in range(7)]
        # etapas (ou provas de um dia) desta semana: (prova, etapa, n.º, total)
        etapas_sem = [(p, e, n + 1, len(p.dias())) for p in provas for n, e in enumerate(p.dias()) if e.data in datas_semana]
        provas_sem = [p for p, *_ in etapas_sem]
        if fase in FASES_CARGA:
            alvo = 7 * (ctl + rampa / k7)
            if any(p.prioridade == "B" for p in provas_sem):
                alvo *= cp.fator_carga_semana_B
                notas.append("mini-afinação para prova B")
        else:
            ref = ultima_carga if ultima_carga is not None else 7 * (ctl + rampa / k7)
            alvo = ref * (agr.fator_recuperacao if fase == "recuperacao" else c.fator_afinacao)

        # --- dias disponíveis nesta semana
        datas = [seg + timedelta(days=d) for d in range(7)]
        datas = [d for d in datas if inicio <= d <= fim]
        # indoor: o treino nunca passa da duração máxima no rolo (D-058)
        disp = {d: min(atleta.disponibilidade[d.weekday()],
                       cfg.indoor.duracao_max_min if amb(d) == "indoor" else 10**4) for d in datas
                if atleta.disponibilidade[d.weekday()] >= c.duracao_minima_treino_min}
        dias_prova = {e.data: p for p, e, *_ in etapas_sem}
        etapa_A = min((e.data for p, e, *_ in etapas_sem if p.prioridade == "A"), default=None)
        dia_prova = etapa_A                         # 1.ª etapa A desta semana (ativação antes dela)
        for d in dias_prova:
            disp.pop(d, None)
        for d in faceis & set(disp):
            disp[d] = min(disp[d], 45)          # dia a seguir à prova: só recuperação
        for d in sem_intensidade & set(disp):
            disp[d] = min(disp[d], cp.duracao_max_antes_min)   # véspera(s): curto e fácil
        max_treino = 7 - int(c.dias_descanso_min[nivel]) - len(dias_prova)  # as provas contam
        if len(disp) > max_treino:
            longo_pref = atleta.dia_longo
            ordem = sorted(disp, key=lambda d: (d.weekday() == longo_pref, disp[d]))
            for d in ordem[: len(disp) - max_treino]:
                disp.pop(d)
            notas.append(f"{int(c.dias_descanso_min[nivel])} dia(s) de descanso mínimo")

        treinos: list[TreinoPlaneado] = []
        for p, e, n, total in etapas_sem:
            treinos.append(TreinoPlaneado(e.data, _treino_prova(p, cfg, e if p.etapas else None, n, total), "prova",
                                          True, "outdoor", prioridade=p.prioridade))

        if not disp:
            notas.append("sem dias disponíveis")
        else:
            longos = [d for d in disp if d.weekday() == atleta.dia_longo]
            if dia_prova is not None or any(p.prioridade == "B" for p in provas_sem):
                longo = None      # semana da prova A ou B: sem treino longo
            else:
                longo = longos[0] if longos else max(disp, key=lambda d: (disp[d], d))

            # --- sessões-chave
            n_chave = int(getattr(c.sessoes_chave, fase)[nivel])
            if fase in FASES_CARGA:      # preferência do atleta (D-069), dentro do máximo
                n_chave = max(0, min(c.sessoes_chave_max, n_chave + agr.sessoes_chave_delta))
            # provas B, C e D contam como sessão-chave dessa semana
            n_chave = max(0, n_chave - sum(cp.conta_como_sessao_chave[p.prioridade] for p in provas_sem
                                           if p.prioridade != "A"))
            com_teste = teste is not None and i == 0
            if com_teste:
                n_chave = max(n_chave, 1)
            tipos = (getattr(c.tipos_por_fase.especifico, atleta.disciplina) if fase == "especifico"
                     else getattr(c.tipos_por_fase, fase, []))
            # só dias onde cabe pelo menos um treino dos tipos desta fase (ou o teste)
            precisos = set(tipos) | ({"teste"} if com_teste else set())
            def minimo_dia(d: date) -> float:
                curtos = [t.minutos for t in libs[amb(d)].values() if t.tipo in precisos
                          and (t.dificuldade <= dif_max or t.tipo == "teste")
                          and (not t.so_sem_potencia or not tem_pot(d))]
                return max(c.duracao_minima_sessao_chave_min, min(curtos) if curtos else 10**4)

            cand = [d for d in disp if d != longo and disp[d] >= minimo_dia(d)
                    and d not in sem_intensidade and d not in faceis]
            if com_teste and len(cand) > 1:
                # o teste não é o primeiro treino do plano: antes, pelo menos um treino fácil
                cand = [d for d in cand if d != min(disp)]
            if not cand and n_chave and longo is not None and disp[longo] >= minimo_dia(longo):
                cand = [longo]
            if fase == "afinacao" and dia_prova is not None:
                # ativação o mais perto possível da prova (2 dias antes no máximo)
                cand = [d for d in cand if 1 <= (dia_prova - d).days <= 2] or cand
            altos_ref = altos | dias_de_prova
            dias_chave = _escolher_dias_chave(cand, n_chave, altos_ref, disp, c.max_dias_alta_intensidade_seguidos,
                                              dias_de_prova)
            if len(dias_chave) < n_chave:
                notas.append(f"só {len(dias_chave)} de {n_chave} sessões-chave (disponibilidade/limite de dias seguidos)")

            for j, d in enumerate(sorted(dias_chave)):
                if com_teste and j == 0:
                    tipo, papel = "teste", "teste"
                else:
                    tipo = tipos[(j + i) % len(tipos)] if tipos else "resistencia"
                    papel = "sessao_chave"
                # progressão dentro da fase, a começar 2 níveis abaixo do máximo do atleta
                dif_alvo = min(dif_max, max(1, dif_max - 2 + agr.dificuldade_delta) + semana_na_fase - 1) \
                    if fase != "afinacao" else 1
                # o teste não depende do nível (é sempre o mesmo protocolo)
                t = _escolher_treino(libs[amb(d)], tipo, disp[d], 5 if tipo == "teste" else dif_alvo,
                                     5 if tipo == "teste" else dif_max, tem_pot(d), mais_leve=fase == "afinacao")
                if t is None:
                    notas.append(f"{d}: nenhum treino '{tipo}' cabe em {disp[d]} min; fica resistência")
                    continue
                treinos.append(TreinoPlaneado(d, t, papel, alta_intensidade(t, cfg), amb(d)))

            # --- ativação 1–2 dias antes das provas que a pedem (ex.: B); não conta como sessão-chave
            for p in {p for p, e, n, _ in etapas_sem if n == 1}:     # antes da 1.ª etapa
                if not cp.ativacao_antes[p.prioridade]:
                    continue
                ocupados = {t.data for t in treinos}
                for k in (1, 2):
                    d = p.data - timedelta(days=k)
                    altos_aqui = altos | dias_de_prova | {t.data for t in treinos if t.alta_intensidade}
                    if _excesso(altos_aqui | {d}, c.max_dias_alta_intensidade_seguidos, dias_de_prova):
                        continue                         # não colar mais um dia intenso às etapas
                    if d in disp and d not in ocupados:
                        ativ = _escolher_treino(libs[amb(d)], "vo2max", disp[d], 1, 5, tem_pot(d), mais_leve=True)
                        if ativ is not None:
                            treinos.append(TreinoPlaneado(d, ativ, "ativacao", alta_intensidade(ativ, cfg), amb(d)))
                            break

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

            # menos treinos, mas com sentido: tirar o dia com menos carga e dá-la aos outros
            # (semanas de carga: ≥ 60 min de resistência; semanas leves: ≥ duração mínima de um treino)
            minimo_r = (c.duracao_minima_resistencia_min if fase in FASES_CARGA else c.duracao_minima_treino_min) \
                * carga_min_resist
            if alocar:
                while len(alocar) > 1:
                    curtos_ = [d for d in alocar if alocar[d] < minimo_r and d != longo]
                    if not curtos_:
                        break
                    tirar = min(curtos_, key=lambda d: (alocar[d], d))
                    sobra = alocar.pop(tirar)
                    for d in sorted(alocar, key=lambda d: -disp[d]):
                        dar = min(sobra, cap[d] - alocar[d])
                        alocar[d] += dar
                        sobra -= dar
            for d, carga in sorted(alocar.items()):
                minutos = min(disp[d], _arredondar_abaixo(carga / carga_min_resist, c.arredondar_min))
                if minutos < c.duracao_minima_treino_min:
                    continue
                if d == longo and minutos > 45:
                    treinos.append(TreinoPlaneado(d, resist(d).com_duracao(minutos), "dia_longo", False, amb(d)))
                elif minutos <= 45:
                    treinos.append(TreinoPlaneado(d, recup(d).com_duracao(minutos), "recuperacao", False, amb(d)))
                else:
                    treinos.append(TreinoPlaneado(d, resist(d).com_duracao(minutos), "resistencia", False, amb(d)))

        # --- verificação da rampa (spec 7.3): encurtar resistência se a Condição subir demais
        def simular(ts: list[TreinoPlaneado]) -> tuple[float, float, float, dict[date, float], date]:
            """Condição e fadiga no fim da semana, a maior subida em quaisquer 7 dias seguidos
            e o dia em que essa subida acontece."""
            cs, a_ = ctl, atl
            por_dia: dict[date, float] = {}
            for t in ts:
                por_dia[t.data] = por_dia.get(t.data, 0.0) + t.carga
            diaria: dict[date, float] = {}
            subida = 0.0
            dia_max = seg
            for k in range(7):
                d = seg + timedelta(days=k)
                carga_d = por_dia.get(d, 0.0)
                cs += (carga_d - cs) * f_c
                a_ += (carga_d - a_) * f_a
                diaria[d] = cs
                antes = condicao_dia.get(d - timedelta(days=7), diaria.get(d - timedelta(days=7), condicao_inicial))
                if cs - antes > subida:
                    subida, dia_max = cs - antes, d
            return cs, a_, subida, diaria, dia_max

        treinos = [com_alternativa(t) for t in treinos]
        ctl_fim, atl_fim, subida, diaria, dia_max = simular(treinos)
        while subida > rampa + 1e-9:
            # só ajuda mexer nos treinos dos 7 dias que terminam no dia do excesso
            janela = [t for t in treinos if t.papel in ("dia_longo", "resistencia", "recuperacao")
                      and dia_max - timedelta(days=6) <= t.data <= dia_max]
            if not janela:
                # sem resistência para encurtar: aliviar a sessão-chave mais pesada da janela
                # (versão mais leve do mesmo tipo; se já for a mais leve, sai) — a segurança vem primeiro
                chaves = [t for t in treinos if t.papel in ("sessao_chave", "teste")
                          and dia_max - timedelta(days=6) <= t.data <= dia_max]
                if not chaves:
                    perto = [p for p in provas if dia_max - timedelta(days=6) <= p.data <= dia_max]
                    notas.append("rampa acima do limite por causa da prova " + ", ".join(p.nome for p in perto)
                                 if perto else "ATENÇÃO: rampa acima do limite sem treinos para ajustar")
                    break
                pesada = max(chaves, key=lambda t: (t.treino.carga, t.data))
                mais_leves = [x for x in libs[amb(pesada.data)].values()
                              if x.tipo == pesada.treino.tipo and x.carga < pesada.treino.carga - 1
                              and (not x.so_sem_potencia or not tem_pot(pesada.data))]
                if mais_leves:
                    leve = max(mais_leves, key=lambda x: (x.carga, x.id))
                    treinos[treinos.index(pesada)] = com_alternativa(
                        replace(pesada, treino=leve, alternativa=None, alta_intensidade=alta_intensidade(leve, cfg)))
                else:
                    treinos.remove(pesada)
                ctl_fim, atl_fim, subida, diaria, dia_max = simular(treinos)
                if "rampa: sessão-chave aliviada" not in notas:
                    notas.append("rampa: sessão-chave aliviada")
                continue
            alvo_t = max(janela, key=lambda t: (t.minutos, t.data))
            novos_min = alvo_t.minutos - c.arredondar_min
            if novos_min < c.duracao_minima_treino_min:
                treinos.remove(alvo_t)          # passa a dia de descanso
            else:
                base_t = resist(alvo_t.data) if alvo_t.treino.base == "resistencia" else recup(alvo_t.data)
                treinos[treinos.index(alvo_t)] = com_alternativa(replace(alvo_t, treino=base_t.com_duracao(novos_min)))
            ctl_fim, atl_fim, subida, diaria, dia_max = simular(treinos)
            if "rampa: resistência encurtada" not in notas:
                notas.append("rampa: resistência encurtada")

        treinos.sort(key=lambda t: t.data)
        condicao_dia.update(diaria)
        altos |= {t.data for t in treinos if t.alta_intensidade}
        depois_de_A = (fase != "recuperacao" and i > 0 and seq[i - 1] == "recuperacao"
                       and any(semana_de(p.ultima_data) < i for p in provas if p.prioridade == "A")
                       and any(i - 1 - cp.semanas_recuperacao_apos_A <= semana_de(p.ultima_data) <= i - 1
                               for p in provas if p.prioridade == "A"))
        if depois_de_A:
            notas.append("verificar prontidão antes de retomar a carga (após prova A)")
        s = Semana(i + 1, seg, fase, alvo, tuple(treinos), ctl, ctl_fim, tuple(notas), depois_de_A)
        semanas.append(s)
        registo.append(f"S{s.numero} ({seg}) {fase}: alvo {alvo:.0f}, planeado {s.carga_planeada:.0f}, "
                       f"condição {ctl:.1f} → {ctl_fim:.1f}" + (f" — {'; '.join(notas)}" if notas else ""))
        if fase in FASES_CARGA:
            ultima_carga = s.carga_planeada
        ctl, atl = ctl_fim, atl_fim

    return Plano(inicio, fim, nivel, tuple(semanas), tuple(registo), cfg.versao)


def trocar_ambiente(tp: TreinoPlaneado, ambiente: Ambiente, lib: dict[str, Treino], cfg: Config) -> TreinoPlaneado:
    """O atleta escolhe fazer o treino noutro ambiente (D-058).

    Usa a versão do mesmo treino na outra biblioteca; se não existir (ex.: Z2 de 4 h indoor), o
    mais parecido (tipo, dificuldade, duração). Indoor nunca passa da duração máxima no rolo.
    A prova não muda de ambiente.
    """
    from ww.treinos import equivalente

    if tp.papel == "prova" or tp.ambiente == ambiente:
        return tp
    limite = cfg.indoor.duracao_max_min if ambiente == "indoor" else None
    t = tp.treino
    if t.base in ("resistencia", "recuperacao"):          # escaláveis: mesma duração (com limite)
        novo_base = lib[t.base + ("_indoor" if ambiente == "indoor" else "")]
        minutos = min(tp.minutos, limite) if limite else tp.minutos
        novo = novo_base.com_duracao(int(minutos))
    else:
        novo = equivalente(t, ambiente, lib, minutos_max=limite)
        if novo is None:
            raise ValueError(f"não há treino {t.tipo} equivalente para {ambiente}")
    return replace(tp, treino=novo, ambiente=ambiente, alta_intensidade=alta_intensidade(novo, cfg))


def escolher(tp: TreinoPlaneado, ambiente: Ambiente, cfg: Config) -> TreinoPlaneado:
    """O atleta toca numa das versões do dia: essa fica escolhida (D-059)."""
    opcoes = tp.opcoes()
    if ambiente not in opcoes:
        raise ValueError(f"não há versão {ambiente} para este treino")
    t = opcoes[ambiente]
    return replace(tp, treino=t, ambiente=ambiente, alternativa=None, escolhido=True,
                   alta_intensidade=alta_intensidade(t, cfg) or tp.papel == "prova")
