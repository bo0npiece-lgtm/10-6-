from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.services import users as service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=schemas.UserOut, status_code=201)
def create_user(data: schemas.UserCreate, db: Session = Depends(get_db)):
    return service.create_user(db, data)


@router.get("", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db)):
    return service.list_users(db)


@router.get("/{user_id}/applications", response_model=list[schemas.MyApplicationOut])
def my_applications(user_id: int, db: Session = Depends(get_db)):
    return service.my_applications(db, user_id)
