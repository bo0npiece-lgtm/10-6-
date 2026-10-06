// 모든 API 호출이 거치는 fetch 래퍼.
// 백엔드 주소는 .env 의 VITE_API_URL 로 바꿀 수 있다.
export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

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
  const url = new URL(path, API_URL);
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
  if (!res.ok) throw new ApiError(res.status, toMessage(data?.detail));
  return data;
}
