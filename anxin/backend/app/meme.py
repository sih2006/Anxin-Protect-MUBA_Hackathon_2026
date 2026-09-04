"""Text-based meme / slang explanation mode (Epic 5, IMG-04, IMG-05).

Explicitly secondary to the fact-check flow (backlog "Secondary scope" and
the scope gate in Table 9) -- this module is only reached after the P0
verification pipeline is complete, and it never sets a green/"verified safe"
style on its own; the frontend renders meme results with distinct, neutral
styling (see frontend/components/MemeResult) precisely so it cannot be
mistaken for a fact-check verdict (IMG-05).
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime

from app.config import Settings
from app.gonka_client import GonkaClient
from app.json_utils import JsonExtractionError, extract_json_object
from app.prompts import MEME_SYSTEM, build_meme_user_prompt
from app.schemas import MemeExplanation

logger = logging.getLogger("anxin.meme")


class MemeExplanationError(Exception):
    pass


def _mock_meme_json(content: str) -> str:
    visual_only = len(content.strip()) < 8
    return json.dumps({
        "literal_meaning_en": f"[MOCK] The text reads: \"{content[:120]}\".",
        "literal_meaning_zh": f"【模拟结果】文字内容为：“{content[:120]}”。",
        "joke_or_reference_en": "[MOCK] This may reference a common internet phrase or in-joke.",
        "joke_or_reference_zh": "【模拟结果】这可能引用了常见的网络流行语或梗。",
        "cultural_context_en": "[MOCK] No specific cultural/safety concern detected in this mock run.",
        "cultural_context_zh": "【模拟结果】本次模拟运行未检测到特定文化或安全风险。",
        "safety_notes_en": "[MOCK] This explanation is illustrative only -- configure a live Gonka key for "
                            "real analysis.",
        "safety_notes_zh": "【模拟结果】此说明仅供演示 —— 请配置真实 Gonka 密钥以获取实际分析结果。",
        "is_visual_only_limitation": visual_only,
    })


async def explain_meme(text_content: str, settings: Settings) -> MemeExplanation:
    client = GonkaClient(settings)
    result = await client.call(
        model_id=settings.gonka_model_a,
        model_label=settings.gonka_model_a_label,
        system_prompt=MEME_SYSTEM,
        user_prompt=build_meme_user_prompt(text_content),
        mock_generator=lambda: _mock_meme_json(text_content),
    )
    if not result.ok or not result.content:
        raise MemeExplanationError(result.error_message or "Meme explanation failed.")

    try:
        data = extract_json_object(result.content)

        def field(name: str) -> str:
            """Fall back across the EN/ZH pair so one missing translation
            degrades the explanation instead of failing it outright."""
            other = name.replace("_en", "_zh") if name.endswith("_en") else name.replace("_zh", "_en")
            value = str(data.get(name) or data.get(other) or "").strip()
            if not value:
                raise KeyError(name)
            return value

        return MemeExplanation(
            report_id=f"meme-{uuid.uuid4().hex[:12]}",
            created_at=datetime.now(UTC),
            literal_meaning_en=field("literal_meaning_en"),
            literal_meaning_zh=field("literal_meaning_zh"),
            joke_or_reference_en=field("joke_or_reference_en"),
            joke_or_reference_zh=field("joke_or_reference_zh"),
            cultural_context_en=field("cultural_context_en"),
            cultural_context_zh=field("cultural_context_zh"),
            safety_notes_en=field("safety_notes_en"),
            safety_notes_zh=field("safety_notes_zh"),
            is_visual_only_limitation=bool(data.get("is_visual_only_limitation", False)),
            meta=result.to_metadata(),
        )
    except (JsonExtractionError, KeyError, TypeError, ValueError) as exc:
        raise MemeExplanationError("Meme explanation response failed schema validation.") from exc
