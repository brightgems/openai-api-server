import secrets
from typing import Union
from fastapi import FastAPI, Request, Body, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from chatgpt import chatbot
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from utils import PermissionNotEnough


app = FastAPI()
security = HTTPBasic()


class Settings(BaseModel):
    authjwt_secret_key: str = "secret"

# region: interface


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
# endregion: interface

# callback to get your configuration


@AuthJWT.load_config
def get_config():
    return Settings()

# exception handler for authjwt
# in production, you can tweak performance using orjson response


@app.post('/login')
def login(user: User, Authorize: AuthJWT = Depends()):
    if user.username != "openaiDriver" or user.password != "hope&poem":
        raise HTTPException(status_code=401, detail="Bad username or password")

    # subject identifier for who this token is for example id or username from database
    access_token = Authorize.create_access_token(subject=user.username)
    return {"access_token": access_token}


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


@app.post("/chat", summary="ChatGPT接口")
async def chat(ask: ChatRequest, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    response = chatbot.ask(ask.message, conversation_id=ask.conversationId)
    return response["choices"][0]["text"]
