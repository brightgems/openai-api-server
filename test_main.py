
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
        'password': "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2NzgzNzM4ODksIm5iZiI6MTY3ODM3Mzg4OSwianRpIjoiYTM2MGJlZjQtMmYwZi00OGQ4LWE4OTgtYTBiNDQ2MzYwNTU3IiwiZXhwIjoxNjc4NDE3MDg5LCJpZGVudGl0eSI6MSwiZnJlc2giOmZhbHNlLCJ0eXBlIjoiYWNjZXNzIiwidXNlcl9jbGFpbXMiOnsiZGVwYXJ0bWVudCI6IkFsbCBCdXNpbmVzcyBMaW5lcyIsInJvbGUiOiJJZGVhVGVzdEJhc2VzQWRtaW58QWRtaW4iLCJwZXJtaXNzaW9ucyI6WyJBRE1JTklTVEVSIiwiVFJFTkRfVklFV0VSIiwiVFJFTkRfQURNSU4iLCJJREVBR0VOX1ZJRVdFUiIsIklERUFHRU5fQ09OVFJJQlVUT1IiLCJJREVBVEVTVF9WSUVXRVIiLCJJREVBVEVTVF9WSUVXRVIiLCJJREVBVEVTVF9DT05UUklCVVRPUiIsIklERUFURVNUX0NPTlRSSUJVVE9SIiwiSURFQVRFU1RfUFJFTUlVTSIsIklERUFURVNUX0JBU0VTX01BTkFHRSIsIklERUFURVNUX0JBU0VTX01BTkFHRSIsIklERUFURVNUX0FETUlOIiwiQ0xBSU1BRFZJU09SX1ZJRVdFUiIsIkNMQUlNQURWSVNPUl9DT05UUklCVVRPUiIsIkNMQUlNQURWSVNPUl9BRE1JTiIsIkdPVEZMX0NPTlRSSUJVVE9SIiwiR09URkxfQURNSU4iLCJQQUlOU19WSUVXRVIiLCJQQUlOU19DT05UUklCVVRPUiIsIlBBSU5TX0FETUlOIiwiREVNQU5EX1ZJRVdFUiIsIkRFTUFORF9BRE1JTiIsIlBBQ0tBR0VfVklFV0VSIiwiUEFDS0FHRV9BRE1JTiIsIlNIT1BQRVJfVklFV0VSIiwiU0hPUFBFUl9BRE1JTiIsIlBST0xJQl9WSUVXRVIiLCJQUk9MSUJfRE9XTkxPQUQiLCJQUk9MSUJfQURNSU4iLCJDT05URU5UX1ZJRVdFUiIsIkNPTlRFTlRfQURNSU4iLCJNQVJLRVRQRVJGX1ZJRVdFUiIsIkQxMDBfQURNSU4iLCJLQV9BRE1JTiJdLCJjYXRlZ29yaWVzIjpbIkhDTCIsIkhDUyIsIlBDUyIsIlBDUCIsIlBXUyIsIlBDTyIsIlJFSSIsIkJTQyIsIkhDSCIsIkRJRCIsIkRJQSIsIlBXSCIsIkJIVyJdfX0.4UTvb1YZpyze8C5T6WMmHBzEPAtNPX32HVdHNz37RJ8"}
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
        "message": "1+1=",
        "conversationId:": 0,
        "parentMessageId:": 0
    }
    response = client.post("/chat", headers=jwt_headers, json=data)
    assert response.status_code != 422, "chat failed:" + str(response.json())
    print(response.json())
