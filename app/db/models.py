from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    trade_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cnpj_root: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    estimated_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    signals: Mapped[list["Signal"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    signal_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    weight_override: Mapped[float | None] = mapped_column(Float, nullable=True)

    company: Mapped[Company] = relationship(back_populates="signals")


class LeadSnapshot(Base):
    __tablename__ = "lead_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    conversion_probability: Mapped[str] = mapped_column(String(20), nullable=False)
    lead_tier: Mapped[str] = mapped_column(String(20), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    hypothesis_of_pain: Mapped[str] = mapped_column(Text, nullable=False)
    best_approach: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_product: Mapped[str] = mapped_column(String(120), nullable=False)
    timing: Mapped[str] = mapped_column(String(120), nullable=False)
    risk: Mapped[str] = mapped_column(String(120), nullable=False)
    score_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
