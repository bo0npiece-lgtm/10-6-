from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.services import rooms as service

router = APIRouter(tags=["rooms"])


@router.get("/rooms", response_model=list[schemas.RoomOut])
def list_rooms(db: Session = Depends(get_db)):
    return service.list_rooms(db)


@router.get("/rooms/{room_id}/reservations", response_model=list[schemas.ReservationOut])
def room_reservations(
    room_id: int,
    day: date = Query(alias="date", description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    return service.room_reservations(db, room_id, day)


@router.get("/studies/{study_id}/reservations", response_model=list[schemas.ReservationOut])
def study_reservations(study_id: int, db: Session = Depends(get_db)):
    return service.study_reservations(db, study_id)


@router.post(
    "/studies/{study_id}/reservations",
    response_model=schemas.ReservationOut,
    status_code=201,
)
def create_reservation(study_id: int, data: schemas.ReservationCreate, db: Session = Depends(get_db)):
    return service.create_reservation(db, study_id, data)


@router.delete("/reservations/{reservation_id}", response_model=schemas.ReservationOut)
def cancel_reservation(
    reservation_id: int,
    user_id: int = Query(description="요청자(방장) user_id"),
    db: Session = Depends(get_db),
):
    return service.cancel_reservation(db, reservation_id, user_id)
