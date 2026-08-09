import pytest

def test_register_success(client, db_session):
    response = client.post("/auth/register", json={
        "username": "new_student",
        "password": "securepassword123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["is_admin"] is False
    
    # Verify in DB
    from models.user import User
    user = db_session.query(User).filter(User.username == "new_student").first()
    assert user is not None
    assert user.is_admin is False

def test_register_duplicate(client, student_user):
    # Attempt to register with the same username as student_user
    response = client.post("/auth/register", json={
        "username": "test_student",
        "password": "anotherpassword"
    })
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_login_success(client, student_user, test_password):
    response = client.post("/auth/login", json={
        "username": "test_student",
        "password": test_password
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["is_admin"] is False

def test_login_admin_success(client, admin_user, test_password):
    response = client.post("/auth/login", json={
        "username": "test_admin",
        "password": test_password
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["is_admin"] is True

def test_login_failure_wrong_password(client, student_user):
    response = client.post("/auth/login", json={
        "username": "test_student",
        "password": "wrongpassword!"
    })
    
    assert response.status_code == 401

def test_login_failure_wrong_username(client):
    response = client.post("/auth/login", json={
        "username": "nonexistent_user",
        "password": "password"
    })
    
    assert response.status_code == 401
