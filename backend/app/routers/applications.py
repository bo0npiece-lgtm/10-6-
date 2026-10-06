from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import ApplicationStatus
from app.services import applications as service

router = APIRouter(tags=["applications"])


@router.post(
    "/studies/{study_id}/applications",
    response_model=schemas.ApplicationOut,
    status_code=201,
)
def apply(study_id: int, data: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    return service.apply(db, study_id, data)


@router.get("/studies/{study_id}/applications", response_model=list[schemas.ApplicationWithUser])
def list_applications(
    study_id: int,
    user_id: int = Query(description="요청자(방장) user_id"),
    status: ApplicationStatus | None = None,
    db: Session = Depends(get_db),
):
    return service.list_applications(db, study_id, user_id, status)


@router.delete("/applications/{application_id}", response_model=schemas.ApplicationOut)
def cancel_application(
    application_id: int,
    user_id: int = Query(description="요청자(신청자 본인) user_id"),
    db: Session = Depends(get_db),
):
    return service.cancel_application(db, application_id, user_id)


@router.post("/applications/{application_id}/approve", response_model=schemas.ApplicationOut)
def approve(application_id: int, data: schemas.RequesterBody, db: Session = Depends(get_db)):
    return service.approve(db, application_id, data.user_id)


@router.post("/applications/{application_id}/reject", response_model=schemas.ApplicationOut)
def reject(application_id: int, data: schemas.RequesterBody, db: Session = Depends(get_db)):
    return service.reject(db, application_id, data.user_id)
