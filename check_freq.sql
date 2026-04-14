SELECT m.contact_id,
       COUNT(*) FILTER (WHERE m.role='assistant' AND m.content ILIKE '%оптимальн%') as optimal_mentions,
       COUNT(*) FILTER (WHERE m.role='assistant') as total_bot_msgs,
       COUNT(*) as total_msgs,
       ROUND(100.0 * COUNT(*) FILTER (WHERE m.role='assistant' AND m.content ILIKE '%оптимальн%') / NULLIF(COUNT(*) FILTER (WHERE m.role='assistant'), 0)) as pct
FROM messages m
GROUP BY m.contact_id
HAVING COUNT(*) FILTER (WHERE m.role='assistant' AND m.content ILIKE '%оптимальн%') > 0
ORDER BY pct DESC
LIMIT 20;
