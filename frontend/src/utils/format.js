// 백엔드는 KST naive datetime("2026-10-07T14:00:00")을 주고받는다.

export const formatDateTime = (s) => s.replace("T", " ").slice(0, 16);

export const formatTime = (s) => s.slice(11, 16);

// <input type="date"> 기본값용 "YYYY-MM-DD" (로컬 기준)
export function toDateInput(d = new Date()) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function tomorrow() {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return toDateInput(d);
}
