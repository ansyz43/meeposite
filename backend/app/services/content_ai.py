"""AI content plan generator — 2-step GPT pipeline.

Step 1: Analyze profile + competitor data → strategy
Step 2: Generate posts based on strategy
"""
import json
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import (
    CompetitorPost,
    CompetitorSource,
    ContentPlan,
    ContentPlanItem,
    ContentProfile,
)

logger = logging.getLogger(__name__)

_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
_MODEL = "gpt-5.4"
_TIMEOUT = 90


async def _call_gpt(messages: list[dict], temperature: float = 0.7) -> str:
    """Call OpenAI API and return content string."""
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": _MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 4000,
    }
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(_OPENAI_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _gather_competitor_data(profile: ContentProfile, db: AsyncSession) -> str:
    """Collect cached competitor posts for the user's profile."""
    sources = await db.execute(
        select(CompetitorSource).where(
            CompetitorSource.profile_id == profile.id,
            CompetitorSource.is_active == True,
        )
    )
    sources = sources.scalars().all()

    if not sources:
        return "Конкурентов не добавлено. Генерируй на основе ниши и ЦА."

    sections = []
    for src in sources:
        posts = await db.execute(
            select(CompetitorPost)
            .where(
                CompetitorPost.platform == src.platform,
                CompetitorPost.channel_username == src.channel_username,
            )
            .order_by(CompetitorPost.posted_at.desc())
            .limit(15)
        )
        posts = posts.scalars().all()
        if not posts:
            continue

        post_texts = []
        for p in posts:
            meta = []
            if p.views:
                meta.append(f"👁 {p.views}")
            if p.reactions:
                meta.append(f"❤️ {p.reactions}")
            meta_str = f" ({', '.join(meta)})" if meta else ""
            post_texts.append(f"- {p.text[:300]}{meta_str}")

        sections.append(
            f"### {src.platform.upper()} @{src.channel_username}\n"
            + "\n".join(post_texts[:10])
        )

    return "\n\n".join(sections) if sections else "Посты конкурентов ещё не загружены."


async def generate_content_plan(
    user_id: int,
    platform: str,
    period_days: int,
    db: AsyncSession,
) -> ContentPlan:
    """Generate a content plan using 2-step GPT pipeline.

    Returns created ContentPlan with items. Status = 'ready' or 'error'.
    """
    # Load profile
    result = await db.execute(
        select(ContentProfile).where(ContentProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise ValueError("Сначала заполните профиль контент-маркетинга")

    topics_str = profile.topics or "здоровье, БАДы, wellness"
    platform_name = "Instagram" if platform == "instagram" else "Telegram"

    # Create plan record
    plan = ContentPlan(
        user_id=user_id,
        title=f"Контент-план {platform_name} на {period_days} дней",
        platform=platform,
        period_days=period_days,
        status="generating",
    )
    db.add(plan)
    await db.flush()

    try:
        # Gather competitor data
        competitor_data = await _gather_competitor_data(profile, db)

        # ── Step 1: Strategy ──────────────────────────────
        strategy_prompt = f"""Ты — эксперт по контент-маркетингу в социальных сетях.

Проанализируй данные и создай стратегию контент-плана.

## Профиль пользователя
- Ниша: {profile.niche}
- Платформа: {platform_name}
- Тон: {profile.tone}
- Целевая аудитория: {profile.target_audience or 'Не указана'}
- Темы: {topics_str}

## Данные конкурентов
{competitor_data}

## Задача
На основе анализа конкурентов и профиля определи:
1. Какие темы лучше всего резонируют с аудиторией (по просмотрам/реакциям)
2. Какие форматы постов самые эффективные
3. Оптимальное время публикаций
4. Какие уникальные углы подачи использовать (не копировать конкурентов)

Ответь ТОЛЬКО в формате JSON:
{{
  "top_themes": ["тема1", "тема2", ...],
  "formats": ["пост", "сторис", "рилс", "карусель"],
  "best_times": ["09:00", "12:00", "18:00"],
  "unique_angles": ["угол1", "угол2", ...],
  "content_ratio": {{"educational": 40, "engaging": 30, "selling": 20, "personal": 10}}
}}"""

        strategy_raw = await _call_gpt(
            [{"role": "user", "content": strategy_prompt}],
            temperature=0.5,
        )

        # Parse strategy JSON (extract from markdown code block if needed)
        strategy_text = strategy_raw.strip()
        if "```" in strategy_text:
            strategy_text = strategy_text.split("```")[1]
            if strategy_text.startswith("json"):
                strategy_text = strategy_text[4:]
            strategy_text = strategy_text.strip()

        try:
            strategy = json.loads(strategy_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse strategy JSON, using raw text")
            strategy = {
                "top_themes": topics_str.split(", "),
                "formats": ["пост", "сторис", "рилс"],
                "best_times": ["09:00", "12:00", "18:00"],
                "unique_angles": ["экспертный контент", "личный опыт"],
                "content_ratio": {"educational": 40, "engaging": 30, "selling": 20, "personal": 10},
            }

        # ── Step 2: Generate posts ────────────────────────
        posts_prompt = f"""Ты — копирайтер для {platform_name}. 
Создай контент-план на {period_days} дней для ниши "{profile.niche}".

## Стратегия
{json.dumps(strategy, ensure_ascii=False, indent=2)}

## Тон общения: {profile.tone}
## Целевая аудитория: {profile.target_audience or 'широкая аудитория'}

## Правила
- Каждый день — 1 пост
- Чередуй форматы согласно стратегии
- Каждый пост должен быть ГОТОВЫМ к публикации (полный текст, не шаблон)
- Для Instagram: добавляй хештеги (5-10 релевантных)
- Для Telegram: без хештегов, но с emoji
- Текст поста: 100-500 символов для сториc/рилс, 300-1500 для постов/каруселей
- Указывай оптимальное время публикации

Ответь СТРОГО в формате JSON-массив:
[
  {{
    "day": 1,
    "type": "пост",
    "topic": "Краткая тема",
    "text": "Полный текст поста...",
    "hashtags": "#тег1 #тег2",
    "time": "09:00"
  }},
  ...
]

Сгенерируй ровно {period_days} постов."""

        posts_raw = await _call_gpt(
            [{"role": "user", "content": posts_prompt}],
            temperature=0.8,
        )

        # Parse posts JSON
        posts_text = posts_raw.strip()
        if "```" in posts_text:
            posts_text = posts_text.split("```")[1]
            if posts_text.startswith("json"):
                posts_text = posts_text[4:]
            posts_text = posts_text.strip()

        posts_list = json.loads(posts_text)

        # Create items
        for item_data in posts_list:
            item = ContentPlanItem(
                plan_id=plan.id,
                day_number=item_data.get("day", 1),
                post_type=item_data.get("type", "пост"),
                topic=item_data.get("topic", "")[:255],
                text=item_data.get("text", ""),
                hashtags=item_data.get("hashtags"),
                best_time=item_data.get("time"),
            )
            db.add(item)

        plan.status = "ready"
        await db.commit()
        logger.info("Content plan #%d generated: %d items", plan.id, len(posts_list))

    except Exception as e:
        logger.error("Content plan generation failed: %s", e, exc_info=True)
        plan.status = "error"
        plan.error_message = str(e)[:500]
        await db.commit()

    # Reload with items
    await db.refresh(plan)
    return plan


async def analyze_profile_from_posts(posts_texts: list[str]) -> dict:
    """Analyze user's own social media posts to auto-detect niche, audience, tone, topics.

    Returns dict with keys: niche, target_audience, tone, topics (list).
    """
    if not posts_texts:
        raise ValueError("Нет постов для анализа")

    sample = "\n---\n".join(posts_texts[:20])

    prompt = f"""Ты — маркетолог-аналитик. Проанализируй посты из социальной сети одного автора и определи его профиль.

## Посты автора
{sample}

## Задача
На основе анализа постов определи:
1. **Ниша** — в какой нише работает автор (1-3 слова, например: "wellness и БАДы", "фитнес", "косметология")
2. **Целевая аудитория** — кто читает эти посты: пол, примерный возраст, интересы, боли, мотивация (2-4 предложения)
3. **Тон** — какой тон использует автор. Выбери ОДИН из: friendly, professional, expert, casual, motivational
4. **Темы** — основные темы постов (3-8 тем через запятую)

Ответь СТРОГО в формате JSON:
{{
  "niche": "...",
  "target_audience": "...",
  "tone": "friendly|professional|expert|casual|motivational",
  "topics": ["тема1", "тема2", ...]
}}"""

    raw = await _call_gpt(
        [{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    text = raw.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    result = json.loads(text)

    # Validate tone
    valid_tones = {"friendly", "professional", "expert", "casual", "motivational"}
    if result.get("tone") not in valid_tones:
        result["tone"] = "friendly"

    return result
