import secrets
from typing import Union
from fastapi import FastAPI, Request, Body, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from chatgpt import chatbot
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from utils import PermissionNotEnough


app = FastAPI()
security = HTTPBasic()


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = b"georgeEdison"
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = b"sword&fish"
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


class ChatRequest(BaseModel):
    name: str
    description: Union[str, None] = None
    price: float
    tax: Union[float, None] = None


class ChatResponse(BaseModel):
    name: str
    description: Union[str, None] = None
    price: float
    tax: Union[float, None] = None


@app.post("/chat" credentials: HTTPBasicCredentials=Depends(security), summary="ChatGPT接口")
async def chat(request: Request, p: str = Body("", title="发言", embed=True)):
    if "authorization" not in request.headers.keys():
        raise PermissionNotEnough()
    else:
        token = request.headers.get("authorization")

        if "user" not in payload["scopes"]:
            raise PermissionNotEnough()
        response = chatbot.ask(p, conversation_id=payload["sub"])
        return response["choices"][0]["text"]
