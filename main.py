import json
import logging
import asyncio
from logging.config import dictConfig
import datetime
from fastapi import FastAPI, Request, Body, Depends, HTTPException, WebSocket, status
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
import pytest
from chatgpt import Chatbot, AsyncChatbot
from config import OPENAI_API_KEY
from utils.log_config import LogConfig
from utils.schema import ChatRequest, EmbeddingRequest, AuthSettings, User
from utils.web_auth import Authenticator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

dictConfig(LogConfig().dict())
logger = logging.getLogger("mycoolapp")


origins = [
    "https://cmiai-agileinnovation.unilever-china.com",
    "https://ai-categorytrend.unilever-china.com",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


@AuthJWT.load_config
def get_config():
    return AuthSettings()


@app.get('/')
def home():
    return {"msg": "Hello World"}


@app.get("/ping", summary="ping test")
def ping(authorize: AuthJWT = Depends()):
    authorize.jwt_required()
    return True


@app.post('/login')
def login(user: User, authorize: AuthJWT = Depends()):
    if not AuthSettings.is_authenticated(user.username, user.password):
        raise HTTPException(status_code=401, detail="Bad username or password")

    # subject identifier for who this token is for example id or username from database
    expires = datetime.timedelta(days=1)
    access_token = authorize.create_access_token(subject=user.username, expires_time=expires)
    return {"access_token": access_token}


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


@app.post("/chat", summary="ChatGPT接口")
def chat(ask: ChatRequest, authorize: AuthJWT = Depends()):
    authorize.jwt_required()
    current_user = authorize.get_jwt_subject()
    logger.debug(current_user + "->" + ask.message)
    # Initialize chatbot
    chatbot_ins = Chatbot(api_key=OPENAI_API_KEY)
    return chatbot_ins.ask(
        ask.message, conversation_id=ask.conversationId, temperature=ask.temperature,
        model=ask.model, max_tokens=ask.max_tokens)


@app.post("/embedding", summary="Embedding接口")
def embedding(args: EmbeddingRequest, authorize: AuthJWT = Depends()):
    authorize.jwt_required()
    chatbot_ins = Chatbot(api_key=OPENAI_API_KEY)
    return chatbot_ins.text_embedding(args.text, args.model)


@app.websocket("/chat_stream", name="ChatGPT流式接口")
async def websocket_endpoint(websocket: WebSocket, authorize: AuthJWT = Depends()):
    """websocket for chat"""
    authorize.jwt_required("websocket", token=websocket.headers['authorization'].split(' ')[1])
    current_user = authorize.get_jwt_subject()
    await websocket.accept()
    # Initialize chatbot
    chatbot_ins = AsyncChatbot(api_key=OPENAI_API_KEY)

    while True:
        message = await websocket.receive_json()
        logger.debug(f'received message: {str(message)}')
        if message is None:
            break
        if current_user:
            logger.info(current_user + "->" + message['prompt'])
        try:
            words = await chatbot_ins.ask_stream(
                message['prompt'], conversation_id=message['conversationId'], temperature=message['temperature'],
                model=message['model'], max_tokens=message['max_tokens'])
        except Exception as ex:
            logger.error("Error occurred while calling OpenAI API: %s", ex)
            await websocket.send_json({'state': 'ERROR'})
            continue

        async for word in words:
            await websocket.send(word)
        await websocket.send_json({'state': 'EMD', 'conversationId': chatbot_ins.conversation_id})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, ws='websockets')
