"""Splitting a transcript into speaker turns, and finding quoted words in them."""

from __future__ import annotations

import re

from . import vocab
from .models import Turn

# One to three words, then a colon. The words may follow on the same line or start on the next. Each word
# starts with a capital letter (any alphabet; hyphens and apostrophes allowed inside; a full stop may end
# it, as in "Dr.") or is a lower-case name particle. See _speaker_of.
_NAME_WORD = r"[^\W\d_](?:[^\W\d_]|['\u2019-])*\.?"
_SPEAKER_LINE = re.compile(rf"^({_NAME_WORD}(?: {_NAME_WORD}){{0,2}}):(?:\s+(.*))?$")
_WORD_CHAR = r"[\w']"
# Words end at a non-word character, or at a possessive: "Wednesday" is found in "Wednesday's fine".
_WORD_END = rf"(?=$|[^\w']|'s(?!{_WORD_CHAR}))"
_SENTENCE_END = ".?!"


class NoSpeakerTurns(ValueError):
    """The text has no line that starts a speaker turn."""


def split_turns(text: str) -> list[Turn]:
    turns: list[Turn] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.strip()
        if not line:
            continue
        match = _SPEAKER_LINE.match(line)
        if match and _is_name(match.group(1)):
            turns.append(Turn(n=len(turns) + 1, speaker=match.group(1), text=(match.group(2) or "").strip()))
        elif turns:
            turns[-1].text = f"{turns[-1].text} {line}".strip()
        else:
            turns.append(Turn(n=1, speaker=None, text=line))
    if not any(turn.speaker for turn in turns):
        raise NoSpeakerTurns("No line starts with a speaker name followed by a colon.")
    return turns


def _is_name(words: str) -> bool:
    parts = words.split(" ")
    capitalised = [part for part in parts if part[0].isupper()]
    return bool(capitalised) and all(part[0].isupper() or part in vocab.NAME_PARTICLES for part in parts)


def normalise(text: str) -> str:
    """Lower-case, straighten curly quotes, collapse whitespace. Nothing else."""
    text = text.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text.lower()).strip()


def locate(text: str, words: str) -> int:
    """Where the words sit in the text, as whole words, or -1. Both sides are normalised first."""
    haystack, needle = normalise(text), normalise(words)
    if not needle:
        return -1
    match = re.search(rf"(?<!{_WORD_CHAR}){re.escape(needle)}{_WORD_END}", haystack)
    return match.start() if match else -1


def find_quote(turns: list[Turn], quote: str) -> Turn | None:
    """The first turn whose words contain the quote, or None. A quote cannot start or end mid-word."""
    for turn in turns:
        if locate(turn.text, quote) >= 0:
            return turn
    return None


def word_count(text: str) -> int:
    return len(normalise(text).split())


def _strip_edges(text: str) -> str:
    return normalise(text).strip(" .,;:!?\"'-")


def meets_length_rule(quote: str, turn: Turn) -> bool:
    """Four words or longer, or a whole turn of two words or more."""
    if word_count(quote) >= 4:
        return True
    return word_count(turn.text) >= 2 and _strip_edges(quote) == _strip_edges(turn.text)


def sentence_holding(turn: Turn, quote: str, phrase: str) -> str:
    """The sentence of the turn that holds the phrase's first occurrence inside the quote."""
    text = normalise(turn.text)
    q_at, p_at = locate(turn.text, quote), locate(quote, phrase)
    if q_at < 0 or p_at < 0:
        return ""
    at = q_at + p_at
    start = max(text.rfind(ch, 0, at) for ch in _SENTENCE_END) + 1
    ends = [i for i in (text.find(ch, at) for ch in _SENTENCE_END) if i >= 0]
    end = min(ends) if ends else len(text)
    return text[start:end].strip()
