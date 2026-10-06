from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import StudyStatus
from app.services import studies as service

router = APIRouter(prefix="/studies", tags=["studies"])


@router.post("", response_model=schemas.StudyOut, status_code=201)
def create_study(data: schemas.StudyCreate, db: Session = Depends(get_db)):
    return service.create_study(db, data)


@router.get("", response_model=list[schemas.StudyOut])
def list_studies(status: StudyStatus | None = None, db: Session = Depends(get_db)):
    return service.list_studies(db, status)


@router.get("/{study_id}", response_model=schemas.StudyDetail)
def get_study(study_id: int, db: Session = Depends(get_db)):
    return service.study_detail(db, study_id)


@router.patch("/{study_id}/capacity", response_model=schemas.StudyOut)
def update_capacity(study_id: int, data: schemas.CapacityUpdate, db: Session = Depends(get_db)):
    return service.update_capacity(db, study_id, data)


@router.post("/{study_id}/transfer-owner", response_model=schemas.StudyDetail)
def transfer_owner(study_id: int, data: schemas.TransferOwner, db: Session = Depends(get_db)):
    return service.transfer_owner(db, study_id, data)
