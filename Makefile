.PHONY: dev test migrate lint build deploy

# ─── Local development ───
dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ─── Tests ───
test:
	cd backend && python -m pytest tests/ -v --tb=short

# ─── Database ───
migrate:
	cd backend && alembic upgrade head

migration:  # usage: make migration MSG="add column foo"
	cd backend && alembic revision --autogenerate -m "$(MSG)"

# ─── Lint ───
lint:
	cd backend && python -m py_compile app/main.py
	cd bot_worker && python -m py_compile worker/main.py

# ─── Docker ───
build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

# ─── Deploy to production ───
deploy:
	ssh root@5.42.112.91 "cd /root/meeposite && git pull origin main && docker compose up -d --build"
