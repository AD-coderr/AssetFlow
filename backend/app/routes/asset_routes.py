from fastapi import APIRouter, HTTPException
from app.schemas.asset_schema import AssetCreate, AssetUpdate
from app.database.database import SessionLocal
from app.models.asset import Asset

router = APIRouter()


@router.get("/assets")
def get_assets():
    db = SessionLocal()

    assets = db.query(Asset).all()

    db.close()

    return assets


@router.get("/assets/{asset_id}")
def get_asset(asset_id: int):
    db = SessionLocal()

    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    db.close()

    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    return asset


@router.put("/assets/{asset_id}")
def update_asset(asset_id: int, updated_asset: AssetUpdate):
    db = SessionLocal()

    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if asset is None:
        db.close()
        raise HTTPException(status_code=404, detail="Asset not found")

    asset.asset_tag = updated_asset.asset_tag
    asset.asset_type = updated_asset.asset_type
    asset.brand = updated_asset.brand
    asset.model = updated_asset.model

    db.commit()
    db.refresh(asset)

    db.close()

    return {
        "message": "Asset updated successfully",
        "asset": asset
    }
from fastapi import APIRouter, HTTPException
from app.schemas.asset_schema import AssetCreate, AssetUpdate
from app.database.database import SessionLocal
from app.models.asset import Asset

router = APIRouter()


@router.get("/assets")
def get_assets():
    db = SessionLocal()

    assets = db.query(Asset).all()

    db.close()

    return assets


@router.get("/assets/{asset_id}")
def get_asset(asset_id: int):
    db = SessionLocal()

    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    db.close()

    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    return asset


@router.put("/assets/{asset_id}")
def update_asset(asset_id: int, updated_asset: AssetUpdate):
    db = SessionLocal()

    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if asset is None:
        db.close()
        raise HTTPException(status_code=404, detail="Asset not found")

    asset.asset_tag = updated_asset.asset_tag
    asset.asset_type = updated_asset.asset_type
    asset.brand = updated_asset.brand
    asset.model = updated_asset.model

    db.commit()
    db.refresh(asset)

    db.close()

    return {
        "message": "Asset updated successfully",
        "asset": asset
    }


@router.delete("/assets/{asset_id}")
def delete_asset(asset_id: int):
    db = SessionLocal()

    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if asset is None:
        db.close()
        raise HTTPException(status_code=404, detail="Asset not found")

    db.delete(asset)
    db.commit()

    db.close()

    return {
        "message": "Asset deleted successfully"
    }

@router.post("/assets")
def create_asset(asset: AssetCreate):
    db = SessionLocal()

    new_asset = Asset(
        asset_tag=asset.asset_tag,
        asset_type=asset.asset_type,
        brand=asset.brand,
        model=asset.model
    )

    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)

    db.close()

    return {
        "message": "Asset created successfully",
        "asset": new_asset
    }