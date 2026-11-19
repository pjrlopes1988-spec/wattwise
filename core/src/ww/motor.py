"""Motor de adaptação diária (spec 7). Determinístico, sem base de dados, sem LLM.

1. `avaliar`: combina os sinais da manhã num estado — verde / amarelo / vermelho / bloqueado
   (spec 7.4) — e diz que dados faltaram.
2. `decidir`: aplica o estado ao treino do dia e devolve uma `Decisao` com o registo completo
   (entradas, regras, treino original, treino final; spec 7.1). Em caso de dúvida, a opção mais
   conservadora (spec 7.1).
3. `reorganizar_semana`: treino falhado (sem acumular), carga real acima do previsto, atividades
   não planeadas (spec 7.4).

Limites de segurança (spec 7.3): alarme → bloqueado; doença → sem intensidade até melhorar;
nunca mais de N dias seguidos de alta intensidade; rampa da Condição.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from typing import Any, Literal

from ww.config import Config
from ww.plano import TreinoPlaneado, alta_intensidade
from ww.recuperacao import EstadoFCR, LinhaBase
from ww.treinos import Treino, biblioteca

Estado = Literal["verde", "amarelo", "vermelho", "bloqueado"]


# ------------------------------------------------------------------ entradas

@dataclass(frozen=True)
class Questionario:
    """Questionário matinal (1–5; cansaço/dores/stress: mais alto = pior; humor: mais baixo = pior)."""
    cansaco: int | None = None
    dores: int | None = None
    stress: int | None = None
    humor: int | None = None
    doenca: bool = False
    febre: bool = False
    melhorou: bool = False               # o atleta indica que já está melhor (fim da doença)
    alarmes: frozenset[str] = frozenset()


@dataclass(frozen=True)
class SinaisDia:
    data: date
    vfc: LinhaBase | None = None
    fc_repouso: EstadoFCR | None = None
    sono_h: float | None = None
    questionario: Questionario | None = None
    frescura_pct: float | None = None


@dataclass(frozen=True)
class EstadoAtleta:
    """O que o motor tem de lembrar de um dia para o outro."""
    doente_desde: date | None = None


# ------------------------------------------------------------------ prontidão

@dataclass(frozen=True)
class Sinal:
    codigo: str
    valor: Any
    limiar: Any
    forte: bool = False                  # forte = vermelho direto


@dataclass(frozen=True)
class Prontidao:
    data: date
    estado: Estado
    sinais: tuple[Sinal, ...]
    em_falta: tuple[str, ...]
    doente: bool


def avaliar(s: SinaisDia, anterior: EstadoAtleta, cfg: Config) -> tuple[Prontidao, EstadoAtleta]:
    m = cfg.motor
    q = s.questionario
    sinais: list[Sinal] = []
    falta: list[str] = []

    # Sinais de alarme → bloquear (spec 7.3)
    if q is not None and q.alarmes & set(m.alarmes):
        alarmes = ",".join(sorted(q.alarmes & set(m.alarmes)))
        return (Prontidao(s.data, "bloqueado", (Sinal("alarme", alarmes, None, True),), (), anterior.doente_desde is not None),
                anterior)

    # Doença: fica ativa até o atleta indicar melhoria (spec 7.3)
    doente_desde = anterior.doente_desde
    if q is not None and q.doenca:
        doente_desde = doente_desde or s.data
    elif q is not None and q.melhorou:
        doente_desde = None
    if doente_desde is not None:
        sinais.append(Sinal("doenca", "febre" if q is not None and q.febre else "sintomas", None, True))

    # VFC
    if s.vfc is None or s.vfc.estado in ("a_calibrar", "sem_dados_recentes"):
        falta.append("vfc" if s.vfc is None or s.vfc.estado == "sem_dados_recentes" else "vfc_a_calibrar")
    elif s.vfc.estado == "abaixo":
        sinais.append(Sinal("vfc_abaixo", round(s.vfc.em_ms(s.vfc.media7) or 0, 1),
                            round(s.vfc.em_ms(s.vfc.faixa_inf) or 0, 1),
                            forte=s.vfc.dias_seguidos_fora >= m.vfc_dias_abaixo_vermelho))

    # FC de repouso
    if s.fc_repouso is None or s.fc_repouso.linha_base.estado in ("a_calibrar", "sem_dados_recentes"):
        falta.append("fc_repouso")
    elif s.fc_repouso.linha_base.estado == "acima":
        lb = s.fc_repouso.linha_base
        sinais.append(Sinal("fc_repouso_alta", round(lb.media7 or 0, 1), round(lb.faixa_sup or 0, 1),
                            forte=s.fc_repouso.alerta))

    # Sono
    if s.sono_h is None:
        falta.append("sono")
    elif s.sono_h < cfg.recuperacao.sono_curto_h:
        sinais.append(Sinal("sono_curto", s.sono_h, cfg.recuperacao.sono_curto_h))

    # Questionário
    if q is None:
        falta.append("questionario")
    else:
        for nome in ("cansaco", "dores", "stress"):
            v = getattr(q, nome)
            if v is not None and v >= m.questionario_limiar_mau:
                sinais.append(Sinal(nome, v, m.questionario_limiar_mau))
        if q.humor is not None and q.humor <= m.humor_limiar_mau:
            sinais.append(Sinal("humor", q.humor, m.humor_limiar_mau))

    # Frescura (forma em %)
    if s.frescura_pct is None:
        falta.append("frescura")
    elif s.frescura_pct < m.frescura_pct_vermelho:
        sinais.append(Sinal("frescura_muito_negativa", round(s.frescura_pct, 1), m.frescura_pct_vermelho, forte=True))
    elif s.frescura_pct < m.frescura_pct_sinal:
        sinais.append(Sinal("frescura_negativa", round(s.frescura_pct, 1), m.frescura_pct_sinal))

    if any(x.forte for x in sinais) or len(sinais) >= m.sinais_para_vermelho:
        estado: Estado = "vermelho"
    elif sinais:
        estado = "amarelo"
    else:
        estado = "verde"
    return (Prontidao(s.data, estado, tuple(sinais), tuple(falta), doente_desde is not None),
            EstadoAtleta(doente_desde))


# ------------------------------------------------------------------ decisão

@dataclass(frozen=True)
class Decisao:
    """Registo de decisão (spec 7.1). `registo()` é o que vai para a auditoria e para o LLM."""
    data: date
    estado: Estado
    regras: tuple[str, ...]
    prontidao: Prontidao
    treino_original: TreinoPlaneado | None
    treino_final: TreinoPlaneado | None
    procurar_medico: bool
    versao_config: str
    versao_motor: str

    def registo(self) -> dict[str, Any]:
        """Sem dados identificáveis (spec 9): só o estado, sinais, regras e treinos."""
        def tr(t: TreinoPlaneado | None) -> dict[str, Any] | None:
            if t is None:
                return None
            return {"opcoes": {amb: {"id": x.id, "nome": x.titulo, "tipo": x.tipo, "minutos": round(x.minutos),
                                     "carga": round(x.carga, 1)} for amb, x in t.opcoes().items()},
                    "papel": t.papel, "alta_intensidade": t.alta_intensidade}
        return {
            "data": self.data.isoformat(), "estado": self.estado, "regras": list(self.regras),
            "sinais": [{"codigo": x.codigo, "valor": x.valor, "limiar": x.limiar, "forte": x.forte}
                       for x in self.prontidao.sinais],
            "dados_em_falta": list(self.prontidao.em_falta),
            "treino_original": tr(self.treino_original), "treino_final": tr(self.treino_final),
            "procurar_medico": self.procurar_medico,
            "versao_config": self.versao_config, "versao_motor": self.versao_motor,
        }


def _arred(minutos: float, passo: int) -> int:
    return int(minutos // passo * passo)


def _recuperacao(t: Treino, minutos: int, lib: dict[str, Treino]) -> Treino:
    return lib["recuperacao_indoor" if t.ambiente == "indoor" else "recuperacao"].com_duracao(minutos)


def _resistencia(t: Treino, minutos: int, lib: dict[str, Treino]) -> Treino:
    return lib["resistencia_indoor" if t.ambiente == "indoor" else "resistencia"].com_duracao(minutos)


def _mais_facil(t: Treino, lib: dict[str, Treino], cfg: Config) -> Treino | None:
    """Mesmo tipo e ambiente, mais fácil, com até `amarelo_fator_carga` da carga."""
    cand = [x for x in biblioteca(lib, t.ambiente).values()
            if x.tipo == t.tipo and x.dificuldade < t.dificuldade and x.carga <= cfg.motor.amarelo_fator_carga * t.carga
            and x.minutos <= t.minutos + 1]
    return max(cand, key=lambda x: (x.carga, x.id)) if cand else None


def _aplicar(tp: TreinoPlaneado, f: Any, papel: str | None, cfg: Config) -> TreinoPlaneado:
    """Aplica a alteração às duas versões (indoor/outdoor) do treino."""
    novo = f(tp.treino)
    alt = f(tp.alternativa) if tp.alternativa is not None else None
    alta = alta_intensidade(novo, cfg) or (alt is not None and alta_intensidade(alt, cfg))
    return replace(tp, treino=novo, alternativa=alt, papel=papel or tp.papel, alta_intensidade=alta)


def decidir(
    tp: TreinoPlaneado | None,
    p: Prontidao,
    lib: dict[str, Treino],
    cfg: Config,
    *,
    verificar_prontidao: bool = False,
) -> Decisao:
    m = cfg.motor
    passo = cfg.plano.arredondar_min
    regras: list[str] = []
    final = tp
    medico = False

    def dec(estado: Estado) -> Decisao:
        return Decisao(p.data, estado, tuple(regras), p, tp, final, medico, cfg.versao, m.versao)

    if p.estado == "bloqueado":
        regras.append("alarme_bloqueia_treino")
        final, medico = None, True
        return dec("bloqueado")

    if tp is None:
        regras.append("dia_de_descanso")
        return dec(p.estado)

    if tp.papel == "prova":
        if p.doente:
            regras.append("doenca_prova_desaconselhada")
            final = None
        else:
            regras.append("prova_mantida" if p.estado == "verde" else "prova_mantida_com_alerta")
        return dec(p.estado)

    if p.doente:
        febre = any(x.codigo == "doenca" and x.valor == "febre" for x in p.sinais)
        if febre and m.doenca_febre_descanso:
            regras.append("doenca_febre_descanso")
            final = None
        else:
            regras.append("doenca_sem_intensidade")
            minutos = min(m.vermelho_recuperacao_min, tp.minutos)
            final = _aplicar(tp, lambda t: _recuperacao(t, minutos, lib), "recuperacao", cfg)
        return dec("vermelho")

    estado = p.estado
    # Depois da recuperação de uma prova A: só retomar a carga com prontidão verde (D-063)
    if verificar_prontidao and estado != "verde" and (tp.alta_intensidade or tp.papel in ("sessao_chave", "teste")):
        regras.append("prontidao_apos_prova_A_prolonga_recuperacao")
        estado = "vermelho"

    if estado == "vermelho":
        if tp.papel == "recuperacao" and tp.minutos <= m.vermelho_recuperacao_min:
            regras.append("vermelho_mantem_recuperacao")
        else:
            regras.append("vermelho_recuperacao_ativa")
            minutos = min(m.vermelho_recuperacao_min, tp.minutos)
            final = _aplicar(tp, lambda t: _recuperacao(t, minutos, lib), "recuperacao", cfg)
        return dec("vermelho") if p.estado != "verde" else dec(p.estado)

    if estado == "amarelo":
        if tp.papel == "teste":
            regras.append("amarelo_teste_adiado")
            final = _aplicar(tp, lambda t: _resistencia(t, max(30, _arred(t.minutos * 0.8, passo)), lib),
                             "resistencia", cfg)
        elif tp.papel in ("sessao_chave", "ativacao") or tp.alta_intensidade:
            facil = _mais_facil(tp.treino, lib, cfg)
            if facil is not None:
                regras.append("amarelo_versao_mais_facil")
                final = _aplicar(tp, lambda t: _mais_facil(t, lib, cfg) or _resistencia(
                    t, max(30, _arred(t.minutos * 0.8, passo)), lib), None, cfg)
            else:
                regras.append("amarelo_troca_por_resistencia")
                final = _aplicar(tp, lambda t: _resistencia(t, max(30, _arred(t.minutos * 0.8, passo)), lib),
                                 "resistencia", cfg)
        elif tp.papel in ("resistencia", "dia_longo"):
            regras.append("amarelo_resistencia_mais_curta")
            minutos = max(30, _arred(tp.minutos * m.amarelo_fator_resistencia, passo))
            final = _aplicar(tp, lambda t: _resistencia(t, min(minutos, round(t.minutos)), lib), None, cfg)
        else:
            regras.append("amarelo_mantem_recuperacao")
        return dec("amarelo")

    regras.append("verde_mantem_treino")
    return dec("verde")


# ------------------------------------------------------------------ semana

@dataclass(frozen=True)
class Feito:
    """Atividade realizada (de ficheiro FIT ou integração), já com a carga calculada."""
    data: date
    carga: float
    intensidade: float | None = None     # IF da atividade (se houver potência)
    planeado: bool = True                # corresponde ao treino planeado desse dia
    alta: bool | None = None             # se None, decide-se pela intensidade

    def alta_intensidade(self, cfg: Config) -> bool:
        if self.alta is not None:
            return self.alta
        return self.intensidade is not None and self.intensidade >= cfg.motor.alta_intensidade_if_feito


@dataclass(frozen=True)
class Reorganizacao:
    treinos: tuple[TreinoPlaneado, ...]
    regras: tuple[str, ...] = field(default_factory=tuple)


def _seguidos_excede(altos: set[date], d: date, maximo: int, provas: set[date]) -> bool:
    from ww.plano import _excesso
    return _excesso(altos | {d}, maximo, provas) > 0


def reorganizar_semana(
    planeados: Iterable[TreinoPlaneado],
    feitos: Mapping[date, Feito],
    hoje: date,
    lib: dict[str, Treino],
    cfg: Config,
    *,
    bloqueados_intensidade: set[date] = frozenset(),  # type: ignore[assignment]
) -> Reorganizacao:
    """Ajusta os treinos de hoje em diante (spec 7.4).

    - Treino-chave falhado: não se acumula; o mais importante passa para um dia de resistência
      que ainda não passou, se isso respeitar os dias seguidos de alta intensidade; os outros caem.
    - Atividade não planeada ou feita com intensidade alta: o dia seguinte não pode ser mais um dia
      intenso se isso passar do limite; a sessão-chave desse dia troca com um dia de resistência
      ou passa a resistência.
    - Carga real dos últimos 7 dias acima do planeado: encurtam-se os próximos treinos de resistência.
    """
    c = cfg.plano
    trs = sorted(planeados, key=lambda t: t.data)
    regras: list[str] = []
    provas = {t.data for t in trs if t.papel == "prova"}

    def altos_atuais() -> set[date]:
        feitos_altos = {d for d, f in feitos.items() if d < hoje and f.alta_intensidade(cfg)}
        futuros = {t.data for t in trs if t.data >= hoje and t.alta_intensidade}
        return feitos_altos | futuros

    # 1) treinos-chave falhados
    falhados = [t for t in trs if t.data < hoje and t.papel in ("sessao_chave", "teste") and t.data not in feitos]
    if falhados:
        principal = max(falhados, key=lambda t: (t.treino.dificuldade, t.treino.carga))
        livres = [t for t in trs if t.data >= hoje and t.papel == "resistencia" and t.data not in bloqueados_intensidade
                  and t.minutos >= principal.minutos]
        movido = False
        for alvo in livres:
            altos = altos_atuais()
            if _seguidos_excede(altos, alvo.data, c.max_dias_alta_intensidade_seguidos, provas):
                continue
            trs[trs.index(alvo)] = replace(principal, data=alvo.data)
            regras.append(f"treino_falhado_movido:{principal.data.isoformat()}->{alvo.data.isoformat()}")
            movido = True
            break
        if not movido:
            regras.append(f"treino_falhado_nao_acumulado:{principal.data.isoformat()}")
        for t in falhados:
            if t is not principal:
                regras.append(f"treino_falhado_nao_acumulado:{t.data.isoformat()}")
            # no histórico fica marcado como falhado (não conta como feito nem como dia intenso)
            trs[trs.index(t)] = replace(t, papel="falhado", alta_intensidade=False)

    # 2) intensidade a mais (não planeada ou acima do previsto): proteger os dias seguintes
    for i, t in enumerate(trs):
        if t.data < hoje or not t.alta_intensidade or t.papel == "prova":
            continue
        altos_feitos = {d for d, f in feitos.items() if d < hoje and f.alta_intensidade(cfg)}
        if not _seguidos_excede(altos_feitos | {x.data for x in trs if x.data >= hoje and x.alta_intensidade and x is not t},
                                t.data, c.max_dias_alta_intensidade_seguidos, provas):
            continue
        # trocar com um dia de resistência mais à frente, se possível; senão, passa a resistência
        trocado = False
        for j, alvo in enumerate(trs):
            if alvo.data <= t.data or alvo.papel != "resistencia" or alvo.data in bloqueados_intensidade:
                continue
            outros = altos_feitos | {x.data for x in trs if x.data >= hoje and x.alta_intensidade and x is not t}
            if not _seguidos_excede(outros, alvo.data, c.max_dias_alta_intensidade_seguidos, provas) \
                    and alvo.minutos >= t.minutos:
                trs[i], trs[j] = replace(alvo, data=t.data), replace(t, data=alvo.data)
                regras.append(f"intensidade_a_mais_sessao_trocada:{t.data.isoformat()}->{alvo.data.isoformat()}")
                trocado = True
                break
        if not trocado:
            trs[i] = _aplicar(t, lambda x: _resistencia(x, round(x.minutos), lib), "resistencia", cfg)
            regras.append(f"intensidade_a_mais_sessao_passa_a_resistencia:{t.data.isoformat()}")

    # 3) carga real acima do planeado nos últimos 7 dias: encurtar a resistência que vem
    janela = {hoje - timedelta(days=k) for k in range(1, 8)}
    real = sum(f.carga for d, f in feitos.items() if d in janela)
    previsto = sum(t.carga for t in trs if t.data in janela)
    if previsto > 0 and real > previsto * (1 + cfg.motor.excesso_carga_7d_pct / 100):
        excesso = real - previsto
        regras.append(f"carga_acima_do_previsto:{real:.0f}>{previsto:.0f}")
        for i, t in enumerate(trs):
            if excesso <= 0:
                break
            if t.data < hoje or t.papel not in ("resistencia", "dia_longo"):
                continue
            por_min = t.carga / max(1, t.minutos)
            cortar = min(t.minutos - c.duracao_minima_treino_min, int(excesso / por_min))
            cortar = int(cortar // c.arredondar_min * c.arredondar_min)
            if cortar <= 0:
                continue
            trs[i] = _aplicar(t, lambda x, n=round(t.minutos) - cortar: _resistencia(x, min(n, round(x.minutos)), lib),
                              None, cfg)
            excesso -= cortar * por_min
            regras.append(f"resistencia_encurtada:{t.data.isoformat()}:-{cortar}min")

    return Reorganizacao(tuple(trs), tuple(regras))
