from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Assignment(Base):
    """One check-out of an asset to an employee. Open while returned_at is NULL."""

    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)

    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)

    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)

    assigned_at = Column(DateTime, nullable=False, default=utcnow)

    returned_at = Column(DateTime, nullable=True)

    notes = Column(String)

    asset = relationship("Asset", back_populates="assignments")

    employee = relationship("Employee", back_populates="assignments")

    @property
    def is_active(self) -> bool:
        return self.returned_at is None
