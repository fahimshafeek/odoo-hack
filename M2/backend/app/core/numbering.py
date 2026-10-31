import datetime
from typing import Literal, Optional
from sqlalchemy import Column, String, Integer, select
from app.core.database import Base
from app.core.clock import today as get_today


class DocumentSequence(Base):
    __tablename__ = "document_sequences"

    kind = Column(String(10), primary_key=True)
    year = Column(Integer, primary_key=True)
    last_seq = Column(Integer, nullable=False, default=0)


def next_number(session, kind: Literal["SUB", "INV"], on: Optional[datetime.date] = None) -> str:
    """Generate next document number in format KIND-YYYY-NNNNNN."""
    d = on or get_today()
    year = d.year

    row = session.execute(
        select(DocumentSequence).where(
            DocumentSequence.kind == kind,
            DocumentSequence.year == year,
        )
    ).scalar_one_or_none()

    if row is None:
        row = DocumentSequence(kind=kind, year=year, last_seq=1)
        session.add(row)
        session.flush()
        seq = 1
    else:
        row.last_seq += 1
        session.flush()
        seq = row.last_seq

    return f"{kind}-{year}-{seq:06d}"
