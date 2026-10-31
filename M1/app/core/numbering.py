from datetime import date
from typing import Literal
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import Session
from app.core.clock import today
from app.core.db import Base

class NumberingCounter(Base):
    __tablename__ = "numbering_counters"

    kind = Column(String(10), primary_key=True)   # "SUB" or "INV"
    year = Column(Integer, primary_key=True)
    current_val = Column(Integer, nullable=False, default=0)

def next_number(session: Session, kind: Literal["SUB", "INV"], on_date: date | None = None) -> str:
    """
    Generates the next sequential document number atomically (e.g. SUB-2026-000001, INV-2026-000001).
    """
    year = (on_date or today()).year
    counter = session.scalar(
        select(NumberingCounter).where(
            NumberingCounter.kind == kind,
            NumberingCounter.year == year
        )
    )

    if not counter:
        counter = NumberingCounter(kind=kind, year=year, current_val=1)
        session.add(counter)
        session.flush()
        seq = 1
    else:
        counter.current_val += 1
        session.flush()
        seq = counter.current_val

    return f"{kind}-{year}-{seq:06d}"
