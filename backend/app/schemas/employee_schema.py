from typing import Optional

from pydantic import BaseModel, ConfigDict


class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    department: Optional[str] = None
    position: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(EmployeeBase):
    pass


class EmployeeRead(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class EmployeeResponse(BaseModel):
    message: str
    employee: EmployeeRead
