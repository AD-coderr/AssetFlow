from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database.database import BACKEND_DIR, engine, Base
from app.models.user import User
from app.models.asset import Asset
from app.models.employee import Employee

from app.routes.user_routes import router as user_router
from app.routes.asset_routes import router as asset_router
from app.routes.employee_routes import router as employee_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AssetFlow")

app.include_router(user_router)
app.include_router(asset_router)
app.include_router(employee_router)


FRONTEND_DIR = BACKEND_DIR.parent / "frontend"


@app.get("/")
def root():
    return {"message": "AssetFlow API Running"}


# Web UI: frontend/ served at /ui (same origin as the API, so no CORS needed).
if FRONTEND_DIR.is_dir():
    app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="ui")