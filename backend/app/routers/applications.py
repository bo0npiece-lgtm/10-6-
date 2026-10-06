from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import ApplicationStatus
from app.schemas import errors
from app.services import applications as service

router = APIRouter(tags=["applications"])


@router.post("/studies/{study_id}/applications", response_model=schemas.ApplicationOut,
             status_code=201, summary="참여 신청", responses=errors(400, 404, 409))
def apply(study_id: int, data: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    """모집중(RECRUITING) 스터디만 신청 가능(아니면 400).
    방장·기존 멤버·대기 중(PENDING) 중복 신청은 409. 거절/취소된 뒤 재신청은 가능."""
    return service.apply(db, study_id, data)


@router.get("/studies/{study_id}/applications", response_model=list[schemas.ApplicationWithUser],
            summary="신청 목록 (방장)", responses=errors(403, 404))
def list_applications(
    study_id: int,
    user_id: int = Query(description="요청자(방장) user_id"),
    status: ApplicationStatus | None = None,
    db: Session = Depends(get_db),
):
    """신청자 닉네임 포함. `status`로 필터 가능."""
    return service.list_applications(db, study_id, user_id, status)


@router.delete("/applications/{application_id}", response_model=schemas.ApplicationOut,
               summary="신청 취소 (본인)", responses=errors(400, 403, 404))
def cancel_application(
    application_id: int,
    user_id: int = Query(description="요청자(신청자 본인) user_id"),
    db: Session = Depends(get_db),
):
    """대기 중(PENDING)인 신청만 취소 가능. 상태가 CANCELED로 바뀐다."""
    return service.cancel_application(db, application_id, user_id)


@router.post("/applications/{application_id}/approve", response_model=schemas.ApplicationOut,
             summary="신청 승인 (방장)", responses=errors(400, 403, 404))
def approve(application_id: int, data: schemas.RequesterBody, db: Session = Depends(get_db)):
    """PENDING만 승인 가능, 정원이 가득 차면 400.
    한 트랜잭션에서 상태 변경 + 멤버 생성 + 정원 도달 시 스터디 CLOSED."""
    return service.approve(db, application_id, data.user_id)


@router.post("/applications/{application_id}/reject", response_model=schemas.ApplicationOut,
             summary="신청 거절 (방장)", responses=errors(400, 403, 404))
def reject(application_id: int, data: schemas.RequesterBody, db: Session = Depends(get_db)):
    """PENDING만 거절 가능."""
    return service.reject(db, application_id, data.user_id)
