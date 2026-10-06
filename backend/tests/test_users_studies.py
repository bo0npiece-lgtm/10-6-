def test_create_and_list_users(client, make_user):
    make_user("a")
    assert client.post("/users", json={"nickname": "a"}).status_code == 409
    assert [u["nickname"] for u in client.get("/users").json()] == ["a"]


def test_create_study_registers_owner(client, make_user):
    a = make_user("a")
    assert client.post("/studies", json={"owner_id": 999, "title": "x", "capacity": 2}).status_code == 404
    assert client.post("/studies", json={"owner_id": a, "title": "x", "capacity": 1}).status_code == 422
    s = client.post("/studies", json={"owner_id": a, "title": "S", "capacity": 2}).json()
    assert s["member_count"] == 1 and s["status"] == "RECRUITING"
    d = client.get(f"/studies/{s['id']}").json()
    assert d["members"] == [{"user_id": a, "nickname": "a", "role": "OWNER"}]
    assert client.get("/studies/999").status_code == 404


def test_capacity_rules(client, make_user, make_study, join):
    a, b = make_user("a"), make_user("b")
    sid = make_study(a, capacity=3)
    join(sid, a, b)
    url = f"/studies/{sid}/capacity"
    assert client.patch(url, json={"user_id": b, "capacity": 4}).status_code == 403
    assert client.patch(url, json={"user_id": a, "capacity": 1}).status_code == 422
    assert client.patch(url, json={"user_id": a, "capacity": 2}).json()["status"] == "CLOSED"
    assert client.patch(url, json={"user_id": a, "capacity": 5}).json()["status"] == "RECRUITING"
    c = make_user("c")
    join(sid, a, c)
    assert client.patch(url, json={"user_id": a, "capacity": 2}).status_code == 400
    assert len(client.get("/studies", params={"status": "RECRUITING"}).json()) == 1


def test_transfer_owner(client, make_user, make_study, join):
    a, b, e = make_user("a"), make_user("b"), make_user("e")
    sid = make_study(a)
    join(sid, a, b)
    url = f"/studies/{sid}/transfer-owner"
    assert client.post(url, json={"user_id": b, "new_owner_id": a}).status_code == 403
    assert client.post(url, json={"user_id": a, "new_owner_id": a}).status_code == 400
    assert client.post(url, json={"user_id": a, "new_owner_id": e}).status_code == 400
    s = client.post(url, json={"user_id": a, "new_owner_id": b}).json()
    assert s["owner_id"] == b
    assert {m["user_id"]: m["role"] for m in s["members"]} == {a: "MEMBER", b: "OWNER"}
    assert client.patch(f"/studies/{sid}/capacity", json={"user_id": a, "capacity": 5}).status_code == 403
