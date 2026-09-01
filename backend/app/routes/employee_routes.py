from fastapi import APIRouter
from app.schemas.employee_schema import EmployeeCreate
from app.database.database import SessionLocal
from app.models.employee import Employee

router = APIRouter()


@router.get("/employees")
def get_employees():
    db = SessionLocal()

    employees = db.query(Employee).all()

    db.close()

    return employees


@router.post("/employees")
def create_employee(employee: EmployeeCreate):
    db = SessionLocal()

    new_employee = Employee(
        first_name=employee.first_name,
        last_name=employee.last_name,
        email=employee.email,
        department=employee.department,
        position=employee.position
    )

    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)

    db.close()

    return {
        "message": "Employee created successfully",
        "employee": new_employee
    }