import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  applyStudy,
  approveApplication,
  cancelApplication,
  getApplications,
  rejectApplication,
} from "../api/applications";
import { getMyApplications } from "../api/users";
import {
  cancelReservation,
  createReservation,
  getRooms,
  getStudyReservations,
} from "../api/rooms";
import { getStudy, transferOwner, updateCapacity } from "../api/studies";
import StatusBadge from "../components/StatusBadge";
import { useApp } from "../context/AppContext";
import { formatDateTime, tomorrow } from "../utils/format";

export default function StudyDetailPage() {
  const { id } = useParams();
  const { currentUser, notify, notifyError } = useApp();
  const [study, setStudy] = useState(null);
  const [reservations, setReservations] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [myPending, setMyPending] = useState(null); // 이 스터디에 대한 내 대기 중 신청
  const [error, setError] = useState(null);
  const me = currentUser?.id;

  const load = useCallback(async () => {
    try {
      const [s, r, rm, mine] = await Promise.all([
        getStudy(id),
        getStudyReservations(id),
        getRooms(),
        me ? getMyApplications(me) : [],
      ]);
      setStudy(s);
      setReservations(r);
      setRooms(rm);
      setMyPending(mine.find((a) => a.study_id === s.id && a.status === "PENDING") ?? null);
      setError(null);
    } catch (e) {
      setError(e.message);
    }
  }, [id, me]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <p className="error-box">{error}</p>;
  if (!study) return <p className="muted">불러오는 중...</p>;

  const isOwner = me === study.owner_id;
  const isMember = study.members.some((m) => m.user_id === me);
  const roomName = (rid) => rooms.find((r) => r.id === rid)?.name ?? `#${rid}`;

  // 액션 공통 처리: 성공 메시지 → 다시 불러오기, 실패 → 에러 toast
  const run = async (fn, message) => {
    try {
      await fn();
      notify(message);
      await load();
      return true;
    } catch (e) {
      notifyError(e);
      return false;
    }
  };

  return (
    <div className="stack">
      <Link to="/" className="muted small">
        ← 목록으로
      </Link>

      <section className="card">
        <div className="row-between">
          <h2>{study.title}</h2>
          <StatusBadge status={study.status} />
        </div>
        <p>{study.description || <span className="muted">설명 없음</span>}</p>
        <p className="count">
          인원 {study.member_count} / {study.capacity}명
        </p>
        <div className="progress">
          <div style={{ width: `${(study.member_count / study.capacity) * 100}%` }} />
        </div>
        <h4>멤버</h4>
        <ul className="chips">
          {study.members.map((m) => (
            <li key={m.user_id} className={m.user_id === me ? "chip me" : "chip"}>
              {m.nickname} <StatusBadge status={m.role} />
            </li>
          ))}
        </ul>
      </section>

      {!isMember && currentUser && myPending && (
        <section className="card row-between">
          <span>
            <StatusBadge status="PENDING" /> 방장의 승인을 기다리는 중입니다.
          </span>
          <button
            className="btn danger small"
            onClick={() => run(() => cancelApplication(myPending.id, me), "신청이 취소되었습니다.")}
          >
            신청 취소
          </button>
        </section>
      )}

      {!isMember && currentUser && !myPending && (
        <ApplyForm
          study={study}
          onApply={(msg) => run(() => applyStudy(study.id, me, msg), "신청이 완료되었습니다.")}
        />
      )}

      {isOwner && (
        <OwnerPanel study={study} userId={me} run={run} notifyError={notifyError} />
      )}

      <section className="card">
        <h3>스터디룸 예약</h3>
        {reservations.length === 0 ? (
          <p className="muted">예약이 없습니다.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>방</th>
                <th>시작</th>
                <th>종료</th>
                {isOwner && <th />}
              </tr>
            </thead>
            <tbody>
              {reservations.map((r) => (
                <tr key={r.id}>
                  <td>{roomName(r.room_id)}</td>
                  <td>{formatDateTime(r.start_at)}</td>
                  <td>{formatDateTime(r.end_at)}</td>
                  {isOwner && (
                    <td>
                      <button
                        className="btn danger small"
                        onClick={() => run(() => cancelReservation(r.id, me), "예약이 취소되었습니다.")}
                      >
                        취소
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {isOwner && (
          <ReservationForm
            rooms={rooms}
            memberCount={study.member_count}
            onSubmit={(body) =>
              run(() => createReservation(study.id, { ...body, user_id: me }), "예약되었습니다.")
            }
          />
        )}
      </section>
    </div>
  );
}

function ApplyForm({ study, onApply }) {
  const [message, setMessage] = useState("");
  if (study.status !== "RECRUITING") {
    return <p className="card muted">모집이 마감된 스터디입니다.</p>;
  }
  return (
    <section className="card">
      <h3>신청하기</h3>
      <form
        className="form inline"
        onSubmit={async (e) => {
          e.preventDefault();
          if (await onApply(message)) setMessage("");
        }}
      >
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="한마디 (선택)"
        />
        <button className="btn">신청</button>
      </form>
    </section>
  );
}

function OwnerPanel({ study, userId, run, notifyError }) {
  const [applications, setApplications] = useState([]);
  const [capacity, setCapacity] = useState(study.capacity);
  const candidates = study.members.filter((m) => m.user_id !== userId);
  const [newOwner, setNewOwner] = useState("");

  const loadApps = useCallback(async () => {
    try {
      setApplications(await getApplications(study.id, userId));
    } catch (e) {
      notifyError(e);
    }
  }, [study.id, userId, notifyError]);

  // 스터디가 바뀔 때(승인 → 인원 변동 등)마다 신청 목록도 갱신
  useEffect(() => {
    loadApps();
    setCapacity(study.capacity);
  }, [loadApps, study]);

  const pending = applications.filter((a) => a.status === "PENDING");
  const done = applications.filter((a) => a.status !== "PENDING");

  return (
    <section className="card owner">
      <h3>👑 방장 관리</h3>

      <h4>대기 중인 신청 ({pending.length})</h4>
      {pending.length === 0 ? (
        <p className="muted small">대기 중인 신청이 없습니다.</p>
      ) : (
        <ul className="list">
          {pending.map((a) => (
            <li key={a.id} className="row-between">
              <span>
                <strong>{a.nickname}</strong> <span className="muted">{a.message}</span>
              </span>
              <span className="actions">
                <button
                  className="btn small"
                  onClick={() => run(() => approveApplication(a.id, userId), `${a.nickname} 님을 승인했습니다.`)}
                >
                  승인
                </button>
                <button
                  className="btn ghost small"
                  onClick={() => run(() => rejectApplication(a.id, userId), `${a.nickname} 님을 거절했습니다.`)}
                >
                  거절
                </button>
              </span>
            </li>
          ))}
        </ul>
      )}
      {done.length > 0 && (
        <details>
          <summary className="muted small">처리된 신청 {done.length}건</summary>
          <ul className="list">
            {done.map((a) => (
              <li key={a.id} className="row-between small">
                <span>{a.nickname}</span>
                <StatusBadge status={a.status} />
              </li>
            ))}
          </ul>
        </details>
      )}

      <div className="grid-2 tight">
        <form
          className="form"
          onSubmit={(e) => {
            e.preventDefault();
            run(() => updateCapacity(study.id, userId, Number(capacity)), "정원이 변경되었습니다.");
          }}
        >
          <h4>정원 변경</h4>
          <div className="inline">
            <input type="number" min={2} value={capacity} onChange={(e) => setCapacity(e.target.value)} />
            <button className="btn">변경</button>
          </div>
        </form>

        <form
          className="form"
          onSubmit={async (e) => {
            e.preventDefault();
            if (!newOwner) return;
            if (await run(() => transferOwner(study.id, userId, Number(newOwner)), "방장이 위임되었습니다."))
              setNewOwner("");
          }}
        >
          <h4>방장 위임</h4>
          <div className="inline">
            <select value={newOwner} onChange={(e) => setNewOwner(e.target.value)}>
              <option value="">멤버 선택</option>
              {candidates.map((m) => (
                <option key={m.user_id} value={m.user_id}>
                  {m.nickname}
                </option>
              ))}
            </select>
            <button className="btn" disabled={!newOwner}>
              위임
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}

function ReservationForm({ rooms, memberCount, onSubmit }) {
  const [form, setForm] = useState({ room_id: "", date: tomorrow(), start: "14:00", end: "16:00" });
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <form
      className="form reservation-form"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({
          room_id: Number(form.room_id),
          start_at: `${form.date}T${form.start}:00`,
          end_at: `${form.date}T${form.end}:00`,
        });
      }}
    >
      <h4>새 예약</h4>
      <div className="inline wrap">
        <select required value={form.room_id} onChange={set("room_id")}>
          <option value="">방 선택</option>
          {rooms.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name} · {r.capacity}명{r.capacity < memberCount ? " (정원 부족)" : ""}
            </option>
          ))}
        </select>
        <input type="date" required value={form.date} onChange={set("date")} />
        <input type="time" required value={form.start} onChange={set("start")} />
        <span>~</span>
        <input type="time" required value={form.end} onChange={set("end")} />
        <button className="btn">예약</button>
      </div>
    </form>
  );
}
