from collections.abc import Iterable
from typing import Protocol

import httpx


class LLM(Protocol):
    def complete(self, messages: list[dict]) -> str: ...


class OllamaLLM:
    """Local model through Ollama's chat API. Free, private, no API key."""

    def __init__(self, model='llama3.2', host='http://localhost:11434', client=None):
        self.model, self.host = model, host.rstrip('/')
        self.client = client or httpx.Client(timeout=120)

    def complete(self, messages: list[dict]) -> str:
        resp = self.client.post(f'{self.host}/api/chat', json={
            'model': self.model,
            'messages': messages,
            'stream': False,
            'format': 'json',
            'options': {'temperature': 0},
        })
        resp.raise_for_status()
        return resp.json()['message']['content']


class ScriptedLLM:
    """Replays canned replies. Makes the loop testable without any model."""

    def __init__(self, replies: Iterable[str]):
        self.replies = list(replies)
        self.calls = 0

    def complete(self, messages: list[dict]) -> str:
        if self.calls >= len(self.replies):
            raise RuntimeError('ScriptedLLM ran out of replies')
        reply = self.replies[self.calls]
        self.calls += 1
        return reply
