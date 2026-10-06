from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import crud
import schemas
from models import ApplicationStatus, Base, SessionLocal, StudyStatus, engine


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        crud.ensure_sample_rooms(db)
    yield


app = FastAPI(title="스터디 모집·신청 서비스", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- User ----------
@app.post("/users", response_model=schemas.UserOut, status_code=201, tags=["users"])
def create_user(data: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, data)


@app.get("/users", response_model=list[schemas.UserOut], tags=["users"])
def list_users(db: Session = Depends(get_db)):
    return crud.list_users(db)


# ---------- Study ----------
@app.post("/studies", response_model=schemas.StudyOut, status_code=201, tags=["studies"])
def create_study(data: schemas.StudyCreate, db: Session = Depends(get_db)):
    return crud.create_study(db, data)


@app.get("/studies", response_model=list[schemas.StudyOut], tags=["studies"])
def list_studies(status: StudyStatus | None = None, db: Session = Depends(get_db)):
    return crud.list_studies(db, status)


@app.get("/studies/{study_id}", response_model=schemas.StudyDetail, tags=["studies"])
def get_study(study_id: int, db: Session = Depends(get_db)):
    return crud.study_detail(db, study_id)


@app.patch("/studies/{study_id}/capacity", response_model=schemas.StudyOut, tags=["studies"])
def update_capacity(study_id: int, data: schemas.CapacityUpdate, db: Session = Depends(get_db)):
    return crud.update_capacity(db, study_id, data)


@app.post("/studies/{study_id}/transfer-owner", response_model=schemas.StudyDetail, tags=["studies"])
def transfer_owner(study_id: int, data: schemas.TransferOwner, db: Session = Depends(get_db)):
    return crud.transfer_owner(db, study_id, data)


# ---------- Application ----------
@app.post(
    "/studies/{study_id}/applications",
    response_model=schemas.ApplicationOut,
    status_code=201,
    tags=["applications"],
)
def apply(study_id: int, data: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    return crud.apply(db, study_id, data)


@app.get(
    "/studies/{study_id}/applications",
    response_model=list[schemas.ApplicationOut],
    tags=["applications"],
)
def list_applications(
    study_id: int,
    user_id: int = Query(description="요청자(방장) user_id"),
    status: ApplicationStatus | None = None,
    db: Session = Depends(get_db),
):
    return crud.list_applications(db, study_id, user_id, status)


@app.delete("/applications/{application_id}", response_model=schemas.ApplicationOut, tags=["applications"])
def cancel_application(
    application_id: int,
    user_id: int = Query(description="요청자(신청자 본인) user_id"),
    db: Session = Depends(get_db),
):
    return crud.cancel_application(db, application_id, user_id)


@app.post("/applications/{application_id}/approve", response_model=schemas.ApplicationOut, tags=["applications"])
def approve(application_id: int, data: schemas.RequesterBody, db: Session = Depends(get_db)):
    return crud.approve(db, application_id, data.user_id)


@app.post("/applications/{application_id}/reject", response_model=schemas.ApplicationOut, tags=["applications"])
def reject(application_id: int, data: schemas.RequesterBody, db: Session = Depends(get_db)):
    return crud.reject(db, application_id, data.user_id)


# ---------- Room / Reservation ----------
@app.get("/rooms", response_model=list[schemas.RoomOut], tags=["rooms"])
def list_rooms(db: Session = Depends(get_db)):
    return crud.list_rooms(db)


@app.get("/rooms/{room_id}/reservations", response_model=list[schemas.ReservationOut], tags=["rooms"])
def room_reservations(
    room_id: int,
    date: date = Query(description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    return crud.room_reservations(db, room_id, date)


@app.post(
    "/studies/{study_id}/reservations",
    response_model=schemas.ReservationOut,
    status_code=201,
    tags=["rooms"],
)
def create_reservation(study_id: int, data: schemas.ReservationCreate, db: Session = Depends(get_db)):
    return crud.create_reservation(db, study_id, data)


@app.delete("/reservations/{reservation_id}", response_model=schemas.ReservationOut, tags=["rooms"])
def cancel_reservation(
    reservation_id: int,
    user_id: int = Query(description="요청자(방장) user_id"),
    db: Session = Depends(get_db),
):
    return crud.cancel_reservation(db, reservation_id, user_id)


# ---------- Demo ----------
@app.post("/seed", tags=["demo"])
def seed(db: Session = Depends(get_db)):
    return crud.seed(db)
