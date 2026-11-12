from typing import Optional

from pydantic import BaseModel, ConfigDict


class AssetBase(BaseModel):
    asset_tag: str
    asset_type: str
    brand: str
    model: str
    serial_number: Optional[str] = None
    status: str = "AVAILABLE"
    location: Optional[str] = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(AssetBase):
    pass


class AssetRead(AssetBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class AssetResponse(BaseModel):
    message: str
    asset: AssetRead
