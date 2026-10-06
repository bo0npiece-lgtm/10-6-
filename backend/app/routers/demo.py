from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import seed as service

router = APIRouter(tags=["demo"])


@router.post("/seed", summary="시연 데이터 생성")
def seed(db: Session = Depends(get_db)):
    """기존 데이터를 모두 지우고 사용자 5명, 스터디 3개, 대기 신청 3건, 방 3개, 예약 1건을 만든다.
    여러 번 호출해도 안전하다."""
    return service.seed(db)
