"""
VK Long Poll handler for Meepo bot worker.
Handles incoming VK community messages via Long Poll API.
"""

import asyncio
import datetime
import json
import logging
import random

import aiohttp
from sqlalchemy import select, update as sa_update

from worker.config import settings
from worker.database import async_session
from worker.models import Contact, Message
from worker.ai_service import get_ai_response
from worker.crypto import decrypt_token

logger = logging.getLogger("meepo.vk")

VK_API = "https://api.vk.com/method"
VK_API_VERSION = "5.199"

# Will be set from main.py
_ai_semaphore: asyncio.Semaphore | None = None

CONSENT_PROMPT = (
    "Перед началом общения подтвердите согласие с условиями соглашения и Политикой "
    "обработки персональных данных. Нажмите «Принимаю» или ответьте «Принимаю»."
)
CONSENT_THANKS = "Спасибо! Теперь я могу помочь вам. Напишите свой вопрос."


def _consent_keyboard_json() -> str:
    return json.dumps({
        "inline": True,
        "buttons": [
            [{
                "action": {
                    "type": "text",
                    "label": "✅ Принимаю",
                    "payload": json.dumps({"action": "accept_terms"}),
                },
                "color": "primary",
            }],
            [{
                "action": {
                    "type": "open_link",
                    "link": settings.OFFER_BOT_URL,
                    "label": "📄 Читать условия",
                    "payload": json.dumps({"action": "open_terms"}),
                },
            }],
        ],
    }, ensure_ascii=False)


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


async def _vk_api(http: aiohttp.ClientSession, method: str, token: str, **params):
    """Call a VK API method."""
    params["access_token"] = token
    params["v"] = VK_API_VERSION
    async with http.post(f"{VK_API}/{method}", data=params) as resp:
        data = await resp.json()
        if "error" in data:
            raise Exception(f"VK API {method}: {data['error'].get('error_msg', data['error'])}")
        return data.get("response")


async def _get_or_create_vk_contact(db_session, bot_id: int, vk_user_id: int,
                                     user_info: dict | None = None) -> Contact:
    """Get or create a Contact for a VK user."""
    result = await db_session.execute(
        select(Contact).where(
            Contact.bot_id == bot_id,
            Contact.vk_id == vk_user_id,
        )
    )
    contact = result.scalar_one_or_none()

    if contact:
        contact.last_message_at = _utcnow()
        contact.message_count += 1
        if user_info:
            contact.first_name = user_info.get("first_name")
            contact.last_name = user_info.get("last_name")
        await db_session.flush()
        return contact

    contact = Contact(
        bot_id=bot_id,
        platform="vk",
        vk_id=vk_user_id,
        first_name=user_info.get("first_name") if user_info else None,
        last_name=user_info.get("last_name") if user_info else None,
        last_message_at=_utcnow(),
        message_count=1,
    )
    db_session.add(contact)
    await db_session.flush()
    await db_session.refresh(contact)
    return contact


async def start_vk_bot(bot_record, seller_name: str):
    """Start VK Long Poll for a single bot. Retries on failure."""
    retry_delay = 5
    max_retry_delay = 60

    while True:
        try:
            token = decrypt_token(bot_record.bot_token_encrypted)
            group_id = bot_record.vk_group_id

            logger.info(f"Starting VK bot #{bot_record.id} (group {group_id})")

            async with aiohttp.ClientSession() as http:
                await _run_long_poll(
                    http, token, group_id, bot_record.id,
                    assistant_name=bot_record.assistant_name,
                    seller_name=seller_name,
                    seller_link=bot_record.seller_link,
                    greeting_message=bot_record.greeting_message,
                )
            retry_delay = 5
        except asyncio.CancelledError:
            logger.info(f"VK bot #{bot_record.id} stopped")
            return
        except Exception as e:
            logger.error(f"VK bot #{bot_record.id} error: {e}")
            logger.info(f"VK bot #{bot_record.id} retrying in {retry_delay}s...")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_retry_delay)


async def _run_long_poll(http, token, group_id, bot_db_id,
                          assistant_name, seller_name, seller_link, greeting_message):
    """Run the VK Long Poll loop."""
    lp = await _vk_api(http, "groups.getLongPollServer", token, group_id=group_id)
    server = lp["server"]
    key = lp["key"]
    ts = lp["ts"]

    logger.info(f"[VK_BOT#{bot_db_id}] Long Poll connected, server={server[:50]}...")

    while True:
        try:
            url = f"{server}?act=a_check&key={key}&ts={ts}&wait=25"
            async with http.get(url, timeout=aiohttp.ClientTimeout(total=90)) as resp:
                data = await resp.json()

            if "failed" in data:
                fail_code = data["failed"]
                logger.warning(f"[VK_BOT#{bot_db_id}] LP fail code {fail_code}")
                if fail_code == 1:
                    ts = data.get("ts", ts)
                    continue
                elif fail_code in (2, 3):
                    lp = await _vk_api(http, "groups.getLongPollServer", token, group_id=group_id)
                    server = lp["server"]
                    key = lp["key"]
                    if fail_code == 3:
                        ts = lp["ts"]
                    continue

            ts = data.get("ts", ts)
            updates = data.get("updates", [])

            if updates:
                logger.info(f"[VK_BOT#{bot_db_id}] Got {len(updates)} updates: {[u.get('type') for u in updates]}")

            for update in updates:
                if update.get("type") == "message_new":
                    msg_obj = update.get("object", {}).get("message", {})
                    logger.info(f"[VK_BOT#{bot_db_id}] message_new from_id={msg_obj.get('from_id')} text={msg_obj.get('text', '')[:50]}")
                    asyncio.create_task(
                        _handle_vk_message(
                            http, token, bot_db_id, msg_obj,
                            assistant_name, seller_name, seller_link, greeting_message,
                        )
                    )
        except asyncio.CancelledError:
            raise
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            logger.error(f"[VK_BOT#{bot_db_id}] LP error: {e}")
            await asyncio.sleep(2)
            lp = await _vk_api(http, "groups.getLongPollServer", token, group_id=group_id)
            server = lp["server"]
            key = lp["key"]
            ts = lp["ts"]


async def _handle_vk_message(http, token, bot_db_id, msg_obj,
                               assistant_name, seller_name, seller_link, greeting_message):
    """Handle a single incoming VK message."""
    from worker.main import send_alert, get_chat_history, save_message

    peer_id = msg_obj.get("peer_id")
    from_id = msg_obj.get("from_id")
    text = (msg_obj.get("text") or "").strip()
    raw_payload = msg_obj.get("payload")
    payload_data = None
    if raw_payload:
        try:
            payload_data = json.loads(raw_payload) if isinstance(raw_payload, str) else raw_payload
        except Exception:
            payload_data = None

    # Ignore outgoing messages (from_id < 0 means group/community)
    if not from_id or from_id < 0:
        return
    if not text and not payload_data:
        return

    try:
        # Get VK user info
        user_info = None
        try:
            result = await _vk_api(http, "users.get", token, user_ids=str(from_id))
            if result and len(result) > 0:
                user_info = result[0]
        except Exception:
            pass

        # ── Consent gate ──
        async with async_session() as db_consent:
            contact_consent = await _get_or_create_vk_contact(db_consent, bot_db_id, from_id, user_info)
            if not contact_consent.terms_accepted_at:
                accept_via_payload = isinstance(payload_data, dict) and payload_data.get("action") == "accept_terms"
                accept_via_text = text.lower() in ("принимаю", "я принимаю", "да", "accept")
                if accept_via_payload or accept_via_text:
                    await db_consent.execute(
                        sa_update(Contact)
                        .where(Contact.id == contact_consent.id)
                        .values(
                            terms_accepted_at=_utcnow(),
                            terms_version=settings.TERMS_VERSION,
                            terms_source="vk",
                        )
                    )
                    await db_consent.commit()
                    post_consent = greeting_message or f"Привет! Я {assistant_name}. Чем могу помочь?"
                    await _vk_api(
                        http, "messages.send", token,
                        peer_id=peer_id,
                        message=post_consent,
                        random_id=random.randint(1, 2**31),
                    )
                    return
                await db_consent.commit()
                await _vk_api(
                    http, "messages.send", token,
                    peer_id=peer_id,
                    message=CONSENT_PROMPT,
                    keyboard=_consent_keyboard_json(),
                    dont_parse_links=1,
                    random_id=random.randint(1, 2**31),
                )
                return

        if not text:
            return

        async with async_session() as db:
            contact = await _get_or_create_vk_contact(db, bot_db_id, from_id, user_info)
            await save_message(db, contact.id, "user", text)
            history = await get_chat_history(db, contact.id, limit=10)
            await db.commit()

        # AI call
        sem = _ai_semaphore or asyncio.Semaphore(30)
        max_retries = 3
        ai_response = None
        last_error = None
        for attempt in range(max_retries):
            try:
                async with sem:
                    ai_response = await asyncio.wait_for(
                        get_ai_response(
                            assistant_name, seller_name, bool(seller_link),
                            history, text,
                        ),
                        timeout=60.0,
                    )
                break
            except asyncio.TimeoutError:
                last_error = "timeout"
                logger.warning(f"[VK_BOT#{bot_db_id}] AI timeout (attempt {attempt+1})")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"[VK_BOT#{bot_db_id}] AI error (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 * (attempt + 1))

        if ai_response is None:
            if last_error == "timeout":
                ai_response = "Извините, ответ занял слишком много времени. Попробуйте ещё раз."
                asyncio.create_task(send_alert(f"VK_BOT#{bot_db_id}: AI timeout after {max_retries} retries"))
            else:
                ai_response = "Извините, произошла временная ошибка. Попробуйте ещё раз через несколько секунд."
                asyncio.create_task(send_alert(f"VK_BOT#{bot_db_id}: AI error — {(last_error or '')[:200]}"))

        # Replace [ССЫЛКА] placeholder
        link_was_sent = False
        text_after = ''
        if not seller_link and '[ССЫЛКА]' in ai_response:
            # Safety: strip raw [ССЫЛКА] markers if no seller link configured
            ai_response = ai_response.replace('[ССЫЛКА]', '').strip()
        elif seller_link and '[ССЫЛКА]' in ai_response:
            parts = ai_response.split('[ССЫЛКА]')
            text_before = parts[0].rstrip(' \u2014-\n')
            text_after = '[ССЫЛКА]'.join(parts[1:]).lstrip(' \u2014-\n') if len(parts) > 1 else ''
            ai_response = text_before
            link_was_sent = True

        # Save AI response
        async with async_session() as db:
            full_text = f"{ai_response}\n{seller_link}" if link_was_sent else ai_response
            await save_message(db, contact.id, "assistant", full_text)
            if link_was_sent:
                await db.execute(
                    sa_update(Contact).where(Contact.id == contact.id).values(link_sent=True)
                )
            await db.commit()

        # Send via VK
        if ai_response.strip():
            await _vk_api(
                http, "messages.send", token,
                peer_id=peer_id,
                message=ai_response,
                random_id=random.randint(1, 2**31),
            )
        if link_was_sent:
            await _vk_api(
                http, "messages.send", token,
                peer_id=peer_id,
                message=seller_link,
                random_id=random.randint(1, 2**31),
            )
        if link_was_sent and text_after.strip():
            await _vk_api(
                http, "messages.send", token,
                peer_id=peer_id,
                message=text_after,
                random_id=random.randint(1, 2**31),
            )
    except Exception as e:
        logger.error(f"[VK_BOT#{bot_db_id}] Error handling message from {from_id}: {e}", exc_info=True)
