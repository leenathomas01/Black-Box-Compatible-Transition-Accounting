import json
import urllib.request
from .base import Backend


class OllamaBackend(Backend):
    """Fully local. Requires Ollama running (https://ollama.com) and a model pulled,
    e.g.:  ollama pull llama3.1:8b
    """

    def __init__(self, model: str = "llama3.1:8b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")

    def generate(self, system: str, messages: list) -> str:
        payload = {
            "model": self.model,
            "system": system,
            "messages": messages,
            "stream": False,
        }
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("message", {}).get("content", "")
