"""
A simple wrapper for the official ChatGPT API
"""
import json
import os
from datetime import date
from typing import Dict, List
import openai
import tiktoken
from config import CHAT_MODEL, OPENAI_API_KEY

ENCODER = tiktoken.get_encoding("gpt2")


def get_max_tokens(prompt: str) -> int:
    """
    Get the max tokens for a prompt
    """
    return 4000 - len(ENCODER.encode(prompt))


class Chatbot:
    """
    Official ChatGPT API
    """

    def __init__(self, api_key: str, buffer: int = None, engine: str = None) -> None:
        """
        Initialize Chatbot with API key (from https://platform.openai.com/account/api-keys)
        """
        openai.api_key = api_key or OPENAI_API_KEY
        self.conversations = Conversation()
        self.prompt = Prompt(buffer=buffer)
        self.engine = engine or CHAT_MODEL

    def _get_completion(
        self,
        messages: List[dict],
        temperature: float = 0.5,
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
        prompt = messages[-1]['content']

        return openai.ChatCompletion.create(
            model=self.engine,
            messages=messages,
            temperature=temperature,
            max_tokens=get_max_tokens(prompt),
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
            raise Exception("ChatGPT API returned no choices")
        if len(completion["choices"]) == 0:
            raise Exception("ChatGPT API returned no choices")
        if completion["choices"][0].get("message") is None:
            raise Exception("ChatGPT API returned no message")
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
                raise Exception("ChatGPT API returned no choices")
            if len(response["choices"]) == 0:
                raise Exception("ChatGPT API returned no choices")
            if response["choices"][0].get("finish_details") is not None:
                break
            if response["choices"][0].get("message") is None:
                raise Exception("ChatGPT API returned no text")
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
        conversation_id: str = None
    ) -> str:
        """
        Send a request to ChatGPT and return the response
        """
        if conversation_id is not None:
            self.load_conversation(conversation_id)
        completion = self._get_completion(
            self.prompt.construct_prompt_messages(user_request),
            temperature,
        )
        response_text = self._process_completion(user_request, completion)
        return response_text

    def ask_stream(
        self,
        user_request: str,
        temperature: float = 0.5,
        conversation_id: str = None,
    ) -> str:
        """
        Send a request to ChatGPT and yield the response
        """
        if conversation_id is not None:
            self.load_conversation(conversation_id)
        messages = self.prompt.construct_prompt_messages(user_request)
        response_text = self._process_completion_stream(
            user_request=user_request,
            completion=self._get_completion(messages, temperature, stream=True)
        )
        return response_text

    def make_conversation(self, conversation_id: str) -> None:
        """
        Make a conversation
        """
        self.conversations.add_conversation(conversation_id, [])

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
        if conversation_id not in self.conversations.conversations:
            # Create a new conversation
            self.make_conversation(conversation_id)
        self.prompt.chat_history = self.conversations.get_conversation(conversation_id)

    def save_conversation(self, conversation_id) -> None:
        """
        Save a conversation to the conversation history
        """
        self.conversations.add_conversation(conversation_id, self.prompt.chat_history)


class AsyncChatbot(Chatbot):
    """
    Official ChatGPT API (async)
    """

    async def _get_completion(
        self,
        messages: List[dict],
        temperature: float = 0.5,
        stream: bool = False,
    ):
        """
        Get the completion function
        """

        prompt = messages[-1]['content']

        return await openai.ChatCompletion.acreate(
            model=self.engine,
            messages=messages,
            temperature=temperature,
            max_tokens=get_max_tokens(prompt),
            stop=["\n\n\n"],
            stream=stream,
        )

    async def ask(
        self,
        user_request: str,
        temperature: float = 0.5
    ) -> str:
        """
        Same as Chatbot.ask but async
        }
        """
        completion = await self._get_completion(
            self.prompt.construct_prompt_messages(user_request),
            temperature,
        )
        response_text = self._process_completion(user_request, completion)
        return response_text

    async def ask_stream(
        self,
        user_request: str,
        temperature: float = 0.5,
    ) -> str:
        """
        Same as Chatbot.ask_stream but async
        """
        prompt = self.prompt.construct_prompt_messages(user_request)
        response_text = self._process_completion_stream(
            user_request=user_request,
            completion=await self._get_completion(prompt, temperature, stream=True)
        )
        return response_text


class Prompt:
    """
    Prompt class with methods to construct prompt
    """

    def __init__(self, buffer: int = None) -> None:
        """
        Initialize prompt with base prompt
        """
        self.base_prompt = os.environ.get("CUSTOM_BASE_PROMPT")
        if not self.base_prompt:
            self.base_prompt = "You are ChatGPT, a large language model trained by OpenAI." + \
                "Respond conversationally. Do not answer as the user. Current date: " + str(date.today())
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
        custom_history: list = None
    ) -> List[dict]:
        """
        Construct prompt based on chat history and request
        """
        messages = [{"role": "system", "content": self.base_prompt}] + \
            self.history(custom_history=custom_history) + \
            [{"role": "user", "content": new_prompt}]
        # Check if prompt over 4000*4 characters
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


# Initialize chatbot
chatbot = Chatbot(api_key=OPENAI_API_KEY)
