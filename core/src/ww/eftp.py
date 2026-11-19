"""FTP estimado automaticamente (eFTP), sem testes (spec 6.1).

Entrada: os melhores esforços de cada atividade (da curva de potência), já com a
indicação de qualidade. Só os esforços de atividades que passaram a verificação
de qualidade entram no cálculo (spec 6.6).

Saída: dois valores, nunca aplicados aqui:
- eFTP da época: só esforços desde o início da época, sem decaimento;
- eFTP com histórico: todos os esforços, com decaimento lento quando são antigos (D-023).

A decisão de propor uma alteração ao atleta está em `ww.ftp_proposta`.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal

from ww.config import Config
from ww.metrics.cp import ModeloPC, cp_de_um_esforco, monod_2p, morton_3p
from ww.stream import Array

OrigemW = Literal["atleta", "populacao"]


@dataclass(frozen=True)
class EsforcoMax:
    """Melhor média de uma atividade numa duração (um ponto da curva de potência)."""
    atividade_id: str
    data: date
    duracao_s: int
    potencia: float
    qualidade_ok: bool


@dataclass(frozen=True)
class PerfilAnaerobio:
    w_linha: float
    pmax: float
    origem: OrigemW


@dataclass(frozen=True)
class Estimativa:
    ftp: float
    cp: float
    metodo: str
    perfil: PerfilAnaerobio
    esforcos: tuple[EsforcoMax, ...]   # os esforços que determinaram o valor (marcadores no gráfico 4)


@dataclass(frozen=True)
class ResultadoEFTP:
    epoca: Estimativa | None
    historico: Estimativa | None
    # eFTP de cada atividade isoladamente (método de 1 esforço), para confirmar subidas
    por_atividade: dict[str, float]


# ---------------------------------------------------------------- auxiliares

def fator_decaimento(data_esforco: date, hoje: date, cfg: Config) -> float:
    """1 durante a carência; depois desce `decaimento_pct_por_semana` por semana (composto)."""
    dias = (hoje - data_esforco).days - cfg.eftp.decaimento_carencia_dias
    if dias <= 0:
        return 1.0
    return float((1.0 - cfg.eftp.decaimento_pct_por_semana / 100.0) ** (dias / 7.0))


def envolvente(esforcos: Iterable[EsforcoMax]) -> dict[int, EsforcoMax]:
    """Melhor esforço por duração."""
    melhor: dict[int, EsforcoMax] = {}
    for e in esforcos:
        if e.duracao_s not in melhor or e.potencia > melhor[e.duracao_s].potencia:
            melhor[e.duracao_s] = e
    return melhor


def _validos(esforcos: Iterable[EsforcoMax], hoje: date) -> list[EsforcoMax]:
    return [e for e in esforcos if e.qualidade_ok and e.data <= hoje and e.potencia > 0]


def _ajuste_3p(env: dict[int, EsforcoMax], cfg: Config) -> ModeloPC | None:
    """Morton 3p se houver esforço curto (≤15 s), médio (2–6 min) e longo (10–30 min)."""
    curtos = [d for d in env if d <= 15]
    medios = [d for d in env if 120 <= d <= 360]
    longos = [d for d in env if 600 <= d <= cfg.modelo_potencia_critica.duracao_maxima_esforco_s]
    if not (curtos and medios and longos):
        return None
    pontos = [(float(d), env[d].potencia) for d in sorted(env) if d <= cfg.modelo_potencia_critica.duracao_maxima_esforco_s]
    try:
        m = morton_3p(pontos)
    except (ValueError, RuntimeError):
        return None
    lo, hi = cfg.eftp.w_linha_plausivel_j
    if not (lo <= m.w_linha <= hi) or m.pmax is None or m.pmax <= m.cp:
        return None
    return m


def perfil_anaerobio(esforcos: Sequence[EsforcoMax], hoje: date, peso_kg: float, cfg: Config) -> PerfilAnaerobio:
    """W′ e Pmax do atleta (janela recente) ou, se não houver dados que cheguem, da população."""
    janela = [e for e in _validos(esforcos, hoje) if (hoje - e.data).days <= cfg.eftp.janela_perfil_dias]
    env = envolvente(janela)
    # Uma só sessão (ex.: intervalos não máximos) dá W′ pouco fiável: exigir várias atividades
    if len({e.atividade_id for e in env.values()}) < cfg.eftp.perfil_minimo_atividades:
        m = None
    else:
        m = _ajuste_3p(env, cfg)
    if m is not None and m.pmax is not None:
        return PerfilAnaerobio(m.w_linha, m.pmax, "atleta")
    pop = cfg.modelo_potencia_critica.populacao
    return PerfilAnaerobio(pop.w_linha_j, pop.pmax_w_por_kg * peso_kg, "populacao")


def _cp_um_esforco(e: EsforcoMax, perfil: PerfilAnaerobio, potencia: float | None = None) -> float | None:
    try:
        return cp_de_um_esforco(e.duracao_s, potencia if potencia is not None else e.potencia,
                                perfil.w_linha, perfil.pmax).cp
    except ValueError:
        return None


# ---------------------------------------------------------------- estimativa

def _estimar(
    esforcos: Sequence[EsforcoMax], perfil: PerfilAnaerobio, cfg: Config, pesos: dict[int, float]
) -> Estimativa | None:
    """Aplica o método configurado. `pesos[id(e)]` = fator de decaimento de cada esforço."""
    mpc = cfg.modelo_potencia_critica
    fator = mpc.ftp_fator_cp
    metodo = cfg.eftp.metodo

    if metodo == "morton_1_esforco":
        melhor: tuple[float, EsforcoMax] | None = None
        for e in esforcos:
            if not (mpc.duracao_minima_esforco_s <= e.duracao_s <= mpc.duracao_maxima_esforco_s):
                continue
            cp = _cp_um_esforco(e, perfil, e.potencia * pesos[id(e)])
            if cp is not None and (melhor is None or cp > melhor[0]):
                melhor = (cp, e)
        if melhor is None:
            return None
        return Estimativa(melhor[0] * fator, melhor[0], metodo, perfil, (melhor[1],))

    env = envolvente(_com_peso(esforcos, pesos))
    if metodo == "morton_3p":
        m = _ajuste_3p(env, cfg)
        if m is None:
            return None
        usados = tuple(env[d] for d in sorted(env) if d <= mpc.duracao_maxima_esforco_s)
        p = PerfilAnaerobio(m.w_linha, m.pmax or perfil.pmax, "atleta")
        return Estimativa(m.cp * fator, m.cp, metodo, p, _originais(usados, esforcos))

    # monod_2p: esforços de 3–5 min e de 10–30 min
    curtos = [env[d] for d in env if 180 <= d <= 300]
    longos = [env[d] for d in env if 600 <= d <= mpc.duracao_maxima_esforco_s]
    if not (curtos and longos):
        return None
    try:
        m = monod_2p([(float(e.duracao_s), e.potencia) for e in curtos + longos])
    except ValueError:
        return None
    p = PerfilAnaerobio(m.w_linha, perfil.pmax, "atleta")
    return Estimativa(m.cp * fator, m.cp, metodo, p, _originais(tuple(curtos + longos), esforcos))


def _com_peso(esforcos: Sequence[EsforcoMax], pesos: dict[int, float]) -> list[EsforcoMax]:
    # Cópias com a potência decaída; `_originais` liga-as de volta aos esforços originais.
    return [EsforcoMax(e.atividade_id, e.data, e.duracao_s, e.potencia * pesos[id(e)], e.qualidade_ok)
            for e in esforcos]


def _originais(usados: Iterable[EsforcoMax], esforcos: Sequence[EsforcoMax]) -> tuple[EsforcoMax, ...]:
    idx = {(e.atividade_id, e.duracao_s): e for e in esforcos}
    return tuple(idx[(u.atividade_id, u.duracao_s)] for u in usados)


def estimar(
    esforcos: Sequence[EsforcoMax],
    *,
    hoje: date,
    inicio_epoca: date,
    peso_kg: float,
    cfg: Config,
) -> ResultadoEFTP:
    validos = _validos(esforcos, hoje)
    perfil = perfil_anaerobio(validos, hoje, peso_kg, cfg)

    epoca = [e for e in validos if e.data >= inicio_epoca]
    sem_decaimento = {id(e): 1.0 for e in validos}
    com_decaimento = {id(e): fator_decaimento(e.data, hoje, cfg) for e in validos}

    por_atividade: dict[str, float] = {}
    mpc = cfg.modelo_potencia_critica
    for e in validos:
        if mpc.duracao_minima_esforco_s <= e.duracao_s <= mpc.duracao_maxima_esforco_s:
            cp = _cp_um_esforco(e, perfil)
            if cp is not None:
                ftp = cp * mpc.ftp_fator_cp
                por_atividade[e.atividade_id] = max(ftp, por_atividade.get(e.atividade_id, 0.0))

    return ResultadoEFTP(
        epoca=_estimar(epoca, perfil, cfg, sem_decaimento),
        historico=_estimar(validos, perfil, cfg, com_decaimento),
        por_atividade=por_atividade,
    )


def ftp_teste_20min(potencia_media_20min: float, cfg: Config) -> float:
    """Alternativa sem dados: teste guiado de 20 min."""
    return potencia_media_20min * cfg.eftp.fator_teste_20min


def esforcos_da_atividade(
    potencia_limpa: Array, atividade_id: str, data: date, qualidade_ok: bool, cfg: Config
) -> list[EsforcoMax]:
    """Pontos da curva de potência de uma atividade (já limpa) nas durações do eFTP."""
    from ww.metrics.power import melhor_media

    out = []
    for d in cfg.eftp.duracoes_curva_s:
        p = melhor_media(potencia_limpa, d)
        if p is not None:
            out.append(EsforcoMax(atividade_id, data, d, p, qualidade_ok))
    return out
