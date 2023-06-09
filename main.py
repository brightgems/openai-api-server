from .utils.log_config import LogConfig
import logging
from logging.config import dictConfig
import datetime
from fastapi import FastAPI, Request, Body, Depends, HTTPException, WebSocket, status
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from chatgpt import Chatbot
from config import OPENAI_API_KEY
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


# api declarations
chatBotIns = Chatbot(api_key=OPENAI_API_KEY)


@app.get('/')
def home():
    return {"msg": "Hello World"}


@app.get("/ping", summary="ping test")
def ping(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    return True


@app.post('/login')
def login(user: User, Authorize: AuthJWT = Depends()):
    if not AuthSettings.is_authenticated(user.username, user.password):
        raise HTTPException(status_code=401, detail="Bad username or password")

    # subject identifier for who this token is for example id or username from database
    expires = datetime.timedelta(days=1)
    access_token = Authorize.create_access_token(subject=user.username, expires_time=expires)
    return {"access_token": access_token}


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


@app.post("/chat", summary="ChatGPT接口")
def chat(ask: ChatRequest, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    current_user = Authorize.get_jwt_subject()
    logger.debug(current_user + "->" + ask.message)
    return chatBotIns.ask(
        ask.message, conversation_id=ask.conversationId, temperature=ask.temperature,
        model=ask.model, max_tokens=ask.max_tokens)


@app.post("/chat_stream", summary="ChatGPT流式接口")
def chat_stream(ask: ChatRequest, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    current_user = Authorize.get_jwt_subject()
    logger.debug(current_user + "->" + ask.message)
    # Initialize chatbot
    return chatBotIns.ask_stream(
        ask.message, conversation_id=ask.conversationId, temperature=ask.temperature,
        model=ask.model, max_tokens=ask.max_tokens)


@app.post("/embedding", summary="Embedding接口")
def chat(args: EmbeddingRequest, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    return chatBotIns.text_embedding(args.text, args.model)


@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    """websocket for chat"""
    while True:
        message = await websocket.receive()
        if message is None:
            break

        prompt = message.data
        # response = openai.Completion.create(
        #     prompt=prompt,
        #     engine="davinci",
        #     max_tokens=100,
        #     temperature=0.7,
        #     top_p=1.0,
        #     do_sample=True,
        # )

        # for word in response.choices[0].text.split():
        #     await websocket.send(word)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
