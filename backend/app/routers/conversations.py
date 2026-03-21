import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, Bot, Contact, Message
from app.schemas import (
    ContactResponse, ContactListResponse,
    ConversationPreview, ConversationListResponse,
    ConversationDetailResponse, MessageResponse,
)
from app.auth import get_current_user

router = APIRouter(prefix="/api", tags=["conversations"])


async def _get_bot_ids(user: User, db: AsyncSession) -> list[int]:
    """Get all bot IDs for the current user (across all platforms)."""
    result = await db.execute(
        select(Bot.id).where(Bot.user_id == user.id)
    )
    ids = [row[0] for row in result.all()]
    if not ids:
        raise HTTPException(status_code=404, detail="No bot connected")
    return ids


# --- Contacts ---

@router.get("/contacts", response_model=ContactListResponse)
async def list_contacts(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: str = Query("", max_length=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot_ids = await _get_bot_ids(user, db)

    query = select(Contact).where(Contact.bot_id.in_(bot_ids))
    count_query = select(func.count(Contact.id)).where(Contact.bot_id.in_(bot_ids))

    if search:
        safe_search = search.replace("%", "\\%").replace("_", "\\_")
        like = f"%{safe_search}%"
        filter_cond = (
            Contact.first_name.ilike(like) |
            Contact.last_name.ilike(like) |
            Contact.telegram_username.ilike(like) |
            Contact.phone.ilike(like)
        )
        query = query.where(filter_cond)
        count_query = count_query.where(filter_cond)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(
        query.order_by(desc(Contact.last_message_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    contacts = result.scalars().all()

    return ContactListResponse(
        contacts=[_contact_response(c) for c in contacts],
        total=total,
    )


@router.get("/contacts/export")
async def export_contacts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot_ids = await _get_bot_ids(user, db)
    result = await db.execute(
        select(Contact).where(Contact.bot_id.in_(bot_ids)).order_by(desc(Contact.last_message_at))
    )
    contacts = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Платформа", "Имя", "Фамилия", "Username", "Телефон", "Первое сообщение", "Последняя активность", "Сообщений"])
    for c in contacts:
        writer.writerow([
            c.platform or "telegram",
            c.first_name or "",
            c.last_name or "",
            c.telegram_username or "",
            c.phone or "",
            c.first_message_at.isoformat() if c.first_message_at else "",
            c.last_message_at.isoformat() if c.last_message_at else "",
            c.message_count,
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contacts.csv"},
    )


# --- Conversations ---

@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: str = Query("", max_length=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot_ids = await _get_bot_ids(user, db)

    query = select(Contact).where(Contact.bot_id.in_(bot_ids), Contact.message_count > 0)
    count_query = select(func.count(Contact.id)).where(Contact.bot_id.in_(bot_ids), Contact.message_count > 0)

    if search:
        safe_search = search.replace("%", "\\%").replace("_", "\\_")
        like = f"%{safe_search}%"
        filter_cond = (
            Contact.first_name.ilike(like) |
            Contact.last_name.ilike(like) |
            Contact.telegram_username.ilike(like)
        )
        query = query.where(filter_cond)
        count_query = count_query.where(filter_cond)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Subquery for last message per contact
    last_msg_sq = (
        select(
            Message.contact_id,
            func.max(Message.id).label("last_msg_id")
        )
        .group_by(Message.contact_id)
        .subquery()
    )

    result = await db.execute(
        query
        .order_by(desc(Contact.last_message_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    contacts = result.scalars().all()

    # Fetch last messages in batch
    contact_ids = [c.id for c in contacts]
    last_messages = {}
    if contact_ids:
        msg_result = await db.execute(
            select(Message)
            .join(last_msg_sq, Message.id == last_msg_sq.c.last_msg_id)
            .where(Message.contact_id.in_(contact_ids))
        )
        for msg in msg_result.scalars().all():
            last_messages[msg.contact_id] = msg.content[:100]

    previews = []
    for c in contacts:
        previews.append(ConversationPreview(
            contact_id=c.id,
            platform=c.platform,
            telegram_username=c.telegram_username,
            first_name=c.first_name,
            last_name=c.last_name,
            last_message=last_messages.get(c.id),
            last_message_at=c.last_message_at,
            message_count=c.message_count,
            link_sent=c.link_sent,
        ))

    return ConversationListResponse(conversations=previews, total=total)


@router.get("/conversations/{contact_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    contact_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot_ids = await _get_bot_ids(user, db)

    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.bot_id.in_(bot_ids))
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Conversation not found")

    count_result = await db.execute(
        select(func.count(Message.id)).where(Message.contact_id == contact.id)
    )
    total = count_result.scalar()

    msg_result = await db.execute(
        select(Message)
        .where(Message.contact_id == contact.id)
        .order_by(Message.created_at.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    messages = msg_result.scalars().all()

    return ConversationDetailResponse(
        contact=_contact_response(contact),
        messages=[MessageResponse(id=m.id, role=m.role, content=m.content, created_at=m.created_at) for m in messages],
        total=total,
    )


@router.get("/conversations/{contact_id}/export")
async def export_conversation(
    contact_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot_ids = await _get_bot_ids(user, db)

    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.bot_id.in_(bot_ids))
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg_result = await db.execute(
        select(Message)
        .where(Message.contact_id == contact.id)
        .order_by(Message.created_at.asc())
    )
    messages = msg_result.scalars().all()

    name = contact.first_name or contact.telegram_username or str(contact.telegram_id or contact.vk_id or contact.id)
    lines = [f"Переписка с {name}", "=" * 40, ""]
    for m in messages:
        ts = m.created_at.strftime("%d.%m.%Y %H:%M") if m.created_at else ""
        role_label = "Клиент" if m.role == "user" else "Бот"
        lines.append(f"[{ts}] {role_label}:")
        lines.append(m.content)
        lines.append("")

    output = "\n".join(lines)
    filename = f"chat_{contact_id}.txt"
    return StreamingResponse(
        io.BytesIO(output.encode("utf-8")),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _contact_response(c: Contact) -> ContactResponse:
    return ContactResponse(
        id=c.id,
        platform=c.platform,
        telegram_id=c.telegram_id,
        vk_id=c.vk_id,
        telegram_username=c.telegram_username,
        first_name=c.first_name,
        last_name=c.last_name,
        phone=c.phone,
        first_message_at=c.first_message_at,
        last_message_at=c.last_message_at,
        message_count=c.message_count,
    )
