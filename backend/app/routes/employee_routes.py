from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.employee import Employee
from app.schemas.employee_schema import (
    EmployeeCreate,
    EmployeeRead,
    EmployeeResponse,
    EmployeeUpdate,
)

router = APIRouter(tags=["employees"])


def _get_employee_or_404(db: Session, employee_id: int) -> Employee:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


def _commit_or_409(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An employee with this email already exists")


@router.get("/employees", response_model=list[EmployeeRead])
def get_employees(db: Session = Depends(get_db)):
    return db.query(Employee).all()


@router.get("/employees/{employee_id}", response_model=EmployeeRead)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    return _get_employee_or_404(db, employee_id)


@router.post("/employees", response_model=EmployeeResponse, status_code=201)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    new_employee = Employee(**employee.model_dump())
    db.add(new_employee)
    _commit_or_409(db)
    db.refresh(new_employee)

    return {"message": "Employee created successfully", "employee": new_employee}


@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: int, updated: EmployeeUpdate, db: Session = Depends(get_db)):
    employee = _get_employee_or_404(db, employee_id)

    for field, value in updated.model_dump().items():
        setattr(employee, field, value)

    _commit_or_409(db)
    db.refresh(employee)

    return {"message": "Employee updated successfully", "employee": employee}


@router.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = _get_employee_or_404(db, employee_id)

    db.delete(employee)
    db.commit()

    return {"message": "Employee deleted successfully"}
