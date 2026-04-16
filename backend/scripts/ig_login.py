#!/usr/bin/env python3
"""Interactive Instagram login — run inside the backend container.

Usage:
    docker compose exec -it backend python scripts/ig_login.py

Handles Instagram challenge (SMS / email verification code).
Saves session to /app/ig_session.json so the parser can reuse it.
"""
import os
import sys

sys.path.insert(0, "/app")

from pathlib import Path
from instagrapi import Client

SESSION_PATH = Path("/app/ig_session.json")


def challenge_code_handler(username, choice):
    method = "SMS" if choice == 1 else "email"
    print(f"\n⚠️  Instagram запросил подтверждение через {method}.")
    print("Введите 6-значный код:")
    code = input("> ").strip()
    return code


def main():
    username = os.environ.get("INSTAGRAM_USERNAME", "")
    password = os.environ.get("INSTAGRAM_PASSWORD", "")

    if not username or not password:
        print("ERROR: INSTAGRAM_USERNAME / INSTAGRAM_PASSWORD env vars not set")
        sys.exit(1)

    print(f"Авторизация @{username} ...")

    cl = Client()
    cl.delay_range = [2, 5]
    cl.challenge_code_handler = challenge_code_handler

    if SESSION_PATH.exists():
        try:
            cl.load_settings(SESSION_PATH)
            cl.login(username, password)
            cl.dump_settings(SESSION_PATH)
            print("✅ Вход по сохранённой сессии — ОК")
            return
        except Exception as e:
            print(f"Сессия невалидна ({e}), пробуем заново…")

    try:
        cl.login(username, password)
        cl.dump_settings(SESSION_PATH)
        print("✅ Успешный вход! Сессия сохранена.")
    except Exception as e:
        print(f"❌ Не удалось войти: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
