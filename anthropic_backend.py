import os
from .base import Backend

try:
    import anthropic
except ImportError:
    anthropic = None


class AnthropicBackend(Backend):
    """Requires: pip install anthropic
    Requires: export ANTHROPIC_API_KEY=sk-...
    """

    def __init__(self, model: str = "claude-sonnet-4-6", max_tokens: int = 1024):
        if anthropic is None:
            raise RuntimeError("pip install anthropic")
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("Set ANTHROPIC_API_KEY in your environment")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def generate(self, system: str, messages: list) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=messages,
        )
        return "".join(
            block.text for block in resp.content if getattr(block, "type", "") == "text"
        )
