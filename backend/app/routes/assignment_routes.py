from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.asset import Asset
from app.models.assignment import Assignment, utcnow
from app.models.employee import Employee
from app.schemas.assignment_schema import AssignmentRead, AssignmentResponse, AssignRequest

router = APIRouter(tags=["assignments"])


def _get_asset_or_404(db: Session, asset_id: int) -> Asset:
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


def _get_employee_or_404(db: Session, employee_id: int) -> Employee:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.post("/assets/{asset_id}/assign", response_model=AssignmentResponse, status_code=201)
def assign_asset(asset_id: int, request: AssignRequest, db: Session = Depends(get_db)):
    """Check an asset out to an employee. Only AVAILABLE assets can be assigned."""
    asset = _get_asset_or_404(db, asset_id)
    employee = _get_employee_or_404(db, request.employee_id)

    if asset.current_assignment is not None:
        raise HTTPException(status_code=409, detail="Asset is already assigned; return it first")
    if asset.status != "AVAILABLE":
        raise HTTPException(
            status_code=409,
            detail=f"Only available assets can be assigned (this one is {asset.status})",
        )

    assignment = Assignment(asset=asset, employee=employee, notes=request.notes)
    asset.status = "ASSIGNED"
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return {
        "message": f"{asset.asset_tag} assigned to {employee.first_name} {employee.last_name}",
        "assignment": assignment,
    }


@router.post("/assets/{asset_id}/return", response_model=AssignmentResponse)
def return_asset(asset_id: int, db: Session = Depends(get_db)):
    """Check an asset back in. Closes the open assignment and frees the asset."""
    asset = _get_asset_or_404(db, asset_id)
    assignment = asset.current_assignment

    if assignment is None:
        raise HTTPException(status_code=409, detail="Asset is not currently assigned")

    assignment.returned_at = utcnow()
    asset.status = "AVAILABLE"
    db.commit()
    db.refresh(assignment)

    return {"message": f"{asset.asset_tag} returned", "assignment": assignment}


@router.get("/assets/{asset_id}/assignments", response_model=list[AssignmentRead])
def get_asset_history(asset_id: int, db: Session = Depends(get_db)):
    """Everyone who has held this asset, newest first."""
    return _get_asset_or_404(db, asset_id).assignments


@router.get("/employees/{employee_id}/assignments", response_model=list[AssignmentRead])
def get_employee_history(employee_id: int, db: Session = Depends(get_db)):
    """Every asset this employee has held, newest first."""
    return _get_employee_or_404(db, employee_id).assignments


@router.get("/assignments", response_model=list[AssignmentRead])
def get_assignments(active: Optional[bool] = None, db: Session = Depends(get_db)):
    """All assignments, newest first. Use ?active=true for open ones only."""
    query = db.query(Assignment)
    if active is True:
        query = query.filter(Assignment.returned_at.is_(None))
    elif active is False:
        query = query.filter(Assignment.returned_at.is_not(None))
    return query.order_by(Assignment.assigned_at.desc(), Assignment.id.desc()).all()
