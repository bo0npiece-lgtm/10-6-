from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.database import KST
from app.models import ApplicationStatus, MemberRole, ReservationStatus, StudyStatus


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- User ----------
class UserCreate(BaseModel):
    nickname: str = Field(min_length=1, max_length=50, examples=["철수"])


class UserOut(ORM):
    id: int
    nickname: str


# ---------- Study ----------
class StudyCreate(BaseModel):
    owner_id: int = Field(examples=[1])
    title: str = Field(min_length=1, max_length=100, examples=["알고리즘 스터디"])
    description: str = Field(default="", examples=["주 2회 백준 문제 풀이"])
    capacity: int = Field(ge=2, examples=[4])


class CapacityUpdate(BaseModel):
    user_id: int = Field(examples=[1])
    capacity: int = Field(ge=2, examples=[5])


class StudyOut(ORM):
    id: int
    title: str
    description: str
    owner_id: int
    capacity: int
    status: StudyStatus
    created_at: datetime
    member_count: int


class MemberOut(ORM):
    user_id: int
    nickname: str
    role: MemberRole


class StudyDetail(StudyOut):
    members: list[MemberOut]


# ---------- Application ----------
class ApplicationCreate(BaseModel):
    user_id: int = Field(examples=[2])
    message: str = Field(default="", examples=["열심히 참여하겠습니다!"])


class RequesterBody(BaseModel):
    user_id: int = Field(examples=[1])


class ApplicationOut(ORM):
    id: int
    study_id: int
    user_id: int
    message: str
    status: ApplicationStatus
    created_at: datetime


class ApplicationWithUser(ApplicationOut):
    nickname: str


class MyApplicationOut(ApplicationOut):
    study_title: str


# ---------- Owner transfer ----------
class TransferOwner(BaseModel):
    user_id: int = Field(examples=[1])
    new_owner_id: int = Field(examples=[2])


# ---------- Room / Reservation ----------
class RoomOut(ORM):
    id: int
    name: str
    capacity: int


class ReservationCreate(BaseModel):
    user_id: int = Field(examples=[1])
    room_id: int = Field(examples=[1])
    start_at: datetime = Field(examples=["2030-01-01T14:00:00"])
    end_at: datetime = Field(examples=["2030-01-01T16:00:00"])

    @field_validator("start_at", "end_at")
    @classmethod
    def to_kst_naive(cls, v: datetime) -> datetime:
        # 타임존이 붙어 오면 KST로 변환 후 naive로 저장
        if v.tzinfo is not None:
            v = v.astimezone(KST).replace(tzinfo=None)
        return v.replace(microsecond=0)


class ReservationOut(ORM):
    id: int
    room_id: int
    study_id: int
    reserved_by: int
    start_at: datetime
    end_at: datetime
    status: ReservationStatus
