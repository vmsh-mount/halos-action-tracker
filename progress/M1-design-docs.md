# M1 — Design docs: progress

Date: 2026-10-11. Tasks: [tasks/M1-design-docs.md](../tasks/M1-design-docs.md).

## Done

Seven documents under `docs/`, each proposed, reviewed and approved before the next:

| Document | Revisions | Independent reviews |
|---|---|---|
| `action-item-rules.md` | 4 | 2 |
| `data-models.md` | 2 | 1 |
| `answer-key-five-standups.md` | 1 | 0 |
| `generalisation-beyond-the-five-standups.md` | 4 | 3 |
| `components-and-data-flow.md` | 3 | 2 |
| `implementation-details.md` | 2 | 1 |
| `evaluation-checks.md` | 2 | 1 |

The plan listed three documents. Four were added during the milestone at the owner's request: data models,
answer key, generalisation, implementation details.

## Evidence

- Every transcript quote used as an example in the rules and the answer key was checked by script to sit
  inside one turn of the right day (55 quotes in the answer key).
- Every turn of the five transcripts is accounted for in the anchor table of `evaluation-checks.md`, checked
  by script; five are bare acknowledgements.
- Writing `implementation-details.md` surfaced 16 contradictions between the earlier documents and 12
  unanswered questions. All were decided and the source documents corrected in the same commit.
- No code exists. Nothing in these documents has been run.

## Time

About 1 h 50 min (13:02 to 14:52), against a budget of 30 min. Elapsed since the start of the session:
about 2 h 20 min.

## Open

- The plan's remaining milestones (M2 to M6) total 3 h 50 min. With 2 h 20 min spent, that passes the
  five-hour limit in the brief by about 1 h 10 min. Either scope is cut, or the overrun is stated in the
  README.
- Held-out transcripts and their expected properties are to be written outside this repository before the
  freeze.
- The model to use through OpenRouter is not chosen; that is the first step of M3.
