from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)

    asset_tag = Column(String, unique=True, nullable=False)

    asset_type = Column(String, nullable=False)

    brand = Column(String, nullable=False)

    model = Column(String, nullable=False)

    serial_number = Column(String, unique=True)

    status = Column(String, default="AVAILABLE")

    location = Column(String)

    assignments = relationship(
        "Assignment",
        back_populates="asset",
        cascade="all, delete-orphan",
        order_by="Assignment.assigned_at.desc()",
        lazy="selectin",
    )

    @property
    def current_assignment(self):
        return next((a for a in self.assignments if a.returned_at is None), None)

    @property
    def assigned_to(self):
        """The employee currently holding this asset, if any."""
        current = self.current_assignment
        return current.employee if current else None
