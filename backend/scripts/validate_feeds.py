import asyncio
import feedparser  # type: ignore
import httpx
from datetime import datetime, timezone
from dateutil import parser as date_parser

CANDIDATE_FEEDS = [
    {
        "name": "Economic Times Markets",
        "slug": "economic-times-markets",
        "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
    },
    {
        "name": "LiveMint Markets",
        "slug": "livemint-markets",
        "url": "https://www.livemint.com/rss/markets"
    },
    {
        "name": "Business Standard Markets",
        "slug": "business-standard-markets",
        "url": "https://www.business-standard.com/rss/markets-106.rss"
    },
    {
        "name": "Moneycontrol Markets",
        "slug": "moneycontrol-markets",
        "url": "https://www.moneycontrol.com/rss/marketreports.xml"
    },
    {
        "name": "SEBI Press Releases",
        "slug": "sebi-press-releases",
        "url": "https://www.sebi.gov.in/sebirss.xml"
    }
]

def format_output(feed_name, url, entries_count, latest_article, status, validation_result):
    print(f"Feed Name:       {feed_name}")
    print(f"URL:             {url}")
    print(f"Entries Count:   {entries_count}")
    print(f"Latest Article:  {latest_article}")
    print(f"Status:          {status}")
    print(f"Validation Res:  {validation_result}")
    print("-" * 60)

async def validate_feed(client, feed_info):
    name = feed_info["name"]
    url = feed_info["url"]
    
    try:
        response = await client.get(url)
        # Handle redirects
        final_url = str(response.url)
        if final_url != url:
            name += " (Redirected)"
        
        response.raise_for_status()
        
        feed = feedparser.parse(response.text)
        
        if feed.bozo and not feed.entries:
            format_output(name, url, 0, "N/A", "FAILED", f"Malformed XML: {getattr(feed, 'bozo_exception', 'Unknown')}")
            return False

        entries_count = len(feed.entries)
        if entries_count == 0:
            format_output(name, url, 0, "N/A", "FAILED", "Valid XML, but 0 entries.")
            return False

        # Extract latest publication timestamp
        latest_time = None
        for entry in feed.entries:
            pub_raw = entry.get("published", entry.get("updated"))
            if pub_raw:
                try:
                    dt = date_parser.parse(pub_raw)
                    if not latest_time or dt > latest_time:
                        latest_time = dt
                except Exception:
                    pass
        
        latest_article = str(latest_time) if latest_time else "Unknown"
        
        # Check staleness
        if latest_time:
            now = datetime.now(timezone.utc)
            # Ensure latest_time is aware
            if latest_time.tzinfo is None:
                latest_time = latest_time.replace(tzinfo=timezone.utc)
            
            diff = now - latest_time
            if diff.total_seconds() > 72 * 3600:
                format_output(name, url, entries_count, latest_article, "STALE", f"Latest article is {diff.days} days old (> 72 hours).")
                # Still technically valid as a feed format, but operationally stale.
                return True
        
        format_output(name, url, entries_count, latest_article, "VALID", "Feed is fully valid and fresh.")
        return True

    except httpx.HTTPStatusError as e:
        format_output(name, url, 0, "N/A", "FAILED", f"HTTP {e.response.status_code}")
        return False
    except Exception as e:
        format_output(name, url, 0, "N/A", "FAILED", f"Error: {str(e)}")
        return False

async def main():
    print("=" * 60)
    print("FEED VALIDATION UTILITY")
    print("=" * 60)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
        tasks = [validate_feed(client, f) for f in CANDIDATE_FEEDS]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
