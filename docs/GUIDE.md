# 해커톤 풀스택 길라잡이: 스터디 모집 서비스로 배우는 백엔드 · 프론트엔드

이 저장소의 **스터디 모집 서비스**를 예시로, 백엔드와 프론트엔드를 처음 배우는 사람이 해커톤에서 한 역할을 맡을 수 있도록 돕는 안내서입니다.

| 부 | 대상 | 내용 |
|---|---|---|
| [1부. 백엔드](#1부-백엔드) | 백엔드를 전혀 모르는 사람 | 기본 개념, **팀원끼리 정해야 하는 것**, **백엔드가 혼자 해야 하는 것**, 코드 읽기, 기능 추가 실습, 테스트, 디버깅, 당일 체크리스트 |
| [2부. 프론트엔드](#2부-프론트엔드) | JS 기초는 알지만 React·API 연동은 처음인 사람 | React 핵심 개념, 빈 폴더에서 이 프로젝트 화면을 다시 만드는 10단계 실습, 디버깅, 연습 과제 |

> 팀 전체가 1부의 **"4. 팀원끼리 정해야 하는 것"** 은 꼭 함께 읽어 주세요. 프론트·백엔드 모두에 해당합니다.

**실행 방법** (터미널 2개)

```bash
# 백엔드: http://localhost:8000/docs
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

# 프론트엔드: http://localhost:5173
cd frontend && npm run dev
```

---

## 1부. 백엔드

백엔드가 무엇인지부터 시작해, 이 프로젝트 코드를 읽고 기능 하나를 직접 추가해 보는 데까지 갑니다.

### 1. 백엔드는 무슨 일을 하나요?

식당에 비유하면 이렇습니다.

| 식당 | 웹 서비스 | 이 프로젝트 |
|---|---|---|
| 손님 | 사용자 | 스터디에 신청하는 사람 |
| 홀 직원 + 메뉴판 | **프론트엔드** (화면) | React 화면 |
| 주문서 | **API 요청** | `POST /studies/1/applications` |
| 주방 | **백엔드** (서버) | FastAPI |
| 냉장고 | **데이터베이스** | SQLite (`app.db`) |
| 주방 규칙 ("재료 없으면 주문 거절") | **비즈니스 로직** | "정원이 꽉 차면 승인 불가" |

백엔드의 일을 요약하면 세 가지입니다.

1. **데이터를 저장하고 꺼낸다**: 사용자, 스터디, 신청, 예약
2. **규칙을 지킨다**: "방장만 승인할 수 있다", "시간이 겹치면 예약 불가"
3. **약속된 형식으로 응답한다**: 프론트가 이해할 수 있는 JSON

> 💡 **왜 규칙을 백엔드에서 지켜야 하나요?**
> 화면에서 버튼을 숨겨도, 누구든 Swagger나 curl로 API를 직접 호출할 수 있습니다.
> 프론트의 검사는 **편의**, 백엔드의 검사는 **보안이자 진실**입니다.

---

### 2. 꼭 알아야 할 기본 개념

#### 2-1. HTTP 요청과 응답

프론트와 백엔드는 HTTP로 대화합니다. 요청 하나는 다음으로 이루어집니다.

```
POST /studies/1/applications          ← 메서드 + 경로
Content-Type: application/json        ← 헤더
                                      
{"user_id": 5, "message": "저도 할래요"} ← 본문(body)
```

응답은 **상태 코드 + 본문**입니다.

```
201 Created
{"id": 7, "study_id": 1, "user_id": 5, "status": "PENDING", ...}
```

#### 2-2. HTTP 메서드: 무엇을 하려는지

| 메서드 | 의미 | 이 프로젝트 예시 |
|---|---|---|
| `GET` | 조회 (데이터를 바꾸지 않음) | `GET /studies` 스터디 목록 |
| `POST` | 생성 / 동작 실행 | `POST /studies` 모집 글 생성, `POST /applications/4/approve` 승인 |
| `PATCH` | 일부 수정 | `PATCH /studies/1/capacity` 정원만 변경 |
| `DELETE` | 삭제 / 취소 | `DELETE /applications/7` 신청 취소 |

#### 2-3. 상태 코드: 결과가 어땠는지

| 코드 | 의미 | 이 프로젝트에서 나오는 상황 |
|---|---|---|
| 200 | 성공 | 조회, 수정 성공 |
| 201 | 생성됨 | 사용자·스터디·신청·예약 생성 |
| 400 | 잘못된 요청 (규칙 위반) | 현재 인원보다 작은 정원, 과거 시간 예약 |
| 403 | 권한 없음 | 방장이 아닌데 승인 시도 |
| 404 | 없음 | 존재하지 않는 스터디 id |
| 409 | 충돌 | 중복 신청, 예약 시간 겹침, 닉네임 중복 |
| 422 | 형식 오류 | 정원에 1 입력, 숫자 자리에 문자 (FastAPI가 자동 처리) |
| 500 | 서버 내부 에러 | **버그**. 절대 의도적으로 내지 않음 |

#### 2-4. REST 스타일 URL: "명사(자원) + 메서드"

```
/studies                  스터디 전체
/studies/1                1번 스터디
/studies/1/applications   1번 스터디의 신청들
/applications/7           7번 신청
/applications/7/approve   7번 신청을 승인하는 "동작"
```
URL은 **무엇을**, 메서드는 **어떻게**를 나타냅니다. `/getStudyList`, `/createStudy` 같은 동사형 URL은 피합니다.

#### 2-5. 데이터베이스와 테이블

DB는 엑셀 시트 여러 장이라고 생각하면 됩니다. 시트 하나가 **테이블**, 한 줄이 **레코드(행)** 입니다.

```
users                     studies
┌────┬──────────┐         ┌────┬───────────────┬──────────┬──────────┬────────────┐
│ id │ nickname │         │ id │ title         │ owner_id │ capacity │ status     │
├────┼──────────┤         ├────┼───────────────┼──────────┼──────────┼────────────┤
│ 1  │ 민수     │◀────────│ 1  │ 알고리즘 스터디 │ 1        │ 4        │ RECRUITING │
│ 2  │ 지영     │         │ 2  │ 토익 900      │ 3        │ 3        │ RECRUITING │
└────┴──────────┘         └────┴───────────────┴──────────┴──────────┴────────────┘
```
`studies.owner_id = 1`은 "users 테이블의 1번(민수)"을 가리킵니다. 이것을 **외래 키(Foreign Key)** 라고 합니다.

#### 2-6. ORM: SQL 대신 파이썬 객체로 DB 다루기

```python
# SQL로 쓰면
SELECT * FROM studies WHERE status = 'RECRUITING';

# SQLAlchemy(ORM)로 쓰면
db.scalars(select(Study).where(Study.status == StudyStatus.RECRUITING))
```
처음에는 SQL을 몰라도 ORM으로 시작할 수 있습니다. 다만 기본 SQL(SELECT, WHERE, JOIN)은 나중에 꼭 익혀 두세요.

#### 2-7. 트랜잭션: 전부 성공하거나, 전부 취소하거나

신청을 **승인**하면 세 가지가 함께 바뀌어야 합니다.

1. 신청 상태: PENDING → APPROVED
2. 멤버 테이블에 한 줄 추가
3. 정원이 찼으면 스터디 상태: RECRUITING → CLOSED

2번까지만 되고 서버가 죽으면 데이터가 꼬입니다. 그래서 **한 트랜잭션**으로 묶고 마지막에 한 번만 `commit()` 합니다. 중간에 에러가 나면 아무것도 저장되지 않습니다.
→ [services/applications.py](../backend/app/services/applications.py)의 `approve()`

---

### 3. 이 프로젝트의 기술 스택

| 도구 | 역할 | 한 줄 설명 |
|---|---|---|
| **Python** | 언어 | 문법이 쉬워 해커톤에 유리 |
| **FastAPI** | 웹 프레임워크 | URL과 함수를 연결, `/docs` 자동 생성 |
| **Pydantic** | 데이터 검증 | "capacity는 2 이상의 정수" 같은 형식 검사를 자동으로 |
| **SQLAlchemy** | ORM | 파이썬 클래스 ↔ DB 테이블 |
| **SQLite** | 데이터베이스 | 파일 하나(`app.db`)로 동작, 설치 불필요 |
| **uvicorn** | 서버 실행기 | FastAPI 앱을 실제로 띄움 |
| **pytest** | 테스트 | API가 규칙대로 동작하는지 자동 확인 |

> 해커톤에서는 **"설치·설정이 가장 적은 조합"** 이 이깁니다. SQLite는 DB 서버를 따로 띄울 필요가 없어서 해커톤에 최적입니다.

---

### 4. 팀원끼리 정해야 하는 것 (개발 시작 전 30분)

백엔드와 프론트가 **동시에** 개발하려면, 서로 기다리지 않도록 "약속"을 먼저 정해야 합니다.
이걸 건너뛰면 해커톤 후반에 "필드 이름이 달라요", "날짜 형식이 안 맞아요"로 시간을 다 씁니다.

#### 4-1. 반드시 합의할 것 ✅

##### ① 기능 범위와 우선순위
"무엇을 만들고, 무엇을 **안** 만들지"부터 정합니다.

| 우선순위 | 이 프로젝트의 예 |
|---|---|
| 필수 (시연에 꼭 필요) | 모집, 신청, 승인, 정원 |
| 있으면 좋음 | 방장 위임, 스터디룸 예약 |
| 안 함 | 로그인, 알림, 채팅, 결제 |

##### ② 인증 방식
이 프로젝트는 **"인증 없음, 요청에 user_id를 담아 누가 요청했는지만 구분"** 으로 정했습니다.
해커톤에서 로그인을 구현하면 반나절이 사라집니다. 시연에 필요 없으면 과감히 빼세요.

##### ③ API 명세 (가장 중요 ⭐)
엔드포인트마다 **메서드, 경로, 요청 body, 응답 예시, 에러 상황**을 표로 정합니다.
이 프로젝트 [README의 API 문서](../README.md#api-문서-swagger)가 바로 그 결과물입니다. 이 프로젝트는 FastAPI가 만든 Swagger 스펙에서 자동 생성합니다 (`backend/scripts/export_openapi.py`).

```
POST /studies/{id}/applications
요청: {"user_id": 5, "message": "저도 할래요"}
응답 201: {"id": 7, "study_id": 1, "user_id": 5, "message": "...", "status": "PENDING", "created_at": "..."}
에러: 404 스터디 없음 / 400 모집 마감 / 409 이미 멤버·중복 신청
```

명세만 정해지면 프론트는 가짜 데이터로 화면을 먼저 만들고, 백엔드는 명세대로 구현하면 됩니다.

##### ④ 데이터 형식 규칙
사소해 보이지만 **가장 많이 부딪히는 부분**입니다.

| 항목 | 이 프로젝트의 결정 | 안 정하면 생기는 문제 |
|---|---|---|
| 필드 이름 표기 | `snake_case` (`owner_id`, `member_count`) | 프론트는 `ownerId`, 백엔드는 `owner_id` |
| 날짜·시간 | `"2026-10-07T14:00:00"`, **한국 시간(KST)** | UTC/KST가 섞여 9시간 차이 |
| 상태값 | 대문자 영어 (`RECRUITING`, `PENDING`) | `"모집중"`, `"recruiting"`이 섞임 |
| 요청자 전달 위치 | GET·DELETE는 쿼리(`?user_id=1`), POST·PATCH는 body | 어디에 넣을지 매번 헷갈림 |
| id 타입 | 정수 | 문자열 `"1"`과 숫자 `1` 비교 실패 |

##### ⑤ 에러 응답 형식
**모든 에러를 같은 모양으로** 보내기로 정합니다. 이 프로젝트는 FastAPI 기본 형식을 그대로 씁니다.

```json
{"detail": "방장만 할 수 있는 작업입니다."}
```
프론트는 `detail`만 꺼내 화면에 띄우면 되므로, 백엔드가 규칙을 추가해도 프론트를 고칠 필요가 없습니다.
메시지 언어(한국어)도 이때 정합니다.

##### ⑥ 연결 방법 (주소, 포트)
| 항목 | 이 프로젝트 |
|---|---|
| 백엔드 주소 | `http://localhost:8000` |
| 프론트 주소 | `http://localhost:5173` |
| 연결 방식 | 프론트가 `/api/...`로 요청 → Vite 프록시가 백엔드로 전달 |
| CORS | 백엔드에서 전체 허용 (해커톤용) |

##### ⑦ 시연 시나리오와 시드 데이터
"심사위원 앞에서 어떤 순서로 무엇을 보여줄지"를 **처음에** 정하면, 그 시나리오에 필요한 기능만 만들게 되어 범위가 줄어듭니다.
이 프로젝트: 모집 → 신청 → 승인 → 정원 변경 → 방장 위임 → 방 예약 ([README 시연 시나리오](../README.md))

##### ⑧ 협업 방식
- Git 브랜치 규칙 (예: 각자 `feat/기능명` 브랜치 → main에 병합)
- 폴더 구조 (`backend/`, `frontend/` 분리 → 서로의 파일을 건드리지 않아 충돌이 적음)
- 명세가 바뀌면 **반드시 팀 채널에 공유**

#### 4-2. 합의 결과를 남기는 템플릿

팀 노션이나 README에 아래를 채워 두세요.

```markdown
## 기능 범위
- 필수:
- 선택:
- 안 함:

## 공통 규칙
- 인증:
- 필드 표기: snake_case
- 날짜 형식: YYYY-MM-DDTHH:MM:SS (KST)
- 에러 형식: {"detail": "한국어 메시지"}
- 백엔드 주소 / 프론트 주소:

## API 명세
| 메서드 | 경로 | 요청 | 응답 | 에러 |
|---|---|---|---|---|

## 시연 시나리오
1.
2.
```

---

### 5. 백엔드 담당이 혼자 해야 하는 것

팀과 합의한 "약속(API 명세)"을 **실제로 동작하게** 만드는 일입니다. 프론트 담당은 신경 쓰지 않아도 되는 영역입니다.

| # | 할 일 | 이 프로젝트에서 | 파일 |
|---|---|---|---|
| 1 | **데이터 모델 설계** | 테이블 6개와 관계 정하기 | [models.py](../backend/app/models.py) |
| 2 | **요청/응답 형식 정의** | 어떤 필드를 받고 돌려줄지, 형식 검증 | [schemas.py](../backend/app/schemas.py) |
| 3 | **비즈니스 규칙 구현** | 권한 검사, 정원 검사, 중복 검사, 시간 겹침 | [services/](../backend/app/services/) |
| 4 | **트랜잭션 처리** | 승인·방장 위임을 한 번에 저장 | `approve()`, `transfer_owner()` |
| 5 | **에러 처리** | 상황별 상태 코드와 메시지 | 모든 service |
| 6 | **API 경로 연결** | URL ↔ 함수 | [routers/](../backend/app/routers/) |
| 7 | **DB 설정** | 연결, 테이블 생성, 초기 데이터 | [database.py](../backend/app/database.py), [main.py](../backend/app/main.py) |
| 8 | **시드 데이터** | 시연용 데이터 한 번에 만들기 | [services/seed.py](../backend/app/services/seed.py) |
| 9 | **테스트** | 규칙이 지켜지는지 자동 확인 | [tests/](../backend/tests/) |
| 10 | **문서화** | `/docs` 확인, README의 API 표 | [README.md](../README.md) |

#### 5-1. 데이터 모델 설계하는 법

**① 명사를 찾는다** → 테이블 후보
> "**사용자**가 **스터디**를 만들고, 다른 사용자가 **신청**하면 방장이 승인해 **멤버**가 된다. 방장은 **스터디룸**을 **예약**한다."

→ User, Study, Application, Member, Room, Reservation

**② 관계를 그린다**

```
User 1 ──── N Study          (한 사용자가 여러 스터디의 방장)
User N ──── N Study          (멤버 관계 → 중간 테이블 Member로 풀기)
Study 1 ──── N Application   (한 스터디에 여러 신청)
Room 1 ──── N Reservation    (한 방에 여러 예약)
Study 1 ──── N Reservation
```

> 💡 **N:N 관계는 중간 테이블로 푼다.** "사용자는 여러 스터디에 속하고, 스터디는 여러 사용자를 가진다" → `Member(study_id, user_id, role)`

**③ 상태가 있는 것은 상태 필드를 둔다**

```
Application:  PENDING ──승인──▶ APPROVED
                 │
                 ├──거절──▶ REJECTED
                 └──취소──▶ CANCELED
```
상태 전이를 그림으로 그려 두면 "PENDING이 아니면 승인 불가" 같은 규칙이 자연스럽게 나옵니다.

**④ 삭제 대신 상태 변경을 고려한다**
신청 취소, 예약 취소를 DB에서 지우지 않고 `CANCELED`로 바꿨습니다. 기록이 남아서 "내 신청 내역"에서 보여줄 수 있습니다.

#### 5-2. 비즈니스 규칙 정리하는 법

기능마다 **"누가 / 언제 / 무엇을 할 수 없는가"** 를 목록으로 만들고, 각각에 상태 코드를 붙입니다.

**예: 신청하기** ([services/applications.py](../backend/app/services/applications.py)의 `apply()`)

| 검사 순서 | 규칙 | 실패 시 |
|---|---|---|
| 1 | 스터디가 존재해야 함 | 404 |
| 2 | 사용자가 존재해야 함 | 404 |
| 3 | 모집 중(RECRUITING)이어야 함 | 400 |
| 4 | 이미 멤버(방장 포함)가 아니어야 함 | 409 |
| 5 | 대기 중인 신청이 없어야 함 | 409 |
| ✅ | 통과하면 PENDING 신청 생성 | 201 |

> 💡 검사 순서는 **존재 여부(404) → 권한(403) → 규칙(400/409)** 이 자연스럽습니다.

#### 5-3. 명세에 없지만 백엔드가 결정해야 하는 것들

명세를 아무리 꼼꼼히 써도 빈틈이 생깁니다. 이 프로젝트에서 백엔드가 직접 결정한 것들입니다.

| 질문 | 결정 |
|---|---|
| 정원을 늘리면 마감된 스터디는? | 다시 RECRUITING으로 |
| 정원이 차서 마감되면 남은 대기 신청은? | 자동으로 REJECTED |
| 거절당한 사람이 다시 신청할 수 있나? | 가능 |
| 14~16시 예약 뒤에 16~18시 예약은 겹치나? | 안 겹침 (맞닿는 건 허용) |
| 취소된 예약도 시간 겹침 검사에 포함하나? | 제외 (CONFIRMED만 검사) |
| 서버를 재시작하면 샘플 방이 또 생기나? | 방이 비어 있을 때만 생성 |

> 이런 결정은 **혼자 정하되, 팀에 공유**하세요. 프론트 화면에 영향을 주는 결정이면 특히 중요합니다.

---

### 6. 코드 읽기: 요청 하나를 끝까지 따라가기

#### 6-1. 폴더 구조와 역할

```
backend/app/
├── main.py          ① 앱 시작점: 앱 생성, CORS, 라우터 등록, 시작 시 테이블 생성
├── database.py      ② DB 연결 설정, 세션, 현재 시간 함수
├── models.py        ③ DB 테이블 정의 (무엇을 저장하나)
├── schemas.py       ④ 요청/응답 형식 정의 (무엇을 주고받나)
├── routers/         ⑤ URL ↔ 함수 연결 (어디로 들어오나)
└── services/        ⑥ 실제 로직과 규칙 (무엇을 하나)
```

**왜 router와 service를 나눴나요?**
- **router**는 "HTTP 접수 창구"입니다. URL, 파라미터, 응답 형식만 다룹니다.
- **service**는 "실제 업무 담당"입니다. 규칙 검사와 DB 작업을 합니다.

나눠 두면 규칙을 고칠 때 service만, URL을 고칠 때 router만 보면 됩니다.

#### 6-2. "신청 승인" 요청 따라가기

프론트에서 방장(민수, id=1)이 4번 신청의 **승인** 버튼을 누르면:

```
POST /applications/4/approve
{"user_id": 1}
```

**① main.py**: 라우터가 등록되어 있어 요청을 받을 준비가 되어 있음
```python
app.include_router(applications.router)
```

**② schemas.py**: body 형식 검사 (Pydantic이 자동으로)
```python
class RequesterBody(BaseModel):
    user_id: int            # user_id가 없거나 정수가 아니면 → 자동으로 422
```

**③ routers/applications.py**: URL과 함수 연결
```python
@router.post("/applications/{application_id}/approve", response_model=schemas.ApplicationOut)
def approve(application_id: int, data: schemas.RequesterBody, db: Session = Depends(get_db)):
    return service.approve(db, application_id, data.user_id)
```
- `{application_id}` → 경로의 `4`가 함수 인자로 들어옴
- `data` → body가 검증된 객체로 들어옴
- `db: Session = Depends(get_db)` → 요청마다 DB 연결을 자동으로 열고 닫아 줌 (**의존성 주입**)
- `response_model` → 응답을 이 형식으로 정리해 보냄

**④ services/applications.py**: 규칙 검사와 저장
```python
def approve(db, application_id, user_id):
    app, study = _pending_for_owner(db, application_id, user_id)   # 404 / 403 / 400 검사
    if member_count(db, study.id) >= study.capacity:
        raise HTTPException(400, "정원이 가득 차 승인할 수 없습니다.")
    # 한 트랜잭션: 상태 변경 + 멤버 생성 + 정원 도달 시 마감
    app.status = ApplicationStatus.APPROVED
    db.add(Member(study_id=study.id, user_id=app.user_id, role=MemberRole.MEMBER))
    db.flush()               # 아직 확정 전, 인원수 계산에 반영되도록 DB에 반영
    sync_status(db, study)   # 정원이 찼으면 CLOSED + 남은 대기 신청 자동 거절
    db.commit()              # ✅ 여기서 한꺼번에 확정
    return app
```
- `raise HTTPException(상태코드, 메시지)` → 즉시 중단하고 `{"detail": 메시지}`로 응답
- 여러 서비스가 함께 쓰는 검사(`get_study`, `require_owner` 등)는 [services/common.py](../backend/app/services/common.py)에 모아 둠

**⑤ 응답**
```json
200 OK
{"id": 4, "study_id": 1, "user_id": 3, "message": "파이썬으로 풀어요", "status": "APPROVED", "created_at": "..."}
```

#### 6-3. 직접 따라 해 보기

1. 서버 실행: `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload`
2. http://localhost:8000/docs 접속 → `POST /seed` → **Try it out** → **Execute**
3. `POST /applications/{application_id}/approve`에서 id `4`, body `{"user_id": 2}` → **403** 확인 (지영은 방장이 아님)
4. body를 `{"user_id": 1}`로 바꿔 다시 → **200**
5. `GET /studies/1`로 인원수가 늘었는지 확인

> `/docs`(Swagger)는 FastAPI가 코드를 읽어 **자동으로** 만들어 줍니다. 프론트 담당에게 이 주소만 알려줘도 API 문서 역할을 합니다.

---

### 7. 실습: 기능 하나 직접 추가하기

**과제: "스터디 탈퇴" 기능** (방장이 아닌 멤버가 스터디에서 나가기)

#### Step 1. 명세부터 정하기
```
DELETE /studies/{study_id}/members/me?user_id=2
응답 204 (본문 없음)
에러: 404 스터디 없음 / 400 멤버가 아님 / 400 방장은 탈퇴 불가(먼저 위임)
부가 효과: 마감 상태였다면 다시 모집중으로
```
> 팀에 공유: "탈퇴 API 추가합니다, 형식은 이렇습니다"

#### Step 2. 규칙을 service에 구현 (`services/studies.py`)
```python
def leave_study(db: Session, study_id: int, user_id: int) -> None:
    study = get_study(db, study_id)                    # 404
    get_user(db, user_id)                              # 404
    member = get_member(db, study_id, user_id)
    if not member:
        raise HTTPException(400, "스터디 멤버가 아닙니다.")
    if member.role == MemberRole.OWNER:
        raise HTTPException(400, "방장은 탈퇴할 수 없습니다. 먼저 방장을 위임하세요.")
    db.delete(member)
    db.flush()
    sync_status(db, study)                             # 인원이 줄었으니 상태 재계산
    db.commit()
```

#### Step 3. router에 경로 연결 (`routers/studies.py`)
```python
@router.delete("/{study_id}/members/me", status_code=204)
def leave_study(study_id: int, user_id: int = Query(), db: Session = Depends(get_db)):
    service.leave_study(db, study_id, user_id)
```
(`from fastapi import Query`를 import에 추가)

#### Step 4. /docs에서 확인
- 시드 후 `DELETE /studies/1/members/me?user_id=2` → 204
- 같은 요청 다시 → 400 (이미 멤버 아님)
- `user_id=1`(방장) → 400

#### Step 5. 테스트 추가 (`tests/test_users_studies.py`)
```python
def test_leave_study(client, make_user, make_study, join):
    a, b = make_user("a"), make_user("b")
    sid = make_study(a, capacity=2)
    join(sid, a, b)                                           # 2/2 → CLOSED
    assert client.delete(f"/studies/{sid}/members/me", params={"user_id": a}).status_code == 400
    assert client.delete(f"/studies/{sid}/members/me", params={"user_id": b}).status_code == 204
    assert client.get(f"/studies/{sid}").json()["status"] == "RECRUITING"
```
```bash
cd backend && pytest
```

#### Step 6. 문서 갱신
README의 API 표에 한 줄 추가하고, 프론트 담당에게 알립니다.

> 이 6단계(**명세 → service → router → 수동 확인 → 테스트 → 문서**)가 백엔드 기능 개발의 기본 순서입니다.

---

### 8. 테스트: 왜, 어떻게

#### 왜 필요한가요?
규칙이 10개를 넘으면 하나를 고칠 때 다른 것이 깨지기 쉽습니다. 매번 Swagger로 수십 번 클릭할 수는 없으니, **코드로 확인을 자동화**합니다.

#### 이 프로젝트의 테스트 구조
```
backend/tests/
├── conftest.py               # 공통 준비물: 테스트용 임시 DB, client, 사용자/스터디 생성 도우미
├── test_users_studies.py     # 사용자, 스터디, 정원, 방장 위임
├── test_applications.py      # 신청, 취소, 승인, 거절
└── test_rooms.py             # 방, 예약, 시드
```

- 테스트는 **실제 DB(`app.db`)를 건드리지 않고** 임시 DB를 씁니다 (conftest.py에서 환경변수로 교체).
- 테스트 하나하나가 깨끗한 DB에서 시작합니다.

#### 무엇을 테스트하나요?
**성공 케이스보다 실패 케이스가 중요합니다.** 규칙 표(5-2)의 각 줄이 테스트 한 줄이 됩니다.

```python
# 방장이 아니면 403
assert client.post(f"/applications/{ap}/approve", json={"user_id": b}).status_code == 403
# 정원이 차면 자동 마감
assert client.get(f"/studies/{sid}").json()["status"] == "CLOSED"
```

```bash
cd backend && pytest        # 전체 실행
pytest -k approve           # 이름에 approve가 들어간 테스트만
pytest -x                   # 처음 실패하는 곳에서 멈춤
```

---

### 9. 디버깅 가이드

#### 막혔을 때 보는 순서
1. **uvicorn 터미널 로그**: 에러가 나면 여기에 빨간 Traceback이 찍힙니다. **맨 아래 줄**부터 읽으세요
2. **/docs에서 같은 요청 직접 보내기**: 프론트 문제인지 백엔드 문제인지 구분
3. **`print()` 찍어 보기**: 가장 원시적이지만 해커톤에서 가장 빠름

#### 자주 만나는 문제

| 증상 | 원인 | 해결 |
|---|---|---|
| `Address already in use` | 8000 포트에 서버가 이미 떠 있음 | 기존 터미널에서 Ctrl+C, 또는 `--port 8001` |
| `ModuleNotFoundError: fastapi` | 가상환경이 꺼져 있음 | `source .venv/bin/activate` (프롬프트에 `(.venv)` 확인) |
| `ModuleNotFoundError: app` | 실행 위치가 틀림 | `backend/` 폴더 안에서 실행 |
| 422 Unprocessable Entity | 요청 형식이 schema와 다름 | 응답 `detail`에 어느 필드가 틀렸는지 나옴 |
| 500 Internal Server Error | **코드 버그** | uvicorn 로그의 Traceback 확인 |
| 모델에 컬럼을 추가했는데 `no such column` 에러 | 기존 테이블은 자동으로 바뀌지 않음 | `backend/app.db` 삭제 후 재시작 (데이터는 `/seed`로 복구) |
| 시간이 9시간 어긋남 | UTC와 KST 혼용 | 이 프로젝트는 `now_kst()`로 통일 |
| 코드를 고쳤는데 반영 안 됨 | `--reload` 없이 실행 | `uvicorn app.main:app --reload` |

---

### 10. 해커톤 당일 체크리스트

#### 시작 직후 (팀 전체, 30분)
- [ ] 기능 범위·우선순위 결정 (필수 / 선택 / 안 함)
- [ ] 시연 시나리오 초안
- [ ] API 명세 표 작성 (필드 이름, 날짜 형식, 상태값, 에러 형식 포함)
- [ ] 저장소 생성, `backend/` `frontend/` 폴더 분리

#### 백엔드 1시간 안에
- [ ] 서버 뜨고 `/docs` 열림
- [ ] CORS 설정
- [ ] 모델 작성, 테이블 자동 생성
- [ ] **가장 단순한 GET 하나**를 프론트와 연결해 확인 (연결 문제는 빨리 발견할수록 좋음)

#### 개발 중
- [ ] 기능 하나 끝날 때마다 `/docs`에서 확인 → 커밋
- [ ] 명세가 바뀌면 즉시 팀에 공유
- [ ] 어려운 규칙은 테스트로 고정

#### 시연 2시간 전
- [ ] `/seed` 엔드포인트 완성 (데이터를 깨끗하게 되돌리기)
- [ ] 시연 시나리오를 처음부터 끝까지 리허설
- [ ] README에 실행 방법과 API 표 정리
- [ ] 새 기능 추가 중단, 버그 수정만

#### 하지 말 것
- ❌ 로그인/회원가입 (시연에 필수가 아니면)
- ❌ DB 서버 설치 (PostgreSQL, MySQL) → SQLite로 충분
- ❌ 처음부터 완벽한 구조 → 동작하는 것 먼저, 정리는 나중에
- ❌ 프론트와 상의 없이 필드 이름 변경

---

### 부록. 용어집

| 용어 | 뜻 |
|---|---|
| API | 프로그램끼리 대화하는 약속. 여기서는 "이 URL로 이렇게 요청하면 이렇게 응답한다" |
| 엔드포인트 | 메서드 + 경로 하나 (예: `POST /studies`) |
| JSON | `{"key": "value"}` 형태의 데이터 형식. 프론트-백엔드 대화의 공용어 |
| 쿼리 파라미터 | URL 뒤 `?user_id=1&status=PENDING` 부분 |
| 경로 파라미터 | URL 안의 변수 `/studies/{id}` 의 `id` |
| 요청 본문(body) | POST/PATCH에 담아 보내는 JSON |
| 스키마 | 데이터의 모양(필드와 타입) 정의 |
| ORM | DB 테이블을 프로그래밍 언어의 객체로 다루게 해 주는 도구 |
| 외래 키 | 다른 테이블의 행을 가리키는 필드 (`owner_id` → users.id) |
| 트랜잭션 | 여러 DB 작업을 "전부 성공 또는 전부 취소"로 묶는 단위 |
| commit | 트랜잭션의 변경을 DB에 확정 |
| 의존성 주입 | 함수에 필요한 것(DB 세션 등)을 프레임워크가 알아서 넣어 주는 것 (`Depends`) |
| CORS | 다른 출처(포트)에서 오는 요청을 브라우저가 막는 규칙. 백엔드가 허용해 줘야 함 |
| 시드 데이터 | 개발·시연용으로 미리 넣어 두는 샘플 데이터 |
| 마이그레이션 | 운영 중인 DB의 테이블 구조를 데이터 손실 없이 바꾸는 작업 (해커톤에서는 생략) |
| Swagger (`/docs`) | API 문서 + 테스트 화면. FastAPI가 자동 생성 |

---

## 2부. 프론트엔드

이 저장소의 `frontend/`를 **처음부터 직접 다시 만들어 보면서** React와 API 연동을 익힙니다.
완성된 코드는 정답지로 두고, 아래 단계를 따라 빈 폴더에서부터 만들어 보세요.

- 대상: HTML/CSS는 조금 다뤄 봤고, JavaScript 기초는 아는데 React와 API 연동은 처음인 사람
- 예상 소요: 단계당 30분~1시간, 전체 1~2일
- 백엔드는 이미 완성되어 있으므로 **프론트만** 신경 쓰면 됩니다 (백엔드 개념은 1부 참고)

### 0. 큰 그림 먼저

#### 프론트엔드가 하는 일은 딱 세 가지

1. **데이터 가져오기**: 백엔드 API를 호출(fetch)해서 JSON을 받는다
2. **화면 그리기**: 받은 데이터를 상태(state)에 넣고, React가 화면을 그린다
3. **사용자 행동 처리**: 버튼·폼 입력 → API 호출 → 성공하면 데이터를 다시 가져와 화면 갱신

이 프로젝트의 모든 화면은 이 세 가지의 반복입니다.

#### 요청이 흘러가는 길

```
[사용자 클릭]
   ↓
pages/StudyDetailPage.jsx      화면 컴포넌트: "승인 버튼이 눌렸다"
   ↓ approveApplication(id, userId)
api/applications.js            어떤 URL·메서드·body로 보낼지
   ↓ request("/applications/4/approve", { method: "POST", body })
api/client.js                  fetch 실행, JSON 변환, 에러 처리
   ↓ HTTP
backend (FastAPI)              검증 후 DB 반영, JSON 응답
   ↓
화면 컴포넌트가 성공 → toast 표시 → 데이터 다시 불러오기 → 화면 갱신
```

> 핵심 원칙: **화면 컴포넌트는 fetch를 직접 부르지 않는다.** URL과 HTTP 세부사항은 `api/` 폴더에만 둔다.
> 그래야 백엔드 주소나 경로가 바뀌어도 고칠 곳이 한 군데뿐입니다.

#### 완성된 폴더 구조

```
frontend/src/
├── main.jsx              # 앱 시작점
├── App.jsx               # 주소(URL) → 어떤 페이지를 보여줄지
├── api/                  # 백엔드 통신 전담
├── context/              # 여러 화면이 함께 쓰는 상태 (현재 사용자, 알림)
├── components/           # 여러 곳에서 재사용하는 작은 UI 조각
├── pages/                # 주소 하나당 화면 하나
├── utils/                # 날짜 포맷 같은 순수 함수
└── index.css
```

---

### 1. 시작 전 체크리스트

#### 알고 있어야 하는 JavaScript 문법

이 프로젝트에서 실제로 쓰인 것만 골랐습니다. 모르는 게 있으면 MDN에서 먼저 찾아보세요.

| 문법 | 예시 | 프로젝트에서 쓰인 곳 |
|---|---|---|
| 화살표 함수 | `(a) => a + 1` | 거의 모든 곳 |
| 구조 분해 | `const { users, notify } = useApp()` | 모든 페이지 상단 |
| 스프레드 | `{ ...form, title: "새 제목" }` | 폼 상태 업데이트 |
| 배열 메서드 | `map`, `filter`, `find`, `some` | 목록 렌더링, 권한 판단 |
| 옵셔널 체이닝 | `currentUser?.id` | 사용자가 없을 수도 있을 때 |
| `??` 연산자 | `x ?? "기본값"` | null/undefined일 때 기본값 |
| 템플릿 문자열 | `` `/studies/${id}` `` | URL 만들기 |
| `async` / `await` | `const data = await getStudies()` | 모든 API 호출 |
| `try` / `catch` | API 에러 처리 | 모든 액션 |
| `import` / `export` | 파일 간 함수 공유 | 모든 파일 |
| `Promise.all` | 여러 요청을 동시에 | 상세 페이지 로딩 |

#### 설치 확인

```bash
node --version   # v18 이상 (이 프로젝트는 v22로 확인)
npm --version
```

#### 백엔드 띄워두기

프론트를 만드는 내내 백엔드가 켜져 있어야 합니다.

```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload
```

http://localhost:8000/docs 를 열어 **Swagger에서 API를 먼저 직접 눌러 보세요.**
어떤 요청을 보내면 어떤 JSON이 오는지 눈으로 확인하는 것이 프론트 개발의 첫걸음입니다.
`POST /seed`를 한 번 실행해 두면 데이터가 채워집니다.

---

### 2. React 핵심 개념 7가지 (이 프로젝트 기준)

개념을 다 외우고 시작할 필요는 없습니다. 단계별 실습에서 하나씩 등장하니, 막힐 때 다시 와서 보세요.

#### ① 컴포넌트: 화면 조각을 만드는 함수

```jsx
function StatusBadge({ status }) {           // props를 받아서
  return <span className="badge">{status}</span>;   // JSX를 돌려준다
}

<StatusBadge status="RECRUITING" />          // 이렇게 사용
```
→ [components/StatusBadge.jsx](../frontend/src/components/StatusBadge.jsx)

#### ② state: 바뀌면 화면이 다시 그려지는 값

```jsx
const [studies, setStudies] = useState([]);  // [현재값, 바꾸는 함수] = useState(초기값)
setStudies(newList);                         // 이걸 호출해야 화면이 갱신됨
```
일반 변수(`let x`)를 바꾸면 화면은 그대로입니다. **화면에 영향을 주는 값은 state**에 넣으세요.

#### ③ useEffect: "화면이 그려진 뒤에" 할 일 (보통 데이터 불러오기)

```jsx
useEffect(() => {
  load();               // API 호출
}, [status]);           // status가 바뀔 때마다 다시 실행
```
- 의존성 배열 `[]`가 비어 있으면 처음 한 번만 실행됩니다
- 배열에 넣은 값이 바뀌면 다시 실행됩니다 (예: 필터 탭 변경 → 목록 재조회)

#### ④ useCallback: 함수를 기억해 두기

`useEffect`의 의존성에 함수를 넣으면, 렌더링마다 함수가 새로 만들어져 무한 루프가 날 수 있습니다.
`useCallback`으로 감싸면 의존 값이 바뀔 때만 새 함수가 됩니다.

```jsx
const load = useCallback(async () => { ... }, [status]);
useEffect(() => { load(); }, [load]);
```
→ [pages/StudyListPage.jsx](../frontend/src/pages/StudyListPage.jsx)의 패턴. 처음엔 "데이터 불러오는 함수는 이렇게 쓴다"고 외워도 충분합니다.

#### ⑤ 제어 컴포넌트: input 값을 state로 관리

```jsx
const [nickname, setNickname] = useState("");
<input value={nickname} onChange={(e) => setNickname(e.target.value)} />
```
입력값이 항상 state에 들어 있으니 제출할 때 그대로 API에 넘기면 됩니다.

#### ⑥ 조건부 렌더링 / 목록 렌더링

```jsx
{isOwner && <OwnerPanel />}                              // 조건이 참일 때만 표시
{loading ? <p>불러오는 중...</p> : <List />}             // 둘 중 하나
{studies.map((s) => <li key={s.id}>{s.title}</li>)}      // 배열 → 요소들 (key 필수!)
```

#### ⑦ Context: 여러 화면이 함께 쓰는 전역 상태

"현재 사용자"는 헤더, 목록, 상세, 내 신청 화면 **모두**가 알아야 합니다.
props로 일일이 넘기는 대신 Context에 두고 어디서든 꺼내 씁니다.

```jsx
const { currentUser, notify } = useApp();
```
→ [context/AppContext.jsx](../frontend/src/context/AppContext.jsx)

---

### 3. 단계별 실습

각 단계는 **목표 → 만들 파일 → 핵심 코드 → 확인 방법 → 자주 하는 실수** 순서입니다.
한 단계를 끝낼 때마다 브라우저에서 동작을 확인하고 git commit 하는 습관을 들이세요.

#### Step 1. Vite로 React 프로젝트 만들기

**목표:** 브라우저에 "Hello" 띄우기

```bash
npm create vite@latest frontend-practice -- --template react
cd frontend-practice
npm install
npm install react-router-dom
npm run dev          # http://localhost:5173
```

생성된 파일 중 `src/App.jsx`만 남기고 내용을 지운 뒤:

```jsx
export default function App() {
  return <h1>스터디 모집</h1>;
}
```

**확인:** 저장하면 브라우저가 자동으로 새로고침되나요? (HMR)

**자주 하는 실수:** 컴포넌트 이름을 소문자로 시작 (`app`) → React는 대문자로 시작해야 컴포넌트로 인식합니다.

---

#### Step 2. API 클라이언트 만들고 백엔드와 처음 연결하기 ⭐ 가장 중요

**목표:** 프론트에서 `GET /users`를 호출해 콘솔에 찍기

**만들 파일:** `vite.config.js`(프록시 추가), `src/api/client.js`, `src/api/users.js`

먼저 **프록시**를 설정합니다. 브라우저가 백엔드(8000)를 직접 부르지 않고, 지금 열려 있는 프론트 서버(5173)에 `/api/...`로 요청하면 Vite가 대신 백엔드로 전달해 줍니다.

```
브라우저 ──/api/users──▶ Vite(5173) ──/users──▶ FastAPI(8000)
```

```js
// vite.config.js
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),   // /api/users → /users
      },
    },
  },
});
```

> **왜 프록시를 쓰나요?** 브라우저에서 `http://localhost:8000`을 직접 부르면 두 가지 문제가 생길 수 있습니다.
> ① 포트가 다르면 출처가 달라서 **CORS** 설정이 필요합니다.
> ② WSL·원격 개발처럼 서버와 브라우저가 다른 환경에 있으면 8000 포트가 브라우저에서 **안 보일 수 있습니다.**
> 이 프로젝트도 실제로 Windows 브라우저에서 "서버에 연결할 수 없습니다"가 떠서 프록시로 바꿨습니다.

```js
// src/api/client.js: 처음엔 이 정도로 시작
// (Vite는 VITE_ 로 시작하는 환경 변수만 코드에 노출함. 비워두면 "/api" 프록시 사용)
export const API_URL = import.meta.env.VITE_API_URL || "/api";

export async function request(path, { method = "GET", body, query } = {}) {
  const url = new URL(API_URL + path, window.location.origin);   // "/api" + "/users"
  if (query) Object.entries(query).forEach(([k, v]) => v != null && url.searchParams.set(k, v));

  const res = await fetch(url, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail);   // FastAPI 에러는 {"detail": "..."} 형태
  return data;
}
```

```js
// src/api/users.js
import { request } from "./client";
export const getUsers = () => request("/users");
export const createUser = (nickname) => request("/users", { method: "POST", body: { nickname } });
```

App에서 시험 호출:

```jsx
import { useEffect } from "react";
import { getUsers } from "./api/users";

export default function App() {
  useEffect(() => { getUsers().then(console.log); }, []);
  return <h1>스터디 모집</h1>;
}
```

**확인:**
1. 브라우저 개발자도구(F12) → **Console** 탭에 사용자 배열이 찍히나요?
2. **Network** 탭에서 `users` 요청을 클릭해 Headers / Response를 보세요. 요청 주소가 `5173/api/users`인지 확인하세요. **이 탭과 친해지는 것이 API 연동 디버깅의 전부입니다.**
3. 브라우저 주소창에 `http://localhost:5173/api/health`를 직접 쳐 보세요. `{"status":"ok"}`가 나오면 프록시가 동작하는 것입니다.

**자주 하는 실수:**
- `vite.config.js`나 `.env`를 고친 뒤 반영이 안 됨 → `npm run dev`를 재시작하세요
- `/api/...` 요청이 **500 / 502** → 프록시는 동작하지만 백엔드(8000)가 꺼져 있음
- `.env`에 `VITE_API_URL=http://localhost:8000`을 넣어 직접 호출했는데 **CORS 에러**나 `Failed to fetch` → 백엔드 CORS 설정이나 포트 접근 문제. 프록시 방식으로 돌아가세요
- 콘솔에 같은 요청이 **두 번** 찍힘 → 개발 모드의 `StrictMode`가 일부러 effect를 두 번 실행합니다. 버그 아님

**더 나아가기:** 완성본 [api/client.js](../frontend/src/api/client.js)는 여기에 ① 서버가 꺼졌을 때 메시지, ② 422 검증 에러 배열 → 문자열 변환, ③ `status` 코드를 담은 `ApiError`를 추가했습니다. 비교해 보세요.

---

#### Step 3. 라우터와 페이지 뼈대

**목표:** 상단 메뉴로 페이지 이동하기

**만들 파일:** `src/main.jsx`, `src/App.jsx`, `src/components/Header.jsx`, `src/pages/*.jsx` (빈 페이지 4개)

```jsx
// main.jsx
<BrowserRouter>
  <App />
</BrowserRouter>
```

```jsx
// App.jsx
<Header />
<Routes>
  <Route path="/" element={<StudyListPage />} />
  <Route path="/studies/:id" element={<StudyDetailPage />} />   {/* :id는 변수 */}
  <Route path="/rooms" element={<RoomsPage />} />
  <Route path="/me" element={<MyPage />} />
</Routes>
```

```jsx
// Header.jsx: <a href> 대신 NavLink (페이지 새로고침 없이 이동 + 현재 메뉴에 active 클래스)
<NavLink to="/" end>스터디</NavLink>
<NavLink to="/rooms">스터디룸</NavLink>
```

**확인:** 메뉴를 눌러도 페이지 전체가 새로고침되지 않고, 주소창 URL은 바뀌나요?

**자주 하는 실수:** `<a href="/rooms">` 사용 → 전체 새로고침이 일어나 state가 날아갑니다.

---

#### Step 4. 현재 사용자 Context (로그인 대신)

**목표:** 헤더 드롭다운에서 사용자를 고르면 모든 페이지가 그 사용자를 안다

**만들 파일:** `src/context/AppContext.jsx`

```jsx
const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [users, setUsers] = useState([]);
  const [currentUserId, setCurrentUserId] = useState(null);

  useEffect(() => { getUsers().then(setUsers); }, []);

  const currentUser = users.find((u) => u.id === currentUserId) ?? null;
  return (
    <AppContext.Provider value={{ users, currentUser, setCurrentUserId }}>
      {children}
    </AppContext.Provider>
  );
}

export const useApp = () => useContext(AppContext);
```

`main.jsx`에서 `<App />`을 `<AppProvider>`로 감싸고, Header에 `<select>`를 만들어 `setCurrentUserId`를 연결합니다.

**확인:** 사용자를 바꾼 뒤 다른 페이지로 이동해도 선택이 유지되나요?

**더 나아가기:**
- 새로고침해도 유지되게 `localStorage`에 저장하기 (완성본 참고)
- `notify(message)` 함수를 Context에 추가해 **toast 알림**을 전역으로 띄우기 → [components/Toast.jsx](../frontend/src/components/Toast.jsx)

---

#### Step 5. 스터디 목록: 데이터 불러와서 그리기

**목표:** `GET /studies` 결과를 카드로 보여주고, 탭으로 상태 필터

**만들 파일:** `src/api/studies.js`, `src/pages/StudyListPage.jsx`

데이터를 불러오는 화면의 **표준 패턴**입니다. 이후 모든 페이지가 이 모양입니다.

```jsx
const [status, setStatus] = useState("");       // 필터
const [studies, setStudies] = useState([]);     // 데이터
const [loading, setLoading] = useState(true);   // 로딩 여부

const load = useCallback(async () => {
  setLoading(true);
  try {
    setStudies(await getStudies(status));
  } catch (e) {
    notifyError(e);
  } finally {
    setLoading(false);
  }
}, [status]);

useEffect(() => { load(); }, [load]);           // status가 바뀌면 자동 재조회
```

렌더링은 **로딩 중 / 비어 있음 / 데이터 있음** 세 경우를 모두 처리합니다.

```jsx
{loading ? <p>불러오는 중...</p>
  : studies.length === 0 ? <p>스터디가 없습니다.</p>
  : <ul>{studies.map((s) => <li key={s.id}>...</li>)}</ul>}
```

**확인:** "모집중" 탭을 누르면 Network 탭에 `/studies?status=RECRUITING` 요청이 보이나요?

**자주 하는 실수:**
- `key`를 빠뜨림 → 콘솔 경고. 배열 index 말고 **고유한 id**를 쓰세요
- `useEffect` 안에서 바로 `async` 함수를 만듦 (`useEffect(async () => ...)`) → effect는 Promise를 반환하면 안 됩니다

---

#### Step 6. 폼으로 데이터 만들기: 모집 글 등록

**목표:** 제목·설명·정원을 입력해 `POST /studies`

```jsx
const [form, setForm] = useState({ title: "", description: "", capacity: 4 });

const handleCreate = async (e) => {
  e.preventDefault();                                   // form 기본 동작(새로고침) 막기
  try {
    await createStudy({ ...form, capacity: Number(form.capacity), owner_id: currentUser.id });
    notify("등록되었습니다.");
    setForm({ title: "", description: "", capacity: 4 }); // 폼 비우기
    load();                                              // ⭐ 목록 다시 불러오기
  } catch (e) {
    notifyError(e);
  }
};

<input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
```

**확인:**
- 정원에 1을 넣고 HTML `min` 속성을 개발자도구로 지운 뒤 제출하면 → 백엔드의 **422** 에러가 toast로 나오나요?
- 등록 후 목록에 바로 나타나나요?

**자주 하는 실수:**
- `e.preventDefault()`를 빠뜨림 → 페이지 전체가 새로고침됩니다
- `<input type="number">`의 값은 **문자열**입니다 → `Number()`로 변환
- 등록 후 `load()`를 안 해서 목록이 안 바뀜

> 💡 **"액션 후 다시 불러오기"** 패턴: 서버가 계산하는 값(인원수, 상태 자동 변경 등)이 많을 때는 프론트에서 직접 계산하지 말고 **다시 조회**하는 게 가장 안전하고 간단합니다.

---

#### Step 7. 상세 페이지: URL 파라미터와 여러 요청 동시에

**목표:** `/studies/1`에서 스터디 정보 + 멤버 + 예약을 함께 보여주기

```jsx
const { id } = useParams();                        // URL의 :id

const [s, r, rooms] = await Promise.all([          // 세 요청을 동시에 → 빠름
  getStudy(id),
  getStudyReservations(id),
  getRooms(),
]);
```

목록 카드는 `<Link to={`/studies/${s.id}`}>`로 감쌉니다.

**확인:** 없는 id(`/studies/999`)로 접속하면 404 메시지가 화면에 나오나요?

---

#### Step 8. 역할에 따라 다른 화면: 신청과 승인

**목표:** 같은 페이지인데 **누가 보느냐**에 따라 다른 UI

```jsx
const me = currentUser?.id;
const isOwner = me === study.owner_id;
const isMember = study.members.some((m) => m.user_id === me);

{!isMember && <ApplyForm />}       {/* 멤버가 아니면: 신청 폼 */}
{isOwner && <OwnerPanel />}        {/* 방장이면: 승인/거절, 정원, 위임 */}
```

액션 버튼이 많아지면 **공통 처리 함수**를 하나 만들어 반복을 줄입니다.

```jsx
const run = async (fn, message) => {
  try {
    await fn();
    notify(message);
    await load();          // 다시 불러오기
    return true;
  } catch (e) {
    notifyError(e);
    return false;
  }
};

<button onClick={() => run(() => approveApplication(a.id, me), "승인했습니다.")}>승인</button>
```

**확인 (시드 데이터 기준):**
1. 사용자 `도윤`으로 알고리즘 스터디에 신청
2. 사용자 `민수`(방장)로 바꾸면 방장 패널이 나타나고 도윤의 신청이 보이나요?
3. 정원까지 승인하면 상태 뱃지가 "마감"으로 바뀌나요? (서버가 바꾼 것을 다시 불러와 보여주는 것)

**자주 하는 실수:**
- `onClick={approve(a.id)}` → 렌더링할 때 **즉시 실행**됩니다. 반드시 `onClick={() => approve(a.id)}`
- 프론트에서만 권한을 숨기고 안심하기 → 화면은 편의일 뿐, 진짜 검사는 백엔드(403)가 합니다. Swagger로 다른 user_id를 넣어 직접 확인해 보세요

---

#### Step 9. 정원 변경·방장 위임·예약: 에러를 UX로

**목표:** 백엔드 규칙 위반(400/403/409)을 사용자에게 친절하게 보여주기

예약 폼에서 날짜와 시간 입력을 합쳐 백엔드 형식으로 만드는 부분이 포인트입니다.

```jsx
// <input type="date"> → "2026-10-07", <input type="time"> → "14:00"
start_at: `${form.date}T${form.start}:00`     // → "2026-10-07T14:00:00"
```

**확인:**
- 이미 예약된 시간과 겹치게 예약 → "해당 시간에 이미 예약이 있습니다" (409)
- 현재 인원보다 작은 정원 → 400 메시지
- 방장을 넘긴 뒤 이전 방장 화면에서 방장 패널이 사라지나요?

> 💡 에러 메시지를 프론트에서 새로 만들지 않고 **백엔드의 `detail`을 그대로 보여주는** 구조라서, 규칙이 추가되어도 프론트 코드를 고칠 필요가 없습니다.

---

#### Step 10. 마무리: 스타일과 반응형

**목표:** 해커톤 시연에서 보기 좋게

- CSS 변수(`:root { --primary: ... }`)로 색을 한 곳에서 관리 → [index.css](../frontend/src/index.css)
- 상태별 색 뱃지: `className={`badge badge-${status.toLowerCase()}`}`
- 2단 레이아웃은 `display: grid`, 좁은 화면에서는 `@media (max-width: 760px)`로 1단
- 개발자도구의 **기기 모드**(Ctrl+Shift+M)로 휴대폰 화면 확인

---

### 4. 디버깅 가이드: 막혔을 때 보는 순서

1. **Console 탭**: 빨간 에러가 있나? 메시지를 그대로 검색해 본다
2. **Network 탭**: 요청이 나갔나? 상태 코드는? Response 내용은?
3. **Swagger(`/docs`)**: 같은 요청을 직접 보내 본다 → 되면 프론트 문제, 안 되면 요청 내용 문제

| 증상 | 원인 | 해결 |
|---|---|---|
| "서버에 연결할 수 없습니다" | 브라우저가 API 주소에 닿지 못함 | `.env`의 `VITE_API_URL`을 비워 프록시 사용, `npm run dev` 재시작 |
| `/api/...`가 500·502 | 프록시는 OK, 백엔드가 꺼짐 | uvicorn 실행 확인 (`localhost:5173/api/health`로 점검) |
| CORS 에러 | 백엔드를 직접 호출하는데 출처가 허용되지 않음 | 프록시 사용, 또는 백엔드 CORS 설정 확인 |
| 422 Unprocessable | body 형식·타입이 스키마와 다름 | Network → Payload와 `/docs`의 스키마 비교 (숫자를 문자열로 보내는 경우가 흔함) |
| 403 | 요청한 `user_id`가 방장/본인이 아님 | 헤더의 현재 사용자 확인 |
| 화면이 안 바뀜 | state를 안 바꿨거나 재조회를 안 함 | `setXxx` 호출, 액션 후 `load()` 확인 |
| 무한 요청 | `useEffect` 의존성에 매번 새로 만들어지는 함수·객체 | `useCallback`, 의존성 배열 점검 |
| `.env` 수정이 반영 안 됨 | dev 서버 재시작 필요 | `npm run dev` 재실행 |

---

### 5. 연습 과제 (난이도 순)

완성본을 이해했다면 직접 기능을 붙여 보세요.

1. ⭐ 스터디 목록에 **제목 검색창** 추가 (프론트에서 `filter`만으로)
2. ⭐ 로딩 중일 때 버튼을 `disabled`로 만들어 **중복 클릭 방지**
3. ⭐⭐ 상세 페이지의 `OwnerPanel`, `ReservationForm`을 **별도 파일로 분리**
4. ⭐⭐ 반복되는 "로딩/에러/데이터" 패턴을 **커스텀 훅** `useAsync(fn, deps)`로 추출
5. ⭐⭐ 스터디룸 페이지를 **시간표 그리드**(9시~22시 칸에 색칠)로 바꾸기
6. ⭐⭐⭐ 데이터 관리를 **TanStack Query**로 교체해 보고, 수동 `load()`와 비교
7. ⭐⭐⭐ 프로젝트를 **TypeScript**로 전환 (`/docs`의 스키마를 보고 타입 정의)

---

### 6. 해커톤 실전 팁

- **API 명세부터 합의:** 백엔드와 "경로, 요청 body, 응답 JSON 예시"를 먼저 정하면 동시에 개발할 수 있습니다 (이 프로젝트 README의 API 표처럼)
- **백엔드가 아직 없으면:** `api/*.js` 함수가 가짜 데이터를 반환하게 해 두고 화면부터 만듭니다. api 레이어를 분리해 둔 덕분에 나중에 그 파일만 바꾸면 됩니다
- **시드 버튼은 필수:** 시연 직전에 데이터를 깨끗하게 되돌릴 수 있어야 합니다
- **에러 메시지는 서버가 주는 걸 그대로:** 프론트에서 규칙을 이중으로 구현하지 마세요
- **시연 시나리오를 미리 클릭해 보기:** README의 "화면 시연 시나리오"처럼 순서를 정해 두고 리허설하세요

---

### 7. 용어집

| 용어 | 뜻 |
|---|---|
| SPA | 페이지 이동 시 HTML 전체를 새로 받지 않고 JS가 화면만 바꾸는 앱 |
| 컴포넌트 | 화면 조각을 반환하는 함수 |
| props | 부모가 자식 컴포넌트에 넘기는 값 |
| state | 바뀌면 화면이 다시 그려지는 값 |
| 렌더링 | 컴포넌트 함수를 실행해 화면을 그리는 것 |
| 훅(Hook) | `use`로 시작하는 React 함수 (`useState`, `useEffect` 등) |
| CORS | 다른 출처(포트가 달라도 다른 출처)로의 요청을 브라우저가 막는 보안 규칙 |
| 환경 변수 | 코드 밖(`.env`)에 두는 설정값. 서버 주소처럼 환경마다 다른 값 |
| HMR | 저장하면 새로고침 없이 바뀐 부분만 반영되는 개발 기능 |
| 상태 코드 | 200 성공, 201 생성됨, 400 잘못된 요청, 403 권한 없음, 404 없음, 409 충돌, 422 형식 오류 |
