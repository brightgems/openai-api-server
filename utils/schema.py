
from pydantic import BaseModel


users = [("openaiDriver", "hope&poem")]


class Settings(BaseModel):
    authjwt_secret_key: str = "secret"
    algorithm = "HS256"


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
