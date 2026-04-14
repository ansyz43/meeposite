# Meepo iOS + Meta — Декомпозиция задач

> Связанные документы:
> - [SPEC.md](SPEC.md) — Техническое задание
> - [ARCHITECTURE.md](ARCHITECTURE.md) — Архитектурный план

---

## Этап 0: Подготовка проекта

### 0.1 Инициализация репозитория
- [ ] Создать новый репозиторий `meepo-ios`
- [ ] Настроить `.gitignore` (Swift, Xcode, Python, Node)
- [ ] Скопировать `spec/` из meeposite
- [ ] Настроить branch protection (main → PR only)

### 0.2 Серверная инфраструктура
- [ ] Арендовать западный VPS (US/EU)
- [ ] Настроить домен (новый, не meepo.su)
- [ ] SSL сертификат (Let's Encrypt / Cloudflare)
- [ ] Docker + Docker Compose на сервере
- [ ] CI/CD pipeline (GitHub Actions)

### 0.3 Внешние аккаунты
- [ ] Apple Developer Account ($99/year)
- [ ] Meta for Developers app (facebook.com/developers)
- [ ] Instagram Business Account для тестирования
- [ ] Facebook Page для тестирования
- [ ] OpenAI API key (новый или существующий)

---

## Этап 1: Preservation Audit

### 1.1 Backend audit
- [ ] Скопировать backend/ из meeposite
- [ ] Составить список файлов: KEEP / MODIFY / DELETE / NEW
- [ ] Пометить все Telegram/VK-специфичные участки кода маркерами `# LEGACY`
- [ ] Документировать все env vars: KEEP / REMOVE / NEW

### 1.2 Worker audit
- [ ] Скопировать из bot_worker/: `ai_service.py`, `rag.py`, `crypto.py`, `database.py`
- [ ] Проверить что ai_service.py не имеет Telegram-зависимостей
- [ ] Проверить что rag.py работает с любыми .txt файлами
- [ ] Составить список зависимостей worker: KEEP / REMOVE / NEW

### 1.3 Knowledge Base
- [ ] Перевести/создать knowledge base на английском языке
- [ ] Проверить что RAG корректно работает с EN текстами
- [ ] Обновить synonym table в rag.py для EN

---

## Этап 2: Data Model Migration

### 2.1 Alembic setup
- [ ] Инициализировать Alembic в backend/
- [ ] Настроить async PostgreSQL connection
- [ ] Создать initial migration (текущее состояние)

### 2.2 Schema evolution — channels
- [ ] Migration: добавить `meta_page_id`, `meta_ig_account_id`, `channel_name`, `webhook_status`, `access_token_encrypted`, `token_expires_at` в таблицу bots
- [ ] Migration: расширить `platform` enum ('instagram', 'facebook_messenger')
- [ ] Обновить `models.py`: модель Bot → Channel (alias или rename)
- [ ] Обновить `schemas.py`: новые Pydantic-схемы для channels

### 2.3 Schema evolution — contacts
- [ ] Migration: добавить `channel_user_id`, `channel_thread_id`, `channel_username`, `profile_pic_url`, `channel_source`
- [ ] Обновить модель Contact в models.py
- [ ] Обновить schemas.py для contacts

### 2.4 Schema evolution — users
- [ ] Migration: добавить `apple_id`, `locale`
- [ ] Обновить модель User
- [ ] Обновить schemas.py

### 2.5 New table — push_tokens
- [ ] Migration: создать таблицу `push_tokens`
- [ ] Модель PushToken в models.py
- [ ] Schema в schemas.py

### 2.6 Referral adaptation
- [ ] Migration: добавить `channel_user_id` в referral_sessions (рядом с legacy telegram_id)
- [ ] Обновить модель ReferralSession

---

## Этап 3: Meta Integration

### 3.1 Meta App setup
- [ ] Создать Meta App на developers.facebook.com
- [ ] Добавить Instagram Messaging product
- [ ] Добавить Messenger product
- [ ] Настроить OAuth redirect URLs
- [ ] Получить App ID + App Secret
- [ ] Настроить Webhook subscriptions (messages, messaging_postbacks)

### 3.2 Backend — Meta webhook endpoints
- [ ] Создать `backend/app/routers/meta_webhook.py`
- [ ] `GET /api/meta/webhook` — verification challenge (hub.verify_token)
- [ ] `POST /api/meta/webhook` — receive events
- [ ] HMAC-SHA256 signature verification (X-Hub-Signature-256)
- [ ] Event parsing: message, postback, referral
- [ ] Unit tests для webhook handler

### 3.3 Backend — Channel router
- [ ] Создать `backend/app/routers/channel.py`
- [ ] `POST /api/channel/instagram/connect` — OAuth code → token exchange
- [ ] `GET /api/channel/instagram` — get channel info
- [ ] `PUT /api/channel/instagram` — update settings
- [ ] `DELETE /api/channel/instagram` — disconnect
- [ ] `POST /api/channel/messenger/connect` — Page token flow
- [ ] `GET /api/channel/messenger` — get channel info
- [ ] `PUT /api/channel/messenger` — update settings
- [ ] `DELETE /api/channel/messenger` — disconnect
- [ ] `GET /api/channel/status` — all channels status
- [ ] Webhook subscription при connect
- [ ] Token encryption via Fernet
- [ ] Unit tests

### 3.4 Meta API client
- [ ] Создать `backend/app/services/meta_client.py`
- [ ] `exchange_code_for_token()` — OAuth code exchange
- [ ] `get_long_lived_token()` — short → long-lived token
- [ ] `get_ig_account_info()` — fetch Instagram account details
- [ ] `get_page_info()` — fetch Facebook Page details
- [ ] `subscribe_webhook()` — subscribe page to webhook events
- [ ] `send_message()` — Send API (text + attachments)
- [ ] `get_user_profile()` — fetch message sender info
- [ ] Rate limiting (200/hour for IG)
- [ ] Error handling + retry
- [ ] Unit tests

### 3.5 Meta Worker
- [ ] Создать `meta_worker/` directory structure
- [ ] `worker/main.py` — webhook event consumer + health check HTTP
- [ ] `worker/webhook_handler.py` — parse & route webhook events
- [ ] `worker/meta_api.py` — send messages via Meta API
- [ ] `worker/token_manager.py` — refresh long-lived tokens (cron)
- [ ] Скопировать `ai_service.py` из bot_worker (unchanged)
- [ ] Скопировать `rag.py` из bot_worker
- [ ] Скопировать `crypto.py`, `database.py`
- [ ] Адаптировать `models.py` под новые поля
- [ ] Адаптировать `config.py` (META_* вместо TELEGRAM_*)
- [ ] Message deduplication (reuse OrderedDict pattern)
- [ ] Contact find-or-create logic
- [ ] Referral session handling (ref_ in first message)
- [ ] Dockerfile
- [ ] requirements.txt
- [ ] Integration tests

### 3.6 Broadcast adaptation
- [ ] Модифицировать `backend/app/routers/broadcast.py`
- [ ] Добавить 24-hour window check перед отправкой
- [ ] Фильтрация eligible contacts (last_message_at < 24h)
- [ ] Возвращать клиенту: eligible_count vs total_count
- [ ] Policy rejection logging
- [ ] Meta Send API для broadcast (throttled)
- [ ] Unit tests

---

## Этап 4: Backend — Auth & Profile changes

### 4.1 Sign in with Apple
- [ ] Создать `backend/app/services/apple_auth.py`
- [ ] JWT verification (RS256, Apple JWKS endpoint)
- [ ] `POST /api/auth/apple` endpoint
- [ ] Find-or-create user by apple_id
- [ ] Auto-generate ref_code for new users
- [ ] Referral linking support
- [ ] Unit tests

### 4.2 Remove Telegram auth
- [ ] Удалить `POST /api/auth/telegram` endpoint
- [ ] Удалить Telegram HMAC verification code
- [ ] Удалить `TELEGRAM_BOT_TOKEN_LOGIN` from config
- [ ] Обновить auth middleware (if needed)

### 4.3 Account deletion
- [ ] `DELETE /api/auth/account` endpoint
- [ ] Cascade delete: user → channels → contacts → messages
- [ ] Revoke Meta tokens on deletion
- [ ] Confirmation flow (require password or re-auth)
- [ ] GDPR: export user data before deletion (optional)
- [ ] Unit tests

### 4.4 Push notifications
- [ ] `POST /api/push/register` — save device token
- [ ] `DELETE /api/push/register` — remove device token
- [ ] APNs send utility in backend
- [ ] Trigger push on new message received
- [ ] Unit tests

---

## Этап 5: iOS App

### 5.1 Project setup
- [ ] Создать Xcode project (SwiftUI, iOS 17+)
- [ ] Настроить targets (Debug, Release)
- [ ] Настроить signing & capabilities
- [ ] Добавить APNs capability
- [ ] Настроить API base URL (debug vs release)
- [ ] Создать theme: colors, fonts, spacing

### 5.2 Core — Networking
- [ ] `APIClient.swift` — URLSession wrapper
- [ ] Automatic JWT injection from Keychain
- [ ] Token refresh interceptor (401 → refresh → retry)
- [ ] `Endpoints.swift` — all API paths as static constants
- [ ] `Models.swift` — Codable structs for all API responses
- [ ] Error handling + user-facing error messages

### 5.3 Core — Auth
- [ ] `AuthManager.swift` — ObservableObject, token lifecycle
- [ ] `KeychainHelper.swift` — save/load/delete tokens
- [ ] `AppleSignIn.swift` — ASAuthorizationController delegate
- [ ] Auth state: `.loading` / `.unauthenticated` / `.authenticated`
- [ ] Auto-login on app launch (check Keychain)

### 5.4 Core — Push
- [ ] `PushManager.swift` — APNs registration
- [ ] Request notification permission
- [ ] Send device token to backend
- [ ] Handle incoming push (foreground + background)
- [ ] Deep link to conversation on push tap

### 5.5 Auth screens
- [ ] `LoginView.swift` — email/password + Apple + Google
- [ ] `RegisterView.swift` — email, name, password + ref_code
- [ ] `ResetPasswordView.swift` — email → code → new password
- [ ] Form validation
- [ ] Loading states + error display

### 5.6 Dashboard
- [ ] `DashboardView.swift` — stats overview
- [ ] Channel status cards
- [ ] Recent conversations preview
- [ ] Quick stats: contacts, messages, active sessions
- [ ] Pull-to-refresh

### 5.7 Channels
- [ ] `ChannelListView.swift` — list connected channels
- [ ] `InstagramConnectView.swift` — OAuth flow (ASWebAuthenticationSession)
- [ ] `MessengerConnectView.swift` — Page connection flow
- [ ] `ChannelSettingsView.swift` — name, greeting, seller_link, avatar
- [ ] Channel status indicator (active/pending/error)
- [ ] Disconnect flow with confirmation

### 5.8 Conversations
- [ ] `ConversationsView.swift` — list with last message preview
- [ ] `ChatDetailView.swift` — full message history
- [ ] Search/filter conversations
- [ ] Channel badge (IG/Messenger icon)
- [ ] Auto-refresh (polling 15s)
- [ ] Pull-to-refresh

### 5.9 Contacts
- [ ] `ContactsView.swift` — searchable list
- [ ] Contact card: name, channel, message count, last active
- [ ] `ContactDetailView.swift` — profile + conversation link
- [ ] Export (share sheet → CSV)

### 5.10 Broadcasts
- [ ] `BroadcastView.swift` — create + list history
- [ ] Compose: text + image
- [ ] Show eligible count vs total
- [ ] Policy warning for Meta
- [ ] Status tracking: pending/sending/completed

### 5.11 Referral
- [ ] `PartnerView.swift` — partner dashboard
- [ ] `CatalogView.swift` — browse available channels
- [ ] Referral link generation + share
- [ ] Credits display
- [ ] Cashback history

### 5.12 Profile
- [ ] `ProfileView.swift` — name, email, cashback balance
- [ ] `SettingsView.swift` — change password, notifications, delete account
- [ ] Edit name
- [ ] Change password (if not OAuth-only)
- [ ] Delete account with confirmation
- [ ] Logout

### 5.13 Tab navigation
- [ ] Bottom TabView: Home, Channels, Chats, Contacts, Profile
- [ ] Navigation stacks per tab
- [ ] Badge on Chats tab (unread count)

---

## Этап 6: QA + App Store

### 6.1 Testing
- [ ] Backend unit tests (pytest)
- [ ] Meta webhook integration tests
- [ ] iOS unit tests (XCTest)
- [ ] iOS UI tests
- [ ] End-to-end: send IG DM → AI reply → visible in app
- [ ] End-to-end: send Messenger msg → AI reply → visible in app
- [ ] Broadcast policy compliance test
- [ ] Referral flow end-to-end
- [ ] Token refresh flow
- [ ] Push notification flow

### 6.2 App Store preparation
- [ ] App icon (1024×1024 + all sizes)
- [ ] Screenshots (6.7", 6.1", iPad optional)
- [ ] App name, subtitle, description (English)
- [ ] Keywords
- [ ] Privacy Policy URL
- [ ] Terms of Service URL
- [ ] Support URL
- [ ] Demo account credentials for reviewer
- [ ] App Review notes (explain Meta integration)
- [ ] Age rating questionnaire
- [ ] App Privacy details (data collection disclosure)

### 6.3 Legal
- [ ] Privacy Policy (English, GDPR-compliant)
- [ ] Terms of Service
- [ ] Data Processing Agreement (if B2B)
- [ ] Cookie policy (web admin panel)
- [ ] Meta Platform Terms compliance check

### 6.4 Demo environment
- [ ] Create demo user account
- [ ] Connect demo Instagram account
- [ ] Connect demo Facebook Page
- [ ] Seed demo conversations (5-10)
- [ ] Seed demo contacts (20-30)
- [ ] Ensure AI responds during review window
- [ ] Document demo flow for reviewer

### 6.5 Deployment
- [ ] Production backend deploy
- [ ] Production meta_worker deploy
- [ ] Verify webhook connectivity
- [ ] Verify AI responses
- [ ] Submit to App Store
- [ ] Monitor review feedback
- [ ] Fix reviewer issues (if any)
- [ ] Release v1.0

---

## Зависимости между этапами

```
Этап 0 (Подготовка)
    │
    ├── Этап 1 (Audit) ─────── нужен до всего
    │       │
    │       ▼
    ├── Этап 2 (DB Migration) ─── нужен до Этапа 3 и 4
    │       │
    │       ├──────────────┐
    │       ▼              ▼
    ├── Этап 3          Этап 4
    │   (Meta)          (Auth)     ← можно параллельно
    │       │              │
    │       └──────┬───────┘
    │              ▼
    ├── Этап 5 (iOS App) ──── нужен backend ready
    │       │
    │       ▼
    └── Этап 6 (QA + Store)
```

**Параллелизация**: Этапы 3 (Meta) и 4 (Auth) можно делать одновременно. iOS (Этап 5) можно начинать с Auth screens параллельно с Этапом 3, используя mock API.

---

## Оценка объёма

| Этап | Задач | Примечание |
|------|-------|------------|
| 0. Подготовка | 8 | Инфра, аккаунты |
| 1. Audit | 9 | Анализ, маркировка |
| 2. DB Migration | 11 | Alembic + models |
| 3. Meta Integration | 30 | Самый большой блок |
| 4. Auth & Profile | 11 | Apple + cleanup |
| 5. iOS App | 34 | UI + networking |
| 6. QA + Store | 16 | Тесты + публикация |
| **Итого** | **119** | |
