"""Base de dados (SQLAlchemy): SQLite nos testes, PostgreSQL na UE em produção (spec 9, 12)."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, LargeBinary, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


def agora() -> datetime:
    return datetime.now(timezone.utc)


class AtletaDB(Base):
    __tablename__ = "atletas"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    perfil: Mapped[dict] = mapped_column(JSON)
    criado: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class ConsentimentoDB(Base):
    """Consentimento explícito e separado para dados de saúde (spec 9)."""
    __tablename__ = "consentimentos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atletas.id", ondelete="CASCADE"))
    tipo: Mapped[str] = mapped_column(String(40))
    versao_texto: Mapped[str] = mapped_column(String(20))
    quando: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class AtividadeDB(Base):
    __tablename__ = "atividades"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atletas.id", ondelete="CASCADE"), index=True)
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    data: Mapped[date] = mapped_column(Date, index=True)
    duracao_s: Mapped[int] = mapped_column(Integer)
    origem: Mapped[str] = mapped_column(String(20))
    carga: Mapped[float | None] = mapped_column(Float, nullable=True)
    resumo: Mapped[dict] = mapped_column(JSON)
    ficheiro: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)   # FIT original, nunca alterado
    principal: Mapped[bool] = mapped_column(default=True)                        # deduplicação (D-030)


class BemEstarDB(Base):
    __tablename__ = "bem_estar"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atletas.id", ondelete="CASCADE"), index=True)
    data: Mapped[date] = mapped_column(Date, index=True)
    dados: Mapped[dict] = mapped_column(JSON)       # sono, VFC, FC repouso, questionário


class DecisaoDB(Base):
    """Registo de auditoria de todas as decisões do motor (spec 7.1, 7.6)."""
    __tablename__ = "decisoes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atletas.id", ondelete="CASCADE"), index=True)
    data: Mapped[date] = mapped_column(Date, index=True)
    registo: Mapped[dict] = mapped_column(JSON)
    escolha: Mapped[str | None] = mapped_column(String(10), nullable=True)   # indoor / outdoor (D-059)
    quando: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


def criar_sessoes(url: str = "sqlite:///:memory:"):  # type: ignore[no-untyped-def]
    kw = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}
    if url == "sqlite:///:memory:":
        from sqlalchemy.pool import StaticPool
        kw["poolclass"] = StaticPool
    motor = create_engine(url, **kw)
    if url.startswith("sqlite"):
        from sqlalchemy import event

        @event.listens_for(motor, "connect")
        def _fk(dbapi, _):  # type: ignore[no-untyped-def]
            dbapi.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(motor)
    return sessionmaker(motor, expire_on_commit=False)
