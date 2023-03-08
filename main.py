import secrets
from typing import Union
from fastapi import FastAPI, Request, Body, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from chatgpt import chatbot
from utils.schema import ChatRequest, Settings, User
from utils.web_auth import Authenticator

app = FastAPI()


@AuthJWT.load_config
def get_config():
    return Settings()

# exception handler for authjwt
# in production, you can tweak performance using orjson response


@app.get('/')
def home():
    return {"msg": "Hello World"}


@app.post('/login')
def login(user: User, Authorize: AuthJWT = Depends()):
    if user.username.startswith("unilever"):
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
    current_user = Authorize.get_jwt_subject()
    print(current_user)
    response = chatbot.ask(ask.message, conversation_id=ask.conversationId)
    return {"ask": ask.message, "reponse": response["choices"][0]["text"]}


@app.post("/auth_token", summary="获取网页端的access token")
async def auth_token(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    au = Authenticator("freemanjameshr@gmail.com", "a12345678")
    au.begin()
    access_token = au.get_access_token()
    return access_token
