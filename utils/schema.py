
from typing import Optional
from pydantic import BaseModel
import requests
from config import JWT_SECRET_KEY, CHAT_MODEL

users = [("openaiDriver", "hope&poem")]


class AuthSettings(BaseModel):
    authjwt_secret_key: str = JWT_SECRET_KEY
    algorithm = "HS256"

    @classmethod
    def is_authenticated(cls, username, password):
        """
         Checks if username and password are valid. This is used to verify a user's access token to the china.

         @param cls - The class that is calling this function
         @param username - The username of the user
         @param password - The password of the user ( JWT ).

         @return True if the user is authenticated False otherwise.
        """
        is_authenticated = username.count("@unilever.com") and password == JWT_SECRET_KEY

        # Checks if the user is authenticated
        if not is_authenticated and password:
            resp = requests.get('https://cmiai-agileinnovation.unilever-china.com/api/v1/me',
                                headers={"Content-Type": "application/json", "Authorization": "Bearer " + password})
            return resp.status_code == 200
        return is_authenticated


class User(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    conversationId: Optional[str] = None
    parentMessageId: Optional[str] = None
    message: str
    # templerature of 0 will create determinstic result
    temperature: Optional[float] = 0.1
    model: str = CHAT_MODEL
    max_tokens: int = 4000
    base_prompt: None


class EmbeddingRequest(BaseModel):
    text: str
    model: Optional[str] = "text-embedding-ada-002"


class ChatResponse(BaseModel):
    ask: str = None
    response: str = None
