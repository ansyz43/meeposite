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
    is_admin: bool = False
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
            v = "https://" + v
        if v:
            lower = v.lower()
            if lower.startswith(("javascript:", "data:", "vbscript:")):
                raise ValueError("Недопустимая ссылка")
        return v


class BotResponse(BaseModel):
    id: int
    platform: str = "telegram"
    bot_username: str | None
    assistant_name: str
    seller_link: str | None
    greeting_message: str | None
    bot_description: str | None
    avatar_url: str | None
    allow_partners: bool
    is_active: bool
    vk_group_id: int | None = None
    created_at: datetime.datetime


class BotStatusResponse(BaseModel):
    is_active: bool
    bot_username: str | None


class VkConnectRequest(BaseModel):
    group_id: int
    group_token: str = Field(min_length=10, max_length=500)
    assistant_name: str = Field(min_length=1, max_length=255)
    seller_link: str | None = Field(None, max_length=500)
    greeting_message: str | None = Field(None, max_length=2000)
    bot_description: str | None = Field(None, max_length=512)

    @field_validator("seller_link")
    @classmethod
    def validate_seller_link(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if v and not v.startswith(("http://", "https://")):
            v = "https://" + v
        if v:
            lower = v.lower()
            if lower.startswith(("javascript:", "data:", "vbscript:")):
                raise ValueError("Недопустимая ссылка")
        return v


# --- Managed Bot creation ---
class CreateBotRequest(BaseModel):
    name: str | None = Field(None, max_length=64)


class CreateBotResponse(BaseModel):
    link: str
    suggested_username: str
    pending_id: int


class CreationStatusResponse(BaseModel):
    status: str  # none | pending | created | failed
    bot: BotResponse | None = None


# --- Contacts ---
class ContactResponse(BaseModel):
    id: int
    platform: str = "telegram"
    telegram_id: int | None = None
    vk_id: int | None = None
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
    platform: str = "telegram"
    telegram_username: str | None
    first_name: str | None
    last_name: str | None
    last_message: str | None
    last_message_at: datetime.datetime | None
    message_count: int
    link_sent: bool = False


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
            v = "https://" + v
        lower = v.lower()
        if lower.startswith(("javascript:", "data:", "vbscript:")):
            raise ValueError("Недопустимая ссылка")
        return v


class ReferralPartnerUpdate(BaseModel):
    seller_link: str = Field(min_length=1, max_length=500)

    @field_validator("seller_link")
    @classmethod
    def validate_seller_link(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
        lower = v.lower()
        if lower.startswith(("javascript:", "data:", "vbscript:")):
            raise ValueError("Недопустимая ссылка")
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


class SimpleReferralResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime.datetime


class TreeNodeResponse(BaseModel):
    id: int
    name: str
    email: str
    level: int
    joined_at: datetime.datetime
    children: list["TreeNodeResponse"] = []


# --- Broadcast ---
class BroadcastResponse(BaseModel):
    id: int
    message_text: str
    image_url: str | None
    total_contacts: int
    sent_count: int
    failed_count: int
    status: str
    created_at: datetime.datetime


class CashbackTransactionResponse(BaseModel):
    id: int
    from_user_name: str
    amount: float
    source_amount: float
    level: int
    source_type: str
    created_at: datetime.datetime


# --- Content Plan ---
class ContentProfileRequest(BaseModel):
    niche: str = Field(min_length=1, max_length=255)
    platforms: list[str] = Field(default=["instagram", "telegram"])
    tone: str = Field(default="friendly", max_length=100)
    target_audience: str = Field(default="", max_length=2000)
    topics: list[str] = Field(default=[])

    @field_validator("platforms")
    @classmethod
    def validate_platforms(cls, v):
        allowed = {"instagram", "telegram"}
        for p in v:
            if p not in allowed:
                raise ValueError(f"Платформа '{p}' не поддерживается. Допустимые: {allowed}")
        return v


class ContentProfileResponse(BaseModel):
    id: int
    niche: str
    platforms: list[str]
    tone: str
    target_audience: str
    topics: list[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime | None
    competitors: list["CompetitorSourceResponse"] = []


class CompetitorSourceAdd(BaseModel):
    platform: str = Field(max_length=20)
    channel_username: str = Field(min_length=1, max_length=255)

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v):
        if v not in ("telegram", "instagram"):
            raise ValueError("Платформа должна быть 'telegram' или 'instagram'")
        return v

    @field_validator("channel_username")
    @classmethod
    def clean_username(cls, v):
        return v.lstrip("@").strip().lower()


class CompetitorSourceResponse(BaseModel):
    id: int
    platform: str
    channel_username: str
    channel_title: str | None
    last_parsed_at: datetime.datetime | None
    is_active: bool
    post_count: int = 0


class CompetitorPostResponse(BaseModel):
    id: int
    text: str
    views: int | None
    reactions: int | None
    posted_at: datetime.datetime | None


class GeneratePlanRequest(BaseModel):
    platform: str = Field(max_length=20)
    period_days: int = Field(default=7, ge=7, le=30)

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v):
        if v not in ("instagram", "telegram"):
            raise ValueError("Платформа должна быть 'instagram' или 'telegram'")
        return v


class ContentPlanItemResponse(BaseModel):
    id: int
    day_number: int
    post_type: str
    topic: str
    text: str
    hashtags: str | None
    best_time: str | None
    script: str | None = None
    is_edited: bool


class ContentPlanItemUpdate(BaseModel):
    text: str | None = Field(default=None, max_length=4000)
    hashtags: str | None = Field(default=None, max_length=1000)
    topic: str | None = Field(default=None, max_length=255)
    script: str | None = Field(default=None, max_length=5000)


class ContentPlanResponse(BaseModel):
    id: int
    title: str
    platform: str
    period_days: int
    status: str
    error_message: str | None
    created_at: datetime.datetime
    items: list[ContentPlanItemResponse] = []


class ContentPlanListItem(BaseModel):
    id: int
    title: str
    platform: str
    period_days: int
    status: str
    created_at: datetime.datetime
    item_count: int = 0
