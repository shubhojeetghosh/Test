from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.admin_portal.models.image import Image
from app.admin_portal.schemas.image import ImageCreate, ImageUpdate


router = APIRouter(
    prefix="/admin/images",
    tags=["Admin Images"],
)


@router.get("")
def get_images(
    db: Session = Depends(get_db),
):
    images = db.scalars(
        select(Image).order_by(Image.id)
    ).all()

    return [
        {
            "id": image.id,
            "file_name": image.file_name,
            "file_url": image.file_url,
            "created_at": image.created_at,
        }
        for image in images
    ]


@router.get("/{image_id}")
def get_image(
    image_id: int,
    db: Session = Depends(get_db),
):
    image = db.scalar(
        select(Image).where(Image.id == image_id)
    )

    if image is None:
        raise HTTPException(
            status_code=404,
            detail="Image not found",
        )

    return {
        "id": image.id,
        "file_name": image.file_name,
        "file_url": image.file_url,
        "created_at": image.created_at,
    }


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def create_image(
    image_data: ImageCreate,
    db: Session = Depends(get_db),
):
    image = Image(
        file_name=image_data.file_name,
        file_url=image_data.file_url,
    )

    db.add(image)
    db.commit()
    db.refresh(image)

    return {
        "message": "Image created successfully",
        "image": {
            "id": image.id,
            "file_name": image.file_name,
            "file_url": image.file_url,
            "created_at": image.created_at,
        },
    }


@router.put("/{image_id}")
def update_image(
    image_id: int,
    image_data: ImageUpdate,
    db: Session = Depends(get_db),
):
    image = db.scalar(
        select(Image).where(Image.id == image_id)
    )

    if image is None:
        raise HTTPException(
            status_code=404,
            detail="Image not found",
        )

    update_data = image_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(image, field, value)

    db.commit()
    db.refresh(image)

    return {
        "message": "Image updated successfully",
        "image": {
            "id": image.id,
            "file_name": image.file_name,
            "file_url": image.file_url,
            "created_at": image.created_at,
        },
    }


@router.delete("/{image_id}")
def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
):
    image = db.scalar(
        select(Image).where(Image.id == image_id)
    )

    if image is None:
        raise HTTPException(
            status_code=404,
            detail="Image not found",
        )

    db.delete(image)
    db.commit()

    return {
        "message": "Image deleted successfully",
        "image_id": image_id,
    }
