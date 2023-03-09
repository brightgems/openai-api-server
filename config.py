from dotenv import load_dotenv, find_dotenv
import os

# important: need to override exising env vars
load_dotenv(find_dotenv(".env"), override=True)

JWT_SECRET_KEY = "Jy771qqJWmvQN7c7oU1"
GPT_ENGINE = os.environ.get("GPT_ENGINE") or "text-davinci-003"
CHAT_MODEL = os.environ.get("CHAT_MODEL") or "gpt-3.5-turbo"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
