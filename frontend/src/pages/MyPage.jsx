import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { cancelApplication } from "../api/applications";
import { createUser, getMyApplications } from "../api/users";
import StatusBadge from "../components/StatusBadge";
import { useApp } from "../context/AppContext";
import { formatDateTime } from "../utils/format";

export default function MyPage() {
  const { currentUser, setCurrentUserId, refreshUsers, notify, notifyError } = useApp();
  const [applications, setApplications] = useState([]);
  const [nickname, setNickname] = useState("");

  const load = useCallback(async () => {
    if (!currentUser) return setApplications([]);
    try {
      setApplications(await getMyApplications(currentUser.id));
    } catch (e) {
      notifyError(e);
    }
  }, [currentUser, notifyError]);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      const user = await createUser(nickname);
      await refreshUsers();
      setCurrentUserId(user.id);
      setNickname("");
      notify(`${user.nickname} 님이 생성되어 현재 사용자로 선택되었습니다.`);
    } catch (e) {
      notifyError(e);
    }
  };

  const handleCancel = async (id) => {
    try {
      await cancelApplication(id, currentUser.id);
      notify("신청이 취소되었습니다.");
      load();
    } catch (e) {
      notifyError(e);
    }
  };

  return (
    <div className="grid-2">
      <section>
        <h2>{currentUser ? `${currentUser.nickname} 님의 신청` : "내 신청"}</h2>
        {applications.length === 0 ? (
          <p className="muted">신청 내역이 없습니다.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>스터디</th>
                <th>메시지</th>
                <th>신청일</th>
                <th>상태</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {applications.map((a) => (
                <tr key={a.id}>
                  <td>
                    <Link to={`/studies/${a.study_id}`}>{a.study_title}</Link>
                  </td>
                  <td className="muted">{a.message}</td>
                  <td className="small">{formatDateTime(a.created_at)}</td>
                  <td>
                    <StatusBadge status={a.status} />
                  </td>
                  <td>
                    {a.status === "PENDING" && (
                      <button className="btn danger small" onClick={() => handleCancel(a.id)}>
                        취소
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <aside className="card">
        <h3>사용자 만들기</h3>
        <p className="muted small">로그인 없이 닉네임만으로 사용자를 만듭니다.</p>
        <form className="form" onSubmit={handleCreateUser}>
          <input
            required
            maxLength={50}
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            placeholder="닉네임"
          />
          <button className="btn">생성</button>
        </form>
      </aside>
    </div>
  );
}
