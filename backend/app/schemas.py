import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


# --- Auth ---
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    ref_code: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class SetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=6, max_length=128)


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class TelegramAuthRequest(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str
    ref_code: str | None = None


class GoogleAuthRequest(BaseModel):
    credential: str
    ref_code: str | None = None


# --- Profile ---
class ProfileResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime.datetime
    has_bot: bool
    ref_code: str | None = None
    ref_link: str | None = None
    cashback_balance: float = 0.0
    referrals_count: int = 0


class ProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=128)


# --- Bot ---
class BotUpdateRequest(BaseModel):
    assistant_name: str = Field(min_length=1, max_length=255)
    seller_link: str | None = Field(None, max_length=500)
    greeting_message: str | None = Field(None, max_length=2000)
    bot_description: str | None = Field(None, max_length=512)
    allow_partners: bool | None = None

    @field_validator("seller_link")
    @classmethod
    def validate_seller_link(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("Ссылка должна начинаться с http:// или https://")
        return v


class BotResponse(BaseModel):
    id: int
    bot_username: str | None
    assistant_name: str
    seller_link: str | None
    greeting_message: str | None
    bot_description: str | None
    avatar_url: str | None
    allow_partners: bool
    is_active: bool
    created_at: datetime.datetime


class BotStatusResponse(BaseModel):
    is_active: bool
    bot_username: str | None


# --- Contacts ---
class ContactResponse(BaseModel):
    id: int
    telegram_id: int
    telegram_username: str | None
    first_name: str | None
    last_name: str | None
    phone: str | None
    first_message_at: datetime.datetime
    last_message_at: datetime.datetime | None
    message_count: int


class ContactListResponse(BaseModel):
    contacts: list[ContactResponse]
    total: int


# --- Conversations ---
class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime.datetime


class ConversationPreview(BaseModel):
    contact_id: int
    telegram_username: str | None
    first_name: str | None
    last_name: str | None
    last_message: str | None
    last_message_at: datetime.datetime | None
    message_count: int


class ConversationListResponse(BaseModel):
    conversations: list[ConversationPreview]
    total: int


class ConversationDetailResponse(BaseModel):
    contact: ContactResponse
    messages: list[MessageResponse]
    total: int


# --- Referral ---
class BotCatalogItem(BaseModel):
    id: int
    bot_username: str | None
    assistant_name: str
    avatar_url: str | None


class ReferralPartnerCreate(BaseModel):
    bot_id: int
    seller_link: str = Field(min_length=1, max_length=500)

    @field_validator("seller_link")
    @classmethod
    def validate_seller_link(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("Ссылка должна начинаться с http:// или https://")
        return v


class ReferralPartnerUpdate(BaseModel):
    seller_link: str = Field(min_length=1, max_length=500)

    @field_validator("seller_link")
    @classmethod
    def validate_seller_link(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("Ссылка должна начинаться с http:// или https://")
        return v


class ReferralPartnerResponse(BaseModel):
    id: int
    bot_id: int
    bot_username: str | None
    assistant_name: str
    seller_link: str
    ref_code: str
    ref_link: str
    credits: int
    is_active: bool
    created_at: datetime.datetime


class ReferralSessionResponse(BaseModel):
    id: int
    telegram_id: int
    telegram_username: str | None
    first_name: str | None
    started_at: datetime.datetime
    expires_at: datetime.datetime
    is_active: bool


class AddCreditsRequest(BaseModel):
    partner_id: int
    credits: int = Field(ge=1, le=1000)


class BotPartnerInfo(BaseModel):
    id: int
    user_name: str
    user_email: str
    seller_link: str
    ref_code: str
    credits: int
    total_sessions: int
    active_sessions: int
    created_at: datetime.datetime


class TreeNodeResponse(BaseModel):
    id: int
    name: str
    email: str
    level: int
    total_spent: float
    cashback_earned: float
    joined_at: datetime.datetime
    children: list["TreeNodeResponse"] = []


class CashbackTransactionResponse(BaseModel):
    id: int
    from_user_name: str
    amount: float
    source_amount: float
    level: int
    source_type: str
    created_at: datetime.datetime
