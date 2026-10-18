from sqlalchemy import select

from app.api.deps import get_db
from app.main import app
from app.models.entities import User


def _register(client, email, org):
    response=client.post("/api/v1/auth/register",json={"organization_name":org,"full_name":"Test User","email":email,"password":"StrongPassword123!","timezone":"UTC"})
    assert response.status_code==201,response.text
    return {"Authorization":f"Bearer {response.json()['access_token']}"}


def _make_superadmin(email):
    db=next(app.dependency_overrides[get_db]())
    try:user=db.scalar(select(User).where(User.email==email));user.role="superadmin";db.commit()
    finally:db.close()


def test_suspended_organization_is_blocked_and_can_be_reactivated(client):
    admin_headers=_register(client,"root@example.com","Platform HQ");_make_superadmin("root@example.com")
    tenant_headers=_register(client,"tenant@example.com","Tenant Ltd")
    assert client.get("/api/v1/auth/me",headers=tenant_headers).status_code==200

    orgs=client.get("/api/v1/admin/organizations",headers=admin_headers).json()
    tenant_org=next(o for o in orgs if o["name"]=="Tenant Ltd")
    assert client.post(f"/api/v1/admin/organizations/{tenant_org['id']}/suspend",headers=admin_headers).status_code==200

    assert client.get("/api/v1/auth/me",headers=tenant_headers).status_code==403
    login=client.post("/api/v1/auth/login",json={"email":"tenant@example.com","password":"StrongPassword123!"})
    assert login.status_code==403
    assert client.get("/api/v1/auth/me",headers=admin_headers).status_code==200

    assert client.post(f"/api/v1/admin/organizations/{tenant_org['id']}/activate",headers=admin_headers).status_code==200
    assert client.get("/api/v1/auth/me",headers=tenant_headers).status_code==200


def test_superadmin_cannot_suspend_own_organization(client):
    admin_headers=_register(client,"root@example.com","Platform HQ");_make_superadmin("root@example.com")
    own=client.get("/api/v1/admin/organizations",headers=admin_headers).json()[0]
    assert client.post(f"/api/v1/admin/organizations/{own['id']}/suspend",headers=admin_headers).status_code==409
