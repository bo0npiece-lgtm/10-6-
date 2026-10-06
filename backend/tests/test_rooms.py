from datetime import timedelta

from app.database import now_kst


def iso(x):
    return x.isoformat()


def setup(make_user, make_study):
    a, b = make_user("a"), make_user("b")
    sid = make_study(a)
    t = (now_kst() + timedelta(days=1)).replace(hour=10, minute=0, second=0)
    body = {"user_id": a, "room_id": 1, "start_at": iso(t), "end_at": iso(t + timedelta(hours=2))}
    return a, b, sid, t, body


def test_sample_rooms(client):
    assert [r["capacity"] for r in client.get("/rooms").json()] == [4, 6, 10]


def test_reservation_rules(client, make_user, make_study):
    a, b, sid, t, body = setup(make_user, make_study)
    url = f"/studies/{sid}/reservations"
    h = lambda n: iso(t + timedelta(hours=n))  # noqa: E731

    assert client.post(url, json={**body, "user_id": b}).status_code == 403
    assert client.post(url, json=body).status_code == 201
    assert client.post(url, json={**body, "start_at": h(1), "end_at": h(3)}).status_code == 409
    assert client.post(url, json={**body, "start_at": h(2), "end_at": h(3)}).status_code == 201  # 맞닿음 허용
    assert client.post(url, json={**body, "room_id": 2, "end_at": h(0)}).status_code == 400
    past = now_kst() - timedelta(hours=2)
    assert client.post(url, json={**body, "room_id": 2, "start_at": iso(past),
                                  "end_at": iso(past + timedelta(hours=1))}).status_code == 400
    assert client.post(url, json={**body, "room_id": 99}).status_code == 404


def test_timezone_input_is_converted_to_kst(client, make_user, make_study):
    a, b, sid, t, body = setup(make_user, make_study)
    start_utc = t + timedelta(days=1, hours=-9)
    r = client.post(f"/studies/{sid}/reservations", json={
        **body, "start_at": iso(start_utc) + "Z", "end_at": iso(start_utc + timedelta(hours=1)) + "Z",
    })
    assert r.status_code == 201
    assert r.json()["start_at"] == iso(t + timedelta(days=1))


def test_list_and_cancel(client, make_user, make_study):
    a, b, sid, t, body = setup(make_user, make_study)
    rid = client.post(f"/studies/{sid}/reservations", json=body).json()["id"]
    day = {"date": t.date().isoformat()}
    assert len(client.get("/rooms/1/reservations", params=day).json()) == 1
    assert len(client.get(f"/studies/{sid}/reservations").json()) == 1
    assert client.delete(f"/reservations/{rid}", params={"user_id": b}).status_code == 403
    assert client.delete(f"/reservations/{rid}", params={"user_id": a}).status_code == 200
    assert client.delete(f"/reservations/{rid}", params={"user_id": a}).status_code == 400
    assert client.get("/rooms/1/reservations", params=day).json() == []
    assert client.post(f"/studies/{sid}/reservations", json=body).status_code == 201  # 취소 후 재예약
    assert client.get("/rooms/1/reservations", params={"date": "bad"}).status_code == 422


def test_room_capacity_exceeded(client, make_user, make_study, join):
    a, b, sid, t, body = setup(make_user, make_study)
    big = make_study(a, capacity=6)
    for n in "cdef":
        join(big, a, make_user(n))
    assert client.post(f"/studies/{big}/reservations", json=body).status_code == 400  # 5명 > A룸 4명


def test_seed_is_idempotent(client):
    for _ in range(2):
        r = client.post("/seed")
        assert r.status_code == 200
    data = r.json()
    assert len(data["users"]) == 5 and len(data["rooms"]) == 3
    assert sorted(s["status"] for s in data["studies"]) == ["CLOSED", "RECRUITING", "RECRUITING"]
    closed = next(s for s in data["studies"] if s["status"] == "CLOSED")
    assert closed["member_count"] == closed["capacity"]
    assert len(client.get("/users").json()) == 5
