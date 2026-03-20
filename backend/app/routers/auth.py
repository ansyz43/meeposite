import secrets
import datetime
import random
import logging
import hashlib
import hmac
import time
from email.message import EmailMessage
import aiosmtplib
import httpx

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models import User, PasswordResetToken, Bot, ReferralPartner
from app.config import settings
from app.schemas import (
    RegisterRequest, LoginRequest, TokenResponse,
    ResetPasswordRequest, SetPasswordRequest, VerifyCodeRequest,
    TelegramAuthRequest, GoogleAuthRequest,
)
from app.auth import hash_password, verify_password, create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/api/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)


async def _auto_create_partnership(db, user_id: int, referrer_id: int):
    """If the referrer has a bot with allow_partners, auto-create a partnership."""
    result = await db.execute(
        select(Bot).where(
            Bot.user_id == referrer_id,
            Bot.allow_partners == True,
            Bot.is_active == True,
        )
    )
    bot = result.scalar_one_or_none()
    if not bot:
        return
    # Check not already a partner
    existing = await db.execute(
        select(ReferralPartner).where(
            ReferralPartner.user_id == user_id,
            ReferralPartner.bot_id == bot.id,
        )
    )
    if existing.scalar_one_or_none():
        return
    partner = ReferralPartner(
        user_id=user_id,
        bot_id=bot.id,
        ref_code=secrets.token_urlsafe(6),
        credits=5,
    )
    db.add(partner)
    await db.flush()


def _generate_user_ref_code() -> str:
    return secrets.token_urlsafe(6)  # 8 chars


def _generate_reset_code() -> str:
    return str(random.SystemRandom().randint(100000, 999999))


async def _send_reset_email(email: str, code: str):
    if not settings.SMTP_HOST:
        logger.warning("SMTP not configured, reset code for %s: %s", email, code)
        return

    msg = EmailMessage()
    msg["Subject"] = "Meepo — код восстановления пароля"
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = email
    msg.set_content(f"Ваш код для восстановления пароля: {code}\n\nКод действителен 15 минут.\n\nЕсли вы не запрашивали сброс пароля, проигнорируйте это письмо.")

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER or None,
        password=settings.SMTP_PASSWORD or None,
        start_tls=True,
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("5/minute")
async def register(request: Request, data: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    # Cleanup expired reset tokens (piggyback on registration)
    await db.execute(
        delete(PasswordResetToken).where(
            (PasswordResetToken.expires_at < func.now()) |
            (PasswordResetToken.used == True)
        )
    )

    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Resolve referrer
    referred_by_id = None
    if data.ref_code:
        result = await db.execute(select(User).where(User.ref_code == data.ref_code))
        referrer = result.scalar_one_or_none()
        if referrer:
            referred_by_id = referrer.id

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
        ref_code=_generate_user_ref_code(),
        referred_by_id=referred_by_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Auto-create partnership if referrer has a bot
    if referred_by_id:
        await _auto_create_partnership(db, user.id, referred_by_id)
        await db.commit()

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/api/auth",
        max_age=7 * 24 * 3600,
    )

    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, data: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/api/auth",
        max_age=7 * 24 * 3600,
    )

    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, db: AsyncSession = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    user_id = decode_token(refresh_token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/reset-password")
@limiter.limit("3/minute")
async def reset_password(request: Request, data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    if not user:
        return {"message": "Если этот email зарегистрирован, код отправлен"}

    # Invalidate previous unused tokens for this user
    await db.execute(
        delete(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False,
        )
    )

    code = _generate_reset_code()
    reset = PasswordResetToken(
        user_id=user.id,
        token=code,
        expires_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=15),
    )
    db.add(reset)
    await db.commit()

    try:
        await _send_reset_email(data.email, code)
    except Exception:
        logger.exception("Failed to send reset email to %s", data.email)

    return {"message": "Если этот email зарегистрирован, код отправлен"}


@router.post("/verify-code")
@limiter.limit("10/minute")
async def verify_code(request: Request, data: VerifyCodeRequest, db: AsyncSession = Depends(get_db)):
    """Verify the 6-digit code and return a one-time token for setting new password."""
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == data.code,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.datetime.utcnow(),
        )
    )
    reset = result.scalar_one_or_none()
    if not reset:
        raise HTTPException(status_code=400, detail="Неверный или просроченный код")

    # Check that the code belongs to the right email
    user_result = await db.execute(select(User).where(User.id == reset.user_id))
    user = user_result.scalar_one_or_none()
    if not user or user.email != data.email:
        raise HTTPException(status_code=400, detail="Неверный или просроченный код")

    # Generate a one-time token for set-password
    set_token = secrets.token_urlsafe(32)
    reset.token = set_token  # replace code with token
    await db.commit()

    return {"token": set_token}


def _verify_telegram_auth(data: TelegramAuthRequest, bot_token: str) -> bool:
    """Verify Telegram Login Widget data hash."""
    check_data = {
        "id": data.id,
        "first_name": data.first_name,
    }
    if data.last_name:
        check_data["last_name"] = data.last_name
    if data.username:
        check_data["username"] = data.username
    if data.photo_url:
        check_data["photo_url"] = data.photo_url
    check_data["auth_date"] = data.auth_date

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(check_data.items())
    )
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed_hash, data.hash)


@router.post("/telegram", response_model=TokenResponse)
@limiter.limit("10/minute")
async def auth_telegram(
    request: Request,
    data: TelegramAuthRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    if not settings.TELEGRAM_BOT_TOKEN_LOGIN:
        raise HTTPException(status_code=501, detail="Telegram login not configured")

    # Reject data older than 5 minutes
    if abs(time.time() - data.auth_date) > 300:
        raise HTTPException(status_code=400, detail="Auth data expired")

    if not _verify_telegram_auth(data, settings.TELEGRAM_BOT_TOKEN_LOGIN):
        raise HTTPException(status_code=401, detail="Invalid Telegram auth data")

    # Find existing user by telegram_id
    result = await db.execute(select(User).where(User.telegram_id == data.id))
    user = result.scalar_one_or_none()

    if not user:
        # Try to find by username-based email match (edge case)
        tg_email = f"tg_{data.id}@telegram.user"

        user = User(
            email=tg_email,
            name=data.first_name + (f" {data.last_name}" if data.last_name else ""),
            telegram_id=data.id,
            auth_provider="telegram",
            ref_code=_generate_user_ref_code(),
        )
        # Resolve referrer
        if data.ref_code:
            ref_result = await db.execute(select(User).where(User.ref_code == data.ref_code))
            referrer = ref_result.scalar_one_or_none()
            if referrer:
                user.referred_by_id = referrer.id

        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Auto-create partnership if referrer has a bot
        if user.referred_by_id:
            await _auto_create_partnership(db, user.id, user.referred_by_id)
            await db.commit()
    elif not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/api/auth",
        max_age=7 * 24 * 3600,
    )

    return TokenResponse(access_token=access_token)


async def _verify_google_token(credential: str) -> dict | None:
    """Verify Google ID token and return user info."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
        )
        if resp.status_code != 200:
            return None
        payload = resp.json()
        # Verify audience matches our client ID
        if payload.get("aud") != settings.GOOGLE_CLIENT_ID:
            return None
        if payload.get("email_verified") != "true":
            return None
        return payload


@router.post("/google", response_model=TokenResponse)
@limiter.limit("10/minute")
async def auth_google(
    request: Request,
    data: GoogleAuthRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google login not configured")

    google_info = await _verify_google_token(data.credential)
    if not google_info:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    google_id = google_info["sub"]
    email = google_info["email"]
    name = google_info.get("name", email.split("@")[0])

    # Find by google_id first
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if not user:
        # Try to find by email (link accounts)
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            # Link Google ID to existing account
            user.google_id = google_id
            if not user.auth_provider:
                user.auth_provider = "email"
            await db.commit()
        else:
            # Create new user
            user = User(
                email=email,
                name=name,
                google_id=google_id,
                auth_provider="google",
                ref_code=_generate_user_ref_code(),
            )
            if data.ref_code:
                ref_result = await db.execute(select(User).where(User.ref_code == data.ref_code))
                referrer = ref_result.scalar_one_or_none()
                if referrer:
                    user.referred_by_id = referrer.id

            db.add(user)
            await db.commit()
            await db.refresh(user)

            # Auto-create partnership if referrer has a bot
            if user.referred_by_id:
                await _auto_create_partnership(db, user.id, user.referred_by_id)
                await db.commit()

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/api/auth",
        max_age=7 * 24 * 3600,
    )

    return TokenResponse(access_token=access_token)


@router.post("/set-password")
async def set_password(data: SetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == data.token,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.datetime.utcnow(),
        )
    )
    reset = result.scalar_one_or_none()
    if not reset:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_result = await db.execute(select(User).where(User.id == reset.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.password_hash = hash_password(data.password)
    reset.used = True
    await db.commit()

    return {"message": "Password updated successfully"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refresh_token", path="/api/auth")
    return {"message": "Logged out"}
