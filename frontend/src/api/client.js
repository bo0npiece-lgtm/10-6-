// 모든 API 호출이 거치는 fetch 래퍼.
// 기본값 "/api" 는 Vite 프록시(vite.config.js)를 거쳐 백엔드로 전달된다.
// 백엔드를 직접 호출하려면 .env 에 VITE_API_URL=http://localhost:8000 처럼 지정.
export const API_URL = import.meta.env.VITE_API_URL || "/api";

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

// FastAPI 에러 응답 → 사람이 읽을 메시지
function toMessage(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    // 422 검증 에러: [{loc, msg}, ...]
    return detail.map((d) => `${d.loc?.slice(1).join(".")}: ${d.msg}`).join(", ");
  }
  return "알 수 없는 오류가 발생했습니다.";
}

export async function request(path, { method = "GET", body, query } = {}) {
  // API_URL 이 "/api" 같은 상대 경로여도 동작하도록 현재 페이지 주소를 기준으로 만든다
  const url = new URL(API_URL + path, window.location.origin);
  if (query) {
    Object.entries(query).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
    });
  }

  let res;
  try {
    res = await fetch(url, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, `서버에 연결할 수 없습니다. (${API_URL})`);
  }

  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) {
    // 프록시 사용 시 백엔드가 꺼져 있으면 detail 없는 5xx 가 온다
    if (!data?.detail && res.status >= 500) {
      throw new ApiError(res.status, `백엔드 서버에 연결할 수 없습니다. 실행 중인지 확인하세요. (${res.status})`);
    }
    throw new ApiError(res.status, toMessage(data?.detail));
  }
  return data;
}
