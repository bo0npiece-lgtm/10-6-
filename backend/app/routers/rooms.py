from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.schemas import errors
from app.services import rooms as service

router = APIRouter(tags=["rooms"])


@router.get("/rooms", response_model=list[schemas.RoomOut], summary="스터디룸 목록")
def list_rooms(db: Session = Depends(get_db)):
    return service.list_rooms(db)


@router.get("/rooms/{room_id}/reservations", response_model=list[schemas.ReservationOut],
            summary="방의 날짜별 예약", responses=errors(404))
def room_reservations(
    room_id: int,
    day: date = Query(alias="date", description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """해당 날짜에 걸쳐 있는 확정(CONFIRMED) 예약만 반환한다."""
    return service.room_reservations(db, room_id, day)


@router.get("/studies/{study_id}/reservations", response_model=list[schemas.ReservationOut],
            summary="스터디의 예약 목록", responses=errors(404))
def study_reservations(study_id: int, db: Session = Depends(get_db)):
    """확정(CONFIRMED) 예약만 시작 시간순으로 반환한다."""
    return service.study_reservations(db, study_id)


@router.post("/studies/{study_id}/reservations", response_model=schemas.ReservationOut,
             status_code=201, summary="스터디룸 예약 (방장)", responses=errors(400, 403, 404, 409))
def create_reservation(study_id: int, data: schemas.ReservationCreate, db: Session = Depends(get_db)):
    """시간은 KST 기준 `YYYY-MM-DDTHH:MM:SS` (타임존이 붙으면 KST로 변환).
    end > start, 과거 시간 불가, 스터디 인원이 방 정원을 넘으면 400.
    같은 방의 확정 예약과 시간이 겹치면 409 (맞닿는 시간은 허용)."""
    return service.create_reservation(db, study_id, data)


@router.delete("/reservations/{reservation_id}", response_model=schemas.ReservationOut,
               summary="예약 취소 (방장)", responses=errors(400, 403, 404))
def cancel_reservation(
    reservation_id: int,
    user_id: int = Query(description="요청자(방장) user_id"),
    db: Session = Depends(get_db),
):
    """상태가 CANCELED로 바뀐다. 이미 취소된 예약이면 400."""
    return service.cancel_reservation(db, reservation_id, user_id)
