"""Narrative core & strategy cache for content profiles.

Generated ONCE per profile using a stronger model (gpt-5.4) and then reused
across every content plan for 30 days (or until the profile is explicitly
updated). This is the main token-saving lever of the whole system.

Returns a cached JSON strategy + a compact narrative-core text that is
prepended to post-generation prompts.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import ContentProfile

logger = logging.getLogger(__name__)

# Stronger model is used only for the one-off narrative/strategy generation.
# Per-plan generation uses a cheaper model (see content_ai._MODEL_POSTS).
_MODEL_CORE = "gpt-5.4"
_DEFAULT_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
_TIMEOUT = 180
_CACHE_TTL_DAYS = 30


def _get_openai_url() -> str:
    if settings.OPENAI_BASE_URL:
        base = settings.OPENAI_BASE_URL.rstrip("/")
        return f"{base}/chat/completions"
    return _DEFAULT_OPENAI_URL


async def _call_gpt_core(messages: list[dict], temperature: float = 0.5) -> str:
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    if settings.CF_AIG_TOKEN:
        headers["cf-aig-authorization"] = f"Bearer {settings.CF_AIG_TOKEN}"
    payload = {
        "model": _MODEL_CORE,
        "messages": messages,
        "temperature": temperature,
        "max_completion_tokens": 4000,
    }
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(_get_openai_url(), json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def _is_cache_valid(profile: ContentProfile) -> bool:
    if not profile.strategy_json or not profile.strategy_generated_at:
        return False
    age = datetime.utcnow() - profile.strategy_generated_at.replace(tzinfo=None)
    return age < timedelta(days=_CACHE_TTL_DAYS)


async def ensure_narrative_core(
    profile: ContentProfile,
    db: AsyncSession,
    *,
    force_refresh: bool = False,
) -> dict:
    """Make sure profile has a cached narrative core + strategy, then return it.

    Returns a dict:
      {
        "strategy": {...},                  # parsed JSON
        "narrative_core_text": "...",       # compact text for post prompts
        "cache_hit": bool,
      }
    """
    if not force_refresh and _is_cache_valid(profile):
        try:
            strategy = json.loads(profile.strategy_json or "{}")
        except json.JSONDecodeError:
            strategy = {}
        return {
            "strategy": strategy,
            "narrative_core_text": _build_core_text(profile, strategy),
            "cache_hit": True,
        }

    # ── Generate new narrative core + strategy in ONE GPT call ──
    prompt = _build_core_prompt(profile)
    raw = await _call_gpt_core([{"role": "user", "content": prompt}], temperature=0.4)

    parsed = _parse_json(raw)

    # Persist to profile (fallback to defaults if GPT omitted fields).
    profile.founder_story = (parsed.get("founder_story") or profile.founder_story or "").strip() or None
    profile.transformation = (parsed.get("transformation") or profile.transformation or "").strip() or None
    profile.signature_metaphors = _join_list(parsed.get("signature_metaphors")) or profile.signature_metaphors
    profile.value_ladder_position = (parsed.get("value_ladder_position") or profile.value_ladder_position or "")[:50] or None

    strategy = parsed.get("strategy") or {}
    profile.strategy_json = json.dumps(strategy, ensure_ascii=False)
    profile.strategy_generated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(profile)

    return {
        "strategy": strategy,
        "narrative_core_text": _build_core_text(profile, strategy),
        "cache_hit": False,
    }


# ── Internal helpers ──────────────────────────────────────────


def _join_list(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return ", ".join(str(x).strip() for x in value if str(x).strip())
    return str(value).strip() or None


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse narrative-core JSON; returning empty dict")
        return {}


def _build_core_prompt(profile: ContentProfile) -> str:
    existing_story = (profile.founder_story or "").strip()
    existing_transform = (profile.transformation or "").strip()
    audience = profile.target_audience or ""
    topics = profile.topics or ""

    existing_block = ""
    if existing_story or existing_transform:
        existing_block = (
            "\n## Уже известно об авторе (используй как основу, не выдумывай противоречий)\n"
            f"История автора: {existing_story or 'не указана'}\n"
            f"Трансформация: {existing_transform or 'не указана'}\n"
        )

    return f"""Ты — стратег по позиционированию и сторителлингу для персонального бренда.

Продукт в основе: БАДы FitLine (PM-International), технология NTC, премиум-сегмент.
Цель автора: вести подписчиков по лестнице Ханта к целевому действию — написать личному AI-ассистенту (Meepo-боту) за бесплатной консультацией.

## Профиль
Ниша: {profile.niche}
Тон: {profile.tone}
Целевая аудитория: {audience or 'не указана'}
Темы: {topics or 'не указаны'}
{existing_block}
## Задача
Создай UNIQUE narrative core для этого автора. Это ОСНОВА, на которой будут строиться все будущие контент-планы. Делай конкретно, без штампов ("я хочу помогать людям"), без клише. Пиши так, будто пишешь байбук для автора, а не slogan-pack.

Верни строго JSON:
{{
  "founder_story": "1 короткий абзац (3-5 предложений): почему автор пришёл в эту нишу, личный триггер/боль. Конкретика, цифры, место, событие.",
  "transformation": "1 абзац: как изменилась жизнь автора — до/после, что именно решил.",
  "signature_metaphors": ["3-5 уникальных образов/метафор, которые автор может повторять из поста в пост (пример: 'тело как гаджет на 10% зарядки')"],
  "value_ladder_position": "unaware|problem|solution|product|most_aware — на какой стадии Ханта сейчас большинство подписчиков автора",
  "strategy": {{
    "audience_pains": ["5-8 конкретных бытовых болей ЦА — не абстракции"],
    "top_themes": ["5-7 основных тематических линий, которые автор ведёт в контенте"],
    "unique_angles": ["3-5 углов, которыми автор отличается от типового wellness-блога"],
    "hook_patterns": ["3-5 готовых типов крючков для первой строки постов"],
    "tone_guardrails": ["3-5 правил стиля: что МОЖНО и ЧЕГО НЕЛЬЗЯ в текстах"]
  }}
}}

Никаких комментариев вне JSON."""


def _build_core_text(profile: ContentProfile, strategy: dict) -> str:
    """Compact text digest of the narrative core, embedded into post-generation prompts."""
    metaphors = profile.signature_metaphors or "—"
    ladder = profile.value_ladder_position or "problem"
    pains = ", ".join(strategy.get("audience_pains") or [])[:600] or "—"
    angles = ", ".join(strategy.get("unique_angles") or [])[:400] or "—"
    hooks = "; ".join(strategy.get("hook_patterns") or [])[:400] or "—"
    guardrails = "; ".join(strategy.get("tone_guardrails") or [])[:400] or "—"

    return (
        "### Narrative core автора (опирайся на это во всех постах, не противоречь)\n"
        f"История: {(profile.founder_story or '—').strip()}\n"
        f"Трансформация: {(profile.transformation or '—').strip()}\n"
        f"Сигнатурные образы: {metaphors}\n"
        f"Где сейчас аудитория на лестнице Ханта: {ladder}\n"
        f"Ключевые боли: {pains}\n"
        f"Уникальные углы: {angles}\n"
        f"Паттерны крючков: {hooks}\n"
        f"Ограничения стиля: {guardrails}\n"
    )


def invalidate_cache(profile: ContentProfile) -> None:
    """Call this after the user edits niche/audience/topics to force regeneration."""
    profile.strategy_json = None
    profile.strategy_generated_at = None
