import { useCallback, useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { createStudy, getStudies } from "../api/studies";
import StatusBadge from "../components/StatusBadge";
import { useApp } from "../context/AppContext";

const FILTERS = [
  { value: "", label: "전체" },
  { value: "RECRUITING", label: "모집중" },
  { value: "CLOSED", label: "마감" },
];

const EMPTY_FORM = { title: "", description: "", capacity: 4 };

export default function StudyListPage() {
  const { currentUser, users, notify, notifyError } = useApp();
  const location = useLocation();
  const [status, setStatus] = useState("");
  const [studies, setStudies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(EMPTY_FORM);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setStudies(await getStudies(status));
    } catch (e) {
      notifyError(e);
    } finally {
      setLoading(false);
    }
  }, [status, notifyError]);

  // 필터 변경, 시드 재생성(location.state) 시 다시 불러오기
  useEffect(() => {
    load();
  }, [load, location.state]);

  const nickname = (id) => users.find((u) => u.id === id)?.nickname ?? `#${id}`;

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!currentUser) return notify("먼저 사용자를 선택하세요.", "error");
    try {
      await createStudy({ ...form, capacity: Number(form.capacity), owner_id: currentUser.id });
      notify("스터디 모집 글이 등록되었습니다.");
      setForm(EMPTY_FORM);
      load();
    } catch (e) {
      notifyError(e);
    }
  };

  return (
    <div className="grid-2">
      <section>
        <div className="section-head">
          <h2>스터디 목록</h2>
          <div className="tabs">
            {FILTERS.map((f) => (
              <button
                key={f.value}
                className={status === f.value ? "tab active" : "tab"}
                onClick={() => setStatus(f.value)}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <p className="muted">불러오는 중...</p>
        ) : studies.length === 0 ? (
          <p className="muted">스터디가 없습니다. 오른쪽에서 모집 글을 올리거나 시드 데이터를 넣어보세요.</p>
        ) : (
          <ul className="card-list">
            {studies.map((s) => (
              <li key={s.id}>
                <Link to={`/studies/${s.id}`} className="card study-card">
                  <div className="row-between">
                    <strong>{s.title}</strong>
                    <StatusBadge status={s.status} />
                  </div>
                  <p className="muted">{s.description || "설명 없음"}</p>
                  <div className="row-between small">
                    <span>방장 {nickname(s.owner_id)}</span>
                    <span className="count">
                      {s.member_count} / {s.capacity}명
                    </span>
                  </div>
                  <div className="progress">
                    <div style={{ width: `${(s.member_count / s.capacity) * 100}%` }} />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <aside className="card">
        <h3>모집하기</h3>
        <p className="muted small">
          방장: <strong>{currentUser?.nickname ?? "선택된 사용자 없음"}</strong>
        </p>
        <form onSubmit={handleCreate} className="form">
          <label>
            제목
            <input
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="알고리즘 스터디"
            />
          </label>
          <label>
            설명
            <textarea
              rows={3}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="주 2회 백준 문제 풀이"
            />
          </label>
          <label>
            정원 (2명 이상)
            <input
              type="number"
              min={2}
              required
              value={form.capacity}
              onChange={(e) => setForm({ ...form, capacity: e.target.value })}
            />
          </label>
          <button className="btn" disabled={!currentUser}>
            모집 글 등록
          </button>
        </form>
      </aside>
    </div>
  );
}
