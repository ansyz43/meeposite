-- Check if AI ever generated [ССЫЛКА] for bot 17
SELECT c.bot_id, m.role, m.created_at, LEFT(m.content, 200) as msg
FROM messages m
JOIN contacts c ON c.id = m.contact_id
WHERE c.bot_id = 17 AND m.role = 'assistant'
ORDER BY m.created_at DESC LIMIT 30;
