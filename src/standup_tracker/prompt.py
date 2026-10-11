"""Builds what is sent to the model: fixed instructions with the team's facts filled in, and today's input."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .llm import LLMRequest
from .models import Item, Standup, Team

TEMPLATE = Path(__file__).parent / "prompts" / "propose_changes.md"

# Described to the model in the instructions; sent along for clients that can use it. Our own code checks the
# answer whatever the provider does with this.
ANSWER_SHAPE = {
    "type": "object",
    "required": ["changes"],
    "properties": {
        "changes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["kind", "fields", "quotes"],
                "properties": {
                    "kind": {"enum": ["add", "update"]},
                    "ref": {"type": "string"},
                    "item_id": {"type": "string"},
                    "fields": {"type": "object"},
                    "quotes": {"type": "array", "items": {"type": "string"}},
                    "review_reason": {"type": "string"},
                },
            },
        },
        "not_tracked": {
            "type": "array",
            "items": {"type": "object", "properties": {"quote": {"type": "string"}, "reason": {"type": "string"}}},
        },
    },
}


def instructions(team: Team) -> str:
    people = "\n".join(
        f"- {p.name}" + (f" (also called {', '.join(p.also)})" if p.also else "") + (f", {p.role}" if p.role else "")
        for p in team.people
    )
    glossary = "\n".join(f"- {term}: {meaning}" for term, meaning in team.glossary.items())
    prefixes = "\n".join(f"- {prefix}-: {meaning}" for prefix, meaning in team.ticket_prefixes.items())
    text = TEMPLATE.read_text(encoding="utf-8")
    for slot, value in (("people", people), ("glossary", glossary), ("ticket_prefixes", prefixes)):
        text = text.replace("{{" + slot + "}}", value or "- (none given)")
    return text


def _item_line(item: Item) -> str:
    due = "none"
    if item.due:
        due = item.due.isoformat() + (f' (said as "{item.due_phrase}")' if item.due_phrase else "")
    elif item.due_phrase:
        due = f'none (said as "{item.due_phrase}")'
    parts = [
        item.id, item.title, f"owner: {item.owner or 'none'}", f"status: {item.status}", f"due: {due}",
        f"ticket: {item.ticket or 'none'}", f"part of: {item.parent or 'none'}", f"note: {item.note or 'none'}",
    ]
    return " | ".join(parts)


def input_text(standup: Standup, items: list[Item]) -> str:
    listed = [i for i in items if not i.removed_on]
    removed = [i for i in items if i.removed_on]
    lines = [f"Standup date: {standup.date.isoformat()} ({standup.date.strftime('%A')})", ""]
    lines.append("The list before today:")
    lines.extend(_item_line(i) for i in listed) if listed else lines.append("(empty)")
    lines.append("")
    lines.append("Removed by the lead, never to be added again:")
    lines.extend(f"{i.id} | {i.title}" for i in removed) if removed else lines.append("(none)")
    lines.append("")
    lines.append("Today's standup:")
    lines.extend(f"[{t.n}] {t.speaker or '(no speaker)'}: {t.text}" for t in standup.turns)
    return "\n".join(lines)


def lookup_key(standup: Standup) -> str:
    """The standup date plus a short hash of the parsed turns, so pasting or re-wrapping the text changes nothing."""
    body = "\n".join(f"{t.speaker or ''}\t{' '.join(t.text.split())}" for t in standup.turns)
    return f"{standup.date.isoformat()}-{hashlib.sha256(body.encode('utf-8')).hexdigest()[:10]}"


def build_request(standup: Standup, items: list[Item], team: Team, *, temperature: float | None = None) -> LLMRequest:
    return LLMRequest(
        instructions=instructions(team),
        input=input_text(standup, items),
        answer_shape=ANSWER_SHAPE,
        lookup_key=lookup_key(standup),
        temperature=temperature,
    )
