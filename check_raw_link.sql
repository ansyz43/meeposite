-- Messages with raw [ССЫЛКА] (not replaced)
SELECT c.bot_id, b.bot_username, m.created_at, LEFT(m.content, 200) as msg
FROM messages m
JOIN contacts c ON c.id = m.contact_id
JOIN bots b ON b.id = c.bot_id
WHERE m.content LIKE '%[ССЫЛКА]%'
ORDER BY m.created_at DESC LIMIT 20;
