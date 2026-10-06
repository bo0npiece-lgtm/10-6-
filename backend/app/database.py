import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# 기본값: backend/app.db (실행 위치와 무관하게 고정). 테스트에서는 환경변수로 교체.
DB_PATH = Path(__file__).resolve().parent.parent / "app.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

KST = ZoneInfo("Asia/Seoul")


def now_kst() -> datetime:
    """모든 시간은 KST naive datetime으로 통일한다."""
    return datetime.now(KST).replace(tzinfo=None, microsecond=0)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI 의존성: 요청마다 세션을 열고 닫는다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
