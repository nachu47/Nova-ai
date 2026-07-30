def test_register_login_and_me(client):
    payload={"organization_name":"Example Ltd","full_name":"Grace Hopper","email":"grace@example.com","password":"VeryStrongPass123!","timezone":"UTC"}
    created=client.post('/api/v1/auth/register',json=payload);assert created.status_code==201
    token=created.json()['access_token'];me=client.get('/api/v1/auth/me',headers={'Authorization':f'Bearer {token}'});assert me.status_code==200;assert me.json()['email']=='grace@example.com';assert me.json()['role']=='owner'
    login=client.post('/api/v1/auth/login',json={'email':payload['email'],'password':payload['password']});assert login.status_code==200;assert login.json()['token_type']=='bearer'


def test_invalid_login(client):
    response=client.post('/api/v1/auth/login',json={'email':'missing@example.com','password':'WrongPassword123!'});assert response.status_code==401
