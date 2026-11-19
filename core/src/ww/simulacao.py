"""Simulação de temporada (spec 10.4): o motor corre dia a dia sobre meses de dados simulados.

O atleta simulado comporta-se como uma pessoa: falha treinos, às vezes faz mais do que o
previsto, aparece em voltas de grupo, dorme mal, fica doente. A VFC, a FC de repouso e o
cansaço reagem à fadiga. No fim, `violacoes` lista cada limite de segurança ultrapassado
(spec 7.3) — uma temporada válida tem a lista vazia.

Tudo é determinístico (semente fixa).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field, replace
from datetime import date, timedelta

from ww.config import Config
from ww.metrics.load import fator
from ww.motor import (Decisao, EstadoAtleta, Feito, Prontidao, Questionario, SinaisDia, avaliar, decidir,
                      guarda_rampa, reorganizar_semana)
from ww.perfil import Atleta, nivel_regras
from ww.plano import Plano, TreinoPlaneado, _excesso, gerar
from ww.recuperacao import MedicaoVFC, fc_repouso, vfc
from ww.treinos import Treino


@dataclass(frozen=True)
class Comportamento:
    semente: int = 1
    cumprimento: float = 0.9                 # probabilidade de fazer o treino prescrito
    excesso_prob: float = 0.1                # faz mais do que o previsto...
    excesso_fator: float = 1.3               # ...com esta carga
    volta_grupo_prob: float = 0.15           # sábado sem treino intenso: vai à volta de grupo
    carga_volta_grupo: float = 130
    doencas: tuple[tuple[int, int, int], ...] = ()   # (dia de início, duração, dias com febre)
    alarme_dia: int | None = None
    com_vfc: bool = True
    responde_questionario: float = 0.8


@dataclass(frozen=True)
class DiaSim:
    data: date
    prontidao: Prontidao
    decisao: Decisao
    feito: Feito | None
    condicao: float
    fadiga: float


@dataclass
class Resultado:
    dias: list[DiaSim] = field(default_factory=list)
    planos: list[Plano] = field(default_factory=list)
    violacoes: list[str] = field(default_factory=list)

    def contagem_estados(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for d in self.dias:
            out[d.prontidao.estado] = out.get(d.prontidao.estado, 0) + 1
        return out


def simular(atleta: Atleta, lib: dict[str, Treino], cfg: Config, *, inicio: date, dias: int = 182,
            comportamento: Comportamento = Comportamento()) -> Resultado:
    rnd = random.Random(comportamento.semente)
    c = cfg.carga_forma
    f_c, f_a = fator(c.constante_condicao_dias, c.fator_media), fator(c.constante_fadiga_dias, c.fator_media)
    nivel = nivel_regras(atleta, inicio, cfg)
    rampa = cfg.plano.rampa_condicao_semana[nivel]
    maximo_seguidos = cfg.plano.max_dias_alta_intensidade_seguidos

    res = Resultado()
    ctl = atl = 0.0
    condicao_dia: dict[date, float] = {}
    feitos: dict[date, Feito] = {}
    meds_vfc: list[MedicaoVFC] = []
    fcr: dict[date, float] = {}
    estado = EstadoAtleta()
    plano: Plano | None = None
    agenda: dict[date, TreinoPlaneado] = {}
    semana_de_verificacao: set[date] = set()
    base_rmssd = 60.0

    doente_em: dict[int, bool] = {}       # dia → febre?
    for ini, dur, febre in comportamento.doencas:
        for k in range(dur):
            doente_em[ini + k] = k < febre

    for k in range(dias):
        hoje = inicio + timedelta(days=k)

        # --- (re)planear quando o plano acaba
        if plano is None or hoje > plano.fim:
            plano = gerar(atleta, lib, cfg, inicio=hoje, condicao_inicial=ctl, fadiga_inicial=atl)
            res.planos.append(plano)
            agenda.update({t.data: t for t in plano.treinos()})
            for s in plano.semanas:
                if s.verificar_prontidao:
                    semana_de_verificacao |= {s.inicio + timedelta(days=i) for i in range(7)}

        # --- sinais fisiológicos simulados (reagem à fadiga e à doença)
        tsb = ctl - atl
        doente = k in doente_em
        stress_fadiga = max(0.0, -tsb - 10) / 40
        if comportamento.com_vfc:
            rmssd = base_rmssd * math.exp(rnd.gauss(0, 0.08) - 0.35 * stress_fadiga - (0.25 if doente else 0))
            meds_vfc.append(MedicaoVFC(hoje, "sim", "rmssd", rmssd))
        fcr[hoje] = 48 + rnd.gauss(0, 1.2) + 4 * stress_fadiga + (6 if doente else 0)
        lb_vfc = vfc(meds_vfc, hoje, hoje, cfg.recuperacao)[0] if comportamento.com_vfc else None
        est_fcr = fc_repouso(fcr, hoje, hoje, cfg.recuperacao)[0]
        sono = max(3.5, rnd.gauss(7.2, 0.6) - (1.5 if rnd.random() < 0.08 else 0))
        q = None
        if rnd.random() < comportamento.responde_questionario or doente or comportamento.alarme_dia == k:
            cans = min(5, max(1, round(2 + 2.5 * stress_fadiga + rnd.gauss(0, 0.6))))
            alarmes = frozenset({"palpitacoes"}) if comportamento.alarme_dia == k else frozenset()
            q = Questionario(cansaco=cans, dores=min(5, max(1, cans + rnd.choice([-1, 0, 0]))), stress=rnd.choice([2, 2, 3]),
                             humor=rnd.choice([3, 4, 4]), doenca=doente, febre=doente_em.get(k, False),
                             melhorou=not doente and estado.doente_desde is not None, alarmes=alarmes)
        frescura_pct = (tsb / ctl * 100) if ctl >= cfg.carga_forma.condicao_minima_para_pct else None
        sinais = SinaisDia(hoje, lb_vfc, est_fcr, round(sono, 1), q, frescura_pct, frescura=tsb, condicao=ctl)

        # --- motor: reorganizar a semana, avaliar, decidir, guarda da rampa
        seg = hoje - timedelta(days=hoje.weekday())
        semana = [t for d, t in agenda.items() if seg <= d < seg + timedelta(days=7)]
        reorg = reorganizar_semana(semana, {d: f for d, f in feitos.items() if d >= seg}, hoje, lib, cfg)
        for t in reorg.treinos:
            agenda[t.data] = t
        prontidao, estado = avaliar(sinais, estado, cfg)
        dec = decidir(agenda.get(hoje), prontidao, lib, cfg, verificar_prontidao=hoje in semana_de_verificacao)
        dec = guarda_rampa(dec, ctl, condicao_dia.get(hoje - timedelta(days=7), 0.0), rampa, lib, cfg)

        # --- o atleta faz (ou não) o que foi prescrito
        presc = dec.treino_final
        feito: Feito | None = None
        if presc is not None and rnd.random() < comportamento.cumprimento:
            fator_c = comportamento.excesso_fator if rnd.random() < comportamento.excesso_prob else 1.0
            feito = Feito(hoje, presc.carga * fator_c, alta=presc.alta_intensidade)
        elif (presc is None or not presc.alta_intensidade) and hoje.weekday() == 5 \
                and prontidao.estado not in ("bloqueado",) and not prontidao.doente \
                and rnd.random() < comportamento.volta_grupo_prob:
            feito = Feito(hoje, comportamento.carga_volta_grupo, intensidade=0.9, planeado=False)
        if feito is not None:
            feitos[hoje] = feito

        carga = feito.carga if feito else 0.0
        ctl += (carga - ctl) * f_c
        atl += (carga - atl) * f_a
        condicao_dia[hoje] = ctl
        res.dias.append(DiaSim(hoje, prontidao, dec, feito, ctl, atl))

    res.violacoes = verificar(res, cfg, rampa, maximo_seguidos)
    return res


def verificar(res: Resultado, cfg: Config, rampa: float, maximo_seguidos: int) -> list[str]:
    """Limites de segurança (spec 7.3) verificados sobre as PRESCRIÇÕES do motor, dia a dia."""
    f_c = fator(cfg.carga_forma.constante_condicao_dias, cfg.carga_forma.fator_media)
    v: list[str] = []
    altos_feitos: set[date] = set()
    provas = {d.data for d in res.dias if d.decisao.treino_final is not None and d.decisao.treino_final.papel == "prova"}
    cond = {d.data: d.condicao for d in res.dias}
    for i, d in enumerate(res.dias):
        p = d.decisao.treino_final
        if d.prontidao.estado == "bloqueado" and p is not None:
            v.append(f"{d.data}: treino prescrito com sinal de alarme")
        if d.prontidao.doente and p is not None and p.alta_intensidade:
            v.append(f"{d.data}: intensidade prescrita com doença")
        if d.decisao.estado == "vermelho" and p is not None and (p.alta_intensidade or p.papel not in ("recuperacao", "prova")):
            v.append(f"{d.data}: dia vermelho com treino que não é recuperação")
        if p is not None and p.alta_intensidade and p.papel != "prova":
            if _excesso(altos_feitos | {d.data}, maximo_seguidos, provas):
                v.append(f"{d.data}: prescrito mais um dia seguido de alta intensidade")
        if p is not None and p.papel not in ("prova",):
            ontem = cond.get(d.data - timedelta(days=1), 0.0)
            com_prescricao = ontem + (p.carga - ontem) * f_c
            if com_prescricao - cond.get(d.data - timedelta(days=7), 0.0) > rampa + 1e-6:
                v.append(f"{d.data}: prescrição faria a Condição subir mais do que {rampa} em 7 dias")
        if d.feito is not None and d.feito.alta_intensidade(cfg):
            altos_feitos.add(d.data)
    # recuperação planeada pelo menos a cada 4 semanas
    for plano in res.planos:
        seguidas = 0
        for s in plano.semanas:
            seguidas = seguidas + 1 if s.fase in ("base", "construcao", "especifico") else 0
            if seguidas > 3:
                v.append(f"plano {plano.inicio}: mais de 3 semanas de carga seguidas (S{s.numero})")
    return v
