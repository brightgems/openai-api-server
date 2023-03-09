
from pydantic import BaseModel


users = [("openaiDriver", "hope&poem")]


class AuthSettings(BaseModel):
    authjwt_secret_key: str = "Jy771qqJWmvQN7c7oU1"
    algorithm = "HS256"

    @classmethod
    def is_authenticated(cls, username, password):
        return username.count("@unilever.com")


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
