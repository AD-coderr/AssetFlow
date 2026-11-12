from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.common import AssetBrief, EmployeeBrief


class AssignRequest(BaseModel):
    employee_id: int
    notes: Optional[str] = None


class AssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assigned_at: datetime
    returned_at: Optional[datetime] = None
    notes: Optional[str] = None
    is_active: bool
    asset: AssetBrief
    employee: EmployeeBrief


class AssignmentResponse(BaseModel):
    message: str
    assignment: AssignmentRead
