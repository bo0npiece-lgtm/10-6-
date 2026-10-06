from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

import schemas
from models import (
    Application,
    ApplicationStatus,
    Member,
    MemberRole,
    Reservation,
    ReservationStatus,
    Room,
    Study,
    StudyStatus,
    User,
    now_kst,
)


# ---------- 공통 헬퍼 ----------
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


def study_out(db: Session, study: Study) -> dict:
    return {
        "id": study.id,
        "title": study.title,
        "description": study.description,
        "owner_id": study.owner_id,
        "capacity": study.capacity,
        "status": study.status,
        "created_at": study.created_at,
        "member_count": member_count(db, study.id),
    }


# ---------- User ----------
def create_user(db: Session, data: schemas.UserCreate) -> User:
    if db.scalar(select(User).where(User.nickname == data.nickname)):
        raise HTTPException(409, "이미 사용 중인 닉네임입니다.")
    user = User(nickname=data.nickname)
    db.add(user)
    db.commit()
    return user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)))


# ---------- Study ----------
def create_study(db: Session, data: schemas.StudyCreate) -> dict:
    get_user(db, data.owner_id)
    study = Study(
        title=data.title,
        description=data.description,
        owner_id=data.owner_id,
        capacity=data.capacity,
        status=StudyStatus.RECRUITING,
    )
    db.add(study)
    db.flush()
    db.add(Member(study_id=study.id, user_id=data.owner_id, role=MemberRole.OWNER))
    db.commit()
    return study_out(db, study)


def list_studies(db: Session, status: StudyStatus | None) -> list[dict]:
    q = select(Study).order_by(Study.id.desc())
    if status:
        q = q.where(Study.status == status)
    return [study_out(db, s) for s in db.scalars(q)]


def study_detail(db: Session, study_id: int) -> dict:
    study = get_study(db, study_id)
    rows = db.execute(
        select(Member.user_id, User.nickname, Member.role)
        .join(User, User.id == Member.user_id)
        .where(Member.study_id == study_id)
        .order_by(Member.role.desc(), Member.id)  # OWNER 먼저
    ).all()
    out = study_out(db, study)
    out["members"] = [{"user_id": r[0], "nickname": r[1], "role": r[2]} for r in rows]
    return out


def update_capacity(db: Session, study_id: int, data: schemas.CapacityUpdate) -> dict:
    study = get_study(db, study_id)
    require_owner(db, study, data.user_id)
    count = member_count(db, study_id)
    if data.capacity < count:
        raise HTTPException(400, f"정원은 현재 인원({count}명)보다 작을 수 없습니다.")
    study.capacity = data.capacity
    sync_status(db, study)
    db.commit()
    return study_out(db, study)


# ---------- Application ----------
def apply(db: Session, study_id: int, data: schemas.ApplicationCreate) -> Application:
    study = get_study(db, study_id)
    get_user(db, data.user_id)
    if study.status != StudyStatus.RECRUITING:
        raise HTTPException(400, "모집 중인 스터디만 신청할 수 있습니다.")
    if get_member(db, study_id, data.user_id):
        raise HTTPException(409, "이미 스터디 멤버(또는 방장)입니다.")
    dup = db.scalar(
        select(Application).where(
            Application.study_id == study_id,
            Application.user_id == data.user_id,
            Application.status == ApplicationStatus.PENDING,
        )
    )
    if dup:
        raise HTTPException(409, "이미 대기 중인 신청이 있습니다.")
    app = Application(study_id=study_id, user_id=data.user_id, message=data.message)
    db.add(app)
    db.commit()
    return app


def cancel_application(db: Session, application_id: int, user_id: int) -> Application:
    app = get_application(db, application_id)
    if app.user_id != user_id:
        raise HTTPException(403, "본인의 신청만 취소할 수 있습니다.")
    if app.status != ApplicationStatus.PENDING:
        raise HTTPException(400, "대기 중(PENDING)인 신청만 취소할 수 있습니다.")
    app.status = ApplicationStatus.CANCELED
    db.commit()
    return app


def list_applications(
    db: Session, study_id: int, user_id: int, status: ApplicationStatus | None
) -> list[Application]:
    study = get_study(db, study_id)
    require_owner(db, study, user_id)
    q = select(Application).where(Application.study_id == study_id).order_by(Application.id)
    if status:
        q = q.where(Application.status == status)
    return list(db.scalars(q))


def _pending_for_owner(db: Session, application_id: int, user_id: int) -> tuple[Application, Study]:
    app = get_application(db, application_id)
    study = get_study(db, app.study_id)
    require_owner(db, study, user_id)
    if app.status != ApplicationStatus.PENDING:
        raise HTTPException(400, "대기 중(PENDING)인 신청만 처리할 수 있습니다.")
    return app, study


def approve(db: Session, application_id: int, user_id: int) -> Application:
    app, study = _pending_for_owner(db, application_id, user_id)
    if member_count(db, study.id) >= study.capacity:
        raise HTTPException(400, "정원이 가득 차 승인할 수 없습니다.")
    # 한 트랜잭션: 상태 변경 + 멤버 생성 + 정원 도달 시 마감
    app.status = ApplicationStatus.APPROVED
    db.add(Member(study_id=study.id, user_id=app.user_id, role=MemberRole.MEMBER))
    db.flush()
    sync_status(db, study)
    db.commit()
    return app


def reject(db: Session, application_id: int, user_id: int) -> Application:
    app, _ = _pending_for_owner(db, application_id, user_id)
    app.status = ApplicationStatus.REJECTED
    db.commit()
    return app


# ---------- Owner transfer ----------
def transfer_owner(db: Session, study_id: int, data: schemas.TransferOwner) -> dict:
    study = get_study(db, study_id)
    require_owner(db, study, data.user_id)
    if data.new_owner_id == data.user_id:
        raise HTTPException(400, "자기 자신을 방장으로 지정할 수 없습니다.")
    get_user(db, data.new_owner_id)
    new_m = get_member(db, study_id, data.new_owner_id)
    if not new_m:
        raise HTTPException(400, "스터디 멤버만 방장으로 지정할 수 있습니다.")
    old_m = get_member(db, study_id, data.user_id)
    # 한 트랜잭션: owner_id 변경 + 역할 교체 (방장은 항상 1명)
    study.owner_id = data.new_owner_id
    old_m.role = MemberRole.MEMBER
    new_m.role = MemberRole.OWNER
    db.commit()
    return study_detail(db, study_id)


# ---------- Room / Reservation ----------
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
    study = get_study(db, r.study_id)
    require_owner(db, study, user_id)
    if r.status != ReservationStatus.CONFIRMED:
        raise HTTPException(400, "이미 취소된 예약입니다.")
    r.status = ReservationStatus.CANCELED
    db.commit()
    return r


# ---------- Seed ----------
def seed(db: Session) -> dict:
    """기존 데이터를 모두 지우고 시연용 데이터를 다시 넣는다 (여러 번 호출해도 안전)."""
    for model in (Reservation, Application, Member, Study, Room, User):
        db.execute(delete(model))
    db.flush()

    users = [User(nickname=n) for n in ["민수", "지영", "현우", "수진", "도윤"]]
    db.add_all(users)
    rooms = [Room(name=n, capacity=c) for n, c in SAMPLE_ROOMS]
    db.add_all(rooms)
    db.flush()
    u = [x.id for x in users]

    def new_study(owner, title, desc, cap, members):
        s = Study(title=title, description=desc, owner_id=owner, capacity=cap)
        db.add(s)
        db.flush()
        db.add(Member(study_id=s.id, user_id=owner, role=MemberRole.OWNER))
        for m in members:
            db.add(Member(study_id=s.id, user_id=m, role=MemberRole.MEMBER))
            db.add(Application(study_id=s.id, user_id=m, message="참여하고 싶어요!",
                               status=ApplicationStatus.APPROVED))
        db.flush()
        sync_status(db, s)
        return s

    # 모집중: 민수 방장, 지영 멤버 (2/4)
    s1 = new_study(u[0], "알고리즘 스터디", "주 2회 백준 문제 풀이", 4, [u[1]])
    # 모집중: 현우 방장 (1/3)
    s2 = new_study(u[2], "토익 900 스터디", "매일 아침 LC/RC 모의고사", 3, [])
    # 마감: 수진 방장, 민수·도윤 멤버 (3/3) -> CLOSED
    new_study(u[3], "CS 면접 스터디", "운영체제·네트워크 질문 정리", 3, [u[0], u[4]])

    # 대기 중인 신청 (시연에서 승인/거절용)
    db.add_all([
        Application(study_id=s1.id, user_id=u[2], message="파이썬으로 풀어요"),
        Application(study_id=s1.id, user_id=u[3], message="주말에도 가능합니다"),
        Application(study_id=s2.id, user_id=u[4], message="목표 점수 900!"),
    ])

    # 예약: 내일 14~16시, A룸, 알고리즘 스터디
    tomorrow = (now_kst() + timedelta(days=1)).replace(hour=14, minute=0, second=0)
    db.add(Reservation(room_id=rooms[0].id, study_id=s1.id, reserved_by=u[0],
                       start_at=tomorrow, end_at=tomorrow + timedelta(hours=2)))
    db.commit()
    return {
        "message": "시연용 데이터가 생성되었습니다.",
        "users": [{"id": x.id, "nickname": x.nickname} for x in users],
        "studies": list_studies(db, None),
        "rooms": [{"id": r.id, "name": r.name, "capacity": r.capacity} for r in rooms],
    }
