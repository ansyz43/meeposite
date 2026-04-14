SELECT m.content FROM messages m WHERE m.role='assistant' AND m.content ILIKE '%оптимальн%' ORDER BY m.created_at DESC LIMIT 20;
