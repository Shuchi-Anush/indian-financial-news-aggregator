# rss_inventory.md

# Indian Financial News Aggregator

## Candidate RSS Feed Inventory

Status Definitions:

* VERIFIED = Officially documented RSS/XML endpoint
* CANDIDATE = Appears to be RSS but requires validation
* REJECTED = Not a direct RSS feed
* STALE = Feed exists but appears outdated
* UNKNOWN = Requires live validation

---

# Tier 1 — Core Financial News Sources

## Economic Times Markets

Slug:
economictimes-markets

Status:
CANDIDATE

URL:
https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms

Priority:
HIGH

Notes:
Frequently referenced ET Markets RSS feed.
Requires live validation.

---

## LiveMint Markets

Slug:
livemint-markets

Status:
CANDIDATE

URL:
https://www.livemint.com/rss/markets

Priority:
HIGH

Notes:
Requires live validation.

---

## Business Standard Markets

Slug:
business-standard-markets

Status:
CANDIDATE

URL:
https://www.business-standard.com/rss/markets-106.rss

Priority:
HIGH

Notes:
Requires live validation.

---

## NDTV Profit

Slug:
ndtv-profit

Status:
CANDIDATE

URL:
https://feeds.feedburner.com/ndtvprofit-latest

Priority:
HIGH

Notes:
Requires live validation.
May redirect.

---

## Moneycontrol Markets

Slug:
moneycontrol-markets

Status:
STALE

URL:
https://www.moneycontrol.com/rss/marketreports.xml

Priority:
LOW

Notes:
Previous validation indicated latest entries from 2024.
Likely unsuitable for production.

---

# Tier 2 — Financial Media

## Financial Express Markets

Slug:
financial-express-markets

Status:
UNKNOWN

Priority:
MEDIUM

Notes:
Collector candidate only.
Requires RSS discovery and validation.

---

## CNBC TV18 Markets

Slug:
cnbc-tv18-markets

Status:
UNKNOWN

Priority:
MEDIUM

Notes:
Collector exists in codebase.
RSS endpoint must be verified.

---

## Business Today Markets

Slug:
business-today-markets

Status:
UNKNOWN

Priority:
MEDIUM

Notes:
Requires discovery and validation.

---

## Hindu BusinessLine Markets

Slug:
businessline-markets

Status:
UNKNOWN

Priority:
MEDIUM

Notes:
Requires discovery and validation.

---

# Tier 3 — Official Regulatory Sources

## SEBI

Slug:
sebi

Status:
VERIFIED

RSS URL:
https://www.sebi.gov.in/sebirss.xml

Priority:
HIGH

Source:
Official SEBI RSS documentation.

Notes:
Official regulator feed.

---

## NSE

Slug:
nse

Status:
VERIFIED_SOURCE_EXISTS

RSS Landing Page:
https://www.nseindia.com/static/rss-feed

Priority:
HIGH

Notes:
Official RSS area exists.
AGY must enumerate individual RSS feeds and validate them.

Do not seed landing page itself.

---

## RBI

Slug:
rbi

Status:
UNKNOWN

Priority:
HIGH

Notes:
Official RSS feeds likely exist.
Requires discovery and validation.

---

## BSE

Slug:
bse

Status:
UNKNOWN

Priority:
HIGH

Notes:
Requires discovery and validation.

---

# Validation Rules

A feed may be seeded only if all checks pass:

1. HTTP 200
2. XML/RSS/Atom content
3. Feedparser parses successfully
4. Contains entries
5. Latest article not stale
6. No login required
7. No HTML page masquerading as RSS
8. No redirect loops

---

# Rejection Rules

Reject automatically if:

* Feed directory
* Feed discovery page
* Feed aggregator
* HTML category page
* News website homepage
* FeedBurner landing page without valid XML
* Stale feed
* Empty feed

---

# MVP Target

The first production ingestion cycle should aim for:

1. Economic Times Markets
2. LiveMint Markets
3. Business Standard Markets
4. NDTV Profit
5. SEBI

Success Criteria:

feed_sources > 0
raw_articles > 0
articles > 0
pipeline_runs > 0

Only validated feeds may enter feed_sources.

This document is the canonical candidate inventory.

AGY must validate every candidate programmatically before seeding.
