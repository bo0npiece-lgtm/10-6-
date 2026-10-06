from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.models import Application, Study, User
from app.services.common import get_user


def create_user(db: Session, data: schemas.UserCreate) -> User:
    if db.scalar(select(User).where(User.nickname == data.nickname)):
        raise HTTPException(409, "이미 사용 중인 닉네임입니다.")
    user = User(nickname=data.nickname)
    db.add(user)
    db.commit()
    return user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)))


def my_applications(db: Session, user_id: int) -> list[dict]:
    get_user(db, user_id)
    rows = db.execute(
        select(Application, Study.title)
        .join(Study, Study.id == Application.study_id)
        .where(Application.user_id == user_id)
        .order_by(Application.id.desc())
    ).all()
    return [
        {**schemas.ApplicationOut.model_validate(a).model_dump(), "study_title": title}
        for a, title in rows
    ]
