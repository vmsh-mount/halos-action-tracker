# Answer key — what a correct run of the five standups produces

Status: **proposal for review**. Written before any code or prompt exists.

For each standup: the changes a correct run proposes, what each should contain, the words that support it,
and the trap it sets. It applies `action-item-rules.md` to the transcripts in `transcripts/`; where the two
disagree, the rules document wins and this one is wrong.

## How to read it

- **It assumes the lead approves each day and edits nothing.**
- **Ids are for reading only.** They follow the order things come up. A real run may number differently, so
  a check must find an item by what it is (ticket, owner, words in the title), never by "A5".
- **†** = depends on a soft rule. A run that differs here is still correct. `open` and `in_progress` are
  interchangeable everywhere and are not marked.
- **Supporting words** are one acceptable choice. Any quote from the same turn that carries the point is fine.
- **Trap** = the specific wrong answer this line invites.
- Dates: the standups run Mon 13 to Fri 17 October 2025.

## Monday 13 October

| Change | Expected | Supporting words | Trap |
|---|---|---|---|
| Add **A1** Fix search latency | Owner Arjun. In progress. **No date**, review reason "hedged" | Arjun: "Should have a fix today, maybe tomorrow worst case." | Setting 13 or 14 Oct from a hedged sentence. Also "I'll know by tonight" is when he learns the cause, not when the fix lands |
| Add **A2** Auth bug | Owner **Dev**. No date, no ticket yet | Dev: "Yeah, I had context. I'll take it." Arjun: "Cool, Dev on auth then." | Owner Priya, who offers first ("I can pick that up") and hands it on in the same breath |
| Add **A3** Hermes staging deploy | Owner Sana. **Blocked**. Note: cert expired, with infra, no reply yet. No date | Sana: "the Hermes staging deploy is blocked." | Skipping it because Arjun says "that's not ours then". The cert is infra's; the deploy and the chasing are Sana's. Also: a second item owned by "infra" |
| Add **A4** Flaky CI test | **No owner**. Open. Review reason "raised, deferred, no decision" | Sana: "Should we do something about the flaky test in CI?" Arjun: "Let's talk about it after, not now." | Leaving it out because nothing was decided, or giving it to Sana because she raised it |
| Add **A5** Export feature | Owner Priya. Due **20 Oct**, phrase "Monday" | Priya: "Monday is more realistic." Arjun: "Fine, Monday." | Three day-words in one sentence: "Friday" (the old date, 17 Oct), "this morning", "Monday". And "Monday" said on a Monday is next week, not today |
| Add **A6** Fix onboarding doc | **No owner**. Open. No date | Priya: "The onboarding doc is out of date." Arjun: "Someone should fix that at some point." | Owner Priya (she noticed) or Arjun (he answered) |
| Not tracked: CSV customer reply | No item | Dev: "I replied last night, that's done." | Adding an item that is already finished |
| Not tracked: Arjun's call | No item | Arjun: "I've got a call at ten fifteen." | Small talk with a time in it |

Six items after Monday. Two carry review reasons (A1, A4), cleared on approval.

## Tuesday 14 October

| Change | Expected | Supporting words | Trap |
|---|---|---|---|
| Update **A1** | Note: it is the index, not the query; bigger fix. **Still no date**, review reason "hedged" | Arjun: "Turns out it's the index, not the query" and "Tomorrow, probably." | 15 Oct. "Tomorrow" alone is a day code understands; only the hedge check stops it |
| Update **A2** | Ticket **PAY-231**. Due **14 Oct**, phrase "today". In progress | Dev: "PAY-231, the auth one." and "fix is going out today" | A new item for PAY-231. This is the first time the ticket is named, so nothing in code links it to Monday's "auth bug" |
| Add **A7** Atlas login slow | Owner Dev. Open. No date | Dev: "someone pinged me about the Atlas login being slow." and "I'll look after." | Folding it into A2 on the strength of "Might be related to 231, might not" |
| Add **A8** † Review Dev's PAY-231 PR | Owner Priya. Part of A2. **No date** | Priya: "I'll look at Dev's PR after this." | A date from "after this". Also a duplicate if both Dev's request and Priya's promise become items |
| Update **A3** | Note: infra says cert tomorrow morning. Still blocked. **No date** | Sana: "They say the cert will be done tomorrow morning." | 15 Oct as the due date. It is infra's estimate for their work, not Sana's commitment. **Code cannot catch this**: "tomorrow morning" is a plain, unhedged day |
| **A5**: nothing | No change shown ("Still Monday" is still 20 Oct) | Priya: "Export's going fine. Still Monday." | A second export item, or a "re-dated" entry for a date that did not move |

Eight items after Tuesday.

## Wednesday 15 October

| Change | Expected | Supporting words | Trap |
|---|---|---|---|
| Update **A1** | Note: fix in review. Not done | Arjun: "Search fix is in review, finally." | Closing it. In review is not shipped |
| Add **A9** † Review Arjun's search PR | Owner **Dev**. Due **15 Oct**, phrase "today". Part of A1 | Dev: "Yeah, I'll review Arjun's search PR today." | Owner Arjun, who asks. Or an update to A8, the other PR review |
| Update **A2** | **Done** | Dev: "Auth is done, by the way, deployed last night, Priya looked at it." | "Auth" is A2. Missing the close because the ticket is not named |
| Update **A8** † | **Done** | Dev: "deployed last night, Priya looked at it." | Staying open because Priya herself never says it is done |
| Update **A7** | **Done**. Note: unrelated to 231, slow query on the roles table | Dev: "The Atlas login thing was unrelated" and "I fixed it while I was in there." | Mixing it up with the "Atlas export" mentioned later in the same standup |
| Update **A3** | **Done** | Sana: "Hermes staging deploy went out this morning, all green." | Staying blocked. It goes blocked → done with no step between |
| Add **A10** Send Falcon doc | Owner Arjun. Due **15 Oct**, phrase "tonight" | Priya: "Is there a doc or anything?" Arjun: "I'll send something tonight." | Skipped: four words, and "something" only makes sense with Priya's question |
| Not tracked: Falcon kickoff | No item | Arjun: "Falcon kickoff is Thursday, two pm." | An item due Thursday. It is a meeting with a time already set |
| **A5**: nothing | No change shown | Priya: "The Atlas export is still on for Monday." | **The duplicate the brief warns about.** First time it is called "Atlas export"; there is no ticket, so code cannot notice a new item |

Ten items after Wednesday.

## Thursday 16 October

| Change | Expected | Supporting words | Trap |
|---|---|---|---|
| Not tracked: Rohan joins | No item. Rohan listed as a new speaker | Arjun: "Rohan's starting today." | An "onboard Rohan" item for Sana from "Sana, be nice" |
| Update **A2** | **Reopened**: in progress. Note: session cookie this time. Old date 14 Oct **cleared** | Dev: "bad news, 231 is back." and "it's the session cookie, not the refresh." | A new item (bare "231"). Or reopening with the old date, so it returns overdue. "Should be quick" is not a date |
| Update **A9** † | **Done** | Dev: "the search PR, I reviewed it, left two comments" | — |
| Update **A1** | **Done** †. Note: merged, watching the numbers | Arjun: "Search is merged, I'm watching the numbers, so far so good." | Dev's "Arjun you can just merge" is an instruction, not the event; Arjun's "Already did." is |
| Not tracked: Falcon staffing | No item | Arjun: "Priya and Dev are on it for the next two weeks." | A "Falcon migration" item with two owners and a two-week date |
| Update **A5** | Due **22 Oct**, phrase "Wednesday". Re-dated from 20 Oct | Priya: "export is going to slip." and "Say Wednesday?" Arjun: "Wednesday's fine." | 15 Oct (yesterday was a Wednesday). Or no change, because Priya only asks |
| Add **A11** Hermes retry bug | Owner Sana. Ticket **APP-402**. Due **17 Oct**, phrase "tomorrow" | Sana: "I'm picking up the Hermes retry bug, APP-402" and "Should be done tomorrow, it's small." | Reopening A3, the other Hermes item Sana owned. Reading "a 400" as a ticket number. Treating "should be" as a hedge |
| Update **A6** | Owner **Rohan** | Rohan: "I can take the onboarding doc, if that's still a thing?" Arjun: "It's still a thing. Yes, take it." | Adding it again: it has been silent since Monday. Or rejecting Rohan as unknown; he is not in the team settings |

Eleven items after Thursday.

## Friday 17 October

| Change | Expected | Supporting words | Trap |
|---|---|---|---|
| Update **A11** | Due **20 Oct**, phrase "Monday". Re-dated from 17 Oct | Arjun: "so anything of hers rolls to Monday." | Nothing happens: no item is named and Sana does not speak. Or the wrong items move: A3 is done, A4 was never hers |
| Update **A2** | **Done**, second time | Dev: "Auth is fixed, for real this time." | Left open because of "unless it comes back a third time" |
| Add **A12** Retro on PAY-231 | **No owner**. Open. No date, phrase "next week". Part of A2 † | Arjun: "We should do a retro on that one next week" | Owner Arjun ("we should" names nobody). A date from "next week". Or skipped as a meeting; it has not been arranged, so it is an action |
| Not tracked: Falcon schema draft | No item | Priya: "Falcon schema draft is up, I put it in the channel." | An item for work already finished |
| Add **A13** † Review Falcon schema draft | Owner Dev. Due **17 Oct**, phrase "today" | Priya: "Dev's reviewing." Dev: "Yeah, today, after lunch." | Owner Priya, who speaks first |
| Update **A6** | Note: draft ready, going to Priya to check. **Still Rohan's, not done** | Rohan: "I've got a draft, I'll send it to Priya to check" | Closing it on "I've got a draft", or moving the owner to Priya |
| Add **A14** † Check onboarding doc draft | Owner Priya. Part of A6. No date | Rohan: "I'll send it to Priya to check, since she flagged it." Priya: "Sure." | Justified by "Sure." alone, which is too short to stand by itself |
| Not tracked: sign-off | No item | Arjun: "Don't deploy on Friday." | A standing rule turned into an action |

Untouched on Friday, and correct to leave so: **A10** (Falcon doc, due 15 Oct, never mentioned again) stays
open and shows as overdue; **A4** and **A5** are not mentioned.

Fourteen items after Friday. The final list is the table in `action-item-rules.md` section 7.

## The main trap for each item

| Item | Trap that matters most | Caught by |
|---|---|---|
| A1 Search latency | Hedged date set anyway, two days running | Code (date step D2) |
| A2 Auth bug / PAY-231 | One item under four names, done twice; must not split | Model. Code helps only once the ticket is on the item |
| A3 Hermes staging deploy | Someone else's estimate taken as our date | Model only |
| A4 Flaky CI test | Undecided, so dropped; or given to whoever raised it | Model only |
| A5 Export | "Atlas export" added as a second item | Model only |
| A6 Onboarding doc | No owner for three days, then picked up; must be found, not re-added | Model only |
| A7 Atlas login | Merged into A2, or confused with the Atlas export | Model only |
| A8 † PR review (Priya) | Closed by someone else's words | Model only |
| A9 † PR review (Dev) | Owner is the asker, not the doer | Model only |
| A10 Falcon doc | A four-word promise skipped; later, silence taken as done | Model (skip); code never closes on silence |
| A11 APP-402 | Blanket "rolls to Monday" applied to nothing or to the wrong items | Model only |
| A12 Retro | Owner invented from "we should" | Model only |
| A13 † Falcon schema review | Owner is the first speaker | Model only |
| A14 † Onboarding draft check | Supported only by "Sure." | Code (quote length rule) |

## What this shows about the checks

Most traps are caught by the model or not at all. Code catches made-up quotes, hedged dates, date
arithmetic and a repeated ticket id. It does not catch a wrong owner, a skipped item, a duplicate without a
ticket, or a real date attached to the wrong thing (A3 on Tuesday). Those are what `evaluation-checks.md`
has to measure on real model output.
