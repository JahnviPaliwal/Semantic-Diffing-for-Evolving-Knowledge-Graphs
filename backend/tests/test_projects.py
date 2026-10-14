"""Tests for project CRUD and user ownership enforcement."""


def test_create_and_list_projects(client, auth_headers):
    # Create project
    create_resp = client.post(
        "/api/projects",
        json={"name": "Acme Corp Policy", "description": "Tracking legal changes"},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    proj_id = create_resp.json()["id"]

    # List projects
    list_resp = client.get("/api/projects", headers=auth_headers)
    assert list_resp.status_code == 200
    projects = list_resp.json()
    assert len(projects) == 1
    assert projects[0]["id"] == proj_id
    assert projects[0]["name"] == "Acme Corp Policy"


def test_project_ownership_isolation(client, auth_headers, other_user_headers):
    # User 1 creates project
    create_resp = client.post(
        "/api/projects",
        json={"name": "Private Project", "description": "Confidential"},
        headers=auth_headers,
    )
    proj_id = create_resp.json()["id"]

    # User 2 tries to access User 1's project -> should get 403 Forbidden
    access_resp = client.get(f"/api/projects/{proj_id}", headers=other_user_headers)
    assert access_resp.status_code == 403
    assert access_resp.json()["error"]["code"] == "FORBIDDEN"

    # User 2 tries to delete User 1's project -> 403
    del_resp = client.delete(f"/api/projects/{proj_id}", headers=other_user_headers)
    assert del_resp.status_code == 403


def test_update_and_delete_project(client, auth_headers):
    create_resp = client.post(
        "/api/projects",
        json={"name": "Initial Name", "description": "Initial Desc"},
        headers=auth_headers,
    )
    proj_id = create_resp.json()["id"]

    # Update
    update_resp = client.put(
        f"/api/projects/{proj_id}",
        json={"name": "Updated Name"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated Name"

    # Delete
    del_resp = client.delete(f"/api/projects/{proj_id}", headers=auth_headers)
    assert del_resp.status_code == 200

    # Ensure deleted
    get_resp = client.get(f"/api/projects/{proj_id}", headers=auth_headers)
    assert get_resp.status_code == 404
