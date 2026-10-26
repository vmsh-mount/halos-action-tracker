# M0 — Setup: progress

Date: 2026-10-11. Tasks: [tasks/M0-setup.md](../tasks/M0-setup.md).

## Done

- Added `.gitignore`, `.env.example`, README stub.
- Saved the five standups under `transcripts/`, named by date.
- Created `tasks/` and `progress/`.

## Evidence

- Transcripts were produced by extracting the source text with `pdftotext` and joining wrapped lines, not retyped.
  Turn counts checked against the source by hand: Mon 13, Tue 6, Wed 9, Thu 10, Fri 8. Word counts: 300, 107,
  125, 229, 119.

## Format note

Each transcript file is one speaker turn per line, `Name: words`. The date is in the file name, not in the
file. The source's line wrapping is removed; nothing else is changed.

## Time

About 10 min (budget 15).

## Open

- Nothing blocking. Stack (Python 3.11+, local web server, JSON file) is as planned;
  local Python is 3.14.
