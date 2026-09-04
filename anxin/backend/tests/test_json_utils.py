"""Real models don't return clean JSON. These are the shapes we actually
have to survive on demo day (see app/json_utils.py)."""
from __future__ import annotations

import pytest

from app.json_utils import JsonExtractionError, extract_json_object


def test_plain_json():
    assert extract_json_object('{"verdict": "likely_true"}') == {"verdict": "likely_true"}


def test_markdown_fenced_json():
    raw = '```json\n{"verdict": "likely_false", "truth_score": 12}\n```'
    assert extract_json_object(raw)["truth_score"] == 12


def test_unlabelled_code_fence():
    assert extract_json_object('```\n{"a": 1}\n```') == {"a": 1}


def test_reasoning_block_before_json():
    raw = '<think>Let me weigh the evidence carefully...</think>\n{"verdict": "misleading"}'
    assert extract_json_object(raw)["verdict"] == "misleading"


def test_unclosed_reasoning_block_is_stripped():
    raw = '{"verdict": "likely_true"}\n<think>wait, actually I should reconsider'
    assert extract_json_object(raw)["verdict"] == "likely_true"


def test_prose_before_and_after_json():
    raw = 'Here is my analysis:\n{"verdict": "unverifiable"}\nHope that helps!'
    assert extract_json_object(raw)["verdict"] == "unverifiable"


def test_braces_inside_string_values_do_not_break_balance():
    raw = '{"reasoning_en": "the post uses {curly} braces", "truth_score": 50}'
    parsed = extract_json_object(raw)
    assert parsed["truth_score"] == 50
    assert "{curly}" in parsed["reasoning_en"]


def test_escaped_quotes_inside_strings():
    raw = '{"reasoning_en": "he said \\"urgent\\" repeatedly", "truth_score": 20}'
    assert extract_json_object(raw)["truth_score"] == 20


def test_nested_objects():
    raw = 'text {"outer": {"inner": {"deep": true}}, "n": 1} more text'
    assert extract_json_object(raw)["outer"]["inner"]["deep"] is True


def test_empty_content_raises():
    with pytest.raises(JsonExtractionError):
        extract_json_object("   ")


def test_no_json_at_all_raises():
    with pytest.raises(JsonExtractionError):
        extract_json_object("I'm sorry, I cannot help with that request.")


def test_truncated_json_raises_rather_than_guessing():
    # finish_reason="length" case -- better to fail honestly than half-parse.
    with pytest.raises(JsonExtractionError):
        extract_json_object('{"verdict": "likely_true", "reasoning_en": "the evidence sug')
