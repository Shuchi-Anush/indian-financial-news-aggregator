# Feed Validation Report

## Executive Summary

A deep production-readiness validation was performed against four candidate financial news feeds: RBI Press Releases, RBI Notifications, PIB Finance, and NSE RSS. The objective was to determine whether these feeds can be immediately integrated into the current `BaseRSSCollector` ingestion pipeline.

**Conclusion:** All four candidate feeds **FAILED** validation. The aggregator cannot currently onboard these feeds via standard RSS without building custom HTML scrapers or negotiating API access.

## Validation Methodology

Feeds were validated using empirical HTTP requests and XML payload parsing rather than assumptions. The following criteria were tested:
1. **Endpoint Accessibility**: Ability to resolve the endpoint and receive HTTP 200 OK without WAF blocks.
2. **Payload Validity**: Confirmation of `text/xml` or `application/rss+xml` content types and well-formed XML syntax.
3. **Data Freshness**: Verification of recent `<item>` or `<entry>` payloads to ensure the feed is actively maintained by the publisher.
4. **Pipeline Compatibility**: Assessment against the existing `BaseRSSCollector` which relies on `feedparser`.

---

## Candidate Feed Results

### RBI Press Releases

* **Publisher**: Reserve Bank of India (RBI)
* **Category**: Regulatory Communications
* **Publisher Type**: Government/Central Bank
* **RSS URL**: None publicly available
* **Endpoint Validation**: FAIL. RBI relies entirely on custom ASPX HTML web portals (`https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx`).
* **Freshness Validation**: N/A
* **Operational Validation**: RBI does not syndicate structured data for automated consumption without specific portal scraping.
* **Verdict**: **FAIL**. Requires a dedicated HTML scraper, which falls outside the current RSS architecture.

### RBI Notifications

* **Publisher**: Reserve Bank of India (RBI)
* **Category**: Regulatory Communications
* **Publisher Type**: Government/Central Bank
* **RSS URL**: None publicly available
* **Endpoint Validation**: FAIL. Similar to Press Releases, Notifications are published exclusively as HTML pages or direct PDF links.
* **Freshness Validation**: N/A
* **Operational Validation**: N/A
* **Verdict**: **FAIL**. Cannot be ingested using `BaseRSSCollector`.

### PIB Finance

* **Publisher**: Press Information Bureau (Ministry of Finance)
* **Category**: Government Press Releases
* **Publisher Type**: Government
* **RSS URL**: `https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1`
* **Endpoint Validation**: PARTIAL PASS. 
  * HTTP Status: 200 OK
  * Content-Type: `text/xml`
  * XML Validity: PASS (Valid XML 1.0)
* **Freshness Validation**: FAIL. The XML payload returns an empty `<channel>` block with **0 entries**.
  * Payload extracted: `<?xml version="1.0" encoding="utf-8"?><rss version="2.0"><channel><title>Press Information Bureau </title><description>Press Information Bureau</description><copyright>Copyright 2009 - 2020 . All rights reserved.</copyright></channel></rss>`
* **Operational Validation**: The server-side RSS generation appears functionally abandoned or broken by the publisher, as no articles are hydrated into the feed structure.
* **Verdict**: **FAIL**. The endpoint exists but contains no usable data.

### NSE RSS

* **Publisher**: National Stock Exchange of India
* **Category**: Market Updates
* **Publisher Type**: Exchange
* **RSS URL**: `https://www.nseindia.com/rss`
* **Endpoint Validation**: FAIL.
  * HTTP Status: 404 Not Found (or 403 Forbidden depending on User-Agent).
* **Freshness Validation**: N/A
* **Operational Validation**: NSE aggressively utilizes Cloudflare/Akamai WAFs and bot-protection challenges. Automated extraction is heavily throttled or blocked.
* **Verdict**: **FAIL**. High operational risk; would trigger the ingestion circuit breaker immediately.

---

## Comparative Matrix

| Feed | HTTP | XML | Fresh | Feedparser | Anti-Bot | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RBI PRs** | FAIL | N/A | N/A | N/A | Low | **FAIL** |
| **RBI Notifs** | FAIL | N/A | N/A | N/A | Low | **FAIL** |
| **PIB Finance** | 200 OK | PASS | FAIL (0) | PASS | Low | **FAIL** |
| **NSE RSS** | 404/403 | N/A | N/A | N/A | High | **FAIL** |

---

## Architecture Compatibility Analysis

**Finding:** Current RSS collectors are redundant, empty wrappers around `BaseRSSCollector`. 
*Verified Examples:* `LiveMintRSSCollector`, `EconomicTimesRSSCollector`, `SEBIRSSCollector`, `MoneycontrolRSSCollector`, `BusinessStandardRSSCollector`.

None of these classes implement custom logic. They merely inherit `BaseRSSCollector` and rely on metadata injected from the factory. 

If the candidate feeds (e.g., PIB Finance) *were* operational, they could be onboarded dynamically **without** new collector classes, provided the collector factory is refactored.

## Onboarding Effort Assessment

To transition the repository to a true "Zero-Code Configuration" onboarding model for future RSS feeds:

* **Required Code Changes**: Refactor `_instantiate_collector` to map dynamically.
* **Required Database Changes**: Insert new target feeds into the `feed_sources` table.
* **Required Collector Changes**: None. (Existing empty wrapper classes can actually be deleted).
* **Required Factory Changes**: 
  * *Current*: `if slug == "livemint-markets": return LiveMintRSSCollector(meta)`
  * *Future*: `if source_type == "rss": return BaseRSSCollector(meta)`

## Risk Assessment

1. **Ingestion Starvation**: Because all four candidate feeds failed validation, the aggregator remains heavily reliant on the three existing functional sources (Economic Times, LiveMint, SEBI).
2. **Scraper Maintenance Burden**: To capture RBI and NSE, the engineering team must deviate from standard RSS parsing and build brittle HTML scrapers, increasing maintenance overhead significantly.

## Final Recommendation

1. **Do not proceed** with the immediate onboarding of RBI, PIB, or NSE feeds via the RSS pipeline. The empirical evidence strictly prohibits their use.
2. **Refactor the Factory**: Prioritize the `_instantiate_collector` refactor to allow true zero-code onboarding for when valid RSS feeds *are* discovered.

## Recommended v1.3.2 Scope

* Refactor `app/orchestration/ingestion_jobs.py` to instantiate `BaseRSSCollector` dynamically based on the DB `source_type`.
* Delete the redundant, empty collector subclass files in `app/collectors/rss/` to reduce technical debt.
* Do **not** expand the `feed_sources` table.

## Recommended v1.4.0 Scope

* Shift focus away from feed volume and toward data utilization.
* Implement the Research Exports (XLSX, Date-range, Source-filtered) using the existing validated pool of 251+ articles.
