"""Date steps D1 to D4: a due phrase, the words around it and the standup date give a date, or none and why."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass

from . import vocab
from .models import Turn
from .transcript import locate, normalise, sentence_holding


@dataclass(frozen=True)
class DateResult:
    step: str  # "D1", "D2", "D3" or "D4"
    date: dt.date | None = None
    reason: str | None = None  # set for D1 and D2; D4 gets one from the caller if a date was cleared
    vague: bool = False  # D4 only: no day and no day-shifting word ("soon"). Says nothing about a date held


def _has_word(text: str, word: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(word)}(?![a-z0-9])", text) is not None


def _remove_word(text: str, word: str, replacement: str = " ") -> str:
    return re.sub(rf"(?<![a-z0-9]){re.escape(word)}(?![a-z0-9])", replacement, text)


_MONTH = "|".join(sorted(vocab.MONTHS, key=len, reverse=True))
_ISO = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
_DAY_MONTH = re.compile(rf"(?<![a-z0-9])(\d{{1,2}})(?:st|nd|rd|th)?(?: of)? ({_MONTH})(?![a-z])(?:,? (\d{{4}}))?")
_MONTH_DAY = re.compile(rf"(?<![a-z0-9])({_MONTH}) (\d{{1,2}})(?:st|nd|rd|th)?(?![a-z0-9])(?:,? (\d{{4}}))?")


def _make_date(year: int | None, month: int, day: int, standup: dt.date) -> dt.date | None:
    try:
        if year is not None:
            return dt.date(year, month, day)
        candidate = dt.date(standup.year, month, day)
        return candidate if candidate >= standup else dt.date(standup.year + 1, month, day)
    except ValueError:
        return None


def days_in_phrase(phrase: str, standup: dt.date) -> tuple[list[dt.date], bool]:
    """Every day the phrase names that code can work out, and whether a day-shifting word is left over."""
    text = normalise(phrase)
    for form in vocab.STANDALONE_TODAY:
        text = _remove_word(text, form, " today ")
    for word in vocab.TIME_OF_DAY:
        text = _remove_word(text, word)

    found: list[dt.date] = []

    def take(pattern: re.Pattern[str], build) -> None:
        nonlocal text
        for match in list(pattern.finditer(text)):
            made = build(match)
            if made:
                found.append(made)
        text = pattern.sub(" ", text)

    take(_ISO, lambda m: _make_date(int(m[1]), int(m[2]), int(m[3]), standup))
    take(_DAY_MONTH, lambda m: _make_date(int(m[3]) if m[3] else None, vocab.MONTHS[m[2]], int(m[1]), standup))
    take(_MONTH_DAY, lambda m: _make_date(int(m[3]) if m[3] else None, vocab.MONTHS[m[1]], int(m[2]), standup))

    for word in re.findall(r"[a-z]+", text):
        if word in ("today", "tonight"):
            found.append(standup)
        elif word == "tomorrow":
            found.append(standup + dt.timedelta(days=1))
        elif word in vocab.WEEKDAYS:
            ahead = (vocab.WEEKDAYS.index(word) - standup.weekday()) % 7 or 7
            found.append(standup + dt.timedelta(days=ahead))

    shifting = any(_has_word(text, word) for word in vocab.DAY_SHIFTING)
    return found, shifting


def resolve_due(phrase: str, quotes: list[tuple[str, Turn]], standup: dt.date) -> DateResult:
    """quotes: the change's quotes, each with the turn it was found in. The first step that matches decides."""
    holder = next(((q, t) for q, t in quotes if locate(q, phrase) >= 0), None)
    if holder is None:
        return DateResult("D1", reason="date phrase not in the quoted words")

    sentence = sentence_holding(holder[1], holder[0], phrase)
    for word in vocab.HEDGE_WORDS:
        if _has_word(sentence, word):
            return DateResult("D2", reason=f"hedged: '{word}'")
    for word in vocab.CONDITION_WORDS:
        if _has_word(sentence, word):
            return DateResult("D2", reason=f"conditional: '{word}'")

    days, shifting = days_in_phrase(phrase, standup)
    distinct = sorted(set(days))
    if len(distinct) >= 2:
        return DateResult("D2", reason="two days named")
    if len(distinct) == 1 and not shifting:
        return DateResult("D3", date=distinct[0])
    return DateResult("D4", vague=not days and not shifting)
