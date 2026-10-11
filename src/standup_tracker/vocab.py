"""Fixed vocabularies. Plain data; the rest of the code reads these and assumes nothing else."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Status:
    key: str
    label: str
    closed: bool = False
    start: bool = False


STATUSES = (
    Status("open", "Open", start=True),
    Status("in_progress", "In progress"),
    Status("blocked", "Blocked"),
    Status("done", "Done", closed=True),
    Status("dropped", "Dropped", closed=True),
)

STATUS_KEYS = tuple(s.key for s in STATUSES)
START_STATUS = next(s.key for s in STATUSES if s.start)
_CLOSED = frozenset(s.key for s in STATUSES if s.closed)


def is_closed(status: str | None) -> bool:
    return status in _CLOSED


# Date step D2: scanned over the sentence that holds the due phrase.
HEDGE_WORDS = ("maybe", "probably", "perhaps", "possibly", "might", "hopefully", "worst case")
CONDITION_WORDS = ("if", "once", "unless")

# Date step D3. Stand-alone forms are checked first and mean the standup date.
STANDALONE_TODAY = ("this morning", "this afternoon", "this evening", "end of day")
# Then set aside, so "tomorrow morning" reads as "tomorrow".
TIME_OF_DAY = ("after lunch", "morning", "afternoon", "evening")

# Date step D4: scanned over the phrase once times of day are set aside.
DAY_SHIFTING = ("next", "last", "previous", "after", "following", "before", "week", "or")

# Lower-case words that may sit inside a speaker's name ("de Souza", "van der Berg").
NAME_PARTICLES = ("de", "da", "di", "du", "del", "della", "dos", "das", "van", "von", "der", "den", "la", "le", "al", "el", "bin", "ibn")

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")

MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
}
