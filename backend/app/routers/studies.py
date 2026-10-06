from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import StudyStatus
from app.schemas import errors
from app.services import studies as service

router = APIRouter(prefix="/studies", tags=["studies"])


@router.post("", response_model=schemas.StudyOut, status_code=201,
             summary="스터디 모집 글 생성", responses=errors(404))
def create_study(data: schemas.StudyCreate, db: Session = Depends(get_db)):
    """생성자는 자동으로 방장(OWNER) 멤버로 등록된다. 정원은 2 이상."""
    return service.create_study(db, data)


@router.get("", response_model=list[schemas.StudyOut], summary="스터디 목록")
def list_studies(status: StudyStatus | None = None, db: Session = Depends(get_db)):
    """`status`로 모집중(RECRUITING)/마감(CLOSED) 필터. 현재 인원수(`member_count`) 포함."""
    return service.list_studies(db, status)


@router.get("/{study_id}", response_model=schemas.StudyDetail,
            summary="스터디 상세", responses=errors(404))
def get_study(study_id: int, db: Session = Depends(get_db)):
    """현재 인원수와 멤버 목록(방장 먼저)을 포함한다."""
    return service.study_detail(db, study_id)


@router.patch("/{study_id}/capacity", response_model=schemas.StudyOut,
              summary="정원 변경 (방장)", responses=errors(400, 403, 404))
def update_capacity(study_id: int, data: schemas.CapacityUpdate, db: Session = Depends(get_db)):
    """현재 인원보다 작으면 400.
    정원 > 인원이면 RECRUITING, 정원 == 인원이면 CLOSED(남은 대기 신청은 자동 거절)로 바뀐다."""
    return service.update_capacity(db, study_id, data)


@router.post("/{study_id}/transfer-owner", response_model=schemas.StudyDetail,
             summary="방장 위임 (방장)", responses=errors(400, 403, 404))
def transfer_owner(study_id: int, data: schemas.TransferOwner, db: Session = Depends(get_db)):
    """대상은 해당 스터디 멤버여야 하고, 자기 자신은 400.
    한 트랜잭션에서 owner_id 변경 + 이전 방장 MEMBER, 새 방장 OWNER."""
    return service.transfer_owner(db, study_id, data)
