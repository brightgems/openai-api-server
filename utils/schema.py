
from pydantic import BaseModel
import requests
from config import JWT_SECRET_KEY

users = [("openaiDriver", "hope&poem")]


class AuthSettings(BaseModel):
    authjwt_secret_key: str = JWT_SECRET_KEY
    algorithm = "HS256"

    @classmethod
    def is_authenticated(cls, username, password):
        is_authenticated = username.count("@unilever.com") and password == JWT_SECRET_KEY
        if not is_authenticated and password:
            resp = requests.get('https://cmiai-agileinnovation.unilever-china.com/api/v1/me',
                                headers={"Content-Type": "application/json", "Authorization": "Bearer "+password})
            return resp.status_code == 200


class User(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    conversationId: int = None
    parentMessageId: int = None
    message: str


class ChatResponse(BaseModel):
    ask: str = None
    response: str = None
