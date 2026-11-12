"""Small nested views shared between asset, employee and assignment schemas."""

from pydantic import BaseModel, ConfigDict


class AssetBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_tag: str
    asset_type: str
    brand: str
    model: str


class EmployeeBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: str
