import { useEffect, useState } from "react";
import { getRoomReservations, getRooms } from "../api/rooms";
import { useApp } from "../context/AppContext";
import { formatTime, tomorrow } from "../utils/format";

export default function RoomsPage() {
  const { notifyError } = useApp();
  const [date, setDate] = useState(tomorrow());
  const [rooms, setRooms] = useState([]);
  const [byRoom, setByRoom] = useState({});

  useEffect(() => {
    (async () => {
      try {
        const list = await getRooms();
        setRooms(list);
        // 방마다 해당 날짜 예약을 병렬로 조회
        const results = await Promise.all(list.map((r) => getRoomReservations(r.id, date)));
        setByRoom(Object.fromEntries(list.map((r, i) => [r.id, results[i]])));
      } catch (e) {
        notifyError(e);
      }
    })();
  }, [date, notifyError]);

  return (
    <div className="stack">
      <div className="section-head">
        <h2>스터디룸 현황</h2>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      </div>
      <p className="muted small">예약은 스터디 상세 화면에서 방장만 할 수 있습니다.</p>
      <div className="room-grid">
        {rooms.map((room) => {
          const list = byRoom[room.id] ?? [];
          return (
            <section key={room.id} className="card">
              <div className="row-between">
                <h3>{room.name}</h3>
                <span className="muted small">최대 {room.capacity}명</span>
              </div>
              {list.length === 0 ? (
                <p className="muted">예약 없음 · 하루 종일 비어 있음</p>
              ) : (
                <ul className="list">
                  {list.map((r) => (
                    <li key={r.id} className="row-between">
                      <span className="time">
                        {formatTime(r.start_at)} ~ {formatTime(r.end_at)}
                      </span>
                      <span className="muted small">스터디 #{r.study_id}</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          );
        })}
      </div>
    </div>
  );
}
