from app.services.crypto import decrypt_token
import sqlalchemy
from sqlalchemy import text
engine = sqlalchemy.create_engine("postgresql://meepo:changeme@db:5432/meepo")
with engine.connect() as conn:
    rows = conn.execute(text("SELECT id, bot_username, bot_token_encrypted FROM bots WHERE platform='telegram' ORDER BY id"))
    for r in rows:
        try:
            token = decrypt_token(r[2])
            bot_id = token.split(":")[0]
            print(r[0], r[1], bot_id)
        except Exception as e:
            print(r[0], r[1], "ERR")
