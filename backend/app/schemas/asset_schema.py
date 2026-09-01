from pydantic import BaseModel


class AssetCreate(BaseModel):
    asset_tag: str
    asset_type: str
    brand: str
    model: str


class AssetUpdate(BaseModel):
    asset_tag: str
    asset_type: str
    brand: str
    model: str