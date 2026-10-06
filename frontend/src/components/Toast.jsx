import { useApp } from "../context/AppContext";

export default function Toast() {
  const { toast } = useApp();
  if (!toast) return null;
  return (
    <div key={toast.key} className={`toast toast-${toast.type}`} role="status">
      {toast.message}
    </div>
  );
}
