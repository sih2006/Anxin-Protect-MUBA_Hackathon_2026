"""Redaction must protect the user's identifiers WITHOUT destroying the scam
signal or the facts being checked (see app/redaction.py)."""
from __future__ import annotations

import pytest

from app.redaction import redact, redaction_note

# --- identifiers are masked ------------------------------------------------

@pytest.mark.parametrize(
    "raw,placeholder",
    [
        ("contact me at john.doe@example.com now", "[EMAIL]"),
        ("my ic is 990101-14-5678 ok", "[ID_NUMBER]"),
        ("call +60 12-345 6789 now", "[PHONE]"),
        ("call 012-3456789 immediately", "[PHONE]"),
    ],
)
def test_identifiers_are_masked(raw, placeholder):
    out = redact(raw).text
    assert placeholder in out


def test_account_number_masked():
    out = redact("transfer to 1234 5678 9012 today").text
    assert "[ACCOUNT_NUMBER]" in out
    assert "9012" not in out


# --- the scam signal survives ---------------------------------------------

def test_scam_structure_is_preserved_not_deleted():
    """The whole point: a verifier must still see that a payment destination
    and an urgent instruction were present."""
    out = redact("URGENT: transfer to account 1234 5678 9012 or call 012-3456789 today").text
    assert "URGENT" in out
    assert "transfer to account" in out
    assert "or call" in out
    assert "today" in out
    assert "[ACCOUNT_NUMBER]" in out


def test_raw_digits_do_not_survive():
    result = redact("my number is 012-345 6789")
    assert "6789" not in result.text


# --- facts under check must NOT be eaten ----------------------------------

@pytest.mark.parametrize(
    "raw",
    [
        "the policy changed in 2026",
        "prices rose by 15% last year",
        "the vaccine is 95 percent effective",
        "over 3000 people attended",
        "it costs RM 250 per month",
    ],
)
def test_ordinary_facts_are_left_alone(raw):
    """Over-redaction would destroy the claim being fact-checked."""
    assert redact(raw).text == raw


# --- reporting -------------------------------------------------------------

def test_note_is_none_when_nothing_redacted():
    assert redaction_note(redact("the sky is blue")) is None


def test_note_is_bilingual_when_something_redacted():
    note = redaction_note(redact("email me at a@b.com"))
    assert note is not None
    en, zh = note
    assert en and zh
    assert "placeholder" in en.lower()


def test_counts_are_reported():
    result = redact("a@b.com and c@d.com")
    assert result.counts["email"] == 2
    assert result.any_redacted is True
