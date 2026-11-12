from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.asset import Asset
from app.schemas.asset_schema import AssetCreate, AssetRead, AssetResponse, AssetUpdate

router = APIRouter(tags=["assets"])

CONFLICT_DETAIL = "An asset with this asset_tag or serial_number already exists"


def _get_asset_or_404(db: Session, asset_id: int) -> Asset:
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


def _commit_or_409(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=CONFLICT_DETAIL)


@router.get("/assets", response_model=list[AssetRead])
def get_assets(db: Session = Depends(get_db)):
    return db.query(Asset).all()


@router.get("/assets/{asset_id}", response_model=AssetRead)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    return _get_asset_or_404(db, asset_id)


@router.post("/assets", response_model=AssetResponse, status_code=201)
def create_asset(asset: AssetCreate, db: Session = Depends(get_db)):
    new_asset = Asset(**asset.model_dump())
    db.add(new_asset)
    _commit_or_409(db)
    db.refresh(new_asset)

    return {"message": "Asset created successfully", "asset": new_asset}


@router.put("/assets/{asset_id}", response_model=AssetResponse)
def update_asset(asset_id: int, updated_asset: AssetUpdate, db: Session = Depends(get_db)):
    asset = _get_asset_or_404(db, asset_id)

    for field, value in updated_asset.model_dump().items():
        setattr(asset, field, value)

    _commit_or_409(db)
    db.refresh(asset)

    return {"message": "Asset updated successfully", "asset": asset}


@router.delete("/assets/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = _get_asset_or_404(db, asset_id)

    db.delete(asset)
    db.commit()

    return {"message": "Asset deleted successfully"}
