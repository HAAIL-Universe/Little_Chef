"""Speech-to-text normalization utilities.

Cleans common dictation artifacts so downstream regex patterns (MATCH,
CHECK, PLAN, CONSUME) fire reliably on voice-transcribed text.
"""

import re

# Filler words that speech engines often insert
_FILLER_RE = re.compile(r"\b(?:um+|uh+|er+|ah+|hmm+|like)\b", re.IGNORECASE)

# Common contractions that STT may expand or drop apostrophes on
_CONTRACTION_MAP: dict[str, str] = {
    "whats": "what's",
    "cant": "can't",
    "dont": "don't",
    "doesnt": "doesn't",
    "shouldnt": "shouldn't",
    "couldnt": "couldn't",
    "wouldnt": "wouldn't",
    "ive": "i've",
    "weve": "we've",
    "thats": "that's",
    "lets": "let's",
    "im": "i'm",
    "youre": "you're",
    "theyre": "they're",
    "hes": "he's",
    "shes": "she's",
    "its": "it's",
    "isnt": "isn't",
    "arent": "aren't",
    "wasnt": "wasn't",
    "werent": "weren't",
    "havent": "haven't",
    "hasnt": "hasn't",
    "didnt": "didn't",
    "wont": "won't",
}

_CONTRACTION_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _CONTRACTION_MAP) + r")\b",
    re.IGNORECASE,
)

# Collapse multi-spaces
_MULTI_SPACE_RE = re.compile(r"\s{2,}")


def normalize_stt(text: str) -> str:
    """Clean a speech-to-text transcript for reliable regex matching.

    Steps:
    1. Strip leading/trailing whitespace
    2. Remove filler words (um, uh, like)
    3. Restore apostrophes in dropped-contraction words
    4. Collapse multi-spaces
    """
    result = text.strip()

    # Remove fillers
    result = _FILLER_RE.sub("", result)

    # Restore contractions
    def _replace_contraction(m: re.Match) -> str:
        word = m.group(1).lower()
        replacement = _CONTRACTION_MAP.get(word, word)
        # Preserve original case for first char
        if m.group(1)[0].isupper():
            return replacement[0].upper() + replacement[1:]
        return replacement

    result = _CONTRACTION_RE.sub(_replace_contraction, result)

    # Collapse spaces
    result = _MULTI_SPACE_RE.sub(" ", result).strip()

    return result


def voice_hint_for(reply_text: str, *, max_chars: int = 200) -> str:
    """Generate a short TTS-friendly hint from a longer reply.

    Takes the first sentence or truncates at max_chars, whichever is shorter.
    """
    # First sentence
    for end in (".\n", ". ", "!\n", "! ", "?\n", "? "):
        idx = reply_text.find(end)
        if idx != -1 and idx < max_chars:
            return reply_text[: idx + 1].strip()

    if len(reply_text) <= max_chars:
        return reply_text.strip()

    # Truncate at word boundary
    truncated = reply_text[:max_chars].rsplit(" ", 1)[0]
    return truncated.rstrip(".,;:!?") + "…"
