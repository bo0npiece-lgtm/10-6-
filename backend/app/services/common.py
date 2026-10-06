"""여러 도메인에서 함께 쓰는 조회/검증 헬퍼."""
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Application,
    ApplicationStatus,
    Member,
    Room,
    Study,
    StudyStatus,
    User,
)


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "존재하지 않는 사용자입니다.")
    return user


def get_study(db: Session, study_id: int) -> Study:
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(404, "존재하지 않는 스터디입니다.")
    return study


def get_application(db: Session, application_id: int) -> Application:
    app = db.get(Application, application_id)
    if not app:
        raise HTTPException(404, "존재하지 않는 신청입니다.")
    return app


def get_room(db: Session, room_id: int) -> Room:
    room = db.get(Room, room_id)
    if not room:
        raise HTTPException(404, "존재하지 않는 스터디룸입니다.")
    return room


def require_owner(db: Session, study: Study, user_id: int) -> None:
    get_user(db, user_id)
    if study.owner_id != user_id:
        raise HTTPException(403, "방장만 할 수 있는 작업입니다.")


def member_count(db: Session, study_id: int) -> int:
    return db.scalar(select(func.count()).select_from(Member).where(Member.study_id == study_id))


def get_member(db: Session, study_id: int, user_id: int) -> Member | None:
    return db.scalar(select(Member).where(Member.study_id == study_id, Member.user_id == user_id))


def sync_status(db: Session, study: Study) -> None:
    """정원 > 인원이면 RECRUITING, 정원 == 인원이면 CLOSED (남은 PENDING 신청은 자동 거절)."""
    if member_count(db, study.id) >= study.capacity:
        study.status = StudyStatus.CLOSED
        pending = db.scalars(
            select(Application).where(
                Application.study_id == study.id,
                Application.status == ApplicationStatus.PENDING,
            )
        )
        for a in pending:
            a.status = ApplicationStatus.REJECTED
    else:
        study.status = StudyStatus.RECRUITING
