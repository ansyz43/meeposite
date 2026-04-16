"""Rank competitor accounts by engagement."""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import async_session
from app.models import CompetitorPost
from sqlalchemy import func, select

async def main():
    async with async_session() as db:
        stmt = (
            select(
                CompetitorPost.channel_username,
                func.count(CompetitorPost.id).label("posts"),
                func.avg(CompetitorPost.reactions).label("avg_reactions"),
                func.max(CompetitorPost.reactions).label("max_reactions"),
                func.sum(CompetitorPost.reactions).label("total_reactions"),
                func.avg(CompetitorPost.views).label("avg_views"),
            )
            .group_by(CompetitorPost.channel_username)
            .order_by(func.avg(CompetitorPost.reactions).desc())
        )
        result = (await db.execute(stmt)).all()

    print(f"{'#':<3} {'Account':<30} {'Posts':>5} {'AvgReact':>9} {'MaxReact':>9} {'TotalReact':>11} {'AvgViews':>9}")
    print("-" * 80)
    for i, s in enumerate(result, 1):
        print(f"{i:<3} {s.channel_username:<30} {s.posts:>5} {s.avg_reactions or 0:>9.0f} {s.max_reactions or 0:>9} {s.total_reactions or 0:>11} {s.avg_views or 0:>9.0f}")

asyncio.run(main())
