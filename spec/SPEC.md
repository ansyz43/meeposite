# Meepo iOS + Meta Channels — Техническое задание

> **Проект**: Meepo iOS + Meta Channels Migration
> **Подход**: preserve core / replace edges
> **Репозиторий-источник**: `github.com/ansyz43/meeposite.git`
> **Дата**: 2026-03-22

---

## 1. Что есть сейчас

Meepo — SaaS-платформа для автоматизации продаж через мессенджеры с AI-ответами:

| Компонент | Стек | Описание |
|-----------|------|----------|
| **backend** | FastAPI, Python 3.11, Gunicorn | API-сервер, бизнес-логика |
| **frontend** | React 18, Vite 5.4, Tailwind CSS 3.4 | Веб-кабинет пользователя |
| **bot_worker** | Python, aiogram 3, aiohttp | Telegram/VK обработка сообщений + AI |
| **database** | PostgreSQL 16 | Все данные |
| **nginx** | Reverse proxy + static | Проксирование + раздача фронта |
| **deploy** | Docker Compose (5 контейнеров) | Оркестрация |

### 1.1 База данных — 10 таблиц

| Таблица | Полей | Ключевые поля |
|---------|-------|---------------|
| **users** | 14 | id, email, password_hash, name, telegram_id, google_id, auth_provider, ref_code, referred_by_id, cashback_balance, is_active, is_admin, created_at |
| **bots** | 14 | id, user_id, platform (`telegram`/`vk`), bot_token_encrypted, bot_username, assistant_name, seller_link, greeting_message, bot_description, avatar_url, vk_group_id, allow_partners, is_active, created_at |
| **contacts** | 12 | id, bot_id, platform, telegram_id, vk_id, telegram_username, first_name, last_name, phone, first_message_at, last_message_at, message_count, link_sent |
| **messages** | 5 | id, contact_id, role (`user`/`assistant`), content, created_at |
| **broadcasts** | 9 | id, bot_id, message_text, image_url, total_contacts, sent_count, failed_count, status, created_at |
| **referral_partners** | 8 | id, user_id, bot_id, seller_link, ref_code, credits, is_active, created_at |
| **referral_sessions** | 8 | id, partner_id, contact_id, telegram_id, started_at, expires_at, is_active |
| **cashback_transactions** | 8 | id, user_id, from_user_id, amount, source_amount, level, source_type, created_at |
| **password_reset_tokens** | 5 | id, user_id, token, expires_at, used |

### 1.2 API — 42 эндпоинта (реальный аудит)

| Группа | Кол-во | Эндпоинты |
|--------|--------|-----------|
| **Auth** | 9 | register, login, refresh, reset-password, verify-code, set-password, logout, telegram, google |
| **Profile** | 3 | get, update name, change password |
| **Bot (TG)** | 7 | claim, get, update, avatar upload, delete, status, broadcast create |
| **Bot (VK)** | 4 | connect, get, update, delete |
| **Broadcasts** | 2 | create, list |
| **Conversations** | 5 | list contacts, export contacts CSV, list conversations, get history, export TXT |
| **Referral** | 8 | catalog, become partner, get partner, update partner, sessions, add credits, my-partners, my-tree, my-cashback |
| **Admin** | 5 | stats, list users, get user, delete user, toggle user, list bots, delete bot |
| **System** | 1 | health check |

### 1.3 Фронтенд — 13 страниц

Landing, Login, Register, ResetPassword, Dashboard, BotPage, Conversations, Contacts, BroadcastPage, CatalogPage, PartnerPage, Profile, AdminPage

### 1.4 Auth — 3 метода

| Метод | Реализация |
|-------|------------|
| Email/Password | bcrypt, JWT HS256 (access 15m / refresh 7d httpOnly cookie) |
| Google OAuth | ID token verification через googleapis.com |
| Telegram Login | HMAC-SHA256 проверка виджета |

### 1.5 AI-слой

| Функция | Реализация |
|---------|------------|
| Основная модель | gpt-4.1-mini через Cloudflare AI Gateway |
| Fallback | gpt-4o-mini напрямую через OpenAI |
| RAG | Поиск по knowledge_base/*.txt с расширением синонимов |
| Circuit Breaker | Открытие после 5 ошибок, авто-сброс через 60с |
| Retry | 3 попытки, backoff 2с → 4с |
| Timeout | 60с asyncio.wait_for |
| Параллельность | asyncio.Semaphore(30) |
| Кеширование | Developer-role static prompt (OpenAI prompt caching) |

### 1.6 Шифрование

- Токены ботов: Fernet (AES-128-CBC), ключ через SHA-256(SECRET_KEY)
- Пароли: bcrypt через passlib
- JWT: HS256

---

## 2. Цель проекта

Перенести Meepo в iOS-приложение для Apple на английском языке для западного рынка, заменив:

- **Клиент**: React web → native iOS (SwiftUI)
- **Каналы**: Telegram/VK → Instagram Direct + Facebook Messenger
- **Транспорт**: aiogram/VK long-poll → Meta Webhooks
- **Прокси**: Telegram API proxy → убрать (не нужен для Meta)

Сохранив:

- Backend FastAPI (ядро)
- PostgreSQL + схема данных
- AI/RAG/LLM pipeline
- Реферальная система
- Contacts/Messages/Conversations
- Broadcasts (адаптированные под Meta policy)
- Auth модель
- Docker deploy модель

---

## 3. Что сохраняется без изменений

- `backend/app/auth.py` — JWT/bcrypt логика
- `backend/app/database.py` — async SQLAlchemy
- `backend/app/routers/profile.py` — профиль
- `backend/app/routers/conversations.py` — диалоги, контакты, экспорт
- `backend/app/routers/referral.py` — реферальная система
- `backend/app/routers/broadcast.py` — рассылки (+ адаптация)
- `backend/app/services/crypto.py` — Fernet шифрование
- `bot_worker/worker/ai_service.py` — AI pipeline
- `bot_worker/worker/rag.py` — RAG (новая knowledge base на EN)
- `nginx/nginx.conf` — проксирование (адаптация)
- `docker-compose.yml` — оркестрация (адаптация)

---

## 4. Что заменяется

| Текущее | Новое | Детали |
|---------|-------|--------|
| `frontend/` (React SPA) | `ios/` (SwiftUI app) | Полная замена клиента |
| `bot_worker/worker/main.py` (aiogram + VK) | `meta_worker/` | Meta Webhooks processor |
| `backend/app/routers/bot.py` (claim/vk/connect) | `backend/app/routers/channel.py` | Instagram/Messenger connect |
| `backend/app/routers/auth.py` (Telegram Login) | Sign in with Apple + Google | Удалить Telegram auth |
| Telegram/VK идентификаторы в contacts | Meta channel_user_id / PSID | Новые поля |
| `TELEGRAM_API_URL`, `PROXY_SECRET` | Удалить | Не нужно для Meta |
| `TELEGRAM_BOT_TOKEN_LOGIN` | Удалить | Apple/Google auth |
| `ALERT_CHAT_ID`, `ALERT_BOT_TOKEN` | Email/Slack alerts | Замена TG-алертов |

---

## 5. Критические внешние ограничения

### 5.1 Instagram Messaging API

- Требуется Instagram Professional/Business account
- Conversation стартует ТОЛЬКО после user-initiated message
- Permission: `instagram_business_manage_messages`
- Нет групповых чатов — только 1:1
- Сообщения старше 30 дней в Requests могут не возвращаться
- Для обслуживания чужих аккаунтов — нужен Advanced Access Level + App Review

### 5.2 Facebook Messenger

- Требуется Page access token с правами на Page
- Send API для отправки
- **24-hour window**: ответ возможен в течение 24ч после последнего сообщения пользователя
- Вне окна — только допустимые Human Agent / Confirmed Event tags
- Промо-рассылки через Messenger невозможны в том же виде, что в Telegram

### 5.3 Apple App Store

- Backend должен быть live во время review
- Demo account обязателен для ревьюера
- Sign in with Apple обязателен, если есть сторонний OAuth
- Удаление аккаунта из приложения обязательно
- Privacy policy + Terms of Service обязательны
- ATT (App Tracking Transparency) если есть трекинг

### 5.4 Ключевой принцип

> Проект реализуется **исключительно** через официальные Meta APIs для business/professional account workflows. Никаких серых схем с личными аккаунтами.

---

## 6. Изменения в БД

### 6.1 Таблица `bots` → переименовать в `channels`

Добавить поля:
```
meta_page_id          VARCHAR     — Facebook Page ID
meta_ig_account_id    VARCHAR     — Instagram Business Account ID
meta_business_id      VARCHAR     — Meta Business Suite ID
channel_name          VARCHAR     — Display name канала
webhook_verify_token  VARCHAR     — Токен верификации webhook
webhook_status        VARCHAR     — active/pending/error
access_token_encrypted VARCHAR   — Page/IG access token (Fernet)
token_expires_at      TIMESTAMP   — Время истечения токена
```

Изменить `platform` enum: `instagram`, `facebook_messenger`

Оставить legacy: `bot_token_encrypted`, `bot_username`, `vk_group_id` как nullable до полной миграции.

### 6.2 Таблица `contacts`

Добавить поля:
```
channel_user_id       VARCHAR     — Instagram Scoped ID / Messenger PSID
channel_thread_id     VARCHAR     — Conversation thread ID
channel_username      VARCHAR     — Instagram handle
profile_pic_url       VARCHAR     — Avatar URL
channel_source        VARCHAR     — instagram / messenger
```

Оставить legacy: `telegram_id`, `vk_id`, `telegram_username` как nullable.

### 6.3 Таблица `referral_sessions`

Заменить `telegram_id` на `channel_user_id` (generic).

### 6.4 Таблица `users`

Добавить:
```
apple_id              VARCHAR     — Sign in with Apple subject
locale                VARCHAR     — en / ru
timezone              VARCHAR     — User timezone
```

Оставить legacy: `telegram_id`, `google_id`.

### 6.5 Принцип миграции

**Эволюционная миграция** через Alembic:
1. Добавить новые nullable поля
2. Переключить код на новые поля
3. Старые поля удалить после стабилизации (отдельная миграция)

---

## 7. Изменения в Backend API

### 7.1 Удаляются (deprecated)

```
POST /api/bot/claim              → нет пула ботов в Meta
POST /api/bot/vk/connect         → VK убирается
GET  /api/bot/vk                 → VK убирается
PUT  /api/bot/vk                 → VK убирается
DELETE /api/bot/vk               → VK убирается
POST /api/auth/telegram          → Telegram Login убирается
```

### 7.2 Добавляются

```
# Каналы
POST   /api/channel/instagram/connect     — OAuth → получить IG access token
GET    /api/channel/instagram             — Текущий Instagram канал
PUT    /api/channel/instagram             — Обновить настройки
DELETE /api/channel/instagram             — Отключить

POST   /api/channel/messenger/connect     — OAuth → получить Page token
GET    /api/channel/messenger             — Текущий Messenger канал  
PUT    /api/channel/messenger             — Обновить настройки
DELETE /api/channel/messenger             — Отключить

GET    /api/channel/status                — Статус всех каналов

# Meta Webhooks
POST   /api/meta/webhook                  — Приём webhook events
GET    /api/meta/webhook                  — Verification challenge

# Auth
POST   /api/auth/apple                    — Sign in with Apple
DELETE /api/auth/account                  — Удаление аккаунта (App Store requirement)
```

### 7.3 Сохраняются с минимальными изменениями

- `/api/auth/register`, `/api/auth/login`, `/api/auth/refresh`, `/api/auth/logout`
- `/api/auth/google` (сохранить, обновить client_id)
- `/api/auth/reset-password`, `/api/auth/verify-code`, `/api/auth/set-password`
- `/api/profile/*`
- `/api/contacts`, `/api/contacts/export`
- `/api/conversations`, `/api/conversations/{id}`, `/api/conversations/{id}/export`
- `/api/referral/*` (все 8 эндпоинтов)
- `/api/bot/broadcast`, `/api/bot/broadcasts` → перенести на `/api/channel/broadcast`
- `/api/admin/*` (все 5+ эндпоинтов)
- `/api/health`

---

## 8. Meta Worker

Новый `meta_worker/` заменяет `bot_worker/`:

### 8.1 Обязанности

1. Принимать webhook events от Meta (Messaging API)
2. Валидировать X-Hub-Signature-256
3. Парсить входящие сообщения (text, attachments)
4. Находить/создавать channel + contact
5. Сохранять сообщение в `messages`
6. Вызывать текущий AI pipeline (`ai_service.py` — без изменений)
7. Отправлять ответ через Meta Send API
8. Обрабатывать delivery/read receipts
9. Refresh access tokens по расписанию
10. Rate limiting (Instagram: 200 msgs/hour per account)

### 8.2 Сохраняемая логика из bot_worker

- `ai_service.py` — полностью
- `rag.py` — полностью (новая EN knowledge base)
- `crypto.py` — полностью
- `database.py` — полностью
- `models.py` — адаптировать под новые поля
- Deduplication pattern (OrderedDict LRU)
- Circuit breaker
- Semaphore concurrency limit
- Health check HTTP server

---

## 9. iOS-приложение

### 9.1 Стек

| Технология | Назначение |
|------------|------------|
| Swift 5.9+ / SwiftUI | UI framework |
| async/await | Networking |
| URLSession | HTTP client |
| Keychain Services | Secure token storage |
| APNs | Push notifications |
| WebSocket (опционально) | Real-time updates |

### 9.2 Экраны

| # | Экран | Аналог в web | Tab |
|---|-------|-------------|-----|
| 1 | Splash + Auth Gate | — | — |
| 2 | Login | Login.jsx | — |
| 3 | Register | Register.jsx | — |
| 4 | Reset Password | ResetPassword.jsx | — |
| 5 | Dashboard | Dashboard.jsx | Home |
| 6 | Instagram Connect | BotPage.jsx (claim) | Channels |
| 7 | Messenger Connect | BotPage.jsx (vk) | Channels |
| 8 | Channel Settings | BotPage.jsx (settings) | Channels |
| 9 | Conversations | Conversations.jsx | Chats |
| 10 | Chat Detail | Conversations.jsx (detail) | Chats |
| 11 | Contacts | Contacts.jsx | Contacts |
| 12 | Broadcasts | BroadcastPage.jsx | Home |
| 13 | Catalog | CatalogPage.jsx | Explore |
| 14 | Partner | PartnerPage.jsx | Partner |
| 15 | Profile | Profile.jsx | Profile |
| 16 | Settings | — | Profile |

### 9.3 Навигация

```
TabBar:
  ├── Home (Dashboard, Broadcasts)
  ├── Channels (Instagram, Messenger, Settings)
  ├── Chats (Conversations → Chat Detail)
  ├── Contacts (List, Search, Export)
  └── Profile (Settings, Partner, Catalog)
```

### 9.4 UX-принцип

Не менять бизнес-логику, только UX-подачу. Те же сценарии, упакованные в iOS:
- Bottom tab bar
- Navigation stacks
- Pull-to-refresh
- Push notifications по новым сообщениям
- Swipe actions (archive, delete)
- Sheet modals для быстрых действий

---

## 10. Broadcast адаптация под Meta Policy

### 10.1 Типы сообщений

| Тип | Instagram | Messenger | Ограничения |
|-----|-----------|-----------|-------------|
| Ответ в диалоге | ✅ | ✅ 24h window | Основной режим работы |
| Сервисное уведомление | ❌ | ✅ Human Agent tag | Только для поддержки |
| Промо-рассылка | ❌ | ⚠️ Ограничено | Требует recurring notification opt-in |

### 10.2 Реализация

- Broadcast сущность сохраняется
- Перед отправкой проверять: последнее сообщение от user < 24ч
- Фильтровать eligible contacts
- Показывать пользователю: "X из Y контактов доступны для рассылки"
- Логировать policy-rejections

---

## 11. Реферальная система — адаптация

Сохранить:
- Партнёрскую привязку, credits, sessions, tree, cashback

Адаптировать:
- Referral deeplink: `https://ig.me/m/<page>?ref=REF_CODE` (Messenger) или IG bio link
- Связывание лида с партнёром через `ref_` параметр в first message payload
- Entry point tracking через Meta referral webhook field

---

## 12. Локализация

- Весь UI на английском языке
- Knowledge base на английском
- API error messages на английском
- Backend допускает `locale` field для будущей мультиязычности

---

## 13. Новые ENV-переменные

```
# Meta
META_APP_ID=
META_APP_SECRET=
META_WEBHOOK_VERIFY_TOKEN=
META_API_VERSION=v21.0

# Apple
APPLE_CLIENT_ID=
APPLE_TEAM_ID=
APPLE_KEY_ID=
APPLE_PRIVATE_KEY=

# Push
APNS_KEY_ID=
APNS_TEAM_ID=
APNS_AUTH_KEY_PATH=

# Alerts (замена Telegram alerts)
ALERT_EMAIL=
ALERT_SLACK_WEBHOOK=
```

Удаляются:
```
TELEGRAM_API_URL
TELEGRAM_BOT_TOKEN_LOGIN
ALERT_CHAT_ID
ALERT_BOT_TOKEN
PROXY_SECRET
```

---

## 14. Нефункциональные требования

- Production HTTPS с валидным SSL
- Webhook uptime > 99.5%
- Sentry + structured logging + request_id
- Secure token storage (Keychain на iOS, Fernet на backend)
- Background push notifications
- Demo account для Apple Review
- Account deletion in-app (App Store requirement)
- Privacy Policy + Terms of Service на EN
- GDPR compliance (data export, deletion)
- Rate limiting на API endpoints

---

## 15. Критерии приёмки

Проект считается завершённым, когда:

1. ✅ Пользователь может зарегистрироваться и войти в iOS app (email + Apple + Google)
2. ✅ Пользователь может подключить Instagram Business Account
3. ✅ Пользователь может подключить Facebook Messenger Page
4. ✅ Входящие DM из Instagram попадают в систему через webhook
5. ✅ Входящие сообщения из Messenger попадают в систему через webhook
6. ✅ AI отвечает через сохранённый pipeline (RAG + fallback + circuit breaker)
7. ✅ Диалоги и контакты отображаются в iOS app
8. ✅ Реферальная система работает с Meta entry points
9. ✅ Broadcast работает в рамках Meta messaging policy
10. ✅ Backend reused core > 70% кодовой базы
11. ✅ Telegram/VK-specific код удалён из прод-конфигурации
12. ✅ App Store review пройден
13. ✅ Push notifications по новым сообщениям работают

---

## 16. Этапы реализации

| Этап | Название | Описание |
|------|----------|----------|
| **0** | Spec & Architecture | Финализация ТЗ, архитектурный план, декомпозиция задач |
| **1** | Preservation Audit | Фиксация reused-модулей, карта legacy-кода |
| **2** | Data Model Migration | Alembic миграции, новые поля, dual-mode |
| **3** | Meta Integration | Instagram + Messenger connect, webhooks, send/receive |
| **4** | iOS App | Auth → Dashboard → Channels → Chats → Contacts → Profile |
| **5** | Broadcast Adaptation | Policy-aware sending, window checks, eligible filtering |
| **6** | QA + App Store | Demo tenant, review notes, test accounts, legal texts |
