UPDATE articles a
SET source_name = fs.name
FROM feed_sources fs
WHERE a.feed_source_id = fs.id
AND (
    a.source_name IS NULL
    OR a.source_name = ''
);
