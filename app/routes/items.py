from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.item import Item, RiskLevel, ItemStatus
from app.models.user import User
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from app.routes.auth import get_current_user
from typing import List
from uuid import UUID
import cloudinary
import cloudinary.uploader
from app.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)

router = APIRouter(prefix="/items", tags=["items"])

@router.post("/", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_item = Item(
        title=item.title,
        description=item.description,
        category=item.category,
        risk_level=item.risk_level,
        status=ItemStatus.available,
        owner_id=current_user.id,
        max_borrow_days=item.max_borrow_days,
        image_url=item.image_url,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@router.get("/", response_model=List[ItemResponse])
def get_items(db: Session = Depends(get_db)):
    return db.query(Item).filter(Item.status == ItemStatus.available).all()

@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: UUID, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/{item_id}", response_model=ItemResponse)
def update_item(item_id: UUID, updates: ItemUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own items")

    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item

@router.delete("/{item_id}")
def delete_item(item_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own items")

    db.delete(item)
    db.commit()
    return {"message": "Item deleted successfully"}

@router.post("/upload-image")
def upload_item_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="unilend_items",
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Image upload failed")

    return {"image_url": result["secure_url"]}