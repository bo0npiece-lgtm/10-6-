# 스터디 모집·신청 서비스 (해커톤 연습용)

백엔드(FastAPI)와 프론트엔드(React)를 나누고 API로 연결하는 연습을 위한 간단한 풀스택 프로젝트입니다.
**인증이 없습니다.** 화면 우측 상단의 "현재 사용자" 선택이 로그인을 대신하고, API는 `user_id`로 요청자를 구분합니다.

| 영역 | 스택 |
|---|---|
| backend | Python 3.12, FastAPI, SQLAlchemy 2, SQLite, Pydantic v2, pytest |
| frontend | Vite, React 19, react-router 7, fetch (추가 라이브러리 없음) |

> 📘 처음 배우는 분은 [풀스택 길라잡이](docs/GUIDE.md)를 보세요. 1부는 백엔드 기초, 팀이 정할 것과 백엔드가 할 일, 기능 추가 실습이고, 2부는 프론트엔드를 처음부터 직접 만들어 보는 실습입니다.

## 디렉토리 구조

```
.
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 앱 생성, CORS, 라우터 등록, 시작 시 테이블/샘플 방 생성
│   │   ├── database.py        # 엔진·세션·Base, get_db 의존성, now_kst()
│   │   ├── models.py          # SQLAlchemy 모델 + 상태 Enum
│   │   ├── schemas.py         # Pydantic 요청/응답 스키마
│   │   ├── routers/           # HTTP 계층: 경로·파라미터·응답 모델만 정의
│   │   │   ├── users.py  studies.py  applications.py  rooms.py  demo.py
│   │   └── services/          # 비즈니스 로직: 검증 + DB 작업 + HTTPException
│   │       ├── common.py      # 공통 조회/권한 검사/정원 상태 동기화
│   │       ├── users.py  studies.py  applications.py  rooms.py  seed.py
│   ├── tests/                 # pytest (테스트 전용 임시 DB 사용)
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── pytest.ini
└── frontend/
    ├── .env.example           # VITE_API_URL (비워두면 /api 프록시 사용)
    ├── index.html
    ├── vite.config.js         # dev 서버 프록시: /api → http://127.0.0.1:8000
    └── src/
        ├── main.jsx           # 진입점 (Router + AppProvider)
        ├── App.jsx            # 라우트 정의
        ├── api/               # ★ 백엔드 호출은 전부 여기에
        │   ├── client.js      # fetch 래퍼: base URL, JSON, 에러 메시지 변환
        │   └── users.js  studies.js  applications.js  rooms.js
        ├── context/AppContext.jsx   # 현재 사용자 + toast 전역 상태
        ├── components/        # Header, StatusBadge, Toast
        ├── pages/             # StudyListPage, StudyDetailPage, RoomsPage, MyPage
        ├── utils/format.js
        └── index.css
```

**요청 흐름:** `pages` → `api/*.js` → `api/client.js` (fetch) → **HTTP** → `routers/*.py` → `services/*.py` → `models` / DB

## 실행

터미널 2개를 띄워서 실행합니다.

```bash
# 1) 백엔드: http://localhost:8000  (Swagger: /docs)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

```bash
# 2) 프론트엔드: http://localhost:5173
cd frontend
cp .env.example .env      # 기본값(프록시) 그대로 두면 됨
npm install
npm run dev
```

처음 실행했다면 화면 우측 상단의 **시드 데이터** 버튼을 누르거나 `POST /seed`를 호출하세요.

```bash
cd backend && pytest      # 백엔드 테스트
```

> 모델을 변경하면 `backend/app.db`를 지우고 재시작하세요 (마이그레이션 도구 없음).

### API 연결 방식

```
브라우저 ──/api/studies──▶ Vite dev 서버(5173) ──/studies──▶ FastAPI(8000)
```
- 프론트는 같은 출처의 `/api/...`로 요청하고, [vite.config.js](frontend/vite.config.js)의 **프록시**가 백엔드로 전달합니다.
  - 브라우저는 5173 포트만 알면 됩니다. Windows 브라우저와 WSL 서버처럼 환경이 나뉘어 있어도 동작합니다.
  - 같은 출처 요청이라 CORS 문제가 없습니다.
- 백엔드를 직접 호출하고 싶으면 `.env`에 `VITE_API_URL=http://localhost:8000`을 지정하세요. 이 방식을 위해 백엔드 CORS도 전체 허용해 두었습니다 ([main.py](backend/app/main.py)).
- 에러가 나면 FastAPI의 `{"detail": "..."}` 응답을 [client.js](frontend/src/api/client.js)가 `ApiError`로 바꿔 던지고, 화면에서는 toast로 보여줍니다. 422 검증 에러 배열도 메시지로 변환합니다.
- 백엔드가 꺼져 있으면 "서버에 연결할 수 없습니다" toast가 뜹니다.

## 규칙 요약

| 영역 | 규칙 |
|---|---|
| user_id 전달 | `GET`/`DELETE`는 **쿼리**, `POST`/`PATCH`는 **body**. 방장 전용 API는 `user_id ≠ owner_id`이면 403 |
| 공통 | 없는 리소스는 404, 시간은 모두 **KST naive** (타임존이 붙어 오면 KST로 변환) |
| 스터디 | 생성자는 자동으로 방장(OWNER) 멤버, 정원 ≥ 2 |
| 정원 | 현재 인원보다 작으면 400, **정원 > 인원이면 RECRUITING / 정원 == 인원이면 CLOSED** |
| 신청 | RECRUITING 스터디만 가능, 방장·멤버·PENDING 중복 신청은 409, 거절·취소된 뒤 재신청 가능 |
| 취소 | 본인만 가능, PENDING만 취소 가능 |
| 승인/거절 | 방장만 가능, PENDING만 처리, 정원이 차면 승인 불가. 승인은 한 트랜잭션(상태 변경 + 멤버 생성 + 정원 도달 시 CLOSED) |
| 마감 | 정원이 차서 CLOSED가 되면 남은 PENDING 신청은 **자동 REJECTED** |
| 방장 위임 | 현재 방장만 가능, 대상은 멤버여야 함, 자기 자신은 400, 방장은 항상 1명 |
| 예약 | 방장만 가능, end > start, 과거 시간 불가, 스터디 인원 > 방 정원이면 400, 같은 방 **CONFIRMED 예약**과 시간이 겹치면 409 (맞닿는 시간은 허용) |

## API 목록

| 메서드 | 경로 | 설명 | 요청 예시 |
|---|---|---|---|
| POST | `/users` | 사용자 생성 (닉네임 중복 409) | `{"nickname": "철수"}` |
| GET | `/users` | 사용자 목록 | - |
| GET | `/users/{id}/applications` | 내 신청 목록 (+`study_title`) | - |
| POST | `/studies` | 스터디 모집 글 생성 | `{"owner_id": 1, "title": "알고리즘 스터디", "description": "주 2회", "capacity": 4}` |
| GET | `/studies` | 스터디 목록 (+`member_count`) | `?status=RECRUITING` (선택) |
| GET | `/studies/{id}` | 스터디 상세 (+인원수, 멤버 목록) | - |
| PATCH | `/studies/{id}/capacity` | 정원 변경 (방장) | `{"user_id": 1, "capacity": 5}` |
| POST | `/studies/{id}/transfer-owner` | 방장 위임 (방장) | `{"user_id": 1, "new_owner_id": 2}` |
| POST | `/studies/{id}/applications` | 참여 신청 | `{"user_id": 3, "message": "참여하고 싶어요"}` |
| GET | `/studies/{id}/applications` | 신청 목록 (방장, +`nickname`) | `?user_id=1&status=PENDING` (status 선택) |
| DELETE | `/applications/{id}` | 신청 취소 (본인, PENDING만) | `?user_id=3` |
| POST | `/applications/{id}/approve` | 신청 승인 (방장) | `{"user_id": 1}` |
| POST | `/applications/{id}/reject` | 신청 거절 (방장) | `{"user_id": 1}` |
| GET | `/rooms` | 스터디룸 목록 | - |
| GET | `/rooms/{id}/reservations` | 해당 날짜의 방 예약(CONFIRMED) | `?date=2026-10-07` |
| GET | `/studies/{id}/reservations` | 스터디의 예약(CONFIRMED) | - |
| POST | `/studies/{id}/reservations` | 스터디룸 예약 (방장) | `{"user_id": 1, "room_id": 1, "start_at": "2026-10-07T14:00:00", "end_at": "2026-10-07T16:00:00"}` |
| DELETE | `/reservations/{id}` | 예약 취소 (방장) | `?user_id=1` |
| POST | `/seed` | 전체 삭제 후 시연 데이터 생성 (여러 번 호출해도 안전) | - |
| GET | `/health` | 헬스 체크 | - |

## 시드 데이터

| 구분 | 내용 |
|---|---|
| 유저 | 1 민수, 2 지영, 3 현우, 4 수진, 5 도윤 |
| 스터디 1 | 알고리즘 스터디: 방장 민수, 멤버 지영, 2/4 **RECRUITING** |
| 스터디 2 | 토익 900 스터디: 방장 현우, 1/3 **RECRUITING** |
| 스터디 3 | CS 면접 스터디: 방장 수진, 멤버 민수·도윤, 3/3 **CLOSED** |
| 대기 신청 | 현우→스터디1, 수진→스터디1, 도윤→스터디2 |
| 방 | 1 A룸(4명), 2 B룸(6명), 3 C룸(10명) |
| 예약 | A룸, **내일 14:00~16:00**, 스터디1 |

## 화면 시연 시나리오 (모집 → 신청 → 승인 → 정원 변경 → 방장 위임 → 방 예약)

> 우측 상단 **시드 데이터** 버튼을 누른 뒤, **현재 사용자** 드롭다운으로 사람을 바꿔 가며 진행합니다.

1. **모집:** 사용자를 `도윤`으로 바꾸고 목록 우측 폼에서 "React 스터디"(정원 3)를 등록합니다. 카드에 1/3으로 표시됩니다.
2. **신청:** `도윤`인 상태로 "알고리즘 스터디"에 들어가 신청합니다. "승인을 기다리는 중" 배너와 취소 버튼이 나타납니다.
3. **승인:** 사용자를 `민수`(방장)로 바꾸면 "👑 방장 관리" 패널이 보입니다. 현우와 수진을 승인하면 4/4 **마감**이 되고, 도윤의 신청은 자동으로 거절됩니다.
4. **정원 변경:** 정원을 3으로 바꾸면 에러 toast("현재 인원보다 작을 수 없습니다")가 뜹니다. 5로 바꾸면 다시 **모집중**이 됩니다.
5. **방장 위임:** "지영"에게 위임하면 민수 화면에서 방장 패널이 사라집니다.
6. **방 예약:** 사용자를 `지영`으로 바꾸고 A룸 내일 15:00~17:00을 예약하면 **409 시간 겹침** 에러가 납니다. B룸으로 바꾸면 성공하고, **스터디룸** 탭에서 날짜별 현황을 확인할 수 있습니다.
7. **내 신청:** 사용자를 `도윤`으로 바꾸고 **내 신청** 탭에서 거절·대기·승인 상태를 확인합니다. 대기 중인 신청은 여기서 취소할 수 있습니다.

같은 흐름을 Swagger(`/docs`)에서 API로 직접 호출해 볼 수도 있습니다. 요청 예시는 API 목록 표를 참고하세요.
