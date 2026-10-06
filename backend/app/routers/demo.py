from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import seed as service

router = APIRouter(tags=["demo"])


@router.post("/seed")
def seed(db: Session = Depends(get_db)):
    return service.seed(db)
