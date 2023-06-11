"""
A simple wrapper for the official ChatGPT API
"""
import uuid
from typing import Dict, List
import openai

from config import CHAT_MODEL, OPENAI_API_KEY
from .utils import ChatgptAPIException, get_max_tokens
from .conversation_store import Prompt, conversation_store


class Chatbot:
    """
    Official ChatGPT API
    """

    def __init__(self, api_key: str, buffer: int = None) -> None:
        """
        Initialize Chatbot with API key (from https://platform.openai.com/account/api-keys)
        """
        openai.api_key = api_key or OPENAI_API_KEY
        self.prompt = Prompt(buffer=buffer)

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
            timeout=60
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

    def make_conversation(self, conversation_id: str) -> None:
        """
        Make a conversation
        """
        conversation_store.add_conversation(conversation_id, [])

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
        if conversation_id not in conversation_store.conversations:
            # Create a new conversation
            self.make_conversation(conversation_id)
        self.prompt.chat_history = conversation_store.get_conversation(conversation_id)

    def save_conversation(self, conversation_id) -> None:
        """
        Save a conversation to the conversation history
        """
        conversation_store.add_conversation(conversation_id, self.prompt.chat_history)

    def text_embedding(self, text: str, model: str = "text-embedding-ada-002"):
        response = openai.Embedding.create(
            input=text,
            model=model)
        embeddings = response['data'][0]['embedding']
        return embeddings


class AsyncChatbot(Chatbot):
    """
    Official ChatGPT API (async)
    """

    async def _process_completion_stream(
        self,
        user_request: str,
        completion: dict,
        conversation_id: str = None
    ) -> str:
        full_response = ""
        async for response in completion:
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

    async def _get_completion(
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
        return await openai.Completion.acreate(
            engine=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=get_max_tokens(model, prompt, max_tokens),
            stop=["\n\n\n"],
            stream=stream,
            timeout=60
        )

    async def ask(
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

    async def ask_stream(
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
        self.conversation_id = conversation_id
        return self._process_completion_stream(
            user_request=user_request,
            completion=completion
        )
