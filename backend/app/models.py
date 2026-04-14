import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, BigInteger, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    auth_provider: Mapped[str | None] = mapped_column(String(20))
    ref_code: Mapped[str | None] = mapped_column(String(16), unique=True, index=True)
    referred_by_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    cashback_balance: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    bots: Mapped[list["Bot"]] = relationship("Bot", back_populates="owner", cascade="all, delete-orphan")
    referred_by: Mapped["User | None"] = relationship("User", remote_side="User.id", foreign_keys=[referred_by_id])
    referrals: Mapped[list["User"]] = relationship("User", back_populates="referred_by", foreign_keys=[referred_by_id])


class Bot(Base):
    __tablename__ = "bots"
    __table_args__ = (UniqueConstraint("user_id", "platform", name="uq_bot_user_platform"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    platform: Mapped[str] = mapped_column(String(10), nullable=False, default="telegram")
    bot_token_encrypted: Mapped[str] = mapped_column(String(500), nullable=False)
    bot_username: Mapped[str | None] = mapped_column(String(255))
    assistant_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Ассистент")
    seller_link: Mapped[str | None] = mapped_column(String(500))
    greeting_message: Mapped[str | None] = mapped_column(Text)
    bot_description: Mapped[str | None] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    vk_group_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    allow_partners: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    owner: Mapped["User"] = relationship("User", back_populates="bots")
    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="bot", cascade="all, delete-orphan")
    referral_partners: Mapped[list["ReferralPartner"]] = relationship("ReferralPartner", back_populates="bot", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint("bot_id", "telegram_id", name="uq_contact_bot_tg"),
        UniqueConstraint("bot_id", "vk_id", name="uq_contact_bot_vk"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(10), nullable=False, default="telegram")
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    vk_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    telegram_username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    first_message_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    last_message_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    link_sent: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    bot: Mapped["Bot"] = relationship("Bot", back_populates="contacts")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="contact", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contact_id: Mapped[int] = mapped_column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(10), nullable=False)  # 'user' | 'assistant'
    content: Mapped[str] = mapped_column(Text(4096), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    contact: Mapped["Contact"] = relationship("Contact", back_populates="messages")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class ReferralPartner(Base):
    __tablename__ = "referral_partners"
    __table_args__ = (UniqueConstraint("user_id", "bot_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_link: Mapped[str] = mapped_column(String(500), nullable=False)
    ref_code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    credits: Mapped[int] = mapped_column(Integer, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User")
    bot: Mapped["Bot"] = relationship("Bot", back_populates="referral_partners")
    sessions: Mapped[list["ReferralSession"]] = relationship("ReferralSession", back_populates="partner", cascade="all, delete-orphan")


class ReferralSession(Base):
    __tablename__ = "referral_sessions"
    __table_args__ = (UniqueConstraint("partner_id", "telegram_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partner_id: Mapped[int] = mapped_column(Integer, ForeignKey("referral_partners.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id: Mapped[int] = mapped_column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    partner: Mapped["ReferralPartner"] = relationship("ReferralPartner", back_populates="sessions")
    contact: Mapped["Contact"] = relationship("Contact")


class Broadcast(Base):
    __tablename__ = "broadcasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500))
    total_contacts: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | sending | completed | failed
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    bot: Mapped["Bot"] = relationship("Bot")


class CashbackTransaction(Base):
    __tablename__ = "cashback_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    from_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    source_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'credits' | 'bot_subscription'
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    from_user: Mapped["User"] = relationship("User", foreign_keys=[from_user_id])


# ── Content Plan ─────────────────────────────────────────────

class ContentProfile(Base):
    """User's content marketing profile — niche, tone, target audience."""
    __tablename__ = "content_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    niche: Mapped[str] = mapped_column(String(255), nullable=False)  # "wellness", "beauty"
    platforms: Mapped[str] = mapped_column(Text, nullable=False, default="instagram,telegram")  # comma-separated
    tone: Mapped[str] = mapped_column(String(100), nullable=False, default="friendly")
    target_audience: Mapped[str] = mapped_column(Text, nullable=False, default="")
    topics: Mapped[str] = mapped_column(Text, nullable=False, default="")  # comma-separated
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, onupdate=func.now())

    user: Mapped["User"] = relationship("User")
    competitor_sources: Mapped[list["CompetitorSource"]] = relationship("CompetitorSource", back_populates="profile", cascade="all, delete-orphan")


class CompetitorSource(Base):
    """A competitor channel/account tracked by user."""
    __tablename__ = "competitor_sources"
    __table_args__ = (UniqueConstraint("profile_id", "platform", "channel_username", name="uq_comp_profile_chan"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("content_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)  # "telegram" | "instagram"
    channel_username: Mapped[str] = mapped_column(String(255), nullable=False)  # "@channel" or "username"
    channel_title: Mapped[str | None] = mapped_column(String(255))
    last_parsed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    profile: Mapped["ContentProfile"] = relationship("ContentProfile", back_populates="competitor_sources")


class CompetitorPost(Base):
    """Cached parsed post from a competitor channel. Shared across users."""
    __tablename__ = "competitor_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    channel_username: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    views: Mapped[int | None] = mapped_column(Integer)
    reactions: Mapped[int | None] = mapped_column(Integer)
    posted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    parsed_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())


class ContentPlan(Base):
    """A generated content plan."""
    __tablename__ = "content_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)  # "instagram" | "telegram"
    period_days: Mapped[int] = mapped_column(Integer, default=7)
    status: Mapped[str] = mapped_column(String(20), default="generating")  # generating | ready | error
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User")
    items: Mapped[list["ContentPlanItem"]] = relationship("ContentPlanItem", back_populates="plan", cascade="all, delete-orphan", order_by="ContentPlanItem.day_number")


class ContentPlanItem(Base):
    """A single post in a content plan."""
    __tablename__ = "content_plan_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("content_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    post_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "пост" | "сторис" | "рилс" | "карусель"
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[str | None] = mapped_column(Text)
    best_time: Mapped[str | None] = mapped_column(String(20))  # "09:00"
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    plan: Mapped["ContentPlan"] = relationship("ContentPlan", back_populates="items")
