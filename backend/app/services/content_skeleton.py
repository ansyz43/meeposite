"""Deterministic content plan skeleton builder.

No GPT calls — pure Python. Decides:
  * Cadence: stories every day, reels every 2nd day, optional posts.
  * Hunt-stage distribution (Ben Hunt's ladder).
  * Reserved Meepo-bot CTA slots (funnel goal).

GPT only fills in the text for each slot; the skeleton itself is free
and fully predictable, which is critical for funnel guarantees.

Hunt stages used in rotation:
  unaware  — entertaining / lifestyle, cold hook
  problem  — pain-aware content (PAS)
  solution — generic approaches, comparisons
  product  — FitLine soft sell via personal story
  most_aware — direct CTA (includes Meepo bot funnel slots)
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal

HuntStage = Literal["unaware", "problem", "solution", "product", "most_aware"]
PostType = Literal["пост", "сторис", "рилс", "карусель"]

# Base rotation over 5 days — repeats to fill the full period.
# Designed so pain/problem content anchors early, product CTA lands weekly,
# and Meepo funnel hits at day 5/10/14/... (every 5th day).
_STAGE_ROTATION: list[HuntStage] = [
    "unaware",   # d1 — cold entry, lifestyle
    "problem",   # d2 — pain point
    "solution",  # d3 — approaches / myths
    "product",   # d4 — soft sell (FitLine via story)
    "most_aware",  # d5 — Meepo bot CTA
]

# Best posting times — rotated to spread presence across the feed.
_BEST_TIMES_IG = ["09:00", "12:30", "18:00", "20:30"]
_BEST_TIMES_TG = ["08:30", "12:00", "18:30", "21:00"]


@dataclass
class Slot:
    day: int
    post_type: PostType
    hunt_stage: HuntStage
    is_meepo_cta: bool
    best_time: str
    brief: str  # human-readable brief that GPT expands into a real post


def _stage_for_day(day: int) -> HuntStage:
    # day is 1-based
    return _STAGE_ROTATION[(day - 1) % len(_STAGE_ROTATION)]


def _brief(
    *,
    post_type: PostType,
    stage: HuntStage,
    is_meepo_cta: bool,
    niche: str,
    meepo_deeplink: str | None,
) -> str:
    """Short brief describing the slot's intent. GPT uses it as guardrail."""
    if is_meepo_cta and meepo_deeplink:
        return (
            f"{post_type.upper()} | стадия Ханта: {stage} | "
            f"цель: подвести подписчика к Meepo-боту ({meepo_deeplink}). "
            f"Подача: личный кейс, как бот помог разобраться в [конкретной боли ниши '{niche}']. "
            f"В конце — прямой CTA написать боту. Никакого FitLine в этом посте."
        )
    stage_hint = {
        "unaware": "развлекательный/лайфстайл крючок, без болей и без продукта",
        "problem": "одна конкретная боль ЦА, формула PAS, без упоминания продукта",
        "solution": "обзор подходов/мифы/сравнение, без прямой продажи",
        "product": "мягкая интеграция FitLine через личную историю (не в лоб)",
        "most_aware": "прямой CTA с авторской позицией",
    }[stage]
    return f"{post_type.upper()} | стадия Ханта: {stage} | {stage_hint}"


def build_skeleton(
    *,
    period_days: int,
    platform: str,
    niche: str,
    meepo_deeplink: str | None,
    include_posts: bool = False,
) -> list[Slot]:
    """Build the list of slots for the whole period.

    Cadence:
      * 1 сторис каждый день  (drives daily presence, cheap to produce)
      * 1 рилс  каждые 2 дня  (heavy format, expensive to produce — limited)
      * optional 1 пост every 3 days (textual depth) when include_posts=True

    Meepo CTA reservation (funnel):
      * Every 5th day's ONE slot becomes a Meepo-bot CTA
        (hunt_stage most_aware). That's ~20% of days.

    All slot counts are deterministic for QA / cost estimation.
    """
    times_pool = _BEST_TIMES_IG if platform == "instagram" else _BEST_TIMES_TG
    slots: list[Slot] = []

    for day in range(1, period_days + 1):
        stage = _stage_for_day(day)
        # Reserve Meepo CTA on the most_aware day of each cycle (every 5th day).
        is_cta_day = (day % 5 == 0)

        # 1) Stories — every day, the "lightweight" channel.
        story_stage: HuntStage = "most_aware" if is_cta_day else stage
        slots.append(
            Slot(
                day=day,
                post_type="сторис",
                hunt_stage=story_stage,
                is_meepo_cta=is_cta_day,
                best_time=times_pool[(day - 1) % len(times_pool)],
                brief=_brief(
                    post_type="сторис",
                    stage=story_stage,
                    is_meepo_cta=is_cta_day,
                    niche=niche,
                    meepo_deeplink=meepo_deeplink,
                ),
            )
        )

        # 2) Reels — every 2nd day.
        if day % 2 == 0:
            slots.append(
                Slot(
                    day=day,
                    post_type="рилс",
                    hunt_stage=stage,
                    is_meepo_cta=False,  # reels are not used as Meepo CTA (expensive format, keep for value)
                    best_time=times_pool[(day) % len(times_pool)],
                    brief=_brief(
                        post_type="рилс",
                        stage=stage,
                        is_meepo_cta=False,
                        niche=niche,
                        meepo_deeplink=meepo_deeplink,
                    ),
                )
            )

        # 3) Long-form posts — optional, every 3rd day.
        if include_posts and day % 3 == 0:
            slots.append(
                Slot(
                    day=day,
                    post_type="пост",
                    hunt_stage=stage,
                    is_meepo_cta=False,
                    best_time=times_pool[(day + 1) % len(times_pool)],
                    brief=_brief(
                        post_type="пост",
                        stage=stage,
                        is_meepo_cta=False,
                        niche=niche,
                        meepo_deeplink=meepo_deeplink,
                    ),
                )
            )

    return slots


def skeleton_to_prompt_table(slots: list[Slot]) -> str:
    """Compact table representation for inclusion in GPT prompts.

    Keeping it short saves input tokens.
    """
    lines = ["day | type | hunt_stage | meepo_cta | brief"]
    for s in slots:
        cta = "YES" if s.is_meepo_cta else "no"
        lines.append(f"{s.day} | {s.post_type} | {s.hunt_stage} | {cta} | {s.brief}")
    return "\n".join(lines)


def slots_as_dicts(slots: list[Slot]) -> list[dict]:
    return [asdict(s) for s in slots]
