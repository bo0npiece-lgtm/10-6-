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


app = FastAPI(title="스터디 모집·신청 서비스", lifespan=lifespan)

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


@app.get("/health", tags=["demo"])
def health():
    return {"status": "ok"}
