from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.models import Member, MemberRole, Study, StudyStatus, User
from app.services.common import (
    get_member,
    get_study,
    get_user,
    member_count,
    require_owner,
    sync_status,
)


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
