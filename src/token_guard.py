"""Step 4: protect the expensive LLM call from huge or costly inputs."""
import re

MAX_INPUT_TOKENS = 120      # per message (small for demo; ~500 in production)
MAX_OUTPUT_TOKENS = 150     # pass this as max_tokens to the LLM
RUN_BUDGET_TOKENS = 1000    # total input tokens allowed per run (demo value)

def count_tokens(text: str) -> int:
    """Rough estimate: ~4 characters per token for English. Swap for tiktoken later."""
    return max(1, len(text) // 4)

_QUOTE = re.compile(r"(?ms)^(>.*$|On .{0,80} wrote:.*$|-{2,}\s*Original Message.*$)")
_SIGNATURE = re.compile(r"(?is)(\n--\s*\n|regards,|sent from my \w+).*$")

def strip_noise(text: str) -> str:
    """Remove quoted reply chains and signatures; they add tokens, not meaning."""
    text = _QUOTE.sub("", text)
    text = _SIGNATURE.sub("", text)
    return text.strip()

def trim_to_limit(text: str, limit: int = MAX_INPUT_TOKENS) -> str:
    """Keep the start AND the end: the real question is often in the last line."""
    if count_tokens(text) <= limit:
        return text
    chars = limit * 4
    head, tail = int(chars * 0.4), int(chars * 0.6)
    return text[:head].rstrip() + " ... " + text[-tail:].lstrip()

class TokenBudget:
    """Tracks total spend. When exhausted, callers must skip the LLM."""
    def __init__(self, total: int = RUN_BUDGET_TOKENS):
        self.total, self.used = total, 0

    def guard(self, text: str):
        """Return (text_for_llm, tokens, allowed). allowed=False -> send to Needs Review."""
        text = trim_to_limit(strip_noise(text))
        tokens = count_tokens(text)
        if self.used + tokens > self.total:
            return text, tokens, False
        self.used += tokens
        return text, tokens, True
