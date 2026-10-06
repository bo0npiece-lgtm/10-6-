import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getUsers } from "../api/users";

// 로그인 대신 "지금 누구로 행동할지"를 고르는 전역 상태 + 알림(toast)
const AppContext = createContext(null);

const STORAGE_KEY = "currentUserId";

function readStoredId() {
  try {
    return Number(localStorage.getItem(STORAGE_KEY)) || null;
  } catch {
    return null;
  }
}

export function AppProvider({ children }) {
  const [users, setUsers] = useState([]);
  const [currentUserId, setCurrentUserIdState] = useState(readStoredId);
  const [toast, setToast] = useState(null);

  const setCurrentUserId = (id) => {
    setCurrentUserIdState(id);
    try {
      localStorage.setItem(STORAGE_KEY, id ?? "");
    } catch {
      /* 저장 실패해도 동작에는 영향 없음 */
    }
  };

  const notify = useCallback((message, type = "success") => {
    setToast({ message, type, key: Date.now() });
  }, []);

  // 에러 객체를 받아 toast 로 보여주는 헬퍼
  const notifyError = useCallback((e) => notify(e.message, "error"), [notify]);

  const refreshUsers = useCallback(async () => {
    try {
      const list = await getUsers();
      setUsers(list);
      // 선택된 사용자가 사라졌으면(시드 재생성 등) 첫 번째 사용자로
      setCurrentUserIdState((prev) =>
        list.some((u) => u.id === prev) ? prev : (list[0]?.id ?? null),
      );
    } catch (e) {
      notifyError(e);
    }
  }, [notifyError]);

  useEffect(() => {
    refreshUsers();
  }, [refreshUsers]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(t);
  }, [toast]);

  const currentUser = users.find((u) => u.id === currentUserId) ?? null;

  return (
    <AppContext.Provider
      value={{
        users,
        currentUser,
        setCurrentUserId,
        refreshUsers,
        toast,
        notify,
        notifyError,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export const useApp = () => useContext(AppContext);
