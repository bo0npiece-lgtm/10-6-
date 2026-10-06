from datetime import timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.database import now_kst
from app.models import (
    Application,
    ApplicationStatus,
    Member,
    MemberRole,
    Reservation,
    Room,
    Study,
    User,
)
from app.services.common import sync_status
from app.services.rooms import SAMPLE_ROOMS
from app.services.studies import list_studies


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
