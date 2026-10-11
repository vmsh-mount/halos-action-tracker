"""The practice week's pieces of work and the transcript turns each rests on (evaluation-checks section 4).

Test data only. An anchor is (day, turn, words): words=None means the whole turn is about this work. Core
anchors are about this work and nothing else; shared anchors are also about another piece of work and are
used only to find an item, never to count where it belongs.
"""

from __future__ import annotations

import datetime as dt
from collections import Counter

from conftest import transcript
from standup_tracker.transcript import locate, normalise, split_turns

MON, TUE, WED, THU, FRI = "2025-10-13", "2025-10-14", "2025-10-15", "2025-10-16", "2025-10-17"

CORE = {
    "W1 search fix": [
        (MON, 1, "Search latency, still on it. I thought it was the query but I'm not sure anymore, I'll know by tonight. Should have a fix today, maybe tomorrow worst case."),
        (TUE, 1, None),
        (WED, 1, "Search fix is in review, finally."),
        (THU, 4, "Already did. Search is merged, I'm watching the numbers, so far so good."),
    ],
    "W2 auth bug": [
        (MON, 2, None), (MON, 3, None), (MON, 4, "Cool, Dev on auth then."),
        (TUE, 2, "PAY-231, the auth one. Confirmed it's token refresh, fix is going out today"),
        (WED, 2, "Auth is done, by the way"),
        (THU, 3, "Okay, so, bad news, 231 is back. Different cause this time, it's the session cookie, not the refresh. Someone reported it last night. I'm on it, should be quick now that I know where to look."),
        (FRI, 2, None),
    ],
    "W3 staging deploy": [(MON, 5, None), (MON, 6, None), (TUE, 4, None), (WED, 4, None)],
    "W4 flaky CI test": [
        (MON, 7, "Should we do something about the flaky test in CI? It failed twice yesterday, and both times it was the same timeout."),
        (MON, 8, "Let's talk about it after, not now."),
    ],
    "W5 export": [
        (MON, 9, None), (MON, 10, "Fine, Monday."), (TUE, 5, "Export's going fine. Still Monday."),
        (WED, 8, None), (THU, 6, None), (THU, 7, None),
    ],
    "W6 onboarding doc": [
        (MON, 12, None), (MON, 13, "Someone should fix that at some point."), (THU, 9, None),
        (THU, 10, "It's still a thing. Yes, take it."), (FRI, 6, "Onboarding doc, I've got a draft"),
    ],
    "W7 login slow": [
        (TUE, 2, "someone pinged me about the Atlas login being slow. Might be related to 231, might not. I'll look after."),
        (WED, 2, "The Atlas login thing was unrelated, it was just a slow query on the roles table, I fixed it while I was in there."),
    ],
    "W8 PR review (soft)": [(TUE, 5, "I'll look at Dev's PR after this."), (WED, 2, "Priya looked at it")],
    "W9 search PR review (soft)": [
        (WED, 2, "I'll review Arjun's search PR today."),
        (THU, 3, "the search PR, I reviewed it, left two comments, nothing big, Arjun you can just merge."),
    ],
    "W10 doc to send": [(WED, 6, None), (WED, 7, None)],
    "W11 retry bug": [(THU, 8, None), (FRI, 1, "so anything of hers rolls to Monday")],
    "W12 retro": [(FRI, 3, None)],
    "W13 schema review (soft)": [(FRI, 4, "Dev's reviewing."), (FRI, 5, None)],
    "W14 draft check (soft)": [(FRI, 7, None)],
}
SOFT = {name for name in CORE if "(soft)" in name}
FIRM = [name for name in CORE if name not in SOFT]

NOT_TRACKED = [
    (MON, 1, "I've got a call at ten fifteen"), (MON, 11, None), (WED, 5, None), (THU, 1, None), (THU, 2, None),
    (THU, 4, "For Rohan's benefit: Falcon is the payments DB migration, we're moving off the old schema. Priya and Dev are on it for the next two weeks. Dev, you're splitting with 231 until that's closed, then full time."),
    (FRI, 4, "Falcon schema draft is up, I put it in the channel."), (FRI, 8, None),
]

_TURNS = {day: split_turns(transcript(day)) for day in (MON, TUE, WED, THU, FRI)}


def _span(day: str, turn: int, words: str | None) -> tuple[int, int]:
    text = normalise(_TURNS[day][turn - 1].text)
    if words is None:
        return 0, len(text)
    start = locate(text, words)
    assert start >= 0, f"anchor not in {day} turn {turn}: {words!r}"
    return start, start + len(normalise(words))


def _overlaps(anchor, day: dt.date, quote) -> bool:
    a_day, a_turn, words = anchor
    if a_day != day.isoformat() or quote.turn != a_turn:
        return False
    a_start, a_end = _span(a_day, a_turn, words)
    q_start, q_end = _span(a_day, a_turn, quote.text)
    return q_start < a_end and a_start < q_end


def core_hits(item) -> Counter:
    """How many of the item's quotes, over its whole history, overlap each piece of work's core anchors."""
    hits: Counter = Counter()
    for entry in item.history:
        for quote in entry.quotes:
            for work, anchors in CORE.items():
                if any(_overlaps(anchor, entry.date, quote) for anchor in anchors):
                    hits[work] += 1
    return hits


def home(item) -> str | None:
    """The piece of work the item belongs to: the one its quotes overlap most. None if none, or if tied."""
    ranked = core_hits(item).most_common(2)
    if not ranked or (len(ranked) == 2 and ranked[0][1] == ranked[1][1]):
        return None
    return ranked[0][0]


def homes(items) -> dict[str, list]:
    """Piece of work -> the items at home on it. Removed items are left out."""
    out: dict[str, list] = {work: [] for work in CORE}
    for item in items:
        if not item.removed_on and home(item):
            out[home(item)].append(item)
    return out


def only(items_at_home: list):
    assert len(items_at_home) == 1, f"expected exactly one item, found {[i.id + ' ' + i.title for i in items_at_home]}"
    return items_at_home[0]


# Every anchor must be found in its turn, or the table above is wrong.
for _anchors in [*CORE.values(), NOT_TRACKED]:
    for _anchor in _anchors:
        _span(*_anchor)
