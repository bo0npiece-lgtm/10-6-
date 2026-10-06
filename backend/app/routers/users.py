from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.schemas import errors
from app.services import users as service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=schemas.UserOut, status_code=201,
             summary="사용자 생성", responses=errors(409))
def create_user(data: schemas.UserCreate, db: Session = Depends(get_db)):
    """닉네임만으로 사용자를 만든다. 닉네임이 중복되면 409."""
    return service.create_user(db, data)


@router.get("", response_model=list[schemas.UserOut], summary="사용자 목록")
def list_users(db: Session = Depends(get_db)):
    return service.list_users(db)


@router.get("/{user_id}/applications", response_model=list[schemas.MyApplicationOut],
            summary="내 신청 목록", responses=errors(404))
def my_applications(user_id: int, db: Session = Depends(get_db)):
    """사용자가 넣은 모든 신청을 최신순으로 반환한다 (스터디 제목 포함)."""
    return service.my_applications(db, user_id)
