from fastapi import HTTPException

from src import app as app_module


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert "Robotics Club" in payload


def test_get_activities_returns_expected_activity_shape(client):
    response = client.get("/activities")

    activity = response.json()["Chess Club"]

    assert set(activity.keys()) == {
        "description",
        "schedule",
        "max_participants",
        "participants",
    }
    assert isinstance(activity["participants"], list)
    assert activity["max_participants"] >= len(activity["participants"])


def test_signup_registers_student_for_activity(client):
    email = "new.student@mergington.edu"

    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in app_module.activities["Chess Club"]["participants"]


def test_signup_rejects_unknown_activity(client):
    response = client.post("/activities/Unknown%20Club/signup", params={"email": "student@mergington.edu"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_student(client):
    email = app_module.activities["Chess Club"]["participants"][0]

    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}


def test_unregister_removes_student_from_activity(client):
    email = app_module.activities["Chess Club"]["participants"][0]

    response = client.delete("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in app_module.activities["Chess Club"]["participants"]


def test_unregister_rejects_unknown_activity(client):
    response = client.delete("/activities/Unknown%20Club/signup", params={"email": "student@mergington.edu"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_student_not_signed_up(client):
    response = client.delete(
        "/activities/Chess%20Club/signup",
        params={"email": "missing.student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}


def test_route_function_signup_mutates_participants_list():
    email = "unit.student@mergington.edu"

    result = app_module.signup_for_activity("Science Club", email)

    assert result == {"message": f"Signed up {email} for Science Club"}
    assert email in app_module.activities["Science Club"]["participants"]


def test_route_function_signup_raises_for_duplicate_registration():
    email = app_module.activities["Science Club"]["participants"][0]

    try:
        app_module.signup_for_activity("Science Club", email)
        raise AssertionError("Expected duplicate signup to raise HTTPException")
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "Student already signed up for this activity"


def test_route_function_unregister_raises_for_missing_registration():
    try:
        app_module.unregister_from_activity("Science Club", "absent.student@mergington.edu")
        raise AssertionError("Expected missing registration to raise HTTPException")
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Student is not signed up for this activity"


def test_tests_are_isolated_between_runs(client):
    email = "isolation.student@mergington.edu"

    signup_response = client.post("/activities/Art%20Studio/signup", params={"email": email})
    assert signup_response.status_code == 200
    assert email in app_module.activities["Art Studio"]["participants"]
