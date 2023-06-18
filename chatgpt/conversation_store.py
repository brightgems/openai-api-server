
import json
import os
import threading
import time
from typing import List

from chatgpt.utils import ENCODER


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
            max_tokens = 3600
        prompt = '\n\n'.join([m['content'] for m in messages])
        if len(ENCODER.encode(prompt)) > max_tokens:
            # Remove oldest chat
            if len(self.chat_history) == 0:
                return messages
            self.chat_history.pop(0)
            # Construct prompt again
            messages = self.construct_prompt_messages(new_prompt, custom_history)
        return messages


SAVE_FILE = 'conversation.json'


class Conversation:
    """
    For handling multiple conversations
    """

    def __init__(self) -> None:
        self.conversations = {}
        if os.path.exists(SAVE_FILE):
            self.load(SAVE_FILE)
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
            self.save(SAVE_FILE)

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


conversation_store = Conversation()
