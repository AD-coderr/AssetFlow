from sqlalchemy import Column, Integer, String
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