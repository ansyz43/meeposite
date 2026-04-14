SELECT m.role, LEFT(m.content, 300) as msg
FROM messages m
WHERE m.contact_id = 36
ORDER BY m.created_at
LIMIT 30;
