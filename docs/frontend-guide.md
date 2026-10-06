# 프론트엔드 길라잡이: 스터디 모집 서비스 직접 만들어 보기

이 문서는 이 저장소의 `frontend/`를 **처음부터 직접 다시 만들어 보면서** React와 API 연동을 익히기 위한 안내서입니다.
완성된 코드는 정답지로 두고, 아래 단계를 따라 빈 폴더에서부터 만들어 보세요.

- 대상: HTML/CSS는 조금 다뤄 봤고, JavaScript 기초는 아는데 React와 API 연동은 처음인 사람
- 예상 소요: 단계당 30분~1시간, 전체 1~2일
- 백엔드는 이미 완성되어 있으므로 **프론트만** 신경 쓰면 됩니다

---

## 0. 큰 그림 먼저

### 프론트엔드가 하는 일은 딱 세 가지

1. **데이터 가져오기**: 백엔드 API를 호출(fetch)해서 JSON을 받는다
2. **화면 그리기**: 받은 데이터를 상태(state)에 넣고, React가 화면을 그린다
3. **사용자 행동 처리**: 버튼·폼 입력 → API 호출 → 성공하면 데이터를 다시 가져와 화면 갱신

이 프로젝트의 모든 화면은 이 세 가지의 반복입니다.

### 요청이 흘러가는 길

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

### 완성된 폴더 구조

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

## 1. 시작 전 체크리스트

### 알고 있어야 하는 JavaScript 문법

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

### 설치 확인

```bash
node --version   # v18 이상 (이 프로젝트는 v22로 확인)
npm --version
```

### 백엔드 띄워두기

프론트를 만드는 내내 백엔드가 켜져 있어야 합니다.

```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload
```

http://localhost:8000/docs 를 열어 **Swagger에서 API를 먼저 직접 눌러 보세요.**
어떤 요청을 보내면 어떤 JSON이 오는지 눈으로 확인하는 것이 프론트 개발의 첫걸음입니다.
`POST /seed`를 한 번 실행해 두면 데이터가 채워집니다.

---

## 2. React 핵심 개념 7가지 (이 프로젝트 기준)

개념을 다 외우고 시작할 필요는 없습니다. 단계별 실습에서 하나씩 등장하니, 막힐 때 다시 와서 보세요.

### ① 컴포넌트: 화면 조각을 만드는 함수

```jsx
function StatusBadge({ status }) {           // props를 받아서
  return <span className="badge">{status}</span>;   // JSX를 돌려준다
}

<StatusBadge status="RECRUITING" />          // 이렇게 사용
```
→ [components/StatusBadge.jsx](../frontend/src/components/StatusBadge.jsx)

### ② state: 바뀌면 화면이 다시 그려지는 값

```jsx
const [studies, setStudies] = useState([]);  // [현재값, 바꾸는 함수] = useState(초기값)
setStudies(newList);                         // 이걸 호출해야 화면이 갱신됨
```
일반 변수(`let x`)를 바꾸면 화면은 그대로입니다. **화면에 영향을 주는 값은 state**에 넣으세요.

### ③ useEffect: "화면이 그려진 뒤에" 할 일 (보통 데이터 불러오기)

```jsx
useEffect(() => {
  load();               // API 호출
}, [status]);           // status가 바뀔 때마다 다시 실행
```
- 의존성 배열 `[]`가 비어 있으면 처음 한 번만 실행됩니다
- 배열에 넣은 값이 바뀌면 다시 실행됩니다 (예: 필터 탭 변경 → 목록 재조회)

### ④ useCallback: 함수를 기억해 두기

`useEffect`의 의존성에 함수를 넣으면, 렌더링마다 함수가 새로 만들어져 무한 루프가 날 수 있습니다.
`useCallback`으로 감싸면 의존 값이 바뀔 때만 새 함수가 됩니다.

```jsx
const load = useCallback(async () => { ... }, [status]);
useEffect(() => { load(); }, [load]);
```
→ [pages/StudyListPage.jsx](../frontend/src/pages/StudyListPage.jsx)의 패턴. 처음엔 "데이터 불러오는 함수는 이렇게 쓴다"고 외워도 충분합니다.

### ⑤ 제어 컴포넌트: input 값을 state로 관리

```jsx
const [nickname, setNickname] = useState("");
<input value={nickname} onChange={(e) => setNickname(e.target.value)} />
```
입력값이 항상 state에 들어 있으니 제출할 때 그대로 API에 넘기면 됩니다.

### ⑥ 조건부 렌더링 / 목록 렌더링

```jsx
{isOwner && <OwnerPanel />}                              // 조건이 참일 때만 표시
{loading ? <p>불러오는 중...</p> : <List />}             // 둘 중 하나
{studies.map((s) => <li key={s.id}>{s.title}</li>)}      // 배열 → 요소들 (key 필수!)
```

### ⑦ Context: 여러 화면이 함께 쓰는 전역 상태

"현재 사용자"는 헤더, 목록, 상세, 내 신청 화면 **모두**가 알아야 합니다.
props로 일일이 넘기는 대신 Context에 두고 어디서든 꺼내 씁니다.

```jsx
const { currentUser, notify } = useApp();
```
→ [context/AppContext.jsx](../frontend/src/context/AppContext.jsx)

---

## 3. 단계별 실습

각 단계는 **목표 → 만들 파일 → 핵심 코드 → 확인 방법 → 자주 하는 실수** 순서입니다.
한 단계를 끝낼 때마다 브라우저에서 동작을 확인하고 git commit 하는 습관을 들이세요.

### Step 1. Vite로 React 프로젝트 만들기

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

### Step 2. API 클라이언트 만들고 백엔드와 처음 연결하기 ⭐ 가장 중요

**목표:** 프론트에서 `GET /users`를 호출해 콘솔에 찍기

**만들 파일:** `.env`, `src/api/client.js`, `src/api/users.js`

```bash
# .env  (Vite는 VITE_ 로 시작하는 변수만 코드에 노출함)
VITE_API_URL=http://localhost:8000
```

```js
// src/api/client.js: 처음엔 이 정도로 시작
export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function request(path, { method = "GET", body, query } = {}) {
  const url = new URL(path, API_URL);
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
2. **Network** 탭에서 `users` 요청을 클릭해 Headers / Response를 보세요. **이 탭과 친해지는 것이 API 연동 디버깅의 전부입니다.**

**자주 하는 실수:**
- `.env`를 고친 뒤 `npm run dev`를 재시작하지 않음 → env는 시작할 때만 읽습니다
- 콘솔에 **CORS 에러** → 백엔드가 다른 주소(5173 → 8000) 요청을 막은 것. 이 프로젝트는 백엔드 [main.py](../backend/app/main.py)에서 전체 허용해 두었습니다
- `Failed to fetch` → 백엔드가 꺼져 있음
- 콘솔에 같은 요청이 **두 번** 찍힘 → 개발 모드의 `StrictMode`가 일부러 effect를 두 번 실행합니다. 버그 아님

**더 나아가기:** 완성본 [api/client.js](../frontend/src/api/client.js)는 여기에 ① 서버가 꺼졌을 때 메시지, ② 422 검증 에러 배열 → 문자열 변환, ③ `status` 코드를 담은 `ApiError`를 추가했습니다. 비교해 보세요.

---

### Step 3. 라우터와 페이지 뼈대

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

### Step 4. 현재 사용자 Context (로그인 대신)

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

### Step 5. 스터디 목록: 데이터 불러와서 그리기

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

### Step 6. 폼으로 데이터 만들기: 모집 글 등록

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

### Step 7. 상세 페이지: URL 파라미터와 여러 요청 동시에

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

### Step 8. 역할에 따라 다른 화면: 신청과 승인

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

### Step 9. 정원 변경·방장 위임·예약: 에러를 UX로

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

### Step 10. 마무리: 스타일과 반응형

**목표:** 해커톤 시연에서 보기 좋게

- CSS 변수(`:root { --primary: ... }`)로 색을 한 곳에서 관리 → [index.css](../frontend/src/index.css)
- 상태별 색 뱃지: `className={`badge badge-${status.toLowerCase()}`}`
- 2단 레이아웃은 `display: grid`, 좁은 화면에서는 `@media (max-width: 760px)`로 1단
- 개발자도구의 **기기 모드**(Ctrl+Shift+M)로 휴대폰 화면 확인

---

## 4. 디버깅 가이드: 막혔을 때 보는 순서

1. **Console 탭**: 빨간 에러가 있나? 메시지를 그대로 검색해 본다
2. **Network 탭**: 요청이 나갔나? 상태 코드는? Response 내용은?
3. **Swagger(`/docs`)**: 같은 요청을 직접 보내 본다 → 되면 프론트 문제, 안 되면 요청 내용 문제

| 증상 | 원인 | 해결 |
|---|---|---|
| `Failed to fetch` / "서버에 연결할 수 없습니다" | 백엔드 꺼짐, 주소 틀림 | uvicorn 실행 확인, `.env`의 `VITE_API_URL` 확인 |
| CORS 에러 | 백엔드가 출처를 허용하지 않음 | 백엔드 CORS 설정 확인 |
| 422 Unprocessable | body 형식·타입이 스키마와 다름 | Network → Payload와 `/docs`의 스키마 비교 (숫자를 문자열로 보내는 경우가 흔함) |
| 403 | 요청한 `user_id`가 방장/본인이 아님 | 헤더의 현재 사용자 확인 |
| 화면이 안 바뀜 | state를 안 바꿨거나 재조회를 안 함 | `setXxx` 호출, 액션 후 `load()` 확인 |
| 무한 요청 | `useEffect` 의존성에 매번 새로 만들어지는 함수·객체 | `useCallback`, 의존성 배열 점검 |
| `.env` 수정이 반영 안 됨 | dev 서버 재시작 필요 | `npm run dev` 재실행 |

---

## 5. 연습 과제 (난이도 순)

완성본을 이해했다면 직접 기능을 붙여 보세요.

1. ⭐ 스터디 목록에 **제목 검색창** 추가 (프론트에서 `filter`만으로)
2. ⭐ 로딩 중일 때 버튼을 `disabled`로 만들어 **중복 클릭 방지**
3. ⭐⭐ 상세 페이지의 `OwnerPanel`, `ReservationForm`을 **별도 파일로 분리**
4. ⭐⭐ 반복되는 "로딩/에러/데이터" 패턴을 **커스텀 훅** `useAsync(fn, deps)`로 추출
5. ⭐⭐ 스터디룸 페이지를 **시간표 그리드**(9시~22시 칸에 색칠)로 바꾸기
6. ⭐⭐⭐ 데이터 관리를 **TanStack Query**로 교체해 보고, 수동 `load()`와 비교
7. ⭐⭐⭐ 프로젝트를 **TypeScript**로 전환 (`/docs`의 스키마를 보고 타입 정의)

---

## 6. 해커톤 실전 팁

- **API 명세부터 합의:** 백엔드와 "경로, 요청 body, 응답 JSON 예시"를 먼저 정하면 동시에 개발할 수 있습니다 (이 프로젝트 README의 API 표처럼)
- **백엔드가 아직 없으면:** `api/*.js` 함수가 가짜 데이터를 반환하게 해 두고 화면부터 만듭니다. api 레이어를 분리해 둔 덕분에 나중에 그 파일만 바꾸면 됩니다
- **시드 버튼은 필수:** 시연 직전에 데이터를 깨끗하게 되돌릴 수 있어야 합니다
- **에러 메시지는 서버가 주는 걸 그대로:** 프론트에서 규칙을 이중으로 구현하지 마세요
- **시연 시나리오를 미리 클릭해 보기:** README의 "화면 시연 시나리오"처럼 순서를 정해 두고 리허설하세요

---

## 7. 용어집

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
