from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    """Public view of a user. Never exposes password_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: str
