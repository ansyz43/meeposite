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
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    bot: Mapped["Bot | None"] = relationship("Bot", back_populates="owner", uselist=False, cascade="all, delete-orphan")
    referred_by: Mapped["User | None"] = relationship("User", remote_side="User.id", foreign_keys=[referred_by_id])
    referrals: Mapped[list["User"]] = relationship("User", back_populates="referred_by", foreign_keys=[referred_by_id])


class Bot(Base):
    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True)
    bot_token_encrypted: Mapped[str] = mapped_column(String(500), nullable=False)
    bot_username: Mapped[str | None] = mapped_column(String(255))
    assistant_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Ассистент")
    seller_link: Mapped[str | None] = mapped_column(String(500))
    greeting_message: Mapped[str | None] = mapped_column(Text)
    bot_description: Mapped[str | None] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    allow_partners: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    owner: Mapped["User"] = relationship("User", back_populates="bot")
    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="bot", cascade="all, delete-orphan")
    referral_partners: Mapped[list["ReferralPartner"]] = relationship("ReferralPartner", back_populates="bot", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("bot_id", "telegram_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    telegram_username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    first_message_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    last_message_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    bot: Mapped["Bot"] = relationship("Bot", back_populates="contacts")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="contact", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contact_id: Mapped[int] = mapped_column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(10), nullable=False)  # 'user' | 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
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
