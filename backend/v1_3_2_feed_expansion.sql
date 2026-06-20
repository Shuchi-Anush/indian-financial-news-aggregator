BEGIN;

-- 1. Disable defunct sources
UPDATE feed_sources 
SET is_active = false 
WHERE slug IN ('moneycontrol-markets', 'business-standard-markets');

-- 2. Upsert expansion sources idempotently
INSERT INTO feed_sources (
    name, slug, url, source_type, timezone_hint, is_active, circuit_breaker_state, success_count, failure_count, consecutive_failures, health_score
) VALUES 
('ET Economy', 'et-economy', 'https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms', 'RSS', 'Asia/Kolkata', true, 'CLOSED', 0, 0, 0, 100.0),
('ET Industry', 'et-industry', 'https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms', 'RSS', 'Asia/Kolkata', true, 'CLOSED', 0, 0, 0, 100.0),
('LiveMint Companies', 'livemint-companies', 'https://www.livemint.com/rss/companies', 'RSS', 'Asia/Kolkata', true, 'CLOSED', 0, 0, 0, 100.0),
('LiveMint Money', 'livemint-money', 'https://www.livemint.com/rss/money', 'RSS', 'Asia/Kolkata', true, 'CLOSED', 0, 0, 0, 100.0),
('Business Today Markets', 'business-today-markets', 'https://www.businesstoday.in/rssfeeds/?id=225346', 'RSS', 'Asia/Kolkata', true, 'CLOSED', 0, 0, 0, 100.0),
('Business Today Corporate', 'business-today-corporate', 'https://www.businesstoday.in/rssfeeds/?id=225345', 'RSS', 'Asia/Kolkata', true, 'CLOSED', 0, 0, 0, 100.0),
('NDTV Profit', 'ndtv-profit', 'https://feeds.feedburner.com/ndtvprofit-latest', 'RSS', 'Asia/Kolkata', true, 'CLOSED', 0, 0, 0, 100.0)
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    url = EXCLUDED.url,
    source_type = EXCLUDED.source_type,
    timezone_hint = EXCLUDED.timezone_hint,
    is_active = true,
    circuit_breaker_state = 'CLOSED';

COMMIT;
