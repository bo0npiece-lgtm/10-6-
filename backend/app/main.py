from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, SessionLocal, engine
from app.routers import applications, demo, rooms, studies, users
from app.services.rooms import ensure_sample_rooms


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_sample_rooms(db)
    yield


DESCRIPTION = """
해커톤 연습용 스터디 모집·신청 서비스 API.

**인증 없음**: 요청자는 `user_id`로만 구분한다.
- `GET` / `DELETE` → `user_id`를 **쿼리**로 전달
- `POST` / `PATCH` → `user_id`를 **body**로 전달
- 방장 전용 API는 `user_id ≠ owner_id`이면 403

에러 응답은 모두 `{"detail": "한국어 메시지"}` 형식이다. 시간은 KST naive datetime(`YYYY-MM-DDTHH:MM:SS`).
"""

TAGS = [
    {"name": "users", "description": "사용자 (닉네임만으로 생성)"},
    {"name": "studies", "description": "스터디 모집, 정원, 방장 위임"},
    {"name": "applications", "description": "참여 신청, 취소, 승인, 거절"},
    {"name": "rooms", "description": "스터디룸과 예약"},
    {"name": "demo", "description": "시연용 데이터, 헬스 체크"},
]

app = FastAPI(
    title="스터디 모집·신청 서비스",
    description=DESCRIPTION,
    version="1.0.0",
    openapi_tags=TAGS,
    lifespan=lifespan,
)

# 프론트(Vite dev server 등) 연동용: 해커톤이므로 전체 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(studies.router)
app.include_router(applications.router)
app.include_router(rooms.router)
app.include_router(demo.router)


@app.get("/health", tags=["demo"], summary="헬스 체크")
def health():
    return {"status": "ok"}
