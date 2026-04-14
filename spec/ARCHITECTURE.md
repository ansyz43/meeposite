# Meepo iOS + Meta — Архитектурный план

> Связанные документы:
> - [SPEC.md](SPEC.md) — Техническое задание
> - [TASKS.md](TASKS.md) — Декомпозиция задач

---

## 1. Архитектурная диаграмма

```
┌─────────────────────────────────────────────────────────────────┐
│                        КЛИЕНТ (iOS)                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐ │
│  │  Auth    │ │Dashboard │ │  Chats   │ │Contacts  │ │Profile│ │
│  │  Flow   │→│  Home    │→│  List    │→│  List    │→│  Tab  │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬───┘ │
│       │            │            │            │           │     │
│       └────────────┴────────────┴────────────┴───────────┘     │
│                              │ HTTPS                           │
│                         Keychain (JWT)                          │
│                         APNs Push                               │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                         NGINX                                    │
│              SSL termination + reverse proxy                     │
│         /api/* → backend:8000    /ws/* → backend:8000            │
└────────┬────────────────────────────────┬────────────────────────┘
         │                                │
         ▼                                ▼
┌─────────────────────┐    ┌───────────────────────────────────────┐
│   BACKEND (FastAPI)  │    │         META WORKER                   │
│                      │    │                                       │
│  ┌────────────────┐  │    │  ┌─────────────┐  ┌───────────────┐  │
│  │ Auth Router    │  │    │  │  Webhook    │  │  AI Service   │  │
│  │ (apple/google/ │  │    │  │  Receiver   │  │  (unchanged)  │  │
│  │  email)        │  │    │  └──────┬──────┘  └───────┬───────┘  │
│  ├────────────────┤  │    │         │                 │          │
│  │ Channel Router │  │    │  ┌──────▼──────┐  ┌───────▼───────┐  │
│  │ (IG/Messenger  │  │    │  │  Message   │  │  RAG Engine   │  │
│  │  connect/CRUD) │  │    │  │  Processor  │  │  (unchanged)  │  │
│  ├────────────────┤  │    │  └──────┬──────┘  └───────────────┘  │
│  │ Conversations  │  │    │         │                            │
│  │ Contacts       │  │    │  ┌──────▼──────┐                     │
│  │ Referral       │  │    │  │  Meta Send  │                     │
│  │ Broadcasts     │  │    │  │  API Client │                     │
│  │ Profile        │  │    │  └─────────────┘                     │
│  │ Admin          │  │    │                                       │
│  └────────────────┘  │    │  Circuit Breaker │ Retry │ Semaphore  │
│                      │    │  Token Refresh   │ Rate Limit         │
└──────────┬───────────┘    └──────────┬────────────────────────────┘
           │                           │
           ▼                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                     PostgreSQL 16                                │
│                                                                  │
│  users │ channels │ contacts │ messages │ broadcasts             │
│  referral_partners │ referral_sessions │ cashback_transactions   │
│  password_reset_tokens │ push_tokens                             │
└──────────────────────────────────────────────────────────────────┘
           │
           │
           ▼
┌──────────────────────┐     ┌──────────────────────┐
│    OpenAI API        │     │    Meta Graph API     │
│  (AI Gateway/direct) │     │  (IG + Messenger)     │
└──────────────────────┘     └──────────────────────┘
```

---

## 2. Принцип переноса: Preserve Core / Replace Edges

```
                    ┌─────────────────────────┐
                    │      PRESERVE (ядро)     │
                    │                         │
                    │  • Auth (JWT/bcrypt)     │
                    │  • AI pipeline          │
                    │  • RAG engine           │
                    │  • Conversations CRUD   │
                    │  • Contacts CRUD        │
                    │  • Referral system      │
                    │  • Cashback logic       │
                    │  • Broadcast entity     │
                    │  • Crypto (Fernet)      │
                    │  • Database layer       │
                    │  • Admin panel          │
                    │  • Health/logging       │
                    └─────────┬───────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │   REPLACE   │  │   REPLACE   │  │    REMOVE   │
     │   Client    │  │  Transport  │  │   Legacy    │
     │             │  │             │  │             │
     │ React SPA → │  │ TG/VK →    │  │ TG proxy    │
     │ iOS SwiftUI │  │ Meta APIs   │  │ TG login    │
     │             │  │             │  │ VK handler  │
     └─────────────┘  └─────────────┘  └─────────────┘
```

---

## 3. Компонентная архитектура

### 3.1 Backend — модульная структура

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, middleware, CORS
│   ├── config.py            # Settings (+ new META_*, APPLE_* vars)
│   ├── database.py          # async SQLAlchemy (unchanged)
│   ├── auth.py              # JWT + bcrypt (+ Apple token verify)
│   ├── models.py            # SQLAlchemy models (evolved schema)
│   ├── schemas.py           # Pydantic schemas (+ channel schemas)
│   │
│   ├── routers/
│   │   ├── auth.py          # MODIFIED: +apple, -telegram
│   │   ├── channel.py       # NEW: replaces bot.py
│   │   ├── conversations.py # UNCHANGED
│   │   ├── profile.py       # MINOR: +account deletion
│   │   ├── referral.py      # MINOR: channel_user_id
│   │   ├── broadcast.py     # MODIFIED: policy-aware
│   │   ├── admin.py         # MINOR CHANGES
│   │   └── meta_webhook.py  # NEW: webhook verify + receive
│   │
│   └── services/
│       ├── crypto.py        # UNCHANGED
│       ├── meta_client.py   # NEW: Meta Graph API client
│       └── apple_auth.py    # NEW: Apple ID token verify
```

### 3.2 Meta Worker

```
meta_worker/
├── worker/
│   ├── __init__.py
│   ├── main.py              # NEW: webhook consumer + health
│   ├── config.py            # ADAPTED from bot_worker
│   ├── database.py          # REUSED from bot_worker
│   ├── models.py            # ADAPTED: new channel fields
│   ├── crypto.py            # REUSED from bot_worker
│   ├── ai_service.py        # REUSED: 100% unchanged
│   ├── rag.py               # REUSED: new EN knowledge_base
│   ├── meta_api.py          # NEW: Instagram/Messenger send
│   ├── webhook_handler.py   # NEW: parse Meta webhook events
│   └── token_manager.py     # NEW: refresh Meta access tokens
├── knowledge_base/
│   └── *.txt                # EN content
├── Dockerfile
└── requirements.txt
```

### 3.3 iOS App

```
MeepoApp/
├── MeepoApp.swift           # @main, TabView
├── Info.plist
│
├── Core/
│   ├── API/
│   │   ├── APIClient.swift      # URLSession wrapper, JWT inject
│   │   ├── Endpoints.swift      # All API endpoint definitions
│   │   └── Models.swift         # Codable response models
│   ├── Auth/
│   │   ├── AuthManager.swift    # Token lifecycle, Keychain
│   │   ├── KeychainHelper.swift # Secure storage
│   │   └── AppleSignIn.swift    # ASAuthorizationController
│   └── Push/
│       └── PushManager.swift    # APNs registration + handling
│
├── Features/
│   ├── Auth/
│   │   ├── LoginView.swift
│   │   ├── RegisterView.swift
│   │   └── ResetPasswordView.swift
│   ├── Dashboard/
│   │   └── DashboardView.swift
│   ├── Channels/
│   │   ├── ChannelListView.swift
│   │   ├── InstagramConnectView.swift
│   │   ├── MessengerConnectView.swift
│   │   └── ChannelSettingsView.swift
│   ├── Chats/
│   │   ├── ConversationsView.swift
│   │   └── ChatDetailView.swift
│   ├── Contacts/
│   │   ├── ContactsView.swift
│   │   └── ContactDetailView.swift
│   ├── Broadcasts/
│   │   └── BroadcastView.swift
│   ├── Referral/
│   │   ├── PartnerView.swift
│   │   └── CatalogView.swift
│   └── Profile/
│       ├── ProfileView.swift
│       └── SettingsView.swift
│
├── Shared/
│   ├── Components/           # Reusable UI components
│   ├── Extensions/           # Swift extensions
│   └── Theme/                # Colors, fonts, styling
│
└── Resources/
    ├── Assets.xcassets
    └── Localizable.strings
```

---

## 4. Потоки данных

### 4.1 Входящее сообщение (Instagram/Messenger → AI → ответ)

```
User sends DM on Instagram
        │
        ▼
Meta Webhook → POST /api/meta/webhook
        │
        ▼
Verify X-Hub-Signature-256
        │
        ▼
Parse messaging event
        │
        ▼
Find channel by page_id/ig_account_id
        │
        ▼
Find or create contact (channel_user_id)
        │
        ▼
Save message (role='user')
        │
        ▼
AI pipeline (ai_service.py)
  ├── RAG: select relevant KB chunks
  ├── Build prompt (system + context + user msg)
  ├── Call OpenAI (circuit breaker + retry)
  └── Parse response
        │
        ▼
Replace {link} placeholders with seller_link
        │
        ▼
Save message (role='assistant')
        │
        ▼
Send via Meta Send API
        │
        ▼
Push notification → iOS app (APNs)
```

### 4.2 Подключение Instagram канала

```
iOS app → Open Instagram OAuth URL
        │
        ▼
User authorizes app on Instagram
        │
        ▼
Redirect with auth code
        │
        ▼
POST /api/channel/instagram/connect { code }
        │
        ▼
Backend exchanges code → access_token
        │
        ▼
Fetch IG account info (username, name, pic)
        │
        ▼
Subscribe webhook for messaging events
        │
        ▼
Save channel record (token encrypted via Fernet)
        │
        ▼
Return channel info to iOS
```

### 4.3 Auth Flow (Sign in with Apple)

```
iOS → ASAuthorizationController
        │
        ▼
User authenticates via Face ID / Apple ID
        │
        ▼
Receive identityToken (JWT) + authorizationCode
        │
        ▼
POST /api/auth/apple { identity_token, name }
        │
        ▼
Backend verifies JWT against Apple public keys
  ├── Check iss = accounts.apple.com
  ├── Check aud = app bundle ID
  └── Extract sub (Apple user ID)
        │
        ▼
Find or create user (by apple_id)
        │
        ▼
Issue access_token + refresh_token
        │
        ▼
Store in Keychain on iOS
```

---

## 5. Безопасность

### 5.1 Сохраняемые механизмы

| Механизм | Реализация | Статус |
|----------|------------|--------|
| Password hashing | bcrypt (passlib) | Unchanged |
| Token encryption | Fernet (AES-128-CBC) | Unchanged |
| JWT | HS256, 15min access / 7d refresh | Unchanged |
| CORS | Origin whitelist | Adapted |
| Request ID | Middleware + logging | Unchanged |

### 5.2 Новые механизмы

| Механизм | Реализация |
|----------|------------|
| Webhook signature | HMAC-SHA256 (X-Hub-Signature-256) |
| Apple JWT verify | RS256, Apple public keys JWKS |
| iOS token storage | Keychain Services |
| Certificate pinning | Optional, для Meta/Apple endpoints |
| Rate limiting | Per-user + per-channel limits |
| Account deletion | Hard delete with cascade |

### 5.3 Удаляемые механизмы

| Механизм | Причина |
|----------|---------|
| Telegram HMAC auth | Канал удаляется |
| Proxy secret | Не нужен для Meta |
| Bot token pool | Нет пула в Meta |

---

## 6. API контракт: iOS ↔ Backend

### 6.1 Аутентификация

Все запросы (кроме auth) содержат:
```
Authorization: Bearer <access_token>
```

Refresh через httpOnly cookie (web legacy) ИЛИ через body (iOS):
```
POST /api/auth/refresh
{ "refresh_token": "..." }
```

### 6.2 Формат ответов

```json
// Успех
{ "id": 1, "email": "user@example.com", ... }

// Ошибка
{ "detail": "Error message" }
// или
{ "detail": [{ "msg": "...", "loc": [...] }] }
```

### 6.3 Пагинация

```
GET /api/contacts?skip=0&limit=50&search=john
GET /api/conversations?skip=0&limit=50
```

---

## 7. Инфраструктура

### 7.1 Docker Compose — целевая конфигурация

```yaml
services:
  db:
    image: postgres:16-alpine
    # unchanged

  backend:
    build: ./backend
    # + new META_*, APPLE_* env vars
    # - TELEGRAM_*, PROXY_* env vars

  meta_worker:              # replaces bot_worker
    build: ./meta_worker
    env:
      - META_APP_SECRET
      - META_WEBHOOK_VERIFY_TOKEN
      - OPENAI_API_KEY
      - DATABASE_URL

  nginx:
    # + webhook endpoint routing
    # - frontend static (served by CDN or separate)

  # frontend container REMOVED (iOS is native)
  # bot_worker container REMOVED (replaced by meta_worker)
```

### 7.2 Хостинг

| Требование | Решение |
|------------|---------|
| Западный рынок | US/EU VPS (не RU) |
| SSL | Let's Encrypt / Cloudflare |
| Webhook uptime | 99.5%+ SLA |
| Domain | Новый домен (не meepo.su) |
| CDN | Cloudflare (optional) |

---

## 8. Миграционная стратегия БД

### Шаг 1: Добавление (non-breaking)
```sql
ALTER TABLE bots ADD COLUMN meta_page_id VARCHAR;
ALTER TABLE bots ADD COLUMN meta_ig_account_id VARCHAR;
ALTER TABLE bots ADD COLUMN channel_name VARCHAR;
ALTER TABLE bots ADD COLUMN webhook_status VARCHAR DEFAULT 'pending';
ALTER TABLE bots ADD COLUMN access_token_encrypted VARCHAR;
ALTER TABLE bots ADD COLUMN token_expires_at TIMESTAMP;

ALTER TABLE contacts ADD COLUMN channel_user_id VARCHAR;
ALTER TABLE contacts ADD COLUMN channel_thread_id VARCHAR;
ALTER TABLE contacts ADD COLUMN channel_username VARCHAR;
ALTER TABLE contacts ADD COLUMN profile_pic_url VARCHAR;
ALTER TABLE contacts ADD COLUMN channel_source VARCHAR;

ALTER TABLE users ADD COLUMN apple_id VARCHAR;
ALTER TABLE users ADD COLUMN locale VARCHAR DEFAULT 'en';

CREATE TABLE push_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    device_token VARCHAR NOT NULL,
    platform VARCHAR DEFAULT 'ios',
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Шаг 2: Код переключается на новые поля

### Шаг 3: Cleanup (отдельная миграция после стабилизации)
```sql
ALTER TABLE bots DROP COLUMN vk_group_id;
ALTER TABLE contacts DROP COLUMN telegram_id;
ALTER TABLE contacts DROP COLUMN vk_id;
ALTER TABLE contacts DROP COLUMN telegram_username;
ALTER TABLE users DROP COLUMN telegram_id;
-- platform enum: drop 'telegram', 'vk'; keep 'instagram', 'facebook_messenger'
```

---

## 9. Решения по ключевым вопросам

| Вопрос | Решение | Обоснование |
|--------|---------|-------------|
| Real-time обновления в iOS? | Polling (15s) + APNs push | WebSocket — overkill для MVP, polling проще |
| Где хранить iOS tokens? | Keychain Services | Apple best practice, encrypted at rest |
| Как refresh Meta tokens? | Background cron в meta_worker | Long-lived page tokens (60d), auto-refresh |
| Broadcast как адаптировать? | Window-check перед отправкой | Meta policy: только в 24h window |
| Нужен ли Sign in with Apple? | Да, обязательно | App Store requirement если есть сторонний OAuth |
| Admin panel — iOS или web? | Web (оставить) | Admin не нужен на мобиле, legacy web достаточно |
| Какой минимальный iOS? | iOS 17+ | SwiftUI features, market coverage ~90% |
