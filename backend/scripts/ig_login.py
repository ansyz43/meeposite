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
from instagrapi.exceptions import (
    ChallengeRequired,
    SelectContactPointRecoveryForm,
    RecaptchaChallenge,
    FeedbackRequired,
    LoginRequired,
)

SESSION_PATH = Path("/app/ig_session.json")


def challenge_code_handler(username, choice):
    """Called by instagrapi when challenge needs a code."""
    print(f"\n⚠️  Instagram запросил код подтверждения (метод: {choice})")
    print("Проверьте SMS или email и введите 6-значный код:")
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

    # Try loading saved session first
    if SESSION_PATH.exists():
        try:
            cl.load_settings(SESSION_PATH)
            cl.login(username, password)
            cl.dump_settings(SESSION_PATH)
            print("✅ Вход по сохранённой сессии — ОК")
            return
        except ChallengeRequired:
            print("Сессия вызвала challenge, пробуем заново…")
            cl = Client()
            cl.delay_range = [2, 5]
            cl.challenge_code_handler = challenge_code_handler
        except Exception as e:
            print(f"Сессия невалидна ({e}), пробуем заново…")
            cl = Client()
            cl.delay_range = [2, 5]
            cl.challenge_code_handler = challenge_code_handler

    # Fresh login with manual challenge handling
    try:
        cl.login(username, password)
        cl.dump_settings(SESSION_PATH)
        print("✅ Успешный вход! Сессия сохранена.")
    except ChallengeRequired:
        print("\n⚠️  Instagram требует пройти проверку (challenge).")
        try:
            # Try to resolve challenge via instagrapi flow
            api_path = cl.last_json.get("challenge", {}).get("api_path")
            if api_path:
                print(f"Challenge API path: {api_path}")
                cl.challenge_resolve(cl.last_json)
                cl.dump_settings(SESSION_PATH)
                print("✅ Challenge пройден! Сессия сохранена.")
            else:
                print("❌ Не удалось определить тип challenge.")
                print(f"   last_json: {cl.last_json}")
                sys.exit(1)
        except Exception as e2:
            print(f"❌ Не удалось пройти challenge: {e2}")
            print(f"   last_json: {cl.last_json}")
            print("\nПопробуйте:")
            print("  1. Войти в Instagram через браузер и подтвердить вход")
            print("  2. Затем запустить этот скрипт снова")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Не удалось войти: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
