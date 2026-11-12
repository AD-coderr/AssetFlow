from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)

    first_name = Column(String, nullable=False)

    last_name = Column(String, nullable=False)

    email = Column(String, unique=True, nullable=False)

    department = Column(String)

    position = Column(String)

    assignments = relationship(
        "Assignment",
        back_populates="employee",
        cascade="all, delete-orphan",
        order_by="Assignment.assigned_at.desc()",
        lazy="selectin",
    )

    @property
    def assets(self):
        """Assets this employee currently holds."""
        return [a.asset for a in self.assignments if a.returned_at is None]
