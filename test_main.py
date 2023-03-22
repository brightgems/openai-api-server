
import pytest
import json
from fastapi.testclient import TestClient
from config import JWT_SECRET_KEY
from main import app

client = TestClient(app)


@pytest.fixture(scope="package")
def jwt_headers():
    data = {
        'username': 'george.pan@unilever.com',
        'password': JWT_SECRET_KEY}
    rep = client.post(
        '/login',
        data=json.dumps(data),
        headers={'content-type': 'application/json'}
    )
    tokens = rep.json()
    return {
        'content-type': 'application/json',
        'authorization': 'Bearer %s' % tokens['access_token']
    }


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}


def test_reject_chat_msg():
    response = client.post("/chat")
    assert response.status_code == 422, "JWT should reject unauthorized request"


def test_ping_jwt(jwt_headers):
    response = client.get("/ping", headers=jwt_headers)
    assert response.status_code == 200


def test_get_web_auth_token(jwt_headers):
    response = client.get("/web_auth_token", headers=jwt_headers)
    assert response.status_code == 200


def test_send_chat_msg(jwt_headers):
    data = {
        "message": "1+1="
    }
    response = client.post("/chat", headers=jwt_headers, json=data)
    assert response.status_code != 422, "chat failed:" + str(response.json())
    print(response.json())


def test_embedding(jwt_headers):
    data = {
        "text": "1+1="
    }
    response = client.post("/embedding", headers=jwt_headers, json=data)
    assert response.status_code != 422, "embedding failed:" + str(response.json())
    print(response.json())
