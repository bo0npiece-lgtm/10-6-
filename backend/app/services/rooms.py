from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import schemas
from app.database import now_kst
from app.models import Reservation, ReservationStatus, Room, Study
from app.services.common import get_room, get_study, member_count, require_owner

SAMPLE_ROOMS = [("A룸 (소형)", 4), ("B룸 (중형)", 6), ("C룸 (대형)", 10)]


def ensure_sample_rooms(db: Session) -> None:
    if not db.scalar(select(func.count()).select_from(Room)):
        db.add_all(Room(name=n, capacity=c) for n, c in SAMPLE_ROOMS)
        db.commit()


def list_rooms(db: Session) -> list[Room]:
    return list(db.scalars(select(Room).order_by(Room.id)))


def room_reservations(db: Session, room_id: int, day: date) -> list[Reservation]:
    get_room(db, room_id)
    start = datetime.combine(day, datetime.min.time())
    end = start + timedelta(days=1)
    return list(
        db.scalars(
            select(Reservation)
            .where(
                Reservation.room_id == room_id,
                Reservation.status == ReservationStatus.CONFIRMED,
                Reservation.start_at < end,
                Reservation.end_at > start,
            )
            .order_by(Reservation.start_at)
        )
    )


def study_reservations(db: Session, study_id: int) -> list[Reservation]:
    get_study(db, study_id)
    return list(
        db.scalars(
            select(Reservation)
            .where(
                Reservation.study_id == study_id,
                Reservation.status == ReservationStatus.CONFIRMED,
            )
            .order_by(Reservation.start_at)
        )
    )


def create_reservation(db: Session, study_id: int, data: schemas.ReservationCreate) -> Reservation:
    study = get_study(db, study_id)
    require_owner(db, study, data.user_id)
    room = get_room(db, data.room_id)
    if data.end_at <= data.start_at:
        raise HTTPException(400, "종료 시간은 시작 시간보다 늦어야 합니다.")
    if data.start_at < now_kst():
        raise HTTPException(400, "과거 시간은 예약할 수 없습니다.")
    count = member_count(db, study_id)
    if count > room.capacity:
        raise HTTPException(400, f"스터디 인원({count}명)이 방 정원({room.capacity}명)을 초과합니다.")
    overlap = db.scalar(
        select(Reservation).where(
            Reservation.room_id == room.id,
            Reservation.status == ReservationStatus.CONFIRMED,
            Reservation.start_at < data.end_at,
            Reservation.end_at > data.start_at,
        )
    )
    if overlap:
        raise HTTPException(409, "해당 시간에 이미 예약이 있습니다.")
    r = Reservation(
        room_id=room.id,
        study_id=study_id,
        reserved_by=data.user_id,
        start_at=data.start_at,
        end_at=data.end_at,
    )
    db.add(r)
    db.commit()
    return r


def cancel_reservation(db: Session, reservation_id: int, user_id: int) -> Reservation:
    r = db.get(Reservation, reservation_id)
    if not r:
        raise HTTPException(404, "존재하지 않는 예약입니다.")
    study: Study = get_study(db, r.study_id)
    require_owner(db, study, user_id)
    if r.status != ReservationStatus.CONFIRMED:
        raise HTTPException(400, "이미 취소된 예약입니다.")
    r.status = ReservationStatus.CANCELED
    db.commit()
    return r
