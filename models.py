import enum
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

KST = ZoneInfo("Asia/Seoul")


def now_kst() -> datetime:
    """모든 시간은 KST naive datetime으로 통일한다."""
    return datetime.now(KST).replace(tzinfo=None, microsecond=0)


class Base(DeclarativeBase):
    pass


class StudyStatus(str, enum.Enum):
    RECRUITING = "RECRUITING"
    CLOSED = "CLOSED"


class MemberRole(str, enum.Enum):
    OWNER = "OWNER"
    MEMBER = "MEMBER"


class ApplicationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELED = "CANCELED"


class ReservationStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    CANCELED = "CANCELED"


def _enum(e):
    return Enum(e, native_enum=False, length=20)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nickname: Mapped[str] = mapped_column(String(50), unique=True)


class Study(Base):
    __tablename__ = "studies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    capacity: Mapped[int] = mapped_column(Integer)
    status: Mapped[StudyStatus] = mapped_column(_enum(StudyStatus), default=StudyStatus.RECRUITING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_kst)


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("studies.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    role: Mapped[MemberRole] = mapped_column(_enum(MemberRole), default=MemberRole.MEMBER)


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("studies.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    message: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[ApplicationStatus] = mapped_column(
        _enum(ApplicationStatus), default=ApplicationStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_kst)


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    capacity: Mapped[int] = mapped_column(Integer)


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"))
    study_id: Mapped[int] = mapped_column(ForeignKey("studies.id"))
    reserved_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    start_at: Mapped[datetime] = mapped_column(DateTime)
    end_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[ReservationStatus] = mapped_column(
        _enum(ReservationStatus), default=ReservationStatus.CONFIRMED
    )
