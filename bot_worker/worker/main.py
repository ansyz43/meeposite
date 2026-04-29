"""
Meepo Bot Worker — manages all Telegram bots from a single process.

Polls the database for active bots and runs them concurrently.
Periodically checks for new/removed bots and adjusts accordingly.
"""

import asyncio
import hashlib
import logging
import datetime
import time
from collections import OrderedDict
from aiohttp import web

import sentry_sdk
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.exceptions import TelegramConflictError, TelegramUnauthorizedError
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select, update

from worker.config import settings
from worker.database import async_session
from worker.models import Bot as BotModel, User, Contact, Message, ReferralPartner, ReferralSession
from worker.crypto import decrypt_token
from worker.ai_service import get_ai_response
from worker.vk_handler import start_vk_bot as _start_vk_bot
import worker.vk_handler as vk_handler


def _utcnow() -> datetime.datetime:
    """Return current UTC time as a naive datetime (no tzinfo) for DB compat."""
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("meepo")

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        environment="production",
    )
    logger.info("Sentry initialized")

# Active bot instances: bot_db_id -> (Bot, Dispatcher, task)
active_bots: dict[int, tuple[Bot, Dispatcher, asyncio.Task]] = {}
# Settings hash per bot to detect changes
bot_settings_hash: dict[int, str] = {}

# Deduplication: track recently processed (chat_id, message_id) to prevent double-processing
_processed_messages: OrderedDict[tuple[int, int], float] = OrderedDict()
_DEDUP_MAX_SIZE = 5000
_DEDUP_TTL = 120  # seconds

# Limit concurrent AI requests to prevent OpenAI rate limit avalanche
_ai_semaphore = asyncio.Semaphore(30)

# Share semaphore with VK handler
vk_handler._ai_semaphore = _ai_semaphore

# ─── Health check HTTP server ───
_worker_started_at = time.monotonic()

async def _health_handler(request: web.Request) -> web.Response:
    """Health check endpoint for Docker."""
    uptime = int(time.monotonic() - _worker_started_at)
    return web.json_response({
        "status": "ok",
        "active_bots": len(active_bots),
        "uptime_seconds": uptime,
    })

async def _start_health_server():
    app = web.Application()
    app.router.add_get("/health", _health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logger.info("Health check server started on :8080")

# ─── Telegram alerts ───
_last_alert_time: float = 0
_ALERT_COOLDOWN = 300  # max 1 alert per 5 minutes

async def send_alert(text: str):
    """Send alert to admin via Telegram (with cooldown)."""
    global _last_alert_time
    if not settings.ALERT_CHAT_ID or not settings.ALERT_BOT_TOKEN:
        return
    now = time.monotonic()
    if now - _last_alert_time < _ALERT_COOLDOWN:
        return
    _last_alert_time = now
    try:
        bot = Bot(token=settings.ALERT_BOT_TOKEN)
        await bot.send_message(chat_id=settings.ALERT_CHAT_ID, text=f"⚠️ Meepo Alert\n\n{text}")
        await bot.session.close()
        logger.info("Alert sent to admin")
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")


def _is_duplicate(chat_id: int, message_id: int) -> bool:
    """Check if this message was already processed. Returns True if duplicate."""
    key = (chat_id, message_id)
    now = time.monotonic()
    # Cleanup old entries
    while _processed_messages and len(_processed_messages) > _DEDUP_MAX_SIZE:
        _processed_messages.popitem(last=False)
    if key in _processed_messages:
        return True
    _processed_messages[key] = now
    return False


def _compute_settings_hash(bot_record: BotModel, seller_name: str) -> str:
    """Compute a hash of bot settings to detect changes."""
    parts = [
        bot_record.assistant_name or "",
        bot_record.seller_link or "",
        bot_record.greeting_message or "",
        bot_record.bot_description or "",
        seller_name,
    ]
    return hashlib.md5("|".join(parts).encode()).hexdigest()


async def get_chat_history(session, contact_id: int, limit: int = 20) -> list[dict]:
    """Load recent chat history from database."""
    result = await session.execute(
        select(Message)
        .where(Message.contact_id == contact_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = list(reversed(result.scalars().all()))
    return [{"role": m.role, "content": m.content} for m in messages]


async def get_or_create_contact(session, bot_id: int, tg_user: types.User) -> Contact:
    """Get or create a contact record for a Telegram user."""
    result = await session.execute(
        select(Contact).where(
            Contact.bot_id == bot_id,
            Contact.telegram_id == tg_user.id,
        )
    )
    contact = result.scalar_one_or_none()

    if contact:
        contact.telegram_username = tg_user.username
        contact.first_name = tg_user.first_name
        contact.last_name = tg_user.last_name
        contact.last_message_at = _utcnow()
        contact.message_count += 1
        await session.flush()
        return contact

    contact = Contact(
        bot_id=bot_id,
        telegram_id=tg_user.id,
        telegram_username=tg_user.username,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
        last_message_at=_utcnow(),
        message_count=1,
    )
    session.add(contact)
    await session.flush()
    await session.refresh(contact)
    return contact


async def save_message(session, contact_id: int, role: str, content: str):
    """Save a message to the database."""
    msg = Message(contact_id=contact_id, role=role, content=content)
    session.add(msg)
    await session.flush()


async def save_phone(session, contact_id: int, phone: str):
    """Save phone number from shared contact."""
    await session.execute(
        update(Contact).where(Contact.id == contact_id).values(phone=phone)
    )
    await session.flush()


# ─── Terms / consent helpers ───
CONSENT_PROMPT = (
    "Перед началом общения подтвердите согласие с условиями соглашения и Политикой "
    "обработки персональных данных."
)
CONSENT_THANKS = "Спасибо! Теперь я могу помочь вам. Напишите свой вопрос."


def _consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принимаю", callback_data="accept_terms")],
        [InlineKeyboardButton(text="📄 Читать условия", url=settings.OFFER_BOT_URL)],
    ])


async def _mark_contact_accepted(session, contact_id: int, source: str):
    await session.execute(
        update(Contact)
        .where(Contact.id == contact_id)
        .values(
            terms_accepted_at=_utcnow(),
            terms_version=settings.TERMS_VERSION,
            terms_source=source,
        )
    )
    await session.flush()


def create_dispatcher(bot_db_id: int, assistant_name: str, seller_name: str,
                      seller_link: str | None, greeting_message: str | None) -> Dispatcher:
    """Create a dispatcher with handlers for a specific bot."""
    dp = Dispatcher()

    # Per-contact partner seller_link override: telegram_id -> seller_link
    partner_links: dict[int, str] = {}

    @dp.update.outer_middleware()
    async def log_all_updates(handler, event, data):
        logger.info(f"[BOT#{bot_db_id}] Update received: type={event.event_type}")
        return await handler(event, data)

    @dp.errors()
    async def on_error(event: types.ErrorEvent):
        logger.error(f"[BOT#{bot_db_id}] Handler error: {event.exception}", exc_info=True)
        return True

    @dp.message(CommandStart())
    async def handle_start(message: types.Message):
        logger.info(f"[BOT#{bot_db_id}] /start from user {message.from_user.id}")
        if _is_duplicate(message.chat.id, message.message_id):
            return

        # Parse deep-link payload: /start p_REFCODE
        payload = message.text.split(maxsplit=1)[1] if message.text and " " in message.text else None

        async with async_session() as db:
            contact = await get_or_create_contact(db, bot_db_id, message.from_user)

            # Handle partner deep-link
            if payload and payload.startswith("p_"):
                ref_code = payload[2:]
                try:
                    result = await db.execute(
                        select(ReferralPartner).where(
                            ReferralPartner.ref_code == ref_code,
                            ReferralPartner.bot_id == bot_db_id,
                            ReferralPartner.is_active == True,
                        )
                    )
                    partner = result.scalar_one_or_none()
                    if partner and partner.credits > 0:
                        # Check if session already exists for this partner+user
                        existing = await db.execute(
                            select(ReferralSession).where(
                                ReferralSession.partner_id == partner.id,
                                ReferralSession.telegram_id == message.from_user.id,
                            )
                        )
                        session_rec = existing.scalar_one_or_none()
                        if session_rec:
                            # Reactivate existing session
                            session_rec.is_active = True
                            session_rec.expires_at = _utcnow() + datetime.timedelta(days=30)
                        else:
                            # Create new session, decrement credits
                            session_rec = ReferralSession(
                                partner_id=partner.id,
                                contact_id=contact.id,
                                telegram_id=message.from_user.id,
                                expires_at=_utcnow() + datetime.timedelta(days=30),
                            )
                            db.add(session_rec)
                            partner.credits -= 1
                        # Cache partner's seller_link for this user
                        partner_links[message.from_user.id] = partner.seller_link
                        logger.info(f"[BOT#{bot_db_id}] Partner session: ref={ref_code} user={message.from_user.id} credits_left={partner.credits}")
                    elif partner and partner.credits <= 0:
                        logger.info(f"[BOT#{bot_db_id}] Partner {ref_code} has no credits left")
                except Exception as e:
                    logger.error(f"[BOT#{bot_db_id}] Partner deep-link error: {e}", exc_info=True)

            greeting = greeting_message or f"Привет! Я {assistant_name}. Чем могу помочь?"
            await save_message(db, contact.id, "assistant", greeting)
            needs_consent = not contact.terms_accepted_at
            await db.commit()

        if needs_consent:
            await message.answer(
                f"{greeting}\n\n{CONSENT_PROMPT}",
                reply_markup=_consent_keyboard(),
                disable_web_page_preview=True,
            )
        else:
            await message.answer(greeting)

    @dp.callback_query(F.data == "accept_terms")
    async def handle_accept_terms(query: types.CallbackQuery):
        async with async_session() as db:
            contact = await get_or_create_contact(db, bot_db_id, query.from_user)
            if not contact.terms_accepted_at:
                await _mark_contact_accepted(db, contact.id, "telegram")
            await db.commit()
        try:
            await query.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await query.answer("Согласие принято", show_alert=False)
        try:
            await query.message.answer(CONSENT_THANKS)
        except Exception:
            pass

    @dp.message(F.contact)
    async def handle_contact(message: types.Message):
        async with async_session() as db:
            contact = await get_or_create_contact(db, bot_db_id, message.from_user)
            if message.contact and message.contact.phone_number:
                await save_phone(db, contact.id, message.contact.phone_number)
            await db.commit()
        if message.contact and message.contact.phone_number:
            await message.answer("Спасибо! Ваш номер сохранён. Чем могу помочь?")

    @dp.message(F.text)
    async def handle_message(message: types.Message):
        logger.info(f"[BOT#{bot_db_id}] Message from user {message.from_user.id}: {message.text[:50]}")
        if _is_duplicate(message.chat.id, message.message_id):
            return

        # Consent gate: если контакт не принял соглашение — предлагаем принять
        # Авто-акцепт по тексту "принимаю" для fallback.
        text_lower = (message.text or "").strip().lower()
        async with async_session() as db_consent:
            contact_consent = await get_or_create_contact(db_consent, bot_db_id, message.from_user)
            if not contact_consent.terms_accepted_at:
                if text_lower in ("принимаю", "я принимаю", "да", "accept", "i accept"):
                    await _mark_contact_accepted(db_consent, contact_consent.id, "telegram")
                    await db_consent.commit()
                    await message.answer(CONSENT_THANKS)
                    return
                await db_consent.commit()
                await message.answer(
                    CONSENT_PROMPT,
                    reply_markup=_consent_keyboard(),
                    disable_web_page_preview=True,
                )
                return
            await db_consent.commit()

        # Determine effective seller_link: partner override or bot owner's
        effective_seller_link = partner_links.get(message.from_user.id) or seller_link

        # If not in memory cache, check DB for active partner session
        if not partner_links.get(message.from_user.id):
            try:
                async with async_session() as db_check:
                    result = await db_check.execute(
                        select(ReferralPartner.seller_link)
                        .join(ReferralSession, ReferralSession.partner_id == ReferralPartner.id)
                        .where(
                            ReferralSession.telegram_id == message.from_user.id,
                            ReferralSession.is_active == True,
                            ReferralSession.expires_at > _utcnow(),
                            ReferralPartner.bot_id == bot_db_id,
                        )
                        .limit(1)
                    )
                    partner_sl = result.scalar_one_or_none()
                    if partner_sl:
                        partner_links[message.from_user.id] = partner_sl
                        effective_seller_link = partner_sl
            except Exception:
                pass

        async with async_session() as db:
            contact = await get_or_create_contact(db, bot_db_id, message.from_user)
            user_text = message.text

            # Save user message
            await save_message(db, contact.id, "user", user_text)

            # Get chat history
            history = await get_chat_history(db, contact.id, limit=10)
            await db.commit()  # commit contact + user message before AI call

        # Show typing indicator while AI is thinking
        try:
            await message.answer_chat_action("typing")
        except Exception:
            pass

        # AI call outside the DB session to free the connection
        # Retry up to 3 times with backoff on transient errors
        max_retries = 3
        ai_response = None
        last_error = None
        for attempt in range(max_retries):
            try:
                async with _ai_semaphore:
                    ai_response = await asyncio.wait_for(
                        get_ai_response(
                            assistant_name, seller_name, bool(effective_seller_link),
                            history, user_text,
                        ),
                        timeout=60.0,
                    )
                break  # success
            except asyncio.TimeoutError:
                last_error = "timeout"
                logger.warning(f"[BOT#{bot_db_id}] AI timeout (attempt {attempt+1}/{max_retries})")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"[BOT#{bot_db_id}] AI error (attempt {attempt+1}/{max_retries}): {e}", exc_info=True)
            if attempt < max_retries - 1:
                await asyncio.sleep(2 * (attempt + 1))  # 2s, 4s backoff
                try:
                    await message.answer_chat_action("typing")
                except Exception:
                    pass

        if ai_response is None:
            if last_error == "timeout":
                logger.error(f"[BOT#{bot_db_id}] AI failed after {max_retries} retries: timeout")
                ai_response = "Извините, ответ занял слишком много времени. Попробуйте ещё раз."
                asyncio.create_task(send_alert(f"BOT#{bot_db_id}: AI timeout after {max_retries} retries"))
            else:
                logger.error(f"[BOT#{bot_db_id}] AI failed after {max_retries} retries: {last_error}")
                ai_response = "Извините, произошла временная ошибка. Попробуйте ещё раз через несколько секунд."
                asyncio.create_task(send_alert(f"BOT#{bot_db_id}: AI error — {last_error[:200]}"))

        # Replace [ССЫЛКА] placeholder with actual seller link
        link_was_sent = False
        if not effective_seller_link and '[ССЫЛКА]' in ai_response:
            # Safety: strip raw [ССЫЛКА] markers if no seller link configured
            ai_response = ai_response.replace('[ССЫЛКА]', '').strip()
        elif effective_seller_link and '[ССЫЛКА]' in ai_response:
            # Split response: send text and link as separate messages
            parts = ai_response.split('[ССЫЛКА]')
            text_before = parts[0].rstrip(" \u2014-\n")
            text_after = '[ССЫЛКА]'.join(parts[1:]).lstrip(" \u2014-\n") if len(parts) > 1 else ''
            ai_response = text_before
            link_was_sent = True

        # Save AI response in a new short session
        async with async_session() as db:
            full_text = f"{ai_response}\n{effective_seller_link}" if link_was_sent else ai_response
            await save_message(db, contact.id, "assistant", full_text)
            if link_was_sent:
                from sqlalchemy import update
                await db.execute(update(Contact).where(Contact.id == contact.id).values(link_sent=True))
            await db.commit()
        if ai_response.strip():
            await message.answer(ai_response)
        if link_was_sent:
            await message.answer(effective_seller_link)
        if link_was_sent and text_after.strip():
            await message.answer(text_after)

    return dp


async def start_bot(bot_record: BotModel, seller_name: str):
    """Start polling for a single bot."""
    retry_delay = 5
    max_retry_delay = 60
    bot_instance = None
    while True:
        try:
            token = decrypt_token(bot_record.bot_token_encrypted)
            if settings.TELEGRAM_API_URL:
                tg_server = TelegramAPIServer.from_base(settings.TELEGRAM_API_URL)
                session = AiohttpSession(api=tg_server)
                bot_instance = Bot(token=token, session=session)
            else:
                bot_instance = Bot(token=token)
            dp = create_dispatcher(
                bot_db_id=bot_record.id,
                assistant_name=bot_record.assistant_name,
                seller_name=seller_name,
                seller_link=bot_record.seller_link,
                greeting_message=bot_record.greeting_message,
            )

            logger.info(f"Starting bot #{bot_record.id} (@{bot_record.bot_username})")
            logger.info("Start polling")
            retry_delay = 5  # reset on successful connect
            # Use _polling directly instead of start_polling to prevent
            # orphan polling tasks on cancel (zombie bot fix)
            allowed_updates = dp.resolve_used_update_types()
            await dp._polling(
                bot=bot_instance,
                handle_as_tasks=True,
                polling_timeout=15,
                allowed_updates=allowed_updates,
            )
        except asyncio.CancelledError:
            logger.info(f"Bot #{bot_record.id} stopped (cancelled)")
            return
        except (TelegramConflictError, TelegramUnauthorizedError) as e:
            # Fatal: another instance running or token revoked — do NOT retry
            logger.warning(f"Bot #{bot_record.id} fatal error, exiting: {e}")
            return
        except Exception as e:
            logger.error(f"Bot #{bot_record.id} error: {e}")
            logger.info(f"Bot #{bot_record.id} retrying in {retry_delay}s...")
            try:
                await asyncio.sleep(retry_delay)
            except asyncio.CancelledError:
                logger.info(f"Bot #{bot_record.id} stopped during retry")
                return
            retry_delay = min(retry_delay * 2, max_retry_delay)
        finally:
            if bot_instance:
                try:
                    await bot_instance.session.close()
                except Exception:
                    pass
                bot_instance = None


async def sync_bots():
    """Check database for new/removed bots and sync with active instances."""
    async with async_session() as session:
        result = await session.execute(
            select(BotModel, User)
            .join(User, BotModel.user_id == User.id)
            .where(BotModel.is_active == True, User.is_active == True)
        )
        db_bots = result.all()

    active_ids = set()
    for bot_record, user_record in db_bots:
        active_ids.add(bot_record.id)
        new_hash = _compute_settings_hash(bot_record, user_record.name)

        if bot_record.id not in active_bots:
            # Start new bot (dispatch by platform)
            if bot_record.platform == "vk":
                task = asyncio.create_task(_start_vk_bot(bot_record, user_record.name))
            else:
                task = asyncio.create_task(start_bot(bot_record, user_record.name))
            active_bots[bot_record.id] = (None, None, task)
            bot_settings_hash[bot_record.id] = new_hash
        elif bot_settings_hash.get(bot_record.id) != new_hash:
            # Settings changed — restart bot
            logger.info(f"Settings changed for bot #{bot_record.id}, restarting...")
            _, _, old_task = active_bots[bot_record.id]
            old_task.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(old_task), timeout=10.0)
            except (asyncio.CancelledError, asyncio.TimeoutError, Exception):
                pass  # old task is dead or timed out — safe to proceed
            if bot_record.platform == "vk":
                task = asyncio.create_task(_start_vk_bot(bot_record, user_record.name))
            else:
                task = asyncio.create_task(start_bot(bot_record, user_record.name))
            active_bots[bot_record.id] = (None, None, task)
            bot_settings_hash[bot_record.id] = new_hash

    # Stop removed/deactivated bots
    to_remove = set(active_bots.keys()) - active_ids
    for bot_id in to_remove:
        logger.info(f"Stopping bot #{bot_id} (deactivated or removed)")
        _, _, task = active_bots[bot_id]
        task.cancel()
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=10.0)
        except (asyncio.CancelledError, asyncio.TimeoutError, Exception):
            pass
        del active_bots[bot_id]
        bot_settings_hash.pop(bot_id, None)


async def main():
    logger.info("Meepo Bot Worker starting...")
    await _start_health_server()

    while True:
        try:
            await sync_bots()
            bot_count = len(active_bots)
            logger.info(f"Active bots: {bot_count}")
        except Exception as e:
            logger.error(f"Sync error: {e}")

        # Check for changes every 10 seconds
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
