SELECT c.bot_id, b.bot_username, c.link_sent, m.role, LEFT(m.content, 120) as msg
FROM messages m
JOIN contacts c ON c.id = m.contact_id
JOIN bots b ON b.id = c.bot_id
WHERE m.content LIKE '%pm-quickstart%' OR m.content LIKE '%pmebusiness%'
ORDER BY m.created_at DESC LIMIT 20;
