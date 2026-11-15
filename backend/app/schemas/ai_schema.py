from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.asset_schema import AssetRead

AssetStatus = Literal["AVAILABLE", "ASSIGNED", "IN_REPAIR", "RETIRED"]

TEXT_FIELDS = ("asset_type", "brand", "model", "location", "assigned_to", "department", "text")


class AssetFilter(BaseModel):
    """The only thing the language model is allowed to produce.

    The model never writes SQL and never touches the database: it fills in
    this structure, the structure is validated here, and the API builds the
    query itself. Unknown keys are dropped, bad values are rejected.
    """

    model_config = ConfigDict(extra="ignore")

    status: Optional[AssetStatus] = None
    asset_type: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    location: Optional[str] = None
    # Name or email fragment of the employee currently holding the asset.
    assigned_to: Optional[str] = None
    # Department of the employee currently holding the asset.
    department: Optional[str] = None
    # Free-text fallback, matched against tag, type, brand, model, serial, location.
    text: Optional[str] = None

    @field_validator("status", mode="before")
    @classmethod
    def _normalise_status(cls, value):
        if isinstance(value, str):
            value = value.strip().upper().replace(" ", "_").replace("-", "_")
            return value or None
        return value

    @field_validator(*TEXT_FIELDS, mode="before")
    @classmethod
    def _clean_text(cls, value):
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("must be a string")
        value = value.strip()
        if len(value) > 100:
            raise ValueError("too long")
        return value or None

    def is_empty(self) -> bool:
        return not self.model_dump(exclude_none=True)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=300)

    @field_validator("question")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question must not be blank")
        return value


class AskResponse(BaseModel):
    question: str
    filters: AssetFilter
    summary: str
    assets: list[AssetRead]


class AiStatus(BaseModel):
    enabled: bool
