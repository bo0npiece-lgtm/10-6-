# 백엔드 길라잡이: 처음 시작하는 사람을 위한 안내서

백엔드를 **전혀 모르는 사람**이 이 프로젝트(스터디 모집 서비스)를 예시로 백엔드 개발을 이해하고, 해커톤에서 백엔드 역할을 맡을 수 있도록 돕는 문서입니다.

- 1~3장: 백엔드가 무엇이고 어떤 개념이 필요한지
- 4장: **팀원끼리 정해야 하는 것** (개발 시작 전에 합의)
- 5장: **백엔드 담당이 혼자 해야 하는 것**
- 6장: 이 프로젝트 코드 읽기 (요청 하나를 끝까지 따라가기)
- 7장: 기능 하나를 직접 추가해 보는 실습
- 8~10장: 테스트, 디버깅, 해커톤 당일 체크리스트

> 프론트엔드 쪽은 [프론트엔드 길라잡이](frontend-guide.md)를 보세요.

---

## 1. 백엔드는 무슨 일을 하나요?

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

## 2. 꼭 알아야 할 기본 개념

### 2-1. HTTP 요청과 응답

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

### 2-2. HTTP 메서드: 무엇을 하려는지

| 메서드 | 의미 | 이 프로젝트 예시 |
|---|---|---|
| `GET` | 조회 (데이터를 바꾸지 않음) | `GET /studies` 스터디 목록 |
| `POST` | 생성 / 동작 실행 | `POST /studies` 모집 글 생성, `POST /applications/4/approve` 승인 |
| `PATCH` | 일부 수정 | `PATCH /studies/1/capacity` 정원만 변경 |
| `DELETE` | 삭제 / 취소 | `DELETE /applications/7` 신청 취소 |

### 2-3. 상태 코드: 결과가 어땠는지

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

### 2-4. REST 스타일 URL: "명사(자원) + 메서드"

```
/studies                  스터디 전체
/studies/1                1번 스터디
/studies/1/applications   1번 스터디의 신청들
/applications/7           7번 신청
/applications/7/approve   7번 신청을 승인하는 "동작"
```
URL은 **무엇을**, 메서드는 **어떻게**를 나타냅니다. `/getStudyList`, `/createStudy` 같은 동사형 URL은 피합니다.

### 2-5. 데이터베이스와 테이블

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

### 2-6. ORM: SQL 대신 파이썬 객체로 DB 다루기

```python
# SQL로 쓰면
SELECT * FROM studies WHERE status = 'RECRUITING';

# SQLAlchemy(ORM)로 쓰면
db.scalars(select(Study).where(Study.status == StudyStatus.RECRUITING))
```
처음에는 SQL을 몰라도 ORM으로 시작할 수 있습니다. 다만 기본 SQL(SELECT, WHERE, JOIN)은 나중에 꼭 익혀 두세요.

### 2-7. 트랜잭션: 전부 성공하거나, 전부 취소하거나

신청을 **승인**하면 세 가지가 함께 바뀌어야 합니다.

1. 신청 상태: PENDING → APPROVED
2. 멤버 테이블에 한 줄 추가
3. 정원이 찼으면 스터디 상태: RECRUITING → CLOSED

2번까지만 되고 서버가 죽으면 데이터가 꼬입니다. 그래서 **한 트랜잭션**으로 묶고 마지막에 한 번만 `commit()` 합니다. 중간에 에러가 나면 아무것도 저장되지 않습니다.
→ [services/applications.py](../backend/app/services/applications.py)의 `approve()`

---

## 3. 이 프로젝트의 기술 스택

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

## 4. 팀원끼리 정해야 하는 것 (개발 시작 전 30분)

백엔드와 프론트가 **동시에** 개발하려면, 서로 기다리지 않도록 "약속"을 먼저 정해야 합니다.
이걸 건너뛰면 해커톤 후반에 "필드 이름이 달라요", "날짜 형식이 안 맞아요"로 시간을 다 씁니다.

### 4-1. 반드시 합의할 것 ✅

#### ① 기능 범위와 우선순위
"무엇을 만들고, 무엇을 **안** 만들지"부터 정합니다.

| 우선순위 | 이 프로젝트의 예 |
|---|---|
| 필수 (시연에 꼭 필요) | 모집, 신청, 승인, 정원 |
| 있으면 좋음 | 방장 위임, 스터디룸 예약 |
| 안 함 | 로그인, 알림, 채팅, 결제 |

#### ② 인증 방식
이 프로젝트는 **"인증 없음, 요청에 user_id를 담아 누가 요청했는지만 구분"** 으로 정했습니다.
해커톤에서 로그인을 구현하면 반나절이 사라집니다. 시연에 필요 없으면 과감히 빼세요.

#### ③ API 명세 (가장 중요 ⭐)
엔드포인트마다 **메서드, 경로, 요청 body, 응답 예시, 에러 상황**을 표로 정합니다.
이 프로젝트 [README의 API 목록](../README.md#api-목록)이 바로 그 결과물입니다.

```
POST /studies/{id}/applications
요청: {"user_id": 5, "message": "저도 할래요"}
응답 201: {"id": 7, "study_id": 1, "user_id": 5, "message": "...", "status": "PENDING", "created_at": "..."}
에러: 404 스터디 없음 / 400 모집 마감 / 409 이미 멤버·중복 신청
```

명세만 정해지면 프론트는 가짜 데이터로 화면을 먼저 만들고, 백엔드는 명세대로 구현하면 됩니다.

#### ④ 데이터 형식 규칙
사소해 보이지만 **가장 많이 부딪히는 부분**입니다.

| 항목 | 이 프로젝트의 결정 | 안 정하면 생기는 문제 |
|---|---|---|
| 필드 이름 표기 | `snake_case` (`owner_id`, `member_count`) | 프론트는 `ownerId`, 백엔드는 `owner_id` |
| 날짜·시간 | `"2026-10-07T14:00:00"`, **한국 시간(KST)** | UTC/KST가 섞여 9시간 차이 |
| 상태값 | 대문자 영어 (`RECRUITING`, `PENDING`) | `"모집중"`, `"recruiting"`이 섞임 |
| 요청자 전달 위치 | GET·DELETE는 쿼리(`?user_id=1`), POST·PATCH는 body | 어디에 넣을지 매번 헷갈림 |
| id 타입 | 정수 | 문자열 `"1"`과 숫자 `1` 비교 실패 |

#### ⑤ 에러 응답 형식
**모든 에러를 같은 모양으로** 보내기로 정합니다. 이 프로젝트는 FastAPI 기본 형식을 그대로 씁니다.

```json
{"detail": "방장만 할 수 있는 작업입니다."}
```
프론트는 `detail`만 꺼내 화면에 띄우면 되므로, 백엔드가 규칙을 추가해도 프론트를 고칠 필요가 없습니다.
메시지 언어(한국어)도 이때 정합니다.

#### ⑥ 연결 방법 (주소, 포트)
| 항목 | 이 프로젝트 |
|---|---|
| 백엔드 주소 | `http://localhost:8000` |
| 프론트 주소 | `http://localhost:5173` |
| 연결 방식 | 프론트가 `/api/...`로 요청 → Vite 프록시가 백엔드로 전달 |
| CORS | 백엔드에서 전체 허용 (해커톤용) |

#### ⑦ 시연 시나리오와 시드 데이터
"심사위원 앞에서 어떤 순서로 무엇을 보여줄지"를 **처음에** 정하면, 그 시나리오에 필요한 기능만 만들게 되어 범위가 줄어듭니다.
이 프로젝트: 모집 → 신청 → 승인 → 정원 변경 → 방장 위임 → 방 예약 ([README 시연 시나리오](../README.md))

#### ⑧ 협업 방식
- Git 브랜치 규칙 (예: 각자 `feat/기능명` 브랜치 → main에 병합)
- 폴더 구조 (`backend/`, `frontend/` 분리 → 서로의 파일을 건드리지 않아 충돌이 적음)
- 명세가 바뀌면 **반드시 팀 채널에 공유**

### 4-2. 합의 결과를 남기는 템플릿

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

## 5. 백엔드 담당이 혼자 해야 하는 것

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

### 5-1. 데이터 모델 설계하는 법

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

### 5-2. 비즈니스 규칙 정리하는 법

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

### 5-3. 명세에 없지만 백엔드가 결정해야 하는 것들

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

## 6. 코드 읽기: 요청 하나를 끝까지 따라가기

### 6-1. 폴더 구조와 역할

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

### 6-2. "신청 승인" 요청 따라가기

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

### 6-3. 직접 따라 해 보기

1. 서버 실행: `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload`
2. http://localhost:8000/docs 접속 → `POST /seed` → **Try it out** → **Execute**
3. `POST /applications/{application_id}/approve`에서 id `4`, body `{"user_id": 2}` → **403** 확인 (지영은 방장이 아님)
4. body를 `{"user_id": 1}`로 바꿔 다시 → **200**
5. `GET /studies/1`로 인원수가 늘었는지 확인

> `/docs`(Swagger)는 FastAPI가 코드를 읽어 **자동으로** 만들어 줍니다. 프론트 담당에게 이 주소만 알려줘도 API 문서 역할을 합니다.

---

## 7. 실습: 기능 하나 직접 추가하기

**과제: "스터디 탈퇴" 기능** (방장이 아닌 멤버가 스터디에서 나가기)

### Step 1. 명세부터 정하기
```
DELETE /studies/{study_id}/members/me?user_id=2
응답 204 (본문 없음)
에러: 404 스터디 없음 / 400 멤버가 아님 / 400 방장은 탈퇴 불가(먼저 위임)
부가 효과: 마감 상태였다면 다시 모집중으로
```
> 팀에 공유: "탈퇴 API 추가합니다, 형식은 이렇습니다"

### Step 2. 규칙을 service에 구현 (`services/studies.py`)
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

### Step 3. router에 경로 연결 (`routers/studies.py`)
```python
@router.delete("/{study_id}/members/me", status_code=204)
def leave_study(study_id: int, user_id: int = Query(), db: Session = Depends(get_db)):
    service.leave_study(db, study_id, user_id)
```
(`from fastapi import Query`를 import에 추가)

### Step 4. /docs에서 확인
- 시드 후 `DELETE /studies/1/members/me?user_id=2` → 204
- 같은 요청 다시 → 400 (이미 멤버 아님)
- `user_id=1`(방장) → 400

### Step 5. 테스트 추가 (`tests/test_users_studies.py`)
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

### Step 6. 문서 갱신
README의 API 표에 한 줄 추가하고, 프론트 담당에게 알립니다.

> 이 6단계(**명세 → service → router → 수동 확인 → 테스트 → 문서**)가 백엔드 기능 개발의 기본 순서입니다.

---

## 8. 테스트: 왜, 어떻게

### 왜 필요한가요?
규칙이 10개를 넘으면 하나를 고칠 때 다른 것이 깨지기 쉽습니다. 매번 Swagger로 수십 번 클릭할 수는 없으니, **코드로 확인을 자동화**합니다.

### 이 프로젝트의 테스트 구조
```
backend/tests/
├── conftest.py               # 공통 준비물: 테스트용 임시 DB, client, 사용자/스터디 생성 도우미
├── test_users_studies.py     # 사용자, 스터디, 정원, 방장 위임
├── test_applications.py      # 신청, 취소, 승인, 거절
└── test_rooms.py             # 방, 예약, 시드
```

- 테스트는 **실제 DB(`app.db`)를 건드리지 않고** 임시 DB를 씁니다 (conftest.py에서 환경변수로 교체).
- 테스트 하나하나가 깨끗한 DB에서 시작합니다.

### 무엇을 테스트하나요?
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

## 9. 디버깅 가이드

### 막혔을 때 보는 순서
1. **uvicorn 터미널 로그**: 에러가 나면 여기에 빨간 Traceback이 찍힙니다. **맨 아래 줄**부터 읽으세요
2. **/docs에서 같은 요청 직접 보내기**: 프론트 문제인지 백엔드 문제인지 구분
3. **`print()` 찍어 보기**: 가장 원시적이지만 해커톤에서 가장 빠름

### 자주 만나는 문제

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

## 10. 해커톤 당일 체크리스트

### 시작 직후 (팀 전체, 30분)
- [ ] 기능 범위·우선순위 결정 (필수 / 선택 / 안 함)
- [ ] 시연 시나리오 초안
- [ ] API 명세 표 작성 (필드 이름, 날짜 형식, 상태값, 에러 형식 포함)
- [ ] 저장소 생성, `backend/` `frontend/` 폴더 분리

### 백엔드 1시간 안에
- [ ] 서버 뜨고 `/docs` 열림
- [ ] CORS 설정
- [ ] 모델 작성, 테이블 자동 생성
- [ ] **가장 단순한 GET 하나**를 프론트와 연결해 확인 (연결 문제는 빨리 발견할수록 좋음)

### 개발 중
- [ ] 기능 하나 끝날 때마다 `/docs`에서 확인 → 커밋
- [ ] 명세가 바뀌면 즉시 팀에 공유
- [ ] 어려운 규칙은 테스트로 고정

### 시연 2시간 전
- [ ] `/seed` 엔드포인트 완성 (데이터를 깨끗하게 되돌리기)
- [ ] 시연 시나리오를 처음부터 끝까지 리허설
- [ ] README에 실행 방법과 API 표 정리
- [ ] 새 기능 추가 중단, 버그 수정만

### 하지 말 것
- ❌ 로그인/회원가입 (시연에 필수가 아니면)
- ❌ DB 서버 설치 (PostgreSQL, MySQL) → SQLite로 충분
- ❌ 처음부터 완벽한 구조 → 동작하는 것 먼저, 정리는 나중에
- ❌ 프론트와 상의 없이 필드 이름 변경

---

## 부록. 용어집

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
