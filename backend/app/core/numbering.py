import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, select
from app.core.clock import today as get_today
from app.core.db import Base


class DocumentSequence(Base):
    __tablename__ = "document_sequences"

    prefix = Column(String(10), primary_key=True)
    year = Column(Integer, primary_key=True)
    last_number = Column(Integer, nullable=False, default=0)

    @property
    def kind(self) -> str:
        return self.prefix

    @kind.setter
    def kind(self, val: str) -> None:
        self.prefix = val

    @property
    def last_seq(self) -> int:
        return self.last_number

    @last_seq.setter
    def last_seq(self, val: int) -> None:
        self.last_number = val


def next_number(
    session,
    prefix_or_kind: str,
    on: Optional[datetime.date] = None,
    on_date: Optional[datetime.date] = None,
) -> str:
    """Generate next document number in format PREFIX-YYYY-NNNNNN."""
    d = on or on_date or get_today()
    year = d.year
    prefix = prefix_or_kind.upper()

    row = session.execute(
        select(DocumentSequence).where(
            DocumentSequence.prefix == prefix,
            DocumentSequence.year == year,
        )
    ).scalar_one_or_none()

    if row is None:
        row = DocumentSequence(prefix=prefix, year=year, last_number=1)
        session.add(row)
        session.flush()
        seq = 1
    else:
        row.last_number += 1
        session.flush()
        seq = row.last_number

    return f"{prefix}-{year}-{seq:06d}"
