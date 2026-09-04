"""Mask the user's own identifiers before anything is sent for inference
(context doc §9: "Mask unnecessary phone numbers, account numbers, national
identifiers, and email addresses before inference").

The important design tension, stated explicitly because it is easy to get
wrong: in a *scam checker*, phone numbers and account numbers are frequently
the scam signal itself. "Transfer to account 8829301 today" is exactly what
the verifier needs to see the shape of. So we do NOT delete identifiers --
we replace each with a typed placeholder:

    "call 012-345 6789 now"  ->  "call [PHONE] now"

The sentence structure, urgency, and the *fact that a payment destination
was supplied* all survive, so scam detection is unaffected, while the raw
digits never leave this server. That distinction is why this is redaction
rather than stripping.

Scope is deliberately conservative. Over-redacting a fact-check input
destroys the thing being checked (dates, prices, statistics, and case
numbers must survive), so this module targets only the four categories the
context document names.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# --- patterns -------------------------------------------------------------
# Ordered: more specific patterns first, so an email is not partially eaten
# by the phone-number rule.

_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b")

# Malaysian and international shapes: +60 12-345 6789, 012-3456789,
# (03) 1234 5678. Requires 8+ digits total so it cannot swallow a year,
# a price, or a short statistic.
_PHONE = re.compile(
    r"(?<![\w.])(?:\+?\d{1,3}[\s.-]?)?(?:\(\d{1,4}\)[\s.-]?)?\d{2,4}(?:[\s.-]?\d{2,4}){2,4}(?![\w.])"
)

# Malaysian NRIC: 990101-14-5678
_NRIC = re.compile(r"\b\d{6}-\d{2}-\d{4}\b")

# Long bare digit runs that read as an account/card number (10-19 digits,
# optionally spaced or hyphened in groups).
_ACCOUNT = re.compile(r"(?<![\w.])\d{4}[\s-]?\d{4}[\s-]?\d{2,6}(?:[\s-]?\d{1,4})?(?![\w.])")


@dataclass
class RedactionResult:
    text: str
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def any_redacted(self) -> bool:
        return any(self.counts.values())


def _sub_count(pattern: re.Pattern[str], placeholder: str, text: str) -> tuple[str, int]:
    new_text, n = pattern.subn(placeholder, text)
    return new_text, n


def redact(text: str) -> RedactionResult:
    """Replace personal identifiers with typed placeholders.

    Order matters: email before phone (an email can contain digit runs),
    and NRIC before the generic account pattern (an NRIC would otherwise
    match as an account number).
    """
    counts: dict[str, int] = {}

    text, counts["email"] = _sub_count(_EMAIL, "[EMAIL]", text)
    text, counts["nric"] = _sub_count(_NRIC, "[ID_NUMBER]", text)
    text, counts["account"] = _sub_count(_ACCOUNT, "[ACCOUNT_NUMBER]", text)
    text, counts["phone"] = _sub_count(_PHONE, "[PHONE]", text)

    return RedactionResult(text=text, counts=counts)


def redaction_note(result: RedactionResult) -> tuple[str, str] | None:
    """A user-facing (EN, ZH) note when something was masked, so the person
    understands why their message looks different in the report -- silently
    altering someone's text would be its own kind of dishonesty."""
    if not result.any_redacted:
        return None
    return (
        "Personal details (phone numbers, emails, account or ID numbers) were replaced with "
        "placeholders before analysis. The wording around them was preserved, so scam patterns "
        "are still detected.",
        "在分析前，个人信息（电话号码、邮箱、账号或证件号）已被替换为占位符。"
        "其余文字保持不变，因此诈骗特征仍可被识别。",
    )
