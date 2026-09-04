# How we solved it

Anxin (安心, "peace of mind") is a web app you paste a suspicious message
into. No account, no install, no stored history. Every design decision
below maps back to something in [PROBLEM.md](PROBLEM.md).

---

## One answer, two languages, same evidence

**Problem it solves:** the family safety net that can't read the message.

Every report comes back in **English and Simplified Chinese at the same
time**. This is not a translate button bolted on afterwards — both
verifier models are asked to explain their reasoning in both languages,
from the same evidence, in the same call. Switching language re-renders
the report; it does not re-run the check or produce a different answer.

So a parent reading Chinese and an adult child reading English are
looking at the *same verdict, the same evidence, the same warning signs*
— and can talk about it without one of them having to translate and lose
the thing that mattered.

## Two scores, never merged

**Problem it solves:** "is this true?" and "is this dangerous?" are
different questions, and scams live in the gap.

A message can be factually plausible and still be a scam. Collapsing
those into one number destroys the distinction that actually protects
someone. So every report shows:

- **Truth Score** — how strongly the evidence supports the claim.
- **Scam risk** — how closely this resembles a manipulation attempt.
- **Confidence** — how much we trust our own answer.

Plus up to **three warning signs in plain language** — "asks you to pay
in gift cards", not "social engineering vector". For someone deciding
whether to act, three concrete signs are worth more than a paragraph of
reasoning.

## Meme and slang explanation

**Problem it solves:** not getting the joke, without having to ask a
friend and admit it.

A second mode explains what a meme, slang phrase, or cultural reference
actually means — literal wording, the joke, cultural context, and any
safety angle — in both languages. It is styled deliberately differently
from a fact-check and carries no verdict, no score and no risk rating,
because explaining a joke is not the same as certifying it.

## Two independent models, and honest disagreement

**Problem it solves:** the audience cannot check the answer they're
given, so a confident single opinion is dangerous.

Two different models (DeepSeek and MiniMax) verify the same claim
independently through Gonka Router, on identical evidence, neither shown
the other's answer. Both calls are pinned so the network cannot quietly
serve the same model twice and present it as two opinions.

Then we refuse to average away the disagreement:

| Gap between their scores | What we report |
|---|---|
| ≤ 20 points | Agreement |
| 21–40 points | A lean, with reduced confidence |
| > 40 points | **Insufficient evidence** — we do not average two contradictory answers into a confident-looking number |

If neither model found usable sources, confidence is capped and the
result is reported as insufficient. A precise score resting on nothing is
the most misleading thing this product could display. The exception is a
scam pattern, which is read off the message itself and needs no external
sources — we never mute a warning for lack of citations.

If only one model answers, the report says so plainly and is **not**
presented as cross-verified.

## Verifiable, not just asserted

**Problem it solves:** why should someone trust this more than the
message they're worried about?

Every model call exposes its Gonka Request ID, the devshard that handled
it, and a link to Gonka's public receipt endpoint. That receipt is
independently checkable against GonkaRouter — not something we could
fabricate on our own server. The report also shows what each model
concluded *on its own*, so cross-verification is something you can
inspect rather than take our word for.

We are equally explicit about the limit: a receipt proves which model
answered and when. It does not prove the claim is true.

## Built for someone who is worried

**Problem it solves:** embarrassment, privacy fear, and being in a hurry.

- **No account, no history, nothing stored.**
- **Personal details are masked before anything reaches a model** —
  phone numbers, emails, account and ID numbers become typed
  placeholders, so the scam's structure survives for analysis while the
  raw digits never leave the server.
- **Screenshots are read by local OCR only**, and you can correct the
  extracted text before anything is analysed. OCR never judges.
- **We never tell you to call a number found inside the message you're
  worried about.** That number reaches the scammer. Every suggested next
  step points to an independently-found official channel.
- **Warnings never rely on colour alone** — icon, label and text
  together, for readers who are older, colour-blind, or on a bad screen.

---

## What it is, and isn't

Anxin is not a truth oracle. It is a transparent pause button for
bilingual families: two independent models, visible disagreement,
plain-language evidence, and one safer next step — in whichever of the
two languages you read.
