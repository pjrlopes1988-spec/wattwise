"""API da Wattwise (FastAPI). Os cálculos e as decisões são do motor (wattwise-core); aqui só se
guardam dados e se chamam as funções já testadas.

Autenticação: fora do âmbito desta fase (Fase 6). Todas as rotas ficam sob /atletas/{id}.
"""


from datetime import date, datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import AtividadeDB, AtletaDB, BemEstarDB, ConsentimentoDB, DecisaoDB, criar_sessoes
from app.serial import atleta_de_json, atleta_para_json
from ww.alvos import descrever
from ww.analise import Fisiologia, analisar
from ww.config import Config, carregar as carregar_cfg
from ww.dedup import AtividadeRef, procurar_duplicado
from ww.eftp import EsforcoMax, esforcos_da_atividade, estimar
from ww.explicacao import explicar
from ww.exportar import nome_ficheiro, para_erg, para_mrc, para_zwo
from ww.fit.reader import ErroFIT, ler_bytes
from ww.metrics.load import fator
from ww.motor import EstadoAtleta, Feito, Questionario, SinaisDia, avaliar, decidir, guarda_rampa, reorganizar_semana
from ww.perfil import (Atleta, FTPInvalido, PerfilInvalido, Prova, ambientes, agressividade, ciclo_sugerido,
                       completar, definir_ftp_manual, ftp_em_vigor, nivel_regras, onde_treina, tem_potencia, validar)
from ww.plano import Plano, TreinoPlaneado, escolher, gerar
from ww.quality.clean import limpar
from ww.recuperacao import MedicaoVFC, fc_repouso, vfc
from ww.treinos import Treino, carregar as carregar_lib

VERSAO_CONSENTIMENTO = "1.0"


def criar_app(url_bd: str = "sqlite:///:memory:", cfg: Config | None = None,
              origens: tuple[str, ...] = ("http://localhost:8081", "http://127.0.0.1:8081")) -> FastAPI:
    from fastapi.middleware.cors import CORSMiddleware

    cfg = cfg or carregar_cfg()
    lib = carregar_lib()
    Sessao = criar_sessoes(url_bd)
    app = FastAPI(title="Wattwise API", version="0.1.0")
    # só para a versão web da app em desenvolvimento; a app nativa não precisa de CORS
    app.add_middleware(CORSMiddleware, allow_origins=list(origens), allow_methods=["*"], allow_headers=["*"])

    def bd():  # type: ignore[no-untyped-def]
        with Sessao() as s:
            yield s

    def obter(s: Session, aid: int) -> AtletaDB:
        r = s.get(AtletaDB, aid)
        if r is None:
            raise HTTPException(404, "atleta não encontrado")
        return r

    def hoje_utc() -> date:
        return datetime.now(timezone.utc).date()

    # ------------------------------------------------------------ cargas, forma e eFTP a partir das atividades

    def atividades(s: Session, aid: int) -> list[AtividadeDB]:
        return list(s.scalars(select(AtividadeDB).where(AtividadeDB.atleta_id == aid, AtividadeDB.principal)
                              .order_by(AtividadeDB.inicio)))

    def forma_ate(s: Session, aid: int, ate: date) -> tuple[float, float, dict[date, float]]:
        """Condição e Fadiga no fim do dia anterior a `ate`, com a carga real; e a Condição dia a dia."""
        c = cfg.carga_forma
        f_c, f_a = fator(c.constante_condicao_dias, c.fator_media), fator(c.constante_fadiga_dias, c.fator_media)
        cargas: dict[date, float] = {}
        for a in atividades(s, aid):
            cargas[a.data] = cargas.get(a.data, 0.0) + (a.carga or 0.0)
        if not cargas:
            return 0.0, 0.0, {}
        ctl = atl = 0.0
        por_dia: dict[date, float] = {}
        d = min(cargas)
        while d < ate:
            x = cargas.get(d, 0.0)
            ctl += (x - ctl) * f_c
            atl += (x - atl) * f_a
            por_dia[d] = ctl
            d += timedelta(days=1)
        return ctl, atl, por_dia

    def eftp(s: Session, aid: int, atleta: Atleta, ate: date) -> float | None:
        esf = [EsforcoMax(str(a.id), a.data, int(d), float(p), bool(a.resumo.get("qualidade_ok")))
               for a in atividades(s, aid) for d, p in a.resumo.get("esforcos", [])]
        r = estimar(esf, hoje=ate, inicio_epoca=date(ate.year, 1, 1), peso_kg=atleta.peso_kg, cfg=cfg)
        return round(r.historico.ftp) if r.historico else None

    def plano_de(reg: AtletaDB, s: Session) -> Plano:
        atleta = completar(atleta_de_json(reg.perfil), hoje_utc(), cfg)
        meta = reg.perfil.get("_plano", {})
        inicio = date.fromisoformat(meta["inicio"]) if meta else hoje_utc()
        return gerar(atleta, lib, cfg, inicio=inicio, condicao_inicial=meta.get("ctl", 0.0), fadiga_inicial=meta.get("atl", 0.0))

    def replanear(reg: AtletaDB, s: Session) -> None:
        h = hoje_utc()
        ctl, atl, _ = forma_ate(s, reg.id, h)
        reg.perfil = {**reg.perfil, "_plano": {"inicio": h.isoformat(), "ctl": ctl, "atl": atl}}

    # ------------------------------------------------------------ representação dos treinos para a app

    def treino_json(t: Treino, atleta: Atleta) -> dict[str, Any]:
        ftp = atleta.ftp.valor if atleta.ftp else None
        fcl = atleta.fc_limiar.valor if atleta.fc_limiar else None
        pot = tem_potencia(atleta, t.ambiente)  # type: ignore[arg-type]
        return {
            "id": t.id, "nome": t.nome, "subtitulo": t.subtitulo, "titulo": t.titulo, "tipo": t.tipo,
            "ambiente": t.ambiente, "minutos": round(t.minutos), "carga": round(t.carga, 1), "descricao": t.descricao,
            "passos": [{"segundos": p.segundos, "pct_min": p.pct_min, "pct_max": p.pct_max, "rampa": p.rampa,
                        "cadencia": p.cadencia, "alvo": descrever(p, ftp=ftp, fc_limiar=fcl, potencia=pot, cfg=cfg)}
                       for p in t.passos],
        }

    def tp_json(tp: TreinoPlaneado | None, atleta: Atleta) -> dict[str, Any] | None:
        if tp is None:
            return None
        return {"data": tp.data.isoformat(), "papel": tp.papel, "alta_intensidade": tp.alta_intensidade,
                "prioridade": tp.prioridade, "escolhido": tp.escolhido,
                "opcoes": [treino_json(t, atleta) for t in tp.opcoes().values()]}

    # ------------------------------------------------------------ atletas

    class NovoAtleta(BaseModel):
        perfil: dict[str, Any]
        consentimento_dados_saude: bool = Field(description="Consentimento explícito e separado (RGPD, spec 9)")

    @app.post("/atletas", status_code=201)
    def criar(body: NovoAtleta, s: Session = Depends(bd)) -> dict[str, Any]:
        if not body.consentimento_dados_saude:
            raise HTTPException(400, "é preciso o consentimento explícito para tratar dados de saúde")
        try:
            atleta = atleta_de_json(body.perfil)
            validar(atleta, hoje_utc(), cfg)
        except (PerfilInvalido, KeyError, ValueError, TypeError) as e:
            raise HTTPException(422, str(e))
        reg = AtletaDB(perfil=atleta_para_json(atleta))
        s.add(reg)
        s.flush()
        s.add(ConsentimentoDB(atleta_id=reg.id, tipo="dados_saude", versao_texto=VERSAO_CONSENTIMENTO))
        replanear(reg, s)
        s.commit()
        return {"id": reg.id, "sugestoes": {"onde_treina": onde_treina(atleta),
                                            "ciclo": ciclo_sugerido(atleta, hoje_utc(), cfg), "intensidade": 3}}

    @app.get("/atletas/{aid}")
    def ver(aid: int, s: Session = Depends(bd)) -> dict[str, Any]:
        reg = obter(s, aid)
        atleta = completar(atleta_de_json(reg.perfil), hoje_utc(), cfg)
        return {"id": aid, "perfil": atleta_para_json(atleta), "eftp": eftp(s, aid, atleta, hoje_utc()),
                "nivel_regras": nivel_regras(atleta, hoje_utc(), cfg), "ambientes": list(ambientes(atleta)),
                "intensidade": agressividade(atleta, hoje_utc(), cfg)}

    class Preferencias(BaseModel):
        onde_treina: str | None = None
        ciclo: str | None = None
        agressividade: int | None = None
        ftp_modo: str | None = None
        disponibilidade: list[int] | None = None
        dia_longo: int | None = None

    @app.put("/atletas/{aid}/preferencias")
    def preferencias(aid: int, body: Preferencias, s: Session = Depends(bd)) -> dict[str, Any]:
        reg = obter(s, aid)
        novo = {**reg.perfil, **{k: v for k, v in body.model_dump().items() if v is not None}}
        try:
            validar(atleta_de_json(novo), hoje_utc(), cfg)
        except PerfilInvalido as e:
            raise HTTPException(422, str(e))
        if body.ftp_modo is not None and body.ftp_modo not in ("automatico", "manual"):
            raise HTTPException(422, "ftp_modo: automatico ou manual")
        reg.perfil = novo
        replanear(reg, s)
        s.commit()
        return {"ok": True}

    class NovaProva(BaseModel):
        nome: str
        prioridade: str
        data: date | None = None
        duracao_h: float | None = None
        etapas: list[dict[str, Any]] = []

    @app.post("/atletas/{aid}/provas", status_code=201)
    def nova_prova(aid: int, body: NovaProva, s: Session = Depends(bd)) -> dict[str, Any]:
        reg = obter(s, aid)
        p = body.model_dump(mode="json")
        if p["etapas"]:
            p["etapas"] = sorted(p["etapas"], key=lambda e: e["data"])
            p["data"] = p["etapas"][0]["data"]
        if not p.get("data"):
            raise HTTPException(422, "a prova precisa de data (ou de etapas)")
        novo = {**reg.perfil, "provas": reg.perfil.get("provas", []) + [p]}
        try:
            validar(atleta_de_json(novo), hoje_utc(), cfg)
        except PerfilInvalido as e:
            raise HTTPException(422, str(e))
        reg.perfil = novo
        replanear(reg, s)
        s.commit()
        return {"provas": novo["provas"]}

    class NovoFTP(BaseModel):
        valor: float
        data: date | None = None
        confirmar: bool = False      # a app pede confirmação quando está longe do eFTP

    @app.put("/atletas/{aid}/ftp")
    def ftp_manual(aid: int, body: NovoFTP, s: Session = Depends(bd)) -> dict[str, Any]:
        reg = obter(s, aid)
        atleta = atleta_de_json(reg.perfil)
        d = body.data or hoje_utc()
        try:
            novo, avisos = definir_ftp_manual(atleta, body.valor, d, cfg, eftp=eftp(s, aid, atleta, d))
        except FTPInvalido as e:
            raise HTTPException(422, str(e))
        if avisos and not body.confirmar:
            return {"guardado": False, "avisos": list(avisos)}
        reg.perfil = {**atleta_para_json(novo), "_plano": reg.perfil.get("_plano", {})}
        s.commit()
        return {"guardado": True, "avisos": list(avisos), "ftp": body.valor, "desde": d.isoformat()}

    # ------------------------------------------------------------ plano e semana

    @app.get("/atletas/{aid}/plano")
    def plano(aid: int, s: Session = Depends(bd)) -> dict[str, Any]:
        reg = obter(s, aid)
        p = plano_de(reg, s)
        atleta = completar(atleta_de_json(reg.perfil), hoje_utc(), cfg)
        return {"inicio": p.inicio.isoformat(), "fim": p.fim.isoformat(), "nivel_regras": p.nivel_regras,
                "registo": list(p.registo),
                "semanas": [{"numero": x.numero, "inicio": x.inicio.isoformat(), "fase": x.fase,
                             "carga_alvo": round(x.carga_alvo), "carga_planeada": round(x.carga_planeada),
                             "condicao_fim": round(x.condicao_fim, 1), "notas": list(x.notas),
                             "verificar_prontidao": x.verificar_prontidao,
                             "treinos": [tp_json(t, atleta) for t in x.treinos]} for x in p.semanas]}

    # ------------------------------------------------------------ manhã (bem-estar) e hoje (decisão)

    class Manha(BaseModel):
        data: date | None = None
        sono_h: float | None = None
        rmssd: float | None = None
        fonte_vfc: str = "manual"
        fc_repouso: float | None = None
        cansaco: int | None = Field(None, ge=1, le=5)
        dores: int | None = Field(None, ge=1, le=5)
        stress: int | None = Field(None, ge=1, le=5)
        humor: int | None = Field(None, ge=1, le=5)
        doenca: bool = False
        febre: bool = False
        melhorou: bool = False
        alarmes: list[str] = []

    @app.post("/atletas/{aid}/manha", status_code=201)
    def manha(aid: int, body: Manha, s: Session = Depends(bd)) -> dict[str, Any]:
        obter(s, aid)
        d = body.data or hoje_utc()
        s.execute(delete(BemEstarDB).where(BemEstarDB.atleta_id == aid, BemEstarDB.data == d))
        s.add(BemEstarDB(atleta_id=aid, data=d, dados=body.model_dump(mode="json", exclude={"data"})))
        s.commit()
        return {"ok": True, "alarme": bool(set(body.alarmes) & set(cfg.motor.alarmes))}

    def decidir_dia(s: Session, aid: int, d: date) -> dict[str, Any]:
        reg = obter(s, aid)
        atleta = completar(atleta_de_json(reg.perfil), d, cfg)
        p = plano_de(reg, s)
        agenda = {t.data: t for t in p.treinos()}
        seg = d - timedelta(days=d.weekday())
        feitos = {a.data: Feito(a.data, a.carga or 0.0, a.resumo.get("intensidade"))
                  for a in atividades(s, aid) if seg <= a.data < d}
        semana = [t for t in agenda.values() if seg <= t.data < seg + timedelta(days=7)]
        reorg = reorganizar_semana(semana, feitos, d, lib, cfg)
        tp = {t.data: t for t in reorg.treinos}.get(d)

        bem = {b.data: b.dados for b in s.scalars(select(BemEstarDB).where(BemEstarDB.atleta_id == aid,
                                                                           BemEstarDB.data <= d))}
        meds = [MedicaoVFC(x, v.get("fonte_vfc", "manual"), "rmssd", v["rmssd"]) for x, v in bem.items() if v.get("rmssd")]
        lb_vfc = vfc(meds, d, d, cfg.recuperacao)[0] if meds else None
        fcr = {x: v["fc_repouso"] for x, v in bem.items() if v.get("fc_repouso")}
        est_fcr = fc_repouso(fcr, d, d, cfg.recuperacao)[0] if fcr else None
        v = bem.get(d)
        q = None
        if v is not None:
            q = Questionario(v.get("cansaco"), v.get("dores"), v.get("stress"), v.get("humor"), v.get("doenca", False),
                             v.get("febre", False), v.get("melhorou", False), frozenset(v.get("alarmes", [])))
        # doença ativa: o último dia com "doença" sem "melhorou" depois
        doente_desde = None
        for x in sorted(bem):
            if bem[x].get("doenca"):
                doente_desde = doente_desde or x
            elif bem[x].get("melhorou"):
                doente_desde = None
        ctl, atl, cond_dia = forma_ate(s, aid, d)
        pct = ((ctl - atl) / ctl * 100) if ctl >= cfg.carga_forma.condicao_minima_para_pct else None
        sinais = SinaisDia(d, lb_vfc, est_fcr, v.get("sono_h") if v else None, q, pct, frescura=ctl - atl, condicao=ctl)
        pront, _ = avaliar(sinais, EstadoAtleta(doente_desde if d != doente_desde else None), cfg)
        semana_verif = {sx.inicio + timedelta(days=k) for sx in p.semanas if sx.verificar_prontidao for k in range(7)}
        dec = decidir(tp, pront, lib, cfg, verificar_prontidao=d in semana_verif)
        rampa = cfg.plano.rampa_condicao_semana[nivel_regras(atleta, d, cfg)]
        dec = guarda_rampa(dec, ctl, cond_dia.get(d - timedelta(days=7), 0.0), rampa, lib, cfg)
        registo = dec.registo()
        s.execute(delete(DecisaoDB).where(DecisaoDB.atleta_id == aid, DecisaoDB.data == d))
        s.add(DecisaoDB(atleta_id=aid, data=d, registo=registo))
        s.commit()
        return {"data": d.isoformat(), "estado": dec.estado, "explicacao": explicar(registo),
                "procurar_medico": dec.procurar_medico, "sinais": registo["sinais"],
                "dados_em_falta": registo["dados_em_falta"], "regras": registo["regras"],
                "treino_original": tp_json(dec.treino_original, atleta), "treino": tp_json(dec.treino_final, atleta),
                "frescura_pct": round(pct, 1) if pct is not None else None, "condicao": round(ctl, 1)}

    @app.get("/atletas/{aid}/hoje")
    def hoje(aid: int, data: date | None = Query(None), s: Session = Depends(bd)) -> dict[str, Any]:
        return decidir_dia(s, aid, data or hoje_utc())

    class Escolha(BaseModel):
        ambiente: str
        data: date | None = None

    @app.post("/atletas/{aid}/hoje/escolha")
    def escolha(aid: int, body: Escolha, s: Session = Depends(bd)) -> dict[str, Any]:
        d = body.data or hoje_utc()
        r = s.scalars(select(DecisaoDB).where(DecisaoDB.atleta_id == aid, DecisaoDB.data == d)).first()
        if r is None:
            raise HTTPException(409, "ainda não há decisão para este dia (pede /hoje primeiro)")
        opcoes = (r.registo.get("treino_final") or {}).get("opcoes", {})
        if body.ambiente not in opcoes:
            raise HTTPException(422, f"não há versão {body.ambiente} hoje")
        r.escolha = body.ambiente
        s.commit()
        return {"escolhido": body.ambiente, "treino": opcoes[body.ambiente]}

    # ------------------------------------------------------------ atividades (FIT)

    @app.post("/atletas/{aid}/atividades", status_code=201)
    async def upload(aid: int, ficheiro: UploadFile = File(...), rpe: float | None = Query(None),
                     s: Session = Depends(bd)) -> dict[str, Any]:
        reg = obter(s, aid)
        dados = await ficheiro.read()
        try:
            serie = ler_bytes(dados, cfg.qualidade.pausa_minima_s)
        except ErroFIT as e:
            raise HTTPException(422, str(e))
        atleta = completar(atleta_de_json(reg.perfil), serie.inicio.date(), cfg)
        d = serie.inicio.date()
        fis = Fisiologia(atleta.sexo, ftp=ftp_em_vigor(atleta, d),
                         fc_limiar=atleta.fc_limiar.valor if atleta.fc_limiar else None,
                         fc_max=atleta.fc_max.valor if atleta.fc_max else None,
                         fc_repouso=atleta.fc_repouso.valor if atleta.fc_repouso else None,
                         estimados=frozenset(k for k in ("ftp", "fc_limiar", "fc_max", "fc_repouso")
                                             if getattr(atleta, k) is not None and getattr(atleta, k).estimado))
        r = analisar(serie, fis, cfg, rpe=rpe)
        limpa, rel = limpar(serie, cfg.qualidade, fis.fc_max)
        ok = rel.serve_para_modelos(cfg.qualidade)
        esf = esforcos_da_atividade(limpa.potencia, "x", d, ok, cfg) if limpa.tem_potencia else []
        nova = AtividadeRef("novo", serie.inicio, r.duracao_s, "dispositivo", limpa.tem_potencia, limpa.tem_fc,
                            rel.indice, datetime.now(timezone.utc))
        existentes = [AtividadeRef(str(a.id), a.inicio if a.inicio.tzinfo else a.inicio.replace(tzinfo=timezone.utc),
                                   a.duracao_s, a.origem, bool(a.resumo.get("tem_potencia")), bool(a.resumo.get("tem_fc")),
                                   float(a.resumo.get("qualidade", 0)), a.inicio)
                      for a in atividades(s, aid)]
        dup = procurar_duplicado(nova, existentes, cfg.dados)
        resumo = {"duracao_s": r.duracao_s, "tempo_movimento_s": r.tempo_movimento_s, "potencia_media": r.potencia_media,
                  "potencia_ponderada": r.potencia_ponderada, "intensidade": r.intensidade, "fc_media": r.fc_media,
                  "fonte_carga": r.fonte_carga, "carga_estimada": r.carga_estimada, "qualidade": rel.indice,
                  "qualidade_ok": ok, "motivos_qualidade": list(rel.motivos), "tempo_zonas_potencia": r.tempo_zonas_potencia,
                  "tempo_zonas_fc": r.tempo_zonas_fc, "esforcos": [[e.duracao_s, e.potencia] for e in esf],
                  "tem_potencia": limpa.tem_potencia, "tem_fc": limpa.tem_fc, "avisos": list(r.avisos),
                  "ftp_usado": fis.ftp, "versao_config": r.versao_config}
        reg_a = AtividadeDB(atleta_id=aid, inicio=serie.inicio, data=d, duracao_s=r.duracao_s, origem="ficheiro",
                            carga=r.carga, resumo=resumo, ficheiro=dados, principal=dup is None)
        s.add(reg_a)
        s.commit()
        return {"id": reg_a.id, "duplicado_de": int(dup.id) if dup else None, "carga": r.carga, **resumo}

    # ------------------------------------------------------------ exportação de treinos e RGPD

    @app.get("/atletas/{aid}/treinos/{dia}/exportar", response_class=PlainTextResponse)
    def exportar_treino(aid: int, dia: date, formato: str = Query("zwo", pattern="^(zwo|erg|mrc)$"),
                        ambiente: str = Query("indoor"), s: Session = Depends(bd)) -> PlainTextResponse:
        reg = obter(s, aid)
        tp = {t.data: t for t in plano_de(reg, s).treinos()}.get(dia)
        if tp is None or tp.papel == "prova":
            raise HTTPException(404, "não há treino para exportar neste dia")
        t = tp.opcoes().get(ambiente) or tp.treino
        atleta = atleta_de_json(reg.perfil)
        if formato == "erg":
            ftp = ftp_em_vigor(atleta, dia)
            if not ftp:
                raise HTTPException(422, "o ERG precisa do FTP")
            texto = para_erg(t, ftp)
        else:
            texto = para_zwo(t) if formato == "zwo" else para_mrc(t)
        return PlainTextResponse(texto, headers={"Content-Disposition": f'attachment; filename="{nome_ficheiro(t, formato)}"'})

    @app.get("/atletas/{aid}/exportar")
    def exportar_dados(aid: int, s: Session = Depends(bd)) -> dict[str, Any]:
        """Todos os dados do atleta (RGPD, spec 9)."""
        reg = obter(s, aid)
        return {
            "perfil": reg.perfil, "criado": reg.criado.isoformat(),
            "consentimentos": [{"tipo": c.tipo, "versao": c.versao_texto, "quando": c.quando.isoformat()}
                               for c in s.scalars(select(ConsentimentoDB).where(ConsentimentoDB.atleta_id == aid))],
            "atividades": [{"id": a.id, "inicio": a.inicio.isoformat(), "carga": a.carga, "resumo": a.resumo}
                           for a in s.scalars(select(AtividadeDB).where(AtividadeDB.atleta_id == aid))],
            "bem_estar": [{"data": b.data.isoformat(), **b.dados}
                          for b in s.scalars(select(BemEstarDB).where(BemEstarDB.atleta_id == aid))],
            "decisoes": [{"data": x.data.isoformat(), "registo": x.registo, "escolha": x.escolha}
                         for x in s.scalars(select(DecisaoDB).where(DecisaoDB.atleta_id == aid))],
        }

    @app.delete("/atletas/{aid}", status_code=204)
    def apagar(aid: int, s: Session = Depends(bd)) -> None:
        """Apaga TODOS os dados do atleta, incluindo ficheiros FIT e auditoria (RGPD; D-018)."""
        obter(s, aid)
        for m in (DecisaoDB, BemEstarDB, AtividadeDB, ConsentimentoDB):
            s.execute(delete(m).where(m.atleta_id == aid))
        s.execute(delete(AtletaDB).where(AtletaDB.id == aid))
        s.commit()

    @app.get("/saude")
    def saude() -> dict[str, str]:
        return {"estado": "ok", "versao_config": cfg.versao, "versao_motor": cfg.motor.versao}

    return app


app = criar_app(__import__("os").environ.get("WATTWISE_BD", "sqlite:///./wattwise_dev.db"))
