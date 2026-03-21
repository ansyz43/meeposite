# Meepo — AI-Powered SaaS Platform for FitLine Distributors

> Готовая SaaS-платформа, которая позволяет дистрибьюторам FitLine (PM-International) подключить персонального AI-консультанта в Telegram и ВКонтакте за 2 минуты. Бот ведёт клиента по 5-этапной воронке продаж, отвечает на вопросы о продукции, отправляет ссылку на заказ и поддерживает реферальную систему.

**Prod:** [meepo.su](https://meepo.su) &nbsp;|&nbsp; **Stack:** FastAPI · React 18 · PostgreSQL 16 · aiogram 3 · OpenAI GPT · Docker  
**Статус:** Production, 8 активных ботов (7 Telegram + 1 VK), 5 Docker-контейнеров

---

## Оглавление

- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Технологический стек](#технологический-стек)
- [API — 31 эндпоинт](#api--31-эндпоинт)
- [База данных — 10 таблиц](#база-данных--10-таблиц)
- [AI / Бот-система](#ai--бот-система)
- [Безопасность](#безопасность)
- [Фронтенд — 11 страниц](#фронтенд--11-страниц)
- [Инфраструктура](#инфраструктура)
- [Быстрый старт](#быстрый-старт)
- [Структура проекта](#структура-проекта)
- [Команды](#команды)
- [Переменные окружения](#переменные-окружения)

---

## Возможности

### Для дистрибьютора (пользователь платформы)
- **Telegram-бот за 2 минуты** — получает бота из пула, настраивает имя / описание / аватар / ссылку на заказ
- **ВКонтакте-бот** — подключение через токен сообщества, VK Long Poll API
- **AI-консультант** — GPT-5.4 с RAG-системой по базе знаний FitLine, 5-этапный фреймворк продаж
- **Диалоги и контакты** — история всех переговоров, фильтры по платформе (TG/VK), экспорт в CSV/TXT
- **Массовые рассылки** — отправка сообщений + изображений всем контактам бота
- **Реферальная система** — генерация партнёрских ссылок, кредиты, 12-часовые сессии, дерево рефералов, кэшбэк
- **Мульти-авторизация** — Email/пароль, Google OAuth, Telegram Login Widget

### Для платформы (техническая сторона)
- **Multi-tenant** — один процесс обслуживает 5000+ ботов одновременно
- **RAG-система** — сокращает промпт с 15K до 2-3K токенов, снижая стоимость API на 80%
- **Fallback LLM** — при сбое GPT-5.4 автоматически переключается на GPT-4o-mini
- **Circuit Breaker** — останавливает запросы к AI после 5 подряд ошибок, автосброс через 60 сек
- **Healthcheck** — Docker healthcheck для backend, bot_worker, DB
- **Мониторинг** — Sentry (ошибки), Telegram-алерты администратору, JSON-логи с request_id
- **Шифрование** — токены ботов зашифрованы Fernet (AES-128) в БД

---

## Архитектура

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│   Nginx     │────▶│   Frontend   │     │  Bot Worker   │
│  (SSL/TLS)  │     │  React SPA   │     │  aiogram 3    │
│  :80 :443   │     │  :3000       │     │  VK Long Poll │
└──────┬──────┘     └──────────────┘     └───────┬───────┘
       │                                         │
       ▼                                         ▼
┌──────────────┐                         ┌───────────────┐
│   Backend    │◀───────────────────────▶│  PostgreSQL   │
│  FastAPI     │         SQLAlchemy      │  16-alpine    │
│  :8000       │         asyncpg         │  :5432        │
└──────┬───────┘                         └───────────────┘
       │
       ▼
┌──────────────┐     ┌───────────────┐
│  OpenAI API  │     │  Cloudflare   │
│  GPT-5.4     │◀────│  AI Gateway   │
│  (fallback:  │     │               │
│  GPT-4o-mini)│     └───────────────┘
└──────────────┘
```

---

## Технологический стек

| Слой | Технологии |
|------|-----------|
| **Frontend** | React 18.3, Vite 5.4, Tailwind CSS 3.4, shadcn/ui, Lucide Icons, Axios |
| **Backend** | FastAPI 0.115, Gunicorn + Uvicorn (4 workers), Pydantic v2, SlowAPI |
| **Database** | PostgreSQL 16 Alpine, SQLAlchemy 2.0 (async), asyncpg, Alembic |
| **AI** | OpenAI GPT-5.4 (primary), GPT-4o-mini (fallback), Cloudflare AI Gateway |
| **Telegram** | aiogram 3.13 (Long Polling), поддержка Local Bot API Server |
| **VK** | VK Long Poll API v5.199, aiohttp |
| **Auth** | JWT (HS256), bcrypt, Google OAuth, Telegram Web Auth (HMAC-SHA256), Fernet |
| **Infra** | Docker Compose (5 сервисов), Nginx + Let's Encrypt, GitHub Actions CI |
| **Monitoring** | Sentry SDK, Telegram alerts, JSON structured logging |

---

## API — 31 эндпоинт

### Auth (`/api/auth`) — 8

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/register` | Регистрация (email + password + ref_code) |
| POST | `/login` | Вход по email/паролю → access_token + refresh cookie |
| POST | `/refresh` | Обновление access_token из httpOnly cookie |
| POST | `/reset-password` | Отправка 6-значного кода на email (SMTP) |
| POST | `/verify-code` | Проверка кода восстановления (15 мин) |
| POST | `/set-password` | Установка нового пароля по одноразовому токену |
| POST | `/telegram` | Telegram Login Widget (HMAC-SHA256 верификация) |
| POST | `/google` | Google OAuth (JWT валидация через googleapis) |

### Bot (`/api/bot`) — 9

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/claim` | Назначить свободного Telegram-бота из пула |
| GET | `/` | Получить конфигурацию Telegram-бота |
| PUT | `/` | Обновить настройки бота (имя, описание, ссылка) |
| POST | `/vk/connect` | Подключить VK-бота (group_id + token) |
| GET | `/vk` | Получить конфигурацию VK-бота |
| PUT | `/vk` | Обновить настройки VK-бота |
| POST | `/avatar` | Загрузить аватар (multipart, JPEG/PNG/WEBP, ≤5MB) |
| POST | `/broadcast` | Создать рассылку (текст + изображение) |
| GET | `/broadcasts` | Список рассылок (limit 50) |

### Contacts & Conversations (`/api`) — 5

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/contacts` | Список контактов (пагинация, поиск, фильтр по платформе) |
| GET | `/contacts/export` | Экспорт контактов в CSV |
| GET | `/conversations` | Список диалогов (только с сообщениями) |
| GET | `/conversations/{id}` | Полная история чата + данные контакта |
| GET | `/conversations/{id}/export` | Экспорт диалога в TXT |

### Profile (`/api/profile`) — 3

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Профиль пользователя + статистика рефералов |
| PUT | `/` | Обновить имя |
| PUT | `/password` | Сменить пароль (требует текущий) |

### Referral (`/api/referral`) — 6

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/catalog` | Каталог ботов, принимающих партнёров |
| POST | `/partner` | Стать партнёром бота |
| GET | `/partner` | Получить текущее партнёрство |
| PUT | `/partner` | Обновить seller_link |
| GET | `/sessions` | Активные реферальные сессии |
| GET | `/my-tree` | Дерево рефералов (для владельца бота) |

### Health — 1

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/health` | Проверка связи с БД |

---

## База данных — 10 таблиц

```
users (12 полей)
├── bots (14 полей)              UQ(user_id, platform)
│   ├── contacts (14 полей)      UQ(bot_id, telegram_id), UQ(bot_id, vk_id)
│   │   └── messages (5 полей)
│   ├── broadcasts (8 полей)
│   └── referral_partners (8 полей)  UQ(user_id, bot_id)
│       └── referral_sessions (7 полей)
├── password_reset_tokens (5 полей)
└── cashback_transactions (8 полей)
```

**Ключевые модели:**

| Таблица | Поля | Назначение |
|---------|------|-----------|
| `users` | id, email, password_hash, name, telegram_id, google_id, auth_provider, ref_code, referred_by_id, cashback_balance, is_active, created_at | Учётные записи, мульти-auth |
| `bots` | id, user_id, platform, bot_token_encrypted, bot_username, assistant_name, seller_link, greeting_message, bot_description, avatar_url, vk_group_id, allow_partners, is_active, created_at | Конфигурация ботов TG/VK |
| `contacts` | id, bot_id, platform, telegram_id, vk_id, telegram_username, first_name, last_name, phone, first_message_at, last_message_at, message_count, link_sent | Собранные контакты |
| `messages` | id, contact_id, role, content, created_at | Вся история переписки |
| `referral_partners` | id, user_id, bot_id, seller_link, ref_code, credits, is_active, created_at | Партнёрские связи |
| `referral_sessions` | id, partner_id, contact_id, telegram_id, started_at, expires_at, is_active | 12-часовые реферальные сессии |

---

## AI / Бот-система

### RAG (Retrieval Augmented Generation)
- База знаний FitLine: ~450 строк, 25+ продуктов, 10+ программ здоровья
- 55+ синонимов для расширения запросов (энергия→устал→бодрость→activize)
- Автоматический подбор 5 релевантных продуктов из каталога
- Фильтрация программ по тематике (суставы, зрение, иммунитет, красота, спорт, дети)
- Сжатие промпта: 15K → 2-3K токенов (-80% стоимости API)

### 5-этапный фреймворк продаж
1. **Установление контакта** — тёплое приветствие, вопрос о потребности
2. **Выявление потребности** — один точный вопрос
3. **Презентация через результат** — язык ощущений, социальное доказательство
4. **Работа с возражениями** — «дорого», «не верю в БАДы», «надо подумать»
5. **Закрытие сделки** — ссылка на заказ только по готовности клиента

### Отказоустойчивость
- **Primary:** GPT-5.4 через Cloudflare AI Gateway (кэширование, аналитика)
- **Fallback:** GPT-4o-mini напрямую через OpenAI API
- **Circuit Breaker:** 5 ошибок → блокировка на 60 сек → автосброс
- **Concurrency:** семафор на 30 параллельных AI-запросов
- **Retry:** 3 попытки с экспоненциальным backoff (2s, 4s)
- **Alerts:** Telegram-уведомление администратору при сбое

---

## Безопасность

| Категория | Реализация |
|-----------|-----------|
| **Аутентификация** | JWT access (15 мин) + refresh (7 дней, httpOnly, Secure), bcrypt 12 раундов |
| **OAuth** | Google (JWT validation), Telegram (HMAC-SHA256 + 5-мин TTL) |
| **Шифрование** | Fernet AES-128 для токенов ботов в БД, TLS 1.2+ на nginx |
| **Rate Limiting** | Auth: 3-10 req/min (slowapi), Nginx: 5-20 req/s (burst 10-40) |
| **XSS-защита** | Валидация seller_link (блок javascript:/data:/vbscript:), CSP заголовки |
| **CORS** | Конфигурируемые origins через env |
| **Заголовки** | HSTS, X-Frame-Options DENY, X-Content-Type-Options, Permissions-Policy |
| **Env-переменные** | Fail-fast: `${VAR:?error}` для критических (DB_PASSWORD, SECRET_KEY, OPENAI_API_KEY) |
| **Логирование** | JSON structured, request_id трассировка, без секретов в логах |
| **Мониторинг** | Sentry (10% trace), Telegram alerts (5-мин cooldown) |
| **БД** | FK constraints, CASCADE deletes, UNIQUE на email/ref_code/telegram_id |

---

## Фронтенд — 11 страниц

| Страница | Маршрут | Описание |
|----------|---------|----------|
| Landing | `/` | Маркетинговая страница с анимированными счётчиками, CTA |
| Login | `/login` | Вход: email/пароль + Google OAuth + Telegram Widget |
| Register | `/register` | Регистрация с отслеживанием ref_code из URL |
| Reset Password | `/reset-password` | 3 шага: email → код → новый пароль |
| Dashboard | `/dashboard` | Главная: статистика, прогресс настройки |
| Profile | `/dashboard/profile` | Редактирование имени, смена пароля |
| Bot | `/dashboard/bot` | Настройки бота (TG/VK вкладки), аватар, партнёры |
| Conversations | `/dashboard/conversations` | Список диалогов, просмотр сообщений, фильтр TG/VK |
| Contacts | `/dashboard/contacts` | Таблица контактов, поиск, экспорт CSV |
| Broadcast | `/dashboard/broadcast` | Создание рассылки, статус отправки |
| Partner | `/dashboard/partner` | Каталог ботов, партнёрская ссылка, дерево рефералов |

**Дизайн-система:** Liquid Glass / Glassmorphism, основной цвет Emerald (#10B981), VK синий (#3B82F6), тёмная тема, шрифт Geist Variable

---

## Инфраструктура

### Docker Compose — 5 сервисов

| Сервис | Образ | Порт | Назначение |
|--------|-------|------|-----------|
| `db` | postgres:16-alpine | 5432 | PostgreSQL, max_connections=200, shared_buffers=256MB |
| `backend` | Python 3.12 (custom) | 8000 | FastAPI + Gunicorn (4 Uvicorn workers), healthcheck |
| `bot_worker` | Python 3.12 (custom) | 8080 | Менеджер ботов TG/VK, healthcheck :8080/health |
| `frontend` | Node 18 (custom) | 3000 | React SPA (Vite build → serve) |
| `nginx` | nginx:alpine | 80, 443 | Reverse proxy, TLS, rate limiting, security headers |

### CI/CD
- **GitHub Actions** — автотесты + syntax check при push в main
- **Deploy:** `ssh → git pull → docker compose up -d --build`

### Сервер
- **OS:** Ubuntu 24.04 LTS
- **Хостинг:** TimeWeb VPS
- **Домен:** meepo.su
- **SSL:** Let's Encrypt (автообновление)

---

## Быстрый старт

### Docker (рекомендуемый)
```bash
git clone https://github.com/ansyz43/meeposite.git
cd meeposite
cp .env.example .env
# Отредактируйте .env — укажите DB_PASSWORD, SECRET_KEY, OPENAI_API_KEY
docker compose up --build
```

### Для локальной разработки

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Bot Worker:**
```bash
cd bot_worker
pip install -r requirements.txt
python -m worker.main
```

**Открыть:**
- Сайт: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

## Структура проекта

```
meepo/
├── .github/workflows/ci.yml    # GitHub Actions CI
├── docker-compose.yml           # 5 сервисов
├── Makefile                     # Команды разработки
├── .env.example                 # Шаблон переменных
│
├── backend/                     # FastAPI API сервер
│   ├── Dockerfile
│   ├── requirements.txt         # 22 зависимости
│   ├── app/
│   │   ├── main.py              # Точка входа, middleware, Sentry
│   │   ├── models.py            # 10 SQLAlchemy моделей
│   │   ├── schemas.py           # 18+ Pydantic-схем
│   │   ├── auth.py              # JWT, bcrypt, токены
│   │   ├── config.py            # Настройки (fail-fast validation)
│   │   ├── database.py          # asyncpg + SQLAlchemy async
│   │   ├── logging_config.py    # JSON logging + RequestID
│   │   ├── services/crypto.py   # Fernet шифрование
│   │   └── routers/
│   │       ├── auth.py          # 8 эндпоинтов авторизации
│   │       ├── bot.py           # 9 эндпоинтов управления ботами
│   │       ├── conversations.py # 5 эндпоинтов диалогов/контактов
│   │       ├── profile.py       # 3 эндпоинта профиля
│   │       ├── referral.py      # 6 эндпоинтов реферальной системы
│   │       └── broadcast.py     # Рассылки
│   ├── alembic/                 # Миграции БД
│   ├── tests/                   # pytest + aiosqlite
│   └── scripts/                 # Утилиты (seed_bots, migrate_oauth)
│
├── bot_worker/                  # Бот-менеджер
│   ├── Dockerfile
│   ├── requirements.txt         # 7 зависимостей
│   ├── knowledge_base/          # База знаний FitLine (read-only mount)
│   └── worker/
│       ├── main.py              # Multi-bot orchestrator
│       ├── ai_service.py        # OpenAI + fallback + circuit breaker
│       ├── rag.py               # RAG: синонимы, scoring, фильтры
│       ├── vk_handler.py        # VK Long Poll API
│       ├── models.py            # Read-only ORM модели
│       ├── crypto.py            # Fernet расшифровка токенов
│       ├── config.py            # Bot worker настройки
│       └── database.py          # asyncpg подключение
│
├── frontend/                    # React SPA
│   ├── Dockerfile
│   ├── package.json             # 13 зависимостей
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── App.jsx              # React Router (11 маршрутов)
│       ├── api.js               # Axios interceptor + token refresh
│       ├── pages/               # 11 страниц
│       ├── components/          # DashboardLayout + UI
│       └── hooks/useAuth.jsx    # Auth context provider
│
├── knowledge_base/              # Исходная база знаний
│   └── fitline.txt              # ~450 строк, 25+ продуктов
│
└── nginx/
    └── nginx.conf               # TLS, rate limiting, security headers
```

---

## Команды

```bash
make dev          # Локальный backend (uvicorn --reload)
make test         # Запуск pytest
make migrate      # Alembic upgrade head
make lint         # Проверка синтаксиса
make build        # Docker compose build
make up           # Docker compose up -d
make down         # Docker compose down
make logs         # Логи (tail -f)
make deploy       # Деплой на production (SSH)
```

---

## Переменные окружения

| Переменная | Обязательна | Описание |
|-----------|:-----------:|----------|
| `DB_PASSWORD` | ✅ | Пароль PostgreSQL |
| `SECRET_KEY` | ✅ | Ключ для JWT + Fernet шифрования |
| `OPENAI_API_KEY` | ✅ | Ключ OpenAI API |
| `CORS_ORIGINS` | — | Разрешённые origins (default: localhost:3000) |
| `OPENAI_BASE_URL` | — | URL прокси/gateway (Cloudflare AI Gateway) |
| `CF_AIG_TOKEN` | — | Токен авторизации Cloudflare AI Gateway |
| `GOOGLE_CLIENT_ID` | — | Google OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | — | Google OAuth Client Secret |
| `TELEGRAM_BOT_TOKEN_LOGIN` | — | Токен бота для Telegram Login Widget |
| `SENTRY_DSN` | — | DSN для Sentry error tracking |
| `ALERT_CHAT_ID` | — | Telegram chat_id для алертов |
| `ALERT_BOT_TOKEN` | — | Токен бота для отправки алертов |
| `VITE_API_URL` | — | URL бэкенда для фронтенда |
| `VITE_GOOGLE_CLIENT_ID` | — | Google Client ID для фронтенда |
| `VITE_TELEGRAM_BOT_NAME` | — | Username бота для Telegram Widget |

---

## Статистика проекта

| Метрика | Значение |
|---------|---------|
| API эндпоинтов | 31 |
| Страниц фронтенда | 11 |
| Таблиц БД | 10 |
| Pydantic-схем | 18+ |
| Зависимостей backend | 22 |
| Зависимостей frontend | 13 |
| Docker-сервисов | 5 |
| Мер безопасности | 15+ |
| Max ботов на процесс | 5000+ |
| Max AI-запросов/сек | 30 |
