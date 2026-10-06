import { NavLink, useNavigate } from "react-router-dom";
import { seed } from "../api/users";
import { useApp } from "../context/AppContext";

export default function Header() {
  const { users, currentUser, setCurrentUserId, refreshUsers, notify, notifyError } = useApp();
  const navigate = useNavigate();

  const handleSeed = async () => {
    if (!confirm("모든 데이터를 지우고 시연용 데이터를 다시 만들까요?")) return;
    try {
      await seed();
      await refreshUsers();
      notify("시연용 데이터가 생성되었습니다.");
      navigate("/", { state: { refresh: Date.now() } });
    } catch (e) {
      notifyError(e);
    }
  };

  return (
    <header className="header">
      <div className="header-inner">
        <NavLink to="/" className="logo">
          📚 스터디 모집
        </NavLink>
        <nav className="nav">
          <NavLink to="/" end>
            스터디
          </NavLink>
          <NavLink to="/rooms">스터디룸</NavLink>
          <NavLink to="/me">내 신청</NavLink>
        </nav>
        <div className="header-right">
          <label className="user-select">
            <span>현재 사용자</span>
            <select
              value={currentUser?.id ?? ""}
              onChange={(e) => setCurrentUserId(Number(e.target.value))}
            >
              {users.length === 0 && <option value="">사용자 없음</option>}
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  #{u.id} {u.nickname}
                </option>
              ))}
            </select>
          </label>
          <button className="btn ghost small" onClick={handleSeed}>
            시드 데이터
          </button>
        </div>
      </div>
    </header>
  );
}
