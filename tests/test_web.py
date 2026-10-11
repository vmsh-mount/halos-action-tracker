"""The review workspace, driven through the app on saved model answers. No network."""

import pytest
from fastapi.testclient import TestClient

from conftest import ROOT, WEEK, transcript
from standup_tracker import store
from standup_tracker.settings import Settings
from standup_tracker.web.app import create_app

MON, TUE = WEEK[0], WEEK[1]


@pytest.fixture
def site(tmp_path):
    settings = Settings(
        state_file=tmp_path / "state.json", team_file=ROOT / "config" / "team.json",
        saved_answers=ROOT / "tests" / "saved_answers", env={"LLM_PROVIDER": "replay"},
    )
    client = TestClient(create_app(settings))
    client.state_file = settings.state_file
    return client


def state_of(site):
    return store.load_state(site.state_file)


def submit(site, day, **extra):
    return site.post("/standup", data={"date": day, "text": transcript(day), **extra})


def item_by_title(site, words):
    return next(i for i in state_of(site).draft.items_after if words in i.title.lower())


def changed_to(before, after):
    return f'<del>{before}</del><span class="arrow" aria-hidden="true">→</span><span class="sr-only">changed to</span><ins>{after}</ins>'


def test_the_empty_workspace_explains_what_to_do_next(site):
    page = site.get("/")
    assert page.status_code == 200 and "Process your first team update" in page.text
    assert "No tracked work yet" in page.text and "Replay mode" in page.text
    assert 'action="/items/' not in page.text


def test_processing_an_update_opens_a_review_with_evidence_beside_each_change(site):
    page = submit(site, MON)
    assert page.status_code == 200 and "Review pending" in page.text
    assert "Update for Monday 13 October 2025" in page.text and "Nothing is saved to tracked work until you approve." in page.text
    assert "<b>6</b> new · <b>3</b> need attention" in page.text and "changed ·" not in page.text.split("Nothing is saved")[0][-200:]
    assert "Should have a fix today, maybe tomorrow worst case." in page.text and '<span class="speaker">Arjun</span>' in page.text
    assert "The date sounded uncertain (“maybe”), so no due date was set." in page.text
    assert "Mentioned, not tracked" in page.text and "Replay mode: this result is a saved model response" in page.text
    assert page.text.index("Needs attention") < page.text.index('id="h-new"')  # what needs a decision comes first


def test_fix_an_owner_and_a_date_then_approve_and_it_carries_forward(site):
    submit(site, MON)
    auth = item_by_title(site, "auth")
    page = site.post(f"/items/{auth.id}/edit", data={"owner": "Sana", "due": "2025-10-16", "status": auth.status})
    assert f"Saved changes to {auth.id}." in page.text and "Edited by you" in page.text
    assert changed_to("Dev", "Sana") in page.text
    assert "Approve changes" in site.get("/").text

    approved = site.post("/approve")
    assert "Update for Mon 13 Oct approved." in approved.text and "Process the next team update" in approved.text
    assert 'value="2025-10-14"' in approved.text  # the next date is offered
    assert 'action="/items/' not in approved.text  # the approved list is read-only

    tuesday = submit(site, TUE)
    assert "Update for Tuesday 14 October 2025" in tuesday.text
    assert "recorded against a different list" in tuesday.text
    kept = next(i for i in state_of(site).draft.items_after if i.id == auth.id)
    assert (kept.owner, kept.ticket) == ("Sana", "PAY-231")


def test_posting_the_form_unchanged_records_nothing(site):
    submit(site, MON)
    export = item_by_title(site, "export")
    site.post(f"/items/{export.id}/edit", data={"owner": export.owner, "due": export.due.isoformat(), "status": export.status})
    again = next(i for i in state_of(site).draft.items_after if i.id == export.id)
    assert again.due_phrase == "Monday" and not [e for e in again.history if e.by == "lead"]


def test_remove_asks_first_and_the_item_leaves_the_list(site):
    page = submit(site, MON)
    flaky = item_by_title(site, "flaky")
    assert f'action="/items/{flaky.id}/remove"' in page.text and "data-confirm=\"Remove " in page.text
    page = site.post(f"/items/{flaky.id}/remove")
    assert "removed. It won’t be added again" in page.text and "Removed by you" in page.text
    assert f'action="/items/{flaky.id}/edit"' not in page.text
    assert "was removed" in site.post(f"/items/{flaky.id}/edit", data={"owner": "Sana", "due": "", "status": "open"}).text


def test_discard_asks_first_and_returns_to_the_approved_state(site):
    page = submit(site, MON)
    assert 'action="/discard" data-confirm="Discard this update?' in page.text
    page = site.post("/discard")
    assert "Update discarded. Tracked work is unchanged." in page.text and state_of(site).draft is None
    assert "Process your first team update" in page.text


def test_a_failed_run_changes_nothing_and_keeps_the_transcript_in_the_form(site):
    page = site.post("/standup", data={"date": MON, "text": "Ana: Something nobody recorded an answer for."})
    assert page.status_code == 502 and "couldn’t be processed, and nothing was changed" in page.text
    assert "No saved answer for this transcript" in page.text
    assert "Ana: Something nobody recorded an answer for." in page.text and state_of(site).draft is None


def test_bad_input_is_refused_with_a_message(site):
    assert "No line starts with a speaker name" in site.post("/standup", data={"date": MON, "text": "pasted notes"}).text
    assert "Choose the date of this update." in site.post("/standup", data={"date": "13/10", "text": "Ana: Hi."}).text
    submit(site, MON)
    blocked = submit(site, TUE)
    assert blocked.status_code == 400 and "Approve or discard it first" in blocked.text
    assert "is not a status" in site.post("/items/A1/edit", data={"owner": "", "due": "", "status": "finished"}).text


def test_processing_the_same_day_again_asks_first(site):
    submit(site, MON)
    site.post("/items/A2/edit", data={"owner": "Priya", "due": "", "status": "open"})
    asked = submit(site, MON)
    assert asked.status_code == 409 and "Reprocess and replace" in asked.text
    assert state_of(site).draft.items_after[1].owner == "Priya"  # nothing replaced yet
    submit(site, MON, confirm_rerun="1")
    assert state_of(site).draft.items_after[1].owner == "Dev"


def test_item_activity_page_and_overdue_marker(site):
    for day in WEEK[:3]:
        submit(site, day)
        if day != WEEK[2]:
            site.post("/approve")
    auth = item_by_title(site, "auth")
    activity = site.get(f"/items/{auth.id}")
    assert activity.status_code == 200 and "Activity" in activity.text and "PAY-231, the auth one." in activity.text
    assert "Review pending" in activity.text
    site.post("/approve")
    for day in WEEK[3:]:
        submit(site, day)
    assert '<span class="chip overdue">Overdue</span>' in site.get("/").text  # the doc promised for Wednesday night


def test_the_overview_counts_and_table_carry_what_the_filters_need(site):
    for day in WEEK:
        submit(site, day)
        site.post("/approve")
    page = site.get("/").text
    assert "Latest update: Friday 17 October" in page and "5 updates processed" in page
    overview = page.split('class="overview"')[1].split("</section>")[0]
    assert [part.split("</div>")[0] for part in overview.split('<div class="n">')[1:]] == ["6", "0", "1", "1"]
    assert 'data-filter="overdue"' in page and 'data-owner-filter' in page and 'data-sort="due"' in page
    assert 'data-status="done" data-group="closed"' in page and 'data-overdue="1"' in page


def test_a_lead_reopen_shows_that_the_status_changed(site):
    for day in WEEK[:3]:
        submit(site, day)
        site.post("/approve")
    submit(site, WEEK[3])
    review_item = item_by_title(site, "review pay-231")  # closed on Wednesday, untouched on Thursday
    page = site.post(f"/items/{review_item.id}/edit", data={"owner": review_item.owner, "due": "", "status": "open"})
    assert ">Reopened</span>" in page.text and changed_to("Done", "Open") in page.text


def test_a_transcript_can_be_uploaded_as_a_file_and_names_its_own_date(site):
    with open(ROOT / "transcripts" / f"{MON}.txt", "rb") as handle:
        page = site.post("/standup", data={"date": "", "text": ""}, files={"file": (f"{MON}.txt", handle, "text/plain")})
    assert page.status_code == 200 and "Update for Monday 13 October 2025" in page.text
    assert len(state_of(site).draft.items_after) == 6


def test_an_uploaded_file_that_fails_is_kept_in_the_box_and_a_non_text_file_is_refused(site):
    upload = {"file": ("notes.txt", b"Ana: Something nobody recorded an answer for.", "text/plain")}
    page = site.post("/standup", data={"date": MON, "text": ""}, files=upload)
    assert page.status_code == 502 and "Ana: Something nobody recorded an answer for." in page.text
    binary = site.post("/standup", data={"date": MON, "text": ""}, files={"file": ("photo.png", b"\x89PNG\xff\xfe", "image/png")})
    assert binary.status_code == 400 and "isn’t a text file" in binary.text
    assert "Paste it or choose a file" in site.post("/standup", data={"date": MON, "text": ""}).text


def test_every_item_shows_the_words_it_rests_on_even_when_today_did_not_touch_it(site):
    for day in WEEK[:3]:
        submit(site, day)
        site.post("/approve")
    thursday = submit(site, WEEK[3]).text
    whole_list = thursday.split("Tracked work after approval")[1].split("Reprocess this update")[0]
    assert "Should we do something about the flaky test in CI?" in whole_list  # untouched since Monday
    assert '<span class="speaker">Sana</span><span class="faint">, Mon 13 Oct</span>' in whole_list
    assert whole_list.count("231 is back") == 0  # changed today: its words are beside the change above, not repeated
    approved = site.post("/approve").text
    assert "bad news, 231 is back." in approved and "I&#39;ll send something tonight." in approved


def test_the_note_is_shown_once_beside_a_change(site):
    submit(site, MON)
    site.post("/approve")
    tuesday = submit(site, TUE).text.split("Tracked work after approval")[0]
    assert tuesday.count("Infra says cert will be done tomorrow morning") == 1


def test_a_state_file_the_app_cannot_read_gives_a_message_not_a_bare_error(site):
    site.state_file.write_text('{"version": 99}')
    page = site.get("/")
    assert page.status_code == 500 and "format version 99" in page.text and "reset" in page.text


def test_a_removed_item_is_listed_once_and_section_counts_match_the_header(site):
    for day in WEEK[:3]:
        submit(site, day)
        site.post("/approve")
    submit(site, WEEK[3])
    draft = state_of(site).draft
    new_item = item_by_title(site, "retry")  # added on Thursday
    changed_item = item_by_title(site, "export")  # re-dated on Thursday
    untouched = item_by_title(site, "flaky")  # not mentioned on Thursday
    for item in (new_item, changed_item, untouched):
        site.post(f"/items/{item.id}/remove")
    page = site.get("/").text
    for item in (new_item, changed_item, untouched):
        assert page.count(f'<article class="change" id="{item.id}">') == 1
    assert 'id="h-removed">Removed by you <span class="count">3</span>' in page
    assert 'id="h-new"' not in page  # the only new item was removed
    assert 'id="h-changed">Changed <span class="count">3</span>' in page and "<b>3</b> changed" in page
    assert len(draft.items_after) == 10


def test_a_new_item_is_marked_new_in_the_list_after_approval_too(site):
    for day in WEEK[:3]:
        submit(site, day)
        site.post("/approve")
    table = submit(site, WEEK[3]).text.split("Tracked work after approval")[1]
    retry_row = table.split("Fix Hermes retry bug")[1].split("</tr>")[0]
    export_row = table.split("Build export feature")[1].split("</tr>")[0]
    assert '<span class="chip new">New</span>' in retry_row and '<span class="chip new">Changed</span>' in export_row


def test_a_flagged_item_leaves_needs_attention_once_the_lead_deals_with_it(site):
    page = submit(site, MON).text
    search = item_by_title(site, "search")
    flaky = item_by_title(site, "flaky")
    assert "<b>3</b> need attention" in page and f'action="/items/{search.id}/reviewed"' in page

    page = site.post(f"/items/{search.id}/edit", data={"owner": search.owner, "due": "2025-10-14", "status": search.status}).text
    attention = page.split('id="h-attention"')[1].split('id="h-new"')[0]
    assert "<b>2</b> need attention" in page and f'id="{search.id}"' not in attention
    card = page.split(f'<article class="change" id="{search.id}">')[1].split("</article>")[0]
    assert "sounded uncertain" not in card and "Edited by you" in card and ">New</span>" in card

    page = site.post(f"/items/{flaky.id}/reviewed").text
    assert f"{flaky.id} kept as proposed." in page and "<b>1</b> needs attention" in page
    assert f'action="/items/{flaky.id}/reviewed"' not in page


def test_labels_describe_the_net_change_not_each_step(site):
    for day in WEEK[:3]:
        submit(site, day)
        site.post("/approve")
    submit(site, WEEK[3])
    auth = item_by_title(site, "auth")  # reopened on Thursday: the model cleared its date
    page = site.post(f"/items/{auth.id}/edit", data={"owner": auth.owner, "due": "2025-10-17", "status": auth.status}).text
    card = page.split(f'<article class="change" id="{auth.id}">')[1].split("</article>")[0]
    head = card.split('class="facts"')[0]
    assert ">Reopened</span>" in head and ">Rescheduled</span>" in head
    assert "Date cleared" not in head and ">Scheduled</span>" not in head
