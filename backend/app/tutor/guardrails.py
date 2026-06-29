"""Guardrails: intent classification + the tutor system prompt.

Two layers of defense (see ai-tutor.md):
1. A cheap, deterministic **intent classifier** that routes obvious "do my homework" and
   "talk to a human" requests *before* generation — so we don't rely on the prompt alone.
2. The **system prompt** the model is given, which keeps it grounded, Socratic, and unwilling
   to hand over a graded assignment verbatim.
"""

from __future__ import annotations

import enum
import re


class Intent(str, enum.Enum):
    question = "question"  # normal course question → retrieve + answer
    assignment = "assignment"  # "do my homework" → guide with hints, don't complete it
    escalate = "escalate"  # student explicitly wants a human


# "Do the graded work for me" phrasings. Worked examples are fine; producing the student's
# actual deliverable verbatim is not.
_ASSIGNMENT_PATTERNS = [
    r"\bdo my (home ?work|assignment|lab|project|quiz|exam|test)\b",
    r"\b(write|solve|complete|finish|answer) (my|the|this) (home ?work|assignment|problem set|pset|lab|exam|quiz|essay)\b",
    r"\bgive me the (answer|solution)s? to (my|the|this|question)\b",
    r"\bwhat('?s| is) the answer to (question|problem|q)\s*\d+\b",
    r"\bjust give me the (code|answer|solution)\b",
]

# Explicit "I want a human" phrasings.
_ESCALATE_PATTERNS = [
    r"\b(talk|speak|connect) (to|with) (my |the )?(professor|instructor|teacher|ta|human)\b",
    r"\bask (my |the )?(professor|instructor|teacher)\b",
    r"\bescalate\b",
    r"\b(can|could) (a|the) (human|person|professor|instructor) (help|answer)\b",
]


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text) for p in patterns)


def classify_intent(question: str) -> Intent:
    text = question.lower()
    if _matches_any(text, _ESCALATE_PATTERNS):
        return Intent.escalate
    if _matches_any(text, _ASSIGNMENT_PATTERNS):
        return Intent.assignment
    return Intent.question


# The guardrail prompt handed to the model on the normal answer path.
TUTOR_SYSTEM_PROMPT = """\
You are AssistAI, a teaching assistant for one specific course. Follow these rules:

1. Ground every answer ONLY in the course material provided to you in the context. If the \
context does not contain the answer, say you are not sure and suggest the student ask the \
instructor — never invent facts or make up a citation.
2. Teach like a tutor. Explain concepts, give intuition, and use illustrative worked \
examples. Help the student understand, don't just hand over answers.
3. Never produce a student's graded assignment, problem set, or exam answer verbatim. If \
asked to, decline and instead guide them with steps, hints, and a similar (not identical) \
worked example.
4. Be concise and clear. Prefer plain language.

You will be given the relevant course material as numbered context passages. Use them.\
"""


# The refusal/guidance message used when the intent classifier catches an assignment request
# (and on the local generator's assignment path).
ASSIGNMENT_GUIDANCE = (
    "I can't just hand over the answer to a graded assignment — but I can absolutely help "
    "you get there. Let's work through it together: tell me which part you're stuck on, and "
    "I'll explain the relevant concept and walk through a similar example step by step."
)

# The message used when nothing in the course material is relevant enough to answer.
NOT_SURE_MESSAGE = (
    "I'm not sure about that based on this course's materials, so I don't want to guess. "
    "I've flagged your question for your instructor — they'll be able to help."
)

# The message used when a student explicitly asks for a human.
ESCALATE_MESSAGE = (
    "Sure — I've sent your question to your instructor so a human can help. "
    "In the meantime, feel free to keep asking me anything else about the course."
)
