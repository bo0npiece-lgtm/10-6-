def test_apply_rules(client, make_user, make_study):
    a, b = make_user("a"), make_user("b")
    sid = make_study(a)
    url = f"/studies/{sid}/applications"
    assert client.post(url, json={"user_id": a}).status_code == 409  # 방장
    assert client.post(url, json={"user_id": b, "message": "hi"}).status_code == 201
    assert client.post(url, json={"user_id": b}).status_code == 409  # PENDING 중복
    assert client.post(url, json={"user_id": 999}).status_code == 404


def test_cancel_and_reapply(client, make_user, make_study):
    a, b = make_user("a"), make_user("b")
    sid = make_study(a)
    app_id = client.post(f"/studies/{sid}/applications", json={"user_id": b}).json()["id"]
    assert client.delete(f"/applications/{app_id}", params={"user_id": a}).status_code == 403
    assert client.delete(f"/applications/{app_id}", params={"user_id": b}).json()["status"] == "CANCELED"
    assert client.delete(f"/applications/{app_id}", params={"user_id": b}).status_code == 400
    assert client.post(f"/studies/{sid}/applications", json={"user_id": b}).status_code == 201
    mine = client.get(f"/users/{b}/applications").json()
    assert [m["status"] for m in mine] == ["PENDING", "CANCELED"]
    assert mine[0]["study_title"] == "스터디"


def test_approve_closes_study_and_rejects_pending(client, make_user, make_study):
    a, b, d, e = (make_user(n) for n in "abde")
    sid = make_study(a, capacity=2)
    url = f"/studies/{sid}/applications"
    ap_b = client.post(url, json={"user_id": b}).json()["id"]
    ap_d = client.post(url, json={"user_id": d}).json()["id"]

    assert client.get(url, params={"user_id": b}).status_code == 403
    listed = client.get(url, params={"user_id": a}).json()
    assert [x["nickname"] for x in listed] == ["b", "d"]

    assert client.post(f"/applications/{ap_b}/approve", json={"user_id": b}).status_code == 403
    assert client.post(f"/applications/{ap_b}/approve", json={"user_id": a}).status_code == 200
    s = client.get(f"/studies/{sid}").json()
    assert s["status"] == "CLOSED" and s["member_count"] == 2
    assert client.get(url, params={"user_id": a, "status": "PENDING"}).json() == []
    assert client.post(f"/applications/{ap_d}/approve", json={"user_id": a}).status_code == 400
    assert client.post(url, json={"user_id": e}).status_code == 400  # 마감


def test_reject(client, make_user, make_study):
    a, b = make_user("a"), make_user("b")
    sid = make_study(a)
    app_id = client.post(f"/studies/{sid}/applications", json={"user_id": b}).json()["id"]
    assert client.post(f"/applications/{app_id}/reject", json={"user_id": a}).json()["status"] == "REJECTED"
    assert client.post(f"/applications/{app_id}/reject", json={"user_id": a}).status_code == 400
