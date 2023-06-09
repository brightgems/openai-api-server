"""
A simple wrapper for the official ChatGPT API
"""
import json
import uuid
import os
import time
import threading
from datetime import date
from typing import Dict, List
import openai
import tiktoken
from config import CHAT_MODEL, OPENAI_API_KEY

ENCODER = tiktoken.get_encoding("gpt2")


def get_model_token_limit(model: str) -> int:
    """get max limit of token by model"""
    if model.startswith('gtp-4'):
        return 8000
    elif model.startswith('gpt-4-32k'):
        return 32000
    else:
        return 4000


def get_max_tokens(model: str, prompt: str, max_expect: int = 4000) -> int:
    """
    Get the max tokens for a complete message
    """
    token_limit = get_model_token_limit(model)
    max_tokens = token_limit - len(ENCODER.encode(prompt))
    if max_tokens < 0 or max_tokens > max_expect:
        return max_expect
    else:
        return max_tokens


class ChatgptAPIException(Exception):
    """ChatGPT API error
    """
    pass


SAVE_FILE = 'conversation.json'


class Chatbot:
    """
    Official ChatGPT API
    """

    def __init__(self, api_key: str, buffer: int = None) -> None:
        """
        Initialize Chatbot with API key (from https://platform.openai.com/account/api-keys)
        """
        openai.api_key = api_key or OPENAI_API_KEY
        self.conversation_store = Conversation()
        if os.path.exists(SAVE_FILE):
            self.conversation_store.load(SAVE_FILE)
        self.prompt = Prompt(buffer=buffer)
        # Create a thread to call conversation_store.save every 10 minutes.
        self.save_thread = threading.Thread(target=self._save_conversation_store)
        self.save_thread.daemon = True
        self.save_thread.start()

    def _save_conversation_store(self) -> None:
        """
        Save the conversation store to disk every 10 minutes.
        """
        while True:
            time.sleep(600)
            self.conversation_store.save(SAVE_FILE)

    def _get_completion(
        self,
        messages: List[dict],
        temperature: float = 0.5,
        model: str = CHAT_MODEL,
        max_tokens: int = 4000,
        stream: bool = False,
    ) -> Dict:
        """Get the completion function

        Arguments:
        messages -- conversation messages, example input:
            ```[{"role": "system", "content": "You are a helpful assistant."},
               {"role": "user", "content": "Who won the world series in 2020?"}]
            ```
        Return: return_description
        """
        # calcuate prompt and completion token length
        prompt = '\n\n'.join([m['content'] for m in messages])

        return openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=get_max_tokens(model, prompt, max_tokens),
            stop=["\n\n\n"],
            stream=stream,
        )

    def _process_completion(
        self,
        user_request: str,
        completion: dict,
        conversation_id: str = None
    ) -> str:
        if completion.get("choices") is None:
            raise ChatgptAPIException("ChatGPT API returned no choices")
        if len(completion["choices"]) == 0:
            raise ChatgptAPIException("ChatGPT API returned no choices")
        if completion["choices"][0].get("message") is None:
            raise ChatgptAPIException("ChatGPT API returned no message")
        response_text = completion["choices"][0]["message"]['content']
        # Add to chat history
        self.prompt.add_to_history(
            user_request,
            response_text
        )
        if conversation_id is not None:
            self.save_conversation(conversation_id)
        return response_text

    def _process_completion_stream(
        self,
        user_request: str,
        completion: dict,
        conversation_id: str = None
    ) -> str:
        full_response = ""
        for response in completion:
            if response.get("choices") is None:
                raise ChatgptAPIException("ChatGPT API returned no choices")
            if len(response["choices"]) == 0:
                raise ChatgptAPIException("ChatGPT API returned no choices")
            if response["choices"][0].get("finish_details") is not None:
                break
            if response["choices"][0].get("message") is None:
                raise ChatgptAPIException("ChatGPT API returned no text")
            response_text = completion["choices"][0]["message"]['content']
            if not response_text.strip():
                break
            yield response_text
            full_response += response_text

        # Add to chat history
        self.prompt.add_to_history(user_request, full_response)
        if conversation_id is not None:
            self.save_conversation(conversation_id)

    def ask(
        self,
        user_request: str,
        temperature: float = 0.5,
        conversation_id: str = None,
        model: str = CHAT_MODEL,
        max_tokens: int = 4000,
        base_prompt: str = None
    ) -> str:
        """
        Send a request to ChatGPT and return the response
        Args:
            model: model support by openai
            max_tokens: max tokens in response
        """
        if conversation_id is None:
            # create new conversation id
            conversation_id = str(uuid.uuid4())
        self.load_conversation(conversation_id)
        completion = self._get_completion(
            self.prompt.construct_prompt_messages(user_request, base_prompt=base_prompt),
            temperature,
            model,
            max_tokens
        )
        response_text = self._process_completion(user_request, completion)
        message_id = completion['id']
        return {'prompt': user_request, 'response': response_text, 'conversationId': conversation_id, 'messageId': message_id}

    def ask_stream(
        self,
        user_request: str,
        temperature: float = 0.5,
        conversation_id: str = None,
        model: str = CHAT_MODEL,
        max_tokens: int = 4000,
        base_prompt: str = None
    ) -> str:
        """
        Send a request to ChatGPT and yield the response
        """
        if conversation_id is None:
            # create new conversation id
            conversation_id = str(uuid.uuid4())
        self.load_conversation(conversation_id)
        completion = self._get_completion(
            self.prompt.construct_prompt_messages(user_request, base_prompt=base_prompt),
            temperature,
            model,
            max_tokens,
            stream=True
        )
        response_text = self._process_completion_stream(
            user_request=user_request,
            completion=completion
        )
        message_id = completion['id']
        return {'prompt': user_request, 'response': response_text, 'conversationId': conversation_id, 'messageId': message_id}

    def make_conversation(self, conversation_id: str) -> None:
        """
        Make a conversation
        """
        self.conversation_store.add_conversation(conversation_id, [])

    def rollback(self, num: int) -> None:
        """
        Rollback chat history num times
        """
        for _ in range(num):
            self.prompt.chat_history.pop()

    def reset(self) -> None:
        """
        Reset chat history
        """
        self.prompt.chat_history = []

    def load_conversation(self, conversation_id) -> None:
        """
        Load a conversation from the conversation history
        """
        if conversation_id not in self.conversation_store.conversations:
            # Create a new conversation
            self.make_conversation(conversation_id)
        self.prompt.chat_history = self.conversation_store.get_conversation(conversation_id)

    def save_conversation(self, conversation_id) -> None:
        """
        Save a conversation to the conversation history
        """
        self.conversation_store.add_conversation(conversation_id, self.prompt.chat_history)

    def text_embedding(self, text: str, model: str = "text-embedding-ada-002"):
        response = openai.Embedding.create(
            input=text,
            model=model)
        embeddings = response['data'][0]['embedding']
        return embeddings


class Prompt:
    """
    Prompt class with methods to construct prompt
    """

    def __init__(self, buffer: int = None) -> None:
        """
        Initialize prompt with base prompt
        """
        self.default_base_prompt = os.environ.get("CUSTOM_BASE_PROMPT")
        if not self.default_base_prompt:
            self.default_base_prompt = "You are ChatGPT, a large language model trained by OpenAI."
        # Track chat history
        self.chat_history: list = []
        self.buffer = buffer

    def add_to_chat_history(self, chat_qa: List) -> None:
        """
        Add chat to chat history for next prompt
        """
        self.chat_history.extend(chat_qa)

    def add_to_history(
        self,
        user_request: str,
        response: str
    ) -> None:
        """
        Add request/response to chat history for next prompt
        """
        self.add_to_chat_history(
            [
                {'role': "user", 'content': user_request},
                {'role': "system", 'content': response}]
        )

    def history(self, custom_history: list = None) -> str:
        """
        Return chat history
        """
        return custom_history or self.chat_history

    def construct_prompt_messages(
        self,
        new_prompt: str,
        custom_history: list = None,
        base_prompt: str = None
    ) -> List[dict]:
        """
        Construct prompt based on chat history and request
        """
        if not base_prompt:
            base_prompt = self.default_base_prompt
        messages = [{"role": "system", "content": base_prompt}] + \
            self.history(custom_history=custom_history) + \
            [{"role": "user", "content": new_prompt}]
        # Check if prompt over 4000 tokens
        if self.buffer is not None:
            max_tokens = 4000 - self.buffer
        else:
            max_tokens = 3200
        prompt = '\n\n'.join([m['content'] for m in messages])
        if len(ENCODER.encode(prompt)) > max_tokens:
            # Remove oldest chat
            if len(self.chat_history) == 0:
                return messages
            self.chat_history.pop(0)
            # Construct prompt again
            messages = self.construct_prompt_messages(new_prompt, custom_history)
        return messages


class Conversation:
    """
    For handling multiple conversations
    """

    def __init__(self) -> None:
        self.conversations = {}

    def add_conversation(self, key: str, history: list) -> None:
        """
        Adds a history list to the conversations dict with the id as the key
        """
        self.conversations[key] = history

    def get_conversation(self, key: str) -> list:
        """
        Retrieves the history list from the conversations dict with the id as the key
        """
        return self.conversations[key]

    def remove_conversation(self, key: str) -> None:
        """
        Removes the history list from the conversations dict with the id as the key
        """
        del self.conversations[key]

    def __str__(self) -> str:
        """
        Creates a JSON string of the conversations
        """
        return json.dumps(self.conversations)

    def save(self, file: str) -> None:
        """
        Saves the conversations to a JSON file
        """
        with open(file, "w", encoding="utf-8") as f:
            f.write(str(self))

    def load(self, file: str) -> None:
        """
        Loads the conversations from a JSON file
        """
        with open(file, encoding="utf-8") as f:
            self.conversations = json.loads(f.read())
