
import pytest
import json
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


@pytest.fixture(scope="package")
def jwt_headers():
    data = {
        'username': 'george.pan',
        'password': 'Unilever1234'
    }
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


def test_send_chat_msg(jwt_headers):
    data = {
        "message": "1+1=",
        "conversationId:": "1",
        "parentMessageId:": "1"
    }
    response = client.post("/chat", headers=jwt_headers, json=data)
    assert response.status_code != 422, "chat failed:" + str(response.json())
