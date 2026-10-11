"""Date steps D1 to D4 (implementation-details section 1.5). Protected."""

import datetime as dt

import pytest

from standup_tracker.dates import days_in_phrase, resolve_due
from standup_tracker.models import Turn

MON, TUE, WED, THU, FRI = (dt.date(2025, 10, d) for d in (13, 14, 15, 16, 17))


def resolve(phrase, sentence, standup, quote=None):
    turn = Turn(n=1, speaker="Sam", text=sentence)
    return resolve_due(phrase, [(quote or sentence, turn)], standup)


# phrase, the turn it sits in, standup date, expected step, expected date
CASES = [
    # D3: one computable day
    ("today", "Fix is going out today.", TUE, "D3", TUE),
    ("tonight", "I'll send something tonight.", WED, "D3", WED),
    ("tomorrow", "Should be done tomorrow, it's small.", THU, "D3", FRI),
    ("Monday", "Monday is more realistic.", MON, "D3", dt.date(2025, 10, 20)),
    ("Monday", "Anything of hers rolls to Monday.", FRI, "D3", dt.date(2025, 10, 20)),
    ("Wednesday", "Say Wednesday?", THU, "D3", dt.date(2025, 10, 22)),
    ("Friday", "Done by Friday.", FRI, "D3", dt.date(2025, 10, 24)),
    ("tomorrow", "Shipping tomorrow.", FRI, "D3", dt.date(2025, 10, 18)),  # weekends are not skipped
    # leftover words are ignored unless they shift the day
    ("Still Monday", "Still Monday.", TUE, "D3", dt.date(2025, 10, 20)),
    ("Should be done tomorrow", "Should be done tomorrow, it's small.", THU, "D3", FRI),
    ("by Friday", "I'll have it by Friday.", MON, "D3", FRI),
    ("this Friday", "Aiming for this Friday.", MON, "D3", FRI),
    # stand-alone forms and times of day
    ("this afternoon", "I'll push it this afternoon.", WED, "D3", WED),
    ("this morning", "Went out this morning.", WED, "D3", WED),
    ("end of day", "You'll have it end of day.", WED, "D3", WED),
    ("tomorrow morning", "The cert will be done tomorrow morning.", TUE, "D3", WED),
    ("today, after lunch", "Yeah, today, after lunch.", FRI, "D3", FRI),
    # written dates
    ("30 October", "Launch is 30 October.", MON, "D3", dt.date(2025, 10, 30)),
    ("Oct 30", "Launch is Oct 30.", MON, "D3", dt.date(2025, 10, 30)),
    ("3 October", "Audit is 3 October.", MON, "D3", dt.date(2026, 10, 3)),  # no year: first on or after
    ("13 October", "Due 13 October.", MON, "D3", MON),
    ("2025-11-02", "Due 2025-11-02.", MON, "D3", dt.date(2025, 11, 2)),
    ("5 November 2026", "Due 5 November 2026.", MON, "D3", dt.date(2026, 11, 5)),
    # D2: hedged, conditional, or two days
    ("today", "Should have a fix today, maybe tomorrow worst case.", MON, "D2", None),
    ("today, maybe tomorrow", "Should have a fix today, maybe tomorrow worst case.", MON, "D2", None),
    ("Tomorrow", "Tomorrow, probably.", TUE, "D2", None),
    ("Friday", "Hopefully Friday.", MON, "D2", None),
    ("tomorrow", "If the cert lands, I'll deploy tomorrow.", MON, "D2", None),
    ("Friday", "Friday, unless review drags.", MON, "D2", None),
    ("Thursday or Friday", "Thursday or Friday.", MON, "D2", None),
    # D4: a day-shifting word, or no day code knows
    ("next Friday", "It lands next Friday.", MON, "D4", None),
    ("last Friday", "We agreed that last Friday.", MON, "D4", None),
    ("next week", "We should do a retro next week.", FRI, "D4", None),
    ("end of week", "Done by end of week.", MON, "D4", None),
    ("after this", "I'll look at the PR after this.", TUE, "D4", None),
    ("the 24th", "It ships the 24th.", MON, "D4", None),
    ("in two days", "Ready in two days.", MON, "D4", None),
    ("at some point", "Someone should fix that at some point.", MON, "D4", None),
    ("end of sprint", "Done by end of sprint.", MON, "D4", None),
    ("10/11", "Due 10/11.", MON, "D4", None),
    ("Friday or so", "Friday or so.", MON, "D4", None),
]


@pytest.mark.parametrize("phrase,sentence,standup,step,date", CASES)
def test_date_steps(phrase, sentence, standup, step, date):
    result = resolve(phrase, sentence, standup)
    assert (result.step, result.date) == (step, date)


def test_phrase_not_in_any_quote_is_d1():
    result = resolve("Friday", "I'll ship it soon, promise.", MON)
    assert result.step == "D1" and result.reason


def test_a_hedge_in_another_sentence_of_the_turn_does_not_count():
    turn = Turn(n=1, speaker="Sam", text="Fix is going out today. Might be related to the other thing, might not.")
    result = resolve_due("today", [("fix is going out today", turn)], TUE)
    assert (result.step, result.date) == ("D3", TUE)


def test_other_days_in_the_sentence_do_not_make_it_a_hedge():
    text = "We said Friday for that, but with me losing this morning to it, Monday is more realistic."
    result = resolve("Monday", text, MON, quote="Monday is more realistic.")
    assert (result.step, result.date) == ("D3", dt.date(2025, 10, 20))


def test_two_days_returned_after_a_self_correction_clear_the_date():
    turn = Turn(n=1, speaker="Sam", text="Tuesday. Sorry, not Tuesday, Thursday.")
    result = resolve_due("not Tuesday, Thursday", [(turn.text, turn)], MON)
    assert result.step == "D2" and result.reason == "two days named"


def test_reasons_name_the_word():
    assert resolve("Tomorrow", "Tomorrow, probably.", TUE).reason == "hedged: 'probably'"
    assert resolve("tomorrow", "Once the cert lands, tomorrow.", TUE).reason == "conditional: 'once'"


def test_days_in_phrase_reports_shifting_words():
    assert days_in_phrase("next Friday", MON) == ([FRI], True)
    assert days_in_phrase("Friday", MON) == ([FRI], False)


def test_a_phrase_is_found_inside_a_possessive():
    result = resolve("Wednesday", "Wednesday's fine.", THU)
    assert (result.step, result.date) == ("D3", dt.date(2025, 10, 22))
