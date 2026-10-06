const LABELS = {
  RECRUITING: "모집중",
  CLOSED: "마감",
  PENDING: "대기",
  APPROVED: "승인",
  REJECTED: "거절",
  CANCELED: "취소",
  CONFIRMED: "확정",
  OWNER: "방장",
  MEMBER: "멤버",
};

export default function StatusBadge({ status }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{LABELS[status] ?? status}</span>;
}
