import pytest

def test_get_students_as_admin(client, admin_token, student_user):
    response = client.get(
        "/admin/students",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    students = response.json()
    assert isinstance(students, list)
    # The student fixture should be in this list
    assert any(s["username"] == "test_student" for s in students)

def test_get_students_as_student(client, student_token):
    response = client.get(
        "/admin/students",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    # Students are not admins, they should be forbidden
    assert response.status_code == 403

def test_get_students_unauthenticated(client):
    response = client.get("/admin/students")
    assert response.status_code == 401

def test_delete_student_as_admin(client, admin_token, student_user, db_session):
    student_id = student_user.id
    
    response = client.delete(
        f"/admin/students/{student_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    assert response.json() == {"message": "Student deleted"}
    
    # Verify deletion in DB
    from models.user import User
    deleted_user = db_session.query(User).filter(User.id == student_id).first()
    assert deleted_user is None

def test_delete_student_not_found(client, admin_token):
    response = client.delete(
        "/admin/students/9999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"

def test_delete_student_as_student(client, student_token, student_user):
    student_id = student_user.id
    
    response = client.delete(
        f"/admin/students/{student_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 403
