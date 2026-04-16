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

_DEFAULT_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
_MODEL = "gpt-5.4"
_TIMEOUT = 120


def _get_openai_url() -> str:
    if settings.OPENAI_BASE_URL:
        base = settings.OPENAI_BASE_URL.rstrip("/")
        return f"{base}/chat/completions"
    return _DEFAULT_OPENAI_URL


async def _call_gpt(messages: list[dict], temperature: float = 0.7) -> str:
    """Call OpenAI API and return content string."""
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    if settings.CF_AIG_TOKEN:
        headers["cf-aig-authorization"] = f"Bearer {settings.CF_AIG_TOKEN}"
    payload = {
        "model": _MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_completion_tokens": 8000,
    }
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(_get_openai_url(), json=payload, headers=headers)
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
        strategy_prompt = f"""Ты — ведущий маркетолог-стратег с 15+ лет опыта в digital-маркетинге, SMM и продвижении wellness/health-брендов через социальные сети.

Твоя специализация — маркетинг через боли целевой аудитории (PAS: Problem → Agitate → Solve). Ты никогда не продаёшь «в лоб». Вместо этого:
- Сначала показываешь, что ПОНИМАЕШЬ проблему человека
- Затем усиливаешь осознание боли (что будет, если ничего не менять)
- И только потом мягко предлагаешь решение

## Контекст бренда
Продвигаем продукцию FitLine (PM-International) — премиальные БАДы немецкого производства с запатентованной технологией NTC (Nutrient Transport Concept):
- Усвоение до 5 раз быстрее обычных добавок
- 70+ патентов, 1000+ профессиональных спортсменов
- Стартовый продукт: Оптимальный Сет (PowerCocktail/Activize + Basics + Restorate)
- Ключевое УТП: единственная в мире технология транспортировки нутриентов на клеточном уровне

## Профиль пользователя
- Ниша: {profile.niche}
- Платформа: {platform_name}
- Тон: {profile.tone}
- Целевая аудитория: {profile.target_audience or 'Не указана'}
- Темы: {topics_str}

## Данные конкурентов
{competitor_data}

## Задача
Проведи глубокий анализ и создай маркетинговую стратегию. Думай как стратег, не как копирайтер.

1. **Боли ЦА** — определи 5-8 конкретных болей/страхов/фрустраций целевой аудитории (не абстрактные, а бытовые: "устаю к 15:00 и не могу работать", "утром не могу встать без кофе", "кожа тусклая несмотря на уходовую косметику")
2. **Триггеры вовлечения** — какие темы вызывают максимум реакций у этой ЦА (по данным конкурентов + понимание психологии)
3. **Форматы** — какие форматы лучше работают на {platform_name} для этой ниши
4. **Продуктовые интеграции** — как мягко вплетать FitLine (НЕ рекламировать, а показывать через личный опыт, кейсы, результаты). Максимум 1-2 раза в неделю (из {period_days} дней)
5. **Подготовка к боту** — 1-2 раза в неделю подводить аудиторию к Telegram-боту (AI-ассистент по здоровью), через CTA типа «задай вопрос боту», «получи персональную рекомендацию»
6. **Уникальные углы подачи** — чем отличаться от конкурентов

Ответь ТОЛЬКО в формате JSON:
{{
  "audience_pains": ["конкретная боль 1", "конкретная боль 2", ...],
  "top_themes": ["тема1", "тема2", ...],
  "formats": ["пост", "сторис", "рилс", "карусель"],
  "best_times": ["09:00", "12:00", "18:00"],
  "unique_angles": ["угол1", "угол2", ...],
  "content_ratio": {{"value_pain_points": 35, "engaging_lifestyle": 25, "soft_sell_fitline": 15, "bot_cta": 10, "personal_story": 15}},
  "soft_sell_days": [3, 7, 10, 14],
  "bot_cta_days": [5, 12]
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
                "audience_pains": ["хроническая усталость к середине дня", "плохой сон", "тусклая кожа", "зависимость от кофе", "частые простуды"],
                "top_themes": topics_str.split(", "),
                "formats": ["пост", "сторис", "рилс"],
                "best_times": ["09:00", "12:00", "18:00"],
                "unique_angles": ["экспертный контент через боли ЦА", "личный опыт с продуктом"],
                "content_ratio": {"value_pain_points": 35, "engaging_lifestyle": 25, "soft_sell_fitline": 15, "bot_cta": 10, "personal_story": 15},
                "soft_sell_days": [3, 7, 10, 14],
                "bot_cta_days": [5, 12],
            }

        # ── Step 2: Generate posts ────────────────────────
        posts_prompt = f"""Ты — топовый SMM-копирайтер и маркетолог-практик с глубоким пониманием психологии продаж.

Твои принципы:
1. **PAS-формула** (Problem → Agitate → Solve): сначала покажи проблему, затем усиль боль, потом дай решение
2. **AIDA** для продающих постов (Attention → Interest → Desire → Action)
3. **Сторителлинг** > прямая реклама: личные истории, кейсы, «до/после»
4. **80/20 правило**: 80% ценного контента, 20% мягких продаж
5. **Каждый пост решает одну конкретную боль** из списка болей ЦА

## Контекст бренда FitLine
- Премиальные БАДы немецкого производства (PM-International)
- Технология NTC — до 5x быстрее усвоение
- Оптимальный Сет — стартовый продукт (энергия утром, восстановление вечером)
- Activize — энергия и концентрация (замена кофе)
- Restorate — сон и восстановление
- Basics — пищеварение и иммунитет
- Omega-3 — мозг и сосуды
- У бренда есть AI Telegram-бот для персональных консультаций по здоровью

## Стратегия (результат анализа)
{json.dumps(strategy, ensure_ascii=False, indent=2)}

## Тон общения: {profile.tone}
## Целевая аудитория: {profile.target_audience or 'широкая аудитория'}
## Платформа: {platform_name}

## ТИПЫ ПОСТОВ (чередуй по стратегии):

### 🎯 Ценный контент (value_pain_points) — ~35% постов
Берёшь конкретную БОЛЬ из audience_pains и раскрываешь через:
- Разрушение мифов: «Почему ваш утренний кофе — не энергия, а долг»
- Чек-листы: «5 признаков, что вашему организму не хватает минералов»
- Мини-гайды: «Что на самом деле происходит, когда вы "просто устали"»
НЕ упоминай FitLine. Просто дай ценность и экспертизу.

### 💫 Вовлекающий/лайфстайл контент — ~25% постов
- Опросы, вопросы аудитории, «а у вас так бывает?»
- Лёгкие посты про образ жизни, привычки, утренние ритуалы
- Истории из жизни, ситуативный контент
CTA: лайки, комментарии, сохранения. Вопрос в конце обязателен.

### 🌿 Мягкая продажа FitLine — ~15% постов (1-2 раза в неделю МАКСИМУМ)
НИКОГДА не пиши «купи», «закажи», «скидка». Вместо этого:
- «Расскажу, что мне реально помогло с [боль]...» → личный кейс с продуктом
- «Подруга спрашивала, что за напиток я пью каждое утро...» → сторителлинг
- «Было/стало за 3 месяца» → визуальный кейс
- Мини-обзор конкретного продукта через призму решения конкретной проблемы
CTA мягкий: «напиши в директ, расскажу подробнее» или «ссылка в шапке профиля»

### 🤖 Подготовка к боту — ~10% постов (1-2 раза в неделю)
Подводи аудиторию к использованию Telegram-бота:
- «Устала гуглить "какие витамины пить"? Я нашла способ проще — AI-ассистент, который подберёт программу под тебя за 2 минуты»
- «Задала боту вопрос про усталость — получила разбор и рекомендацию. Делюсь»
- «Хочешь персональную программу питания? Бот в Telegram поможет бесплатно 👇»
CTA: ссылка на бота в Telegram

### 👤 Личная история — ~15% постов
- Авторская позиция, ценности, закулисье
- «Почему я занимаюсь здоровьем», «мой путь»
- Усиливает доверие и связь с аудиторией

## ПРАВИЛА ГЕНЕРАЦИИ
- Каждый день — 1 пост
- Каждый пост должен быть ГОТОВЫМ к публикации (полный текст, НЕ шаблон, НЕ placeholder)
- Первая строка — крючок (hook), который останавливает скроллинг
- Для Instagram: 5-10 релевантных хештегов
- Для Telegram: без хештегов, с emoji
- Текст поста: 100-500 символов для сторис/рилс, 500-1500 для постов/каруселей
- Продающие посты размещай на дни из soft_sell_days стратегии
- Посты с ботом размещай на дни из bot_cta_days стратегии
- В продающих постах НЕ называй конкретную цену
- Указывай оптимальное время публикации

Ответь СТРОГО в формате JSON-массив (без markdown, без комментариев):
[
  {{
    "day": 1,
    "type": "пост|сторис|рилс|карусель",
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
