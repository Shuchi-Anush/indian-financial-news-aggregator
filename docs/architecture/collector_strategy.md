# Collector Strategy

## Source Selection Criteria

Indian financial news sources selected based on:
1. **RSS feed availability** — must have a working public RSS/Atom feed
2. **Content quality** — established financial news publishers
3. **Update frequency** — at least daily updates
4. **No authentication required** — RSS feeds are open access

## Configured Sources (Phase 1)

| Source | Feed | Type | Category | Update Frequency |
|--------|------|------|----------|-----------------|
| Economic Times — Markets | `economictimes.indiatimes.com/.../1977021501.cms` | RSS | Markets | ~30 min |
| Economic Times — Economy | `economictimes.indiatimes.com/.../1373380680.cms` | RSS | Economy | ~1 hr |
| Moneycontrol — Markets | `moneycontrol.com/rss/marketreports.xml` | RSS | Markets | ~30 min |
| Moneycontrol — Business | `moneycontrol.com/rss/business.xml` | RSS | Business | ~1 hr |
| LiveMint — Markets | `livemint.com/rss/markets` | RSS | Markets | ~1 hr |
| LiveMint — Economy | `livemint.com/rss/economy` | RSS | Economy | ~2 hr |
| NDTV Profit | `feeds.feedburner.com/ndtvprofit-latest` | RSS | General | ~1 hr |
| Business Standard — Markets | `business-standard.com/rss/markets-106.rss` | RSS | Markets | ~1 hr |

## Optional API Sources (Phase 2)

| Source | API | Requires | Status |
|--------|-----|----------|--------|
| NewsData.io | REST API | `NEWSDATA_API_KEY` | Skipped if no key |
| GNews | REST API | `GNEWS_API_KEY` | Skipped if no key |

These are opt-in. The core pipeline works entirely with free RSS feeds.

## Collector Architecture

```
BaseCollector (ABC)
├── RSSCollector          — handles all RSS feeds via feedparser
│   └── Uses feed_sources table for URLs
└── NewsDataCollector     — optional, API-based (Phase 2)
    └── Uses NEWSDATA_API_KEY from config
```

### Why One RSSCollector for All Feeds

Individual RSS feeds share the same parsing logic (feedparser handles RSS 2.0, Atom, etc.). A per-source collector class would be premature abstraction. The `RSSCollector` iterates over all active `feed_sources` of type `rss` and fetches them concurrently.

If a specific source requires custom parsing (e.g., non-standard date formats, paywall detection), that logic belongs in the normalizer, not in a separate collector.

## Fetch Strategy

```python
async def collect(self) -> list[ArticleCreate]:
    tasks = [self._fetch_and_parse(feed) for feed in active_feeds]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

- **Concurrent execution** — all feeds fetched simultaneously
- **Per-feed timeout** — 30 seconds per feed (configurable)
- **Retry** — 3 attempts with exponential backoff (via tenacity)
- **Failure isolation** — one feed failure doesn't affect others
- **HTTP client reuse** — single `httpx.AsyncClient` shared across feeds

## RSS Feed Parsing

Fields extracted from each RSS entry:

| RSS Field | Maps To | Fallback |
|-----------|---------|----------|
| `title` | `ArticleCreate.title` | Required — skip entry if missing |
| `link` | `ArticleCreate.url` | Required — skip entry if missing |
| `summary` / `description` | `ArticleCreate.summary` | Empty string |
| `author` / `dc:creator` | `ArticleCreate.author` | None |
| `published` / `pubDate` | `ArticleCreate.published_at` | None |
| `category` / `tags` | `ArticleCreate.tags` | None |
| Feed-level category | `ArticleCreate.category` | From feed_source config |

## Known Quirks

| Source | Quirk | Mitigation |
|--------|-------|------------|
| Economic Times | Sometimes returns HTML entities in titles | Normalizer: HTML unescape |
| Moneycontrol | Dates in IST without timezone info | Normalizer: assume IST, convert to UTC |
| LiveMint | Feed occasionally returns 403 | Retry with backoff, User-Agent header |
| NDTV (FeedBurner) | FeedBurner redirects, slower response | Extended timeout |
| Business Standard | Summary contains full HTML markup | Normalizer: strip HTML tags |
