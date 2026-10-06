from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.models import (
    Application,
    ApplicationStatus,
    Member,
    MemberRole,
    Study,
    StudyStatus,
    User,
)
from app.services.common import (
    get_application,
    get_member,
    get_study,
    get_user,
    member_count,
    require_owner,
    sync_status,
)


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
) -> list[dict]:
    study = get_study(db, study_id)
    require_owner(db, study, user_id)
    q = (
        select(Application, User.nickname)
        .join(User, User.id == Application.user_id)
        .where(Application.study_id == study_id)
        .order_by(Application.id)
    )
    if status:
        q = q.where(Application.status == status)
    return [
        {**schemas.ApplicationOut.model_validate(a).model_dump(), "nickname": nick}
        for a, nick in db.execute(q).all()
    ]


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
