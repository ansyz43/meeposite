# Meepo — SaaS-платформа для дистрибьюторов FitLine

## Быстрый старт

### 1. Клонирование и настройка
```bash
cd meepo
cp .env.example .env
# Отредактируйте .env — укажите OPENAI_API_KEY и SECRET_KEY
```

### 2. Запуск через Docker
```bash
docker compose up --build
```

### 3. Открыть в браузере
- Сайт: http://localhost
- API: http://localhost:8000/docs

### Для разработки без Docker

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

## Структура
```
meepo/
├── backend/           # FastAPI — API сервер
│   └── app/
│       ├── main.py          # Точка входа
│       ├── models.py        # Модели БД
│       ├── schemas.py       # Pydantic-схемы
│       ├── auth.py          # JWT аутентификация
│       ├── config.py        # Настройки
│       ├── database.py      # Подключение к БД
│       ├── services/
│       │   └── crypto.py    # Шифрование токенов
│       └── routers/
│           ├── auth.py      # /api/auth/*
│           ├── profile.py   # /api/profile/*
│           ├── bot.py       # /api/bot/*
│           └── conversations.py  # /api/conversations/*, /api/contacts/*
├── bot_worker/        # Telegram-боты (aiogram)
│   └── worker/
│       ├── main.py          # Менеджер всех ботов
│       ├── ai_service.py    # OpenAI интеграция
│       ├── models.py        # Модели (read-only)
│       ├── crypto.py        # Расшифровка токенов
│       ├── config.py        # Настройки
│       └── database.py      # Подключение к БД
├── frontend/          # React + Tailwind
│   └── src/
│       ├── App.jsx          # Роутинг
│       ├── api.js           # Axios с авторизацией
│       ├── pages/           # Страницы
│       ├── components/      # UI компоненты
│       └── hooks/           # useAuth
├── knowledge_base/    # База знаний FitLine
├── nginx/             # Reverse proxy
├── docker-compose.yml
└── .env.example
```
