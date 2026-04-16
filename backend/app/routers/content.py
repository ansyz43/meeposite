"""Content plan router — /api/content

Isolated from all existing routers. No shared state.
"""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select, func as sa_func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    CompetitorPost,
    CompetitorSource,
    ContentPlan,
    ContentPlanItem,
    ContentProfile,
    User,
)
from app.schemas import (
    CompetitorPostResponse,
    CompetitorSourceAdd,
    CompetitorSourceResponse,
    ContentPlanItemUpdate,
    ContentPlanListItem,
    ContentPlanResponse,
    ContentProfileRequest,
    ContentProfileResponse,
    GeneratePlanRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/content", tags=["content"])


# ── Profile ──────────────────────────────────────────────────

@router.get("/profile", response_model=ContentProfileResponse | None)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ContentProfile)
        .options(selectinload(ContentProfile.competitor_sources))
        .where(ContentProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        return None

    # Build response with competitor post counts
    competitors = []
    for src in profile.competitor_sources:
        count = await db.execute(
            select(sa_func.count(CompetitorPost.id)).where(
                CompetitorPost.platform == src.platform,
                CompetitorPost.channel_username == src.channel_username,
            )
        )
        competitors.append(CompetitorSourceResponse(
            id=src.id,
            platform=src.platform,
            channel_username=src.channel_username,
            channel_title=src.channel_title,
            last_parsed_at=src.last_parsed_at,
            is_active=src.is_active,
            post_count=count.scalar() or 0,
        ))

    return ContentProfileResponse(
        id=profile.id,
        niche=profile.niche,
        platforms=profile.platforms.split(",") if profile.platforms else [],
        tone=profile.tone,
        target_audience=profile.target_audience,
        topics=profile.topics.split(",") if profile.topics else [],
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        competitors=competitors,
    )


@router.post("/profile", response_model=ContentProfileResponse)
async def upsert_profile(
    data: ContentProfileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ContentProfile).where(ContentProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()

    platforms_str = ",".join(data.platforms)
    topics_str = ",".join(data.topics)

    if profile:
        profile.niche = data.niche
        profile.platforms = platforms_str
        profile.tone = data.tone
        profile.target_audience = data.target_audience
        profile.topics = topics_str
    else:
        profile = ContentProfile(
            user_id=user.id,
            niche=data.niche,
            platforms=platforms_str,
            tone=data.tone,
            target_audience=data.target_audience,
            topics=topics_str,
        )
        db.add(profile)

    await db.commit()
    await db.refresh(profile)

    return ContentProfileResponse(
        id=profile.id,
        niche=profile.niche,
        platforms=data.platforms,
        tone=profile.tone,
        target_audience=profile.target_audience,
        topics=data.topics,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        competitors=[],
    )


# ── Competitors ──────────────────────────────────────────────

@router.post("/competitors", response_model=CompetitorSourceResponse)
async def add_competitor(
    data: CompetitorSourceAdd,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Must have profile first
    result = await db.execute(
        select(ContentProfile).where(ContentProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(400, "Сначала создайте профиль")

    # Check limit (max 10 competitors)
    count = await db.execute(
        select(sa_func.count(CompetitorSource.id)).where(
            CompetitorSource.profile_id == profile.id,
        )
    )
    if (count.scalar() or 0) >= 10:
        raise HTTPException(400, "Максимум 10 конкурентов")

    # Check duplicate
    existing = await db.execute(
        select(CompetitorSource).where(
            CompetitorSource.profile_id == profile.id,
            CompetitorSource.platform == data.platform,
            CompetitorSource.channel_username == data.channel_username,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Этот конкурент уже добавлен")

    source = CompetitorSource(
        profile_id=profile.id,
        platform=data.platform,
        channel_username=data.channel_username,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)

    # Trigger parse in background
    background_tasks.add_task(_parse_competitor_bg, data.platform, data.channel_username)

    return CompetitorSourceResponse(
        id=source.id,
        platform=source.platform,
        channel_username=source.channel_username,
        channel_title=source.channel_title,
        last_parsed_at=source.last_parsed_at,
        is_active=source.is_active,
        post_count=0,
    )


@router.delete("/competitors/{source_id}")
async def delete_competitor(
    source_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CompetitorSource)
        .join(ContentProfile)
        .where(
            CompetitorSource.id == source_id,
            ContentProfile.user_id == user.id,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(404, "Конкурент не найден")

    await db.delete(source)
    await db.commit()
    return {"ok": True}


@router.get("/competitors/{source_id}/posts", response_model=list[CompetitorPostResponse])
async def get_competitor_posts(
    source_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CompetitorSource)
        .join(ContentProfile)
        .where(
            CompetitorSource.id == source_id,
            ContentProfile.user_id == user.id,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(404, "Конкурент не найден")

    posts = await db.execute(
        select(CompetitorPost)
        .where(
            CompetitorPost.platform == source.platform,
            CompetitorPost.channel_username == source.channel_username,
        )
        .order_by(CompetitorPost.posted_at.desc())
        .limit(30)
    )
    return [
        CompetitorPostResponse(
            id=p.id,
            text=p.text[:500],  # truncate for listing
            views=p.views,
            reactions=p.reactions,
            posted_at=p.posted_at,
        )
        for p in posts.scalars().all()
    ]


@router.post("/competitors/{source_id}/parse")
async def parse_competitor(
    source_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger re-parse of a competitor."""
    result = await db.execute(
        select(CompetitorSource)
        .join(ContentProfile)
        .where(
            CompetitorSource.id == source_id,
            ContentProfile.user_id == user.id,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(404, "Конкурент не найден")

    background_tasks.add_task(_parse_competitor_bg, source.platform, source.channel_username, force=True)
    return {"ok": True, "message": "Парсинг запущен"}


# ── Plans ────────────────────────────────────────────────────

@router.get("/plans", response_model=list[ContentPlanListItem])
async def list_plans(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ContentPlan)
        .where(ContentPlan.user_id == user.id)
        .order_by(ContentPlan.created_at.desc())
        .limit(20)
    )
    plans = result.scalars().all()

    items = []
    for plan in plans:
        count = await db.execute(
            select(sa_func.count(ContentPlanItem.id)).where(ContentPlanItem.plan_id == plan.id)
        )
        items.append(ContentPlanListItem(
            id=plan.id,
            title=plan.title,
            platform=plan.platform,
            period_days=plan.period_days,
            status=plan.status,
            created_at=plan.created_at,
            item_count=count.scalar() or 0,
        ))

    return items


@router.get("/plans/{plan_id}", response_model=ContentPlanResponse)
async def get_plan(
    plan_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ContentPlan)
        .options(selectinload(ContentPlan.items))
        .where(ContentPlan.id == plan_id, ContentPlan.user_id == user.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "План не найден")

    return ContentPlanResponse(
        id=plan.id,
        title=plan.title,
        platform=plan.platform,
        period_days=plan.period_days,
        status=plan.status,
        error_message=plan.error_message,
        created_at=plan.created_at,
        items=[
            {
                "id": item.id,
                "day_number": item.day_number,
                "post_type": item.post_type,
                "topic": item.topic,
                "text": item.text,
                "hashtags": item.hashtags,
                "best_time": item.best_time,
                "is_edited": item.is_edited,
            }
            for item in plan.items
        ],
    )


@router.post("/plans/generate", response_model=ContentPlanResponse)
async def generate_plan(
    data: GeneratePlanRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.content_ai import generate_content_plan

    try:
        plan = await generate_content_plan(
            user_id=user.id,
            platform=data.platform,
            period_days=data.period_days,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    # Reload with items
    result = await db.execute(
        select(ContentPlan)
        .options(selectinload(ContentPlan.items))
        .where(ContentPlan.id == plan.id)
    )
    plan = result.scalar_one()

    return ContentPlanResponse(
        id=plan.id,
        title=plan.title,
        platform=plan.platform,
        period_days=plan.period_days,
        status=plan.status,
        error_message=plan.error_message,
        created_at=plan.created_at,
        items=[
            {
                "id": item.id,
                "day_number": item.day_number,
                "post_type": item.post_type,
                "topic": item.topic,
                "text": item.text,
                "hashtags": item.hashtags,
                "best_time": item.best_time,
                "is_edited": item.is_edited,
            }
            for item in plan.items
        ],
    )


@router.put("/plans/{plan_id}/items/{item_id}", response_model=dict)
async def update_plan_item(
    plan_id: int,
    item_id: int,
    data: ContentPlanItemUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify ownership
    result = await db.execute(
        select(ContentPlanItem)
        .join(ContentPlan)
        .where(
            ContentPlanItem.id == item_id,
            ContentPlanItem.plan_id == plan_id,
            ContentPlan.user_id == user.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Пост не найден")

    if data.text is not None:
        item.text = data.text
    if data.hashtags is not None:
        item.hashtags = data.hashtags
    if data.topic is not None:
        item.topic = data.topic
    item.is_edited = True

    await db.commit()
    return {"ok": True}


@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ContentPlan).where(ContentPlan.id == plan_id, ContentPlan.user_id == user.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "План не найден")

    await db.delete(plan)
    await db.commit()
    return {"ok": True}


# ── Auto-detect profile ──────────────────────────────────────

@router.post("/profile/auto-detect")
async def auto_detect_profile(
    data: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Parse user's own social media and auto-detect niche, audience, tone, topics."""
    platform = data.get("platform", "").lower()
    username = data.get("username", "").strip().lstrip("@").lower()

    if not username:
        raise HTTPException(400, "Укажите username аккаунта")
    if platform not in ("telegram", "instagram"):
        raise HTTPException(400, "Поддерживается только Telegram и Instagram")

    # Parse posts using existing parsers
    try:
        if platform == "telegram":
            from app.services.parser_telegram import parse_telegram_channel
            result = await parse_telegram_channel(username, db, force=True, max_posts=30)
        else:
            from app.services.parser_instagram import parse_instagram_profile
            result = await parse_instagram_profile(username, db, force=True)

        if result.get("status") == "error":
            raise HTTPException(400, result.get("error", "Ошибка парсинга"))
        if result.get("status") == "rate_limited":
            raise HTTPException(429, "Слишком много запросов, попробуйте через минуту")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Auto-detect parse failed: %s", e, exc_info=True)
        raise HTTPException(400, f"Не удалось загрузить посты: {e}")

    # Fetch parsed posts from DB
    posts_result = await db.execute(
        select(CompetitorPost.text)
        .where(
            CompetitorPost.platform == platform,
            CompetitorPost.channel_username == username,
        )
        .order_by(CompetitorPost.posted_at.desc())
        .limit(20)
    )
    posts_texts = [row[0] for row in posts_result.all() if row[0]]

    if not posts_texts:
        raise HTTPException(400, "Не найдено постов для анализа")

    # AI analysis
    from app.services.content_ai import analyze_profile_from_posts

    try:
        profile_data = await analyze_profile_from_posts(posts_texts)
    except Exception as e:
        logger.error("Auto-detect AI failed: %s", e, exc_info=True)
        raise HTTPException(500, "Ошибка AI-анализа, попробуйте ещё раз")

    return {
        "niche": profile_data.get("niche", ""),
        "target_audience": profile_data.get("target_audience", ""),
        "tone": profile_data.get("tone", "friendly"),
        "topics": profile_data.get("topics", []),
    }


# ── Background tasks ─────────────────────────────────────────

async def _parse_competitor_bg(platform: str, username: str, force: bool = False):
    """Background task: parse a competitor channel/profile."""
    from app.database import async_session

    async with async_session() as db:
        try:
            if platform == "telegram":
                from app.services.parser_telegram import parse_telegram_channel
                result = await parse_telegram_channel(username, db, force=force)
            elif platform == "instagram":
                from app.services.parser_instagram import parse_instagram_profile
                result = await parse_instagram_profile(username, db, force=force)
            else:
                logger.warning("Unknown platform: %s", platform)
                return

            logger.info("Background parse %s @%s: %s", platform, username, result.get("status"))
        except Exception as e:
            logger.error("Background parse error %s @%s: %s", platform, username, e, exc_info=True)
