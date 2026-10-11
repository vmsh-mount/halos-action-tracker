"""Turn splitting and quote matching (data-models section 2, implementation-details section 3.3)."""

import pytest

from standup_tracker.transcript import NoSpeakerTurns, find_quote, meets_length_rule, sentence_holding, split_turns

TEXT = """Ana: Okay, let's go. Search is still on me.
Ben: I'll take the login bug. Should be quick.
Ana: Sure.
Cy: APP merged.
Ben: Falcon is the migration. For
Rohan's benefit: it moves us off the old schema."""


@pytest.fixture
def turns():
    return split_turns(TEXT)


def test_one_turn_per_speaker_line_and_wrapped_lines_continue(turns):
    assert [(t.n, t.speaker) for t in turns] == [(1, "Ana"), (2, "Ben"), (3, "Ana"), (4, "Cy"), (5, "Ben")]
    assert turns[4].text.endswith("For Rohan's benefit: it moves us off the old schema.")


def test_crlf_input_gives_the_same_turns(turns):
    assert [t.text for t in split_turns(TEXT.replace("\n", "\r\n"))] == [t.text for t in turns]


def test_text_before_the_first_speaker_is_a_turn_with_no_speaker():
    turns = split_turns("Standup notes\nAna: Morning.")
    assert (turns[0].speaker, turns[0].text) == (None, "Standup notes")


def test_no_speaker_turn_stops():
    with pytest.raises(NoSpeakerTurns):
        split_turns("just some pasted text\nwith no speakers at all")


def test_quote_matching_ignores_case_spacing_and_curly_quotes(turns):
    assert find_quote(turns, "i’ll   TAKE the login bug").n == 2


def test_a_quote_with_an_ellipsis_is_not_found(turns):
    assert find_quote(turns, "I'll take ... Should be quick") is None


def test_a_quote_joining_two_turns_is_not_found(turns):
    assert find_quote(turns, "Should be quick. Sure.") is None


def test_changed_wording_is_not_found(turns):
    assert find_quote(turns, "I will take the login bug") is None


def test_length_rule(turns):
    assert meets_length_rule("I'll take the login bug", turns[1])  # four words or more
    assert not meets_length_rule("Should be quick.", turns[1])  # three words, part of a turn
    assert meets_length_rule("APP merged.", turns[3])  # a whole turn of two words
    assert meets_length_rule("app merged", turns[3])  # edge punctuation ignored
    assert not meets_length_rule("Sure.", turns[2])  # a whole turn, but one word


def test_sentence_holding_the_phrase(turns):
    assert sentence_holding(turns[1], "Should be quick.", "quick") == "should be quick"


def test_speaker_names_in_other_alphabets_with_hyphens_and_apostrophes():
    turns = split_turns("José: Listo.\nMary-Ann: Mine.\nO'Brien: Yes.\nDe Souza: Later.\nnote: not a speaker\nRohan's benefit: nor this")
    assert [t.speaker for t in turns] == ["José", "Mary-Ann", "O'Brien", "De Souza"]
    assert turns[3].text == "Later. note: not a speaker Rohan's benefit: nor this"


def test_a_name_alone_on_its_line_starts_a_turn():
    turns = split_turns("Ana:\nSearch is still on me.\nBen: Okay.")
    assert [(t.speaker, t.text) for t in turns] == [("Ana", "Search is still on me."), ("Ben", "Okay.")]


def test_times_and_urls_are_not_speakers():
    turns = split_turns("Ana: The call is at\n10:15 and the doc is at\nhttps://example.com/x")
    assert len(turns) == 1


def test_particles_and_titles_in_speaker_names():
    turns = split_turns("de Souza: One.\nDr. Rao: Two.\nVan der Berg: Three.\nthe plan: not a speaker\nde la: nor this")
    assert [t.speaker for t in turns] == ["de Souza", "Dr. Rao", "Van der Berg"]


def test_words_are_found_before_a_possessive_but_not_inside_a_word(turns):
    from standup_tracker.transcript import locate
    assert locate("Wednesday's fine.", "Wednesday") == 0
    assert locate("Wednesdays are fine.", "Wednesday") == -1
    assert locate("I'll take it", "I") == -1
    assert find_quote(split_turns("Ana: I'll look at Ben's PR after this."), "look at Ben").n == 1
