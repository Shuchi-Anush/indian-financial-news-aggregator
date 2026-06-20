# Feed Audit Report v1

**Project:** Indian Financial News Aggregator
**Version:** v1.3.1-source-name-fix
**Audit Date:** 2026-06-19
**Purpose:** Validate the operational health, freshness, reliability, and usefulness of all configured ingestion sources.

---

# Executive Summary

The platform currently contains five configured RSS feeds. Three feeds are operating correctly and producing fresh, usable financial news content. Two feeds are non-viable for production use.

The audit confirms that the ingestion architecture, normalization pipeline, deduplication engine, enrichment layer, persistence layer, and scheduler are functioning correctly. The primary limitation is upstream feed quality rather than internal system behavior.

Current source coverage is therefore effectively limited to:

* Economic Times Markets
* LiveMint Markets
* SEBI Press Releases

Business Standard is blocked by anti-bot protections and Moneycontrol provides stale content that is no longer suitable for near-real-time market intelligence.

---

# Audit Methodology

Each source was evaluated across the following dimensions:

1. HTTP Accessibility
2. RSS Validity
3. Content Freshness
4. Scheduler Compatibility
5. Historical Reliability
6. Data Quality
7. Production Suitability

Verification was performed through:

* Direct RSS inspection
* Scheduler execution logs
* Database validation queries
* Feed source health metrics
* Article ingestion statistics

---

# Feed Inventory

| Feed                      | Status   | Freshness | Reliability | Production Ready |
| ------------------------- | -------- | --------- | ----------- | ---------------- |
| SEBI Press Releases       | Healthy  | Fresh     | High        | Yes              |
| Economic Times Markets    | Healthy  | Fresh     | High        | Yes              |
| LiveMint Markets          | Healthy  | Fresh     | High        | Yes              |
| Moneycontrol Markets      | Degraded | Stale     | Medium      | No               |
| Business Standard Markets | Failed   | Blocked   | Low         | No               |

---

# Source Analysis

## 1. SEBI Press Releases

### Configuration

```text
Name: SEBI Press Releases
Slug: sebi-press-releases
Type: RSS
```

### Operational Metrics

```text
Health Score: 100
Success Count: 10
Failure Count: 0
Circuit Breaker: CLOSED
```

### Database Contribution

```text
Articles Stored: 69
```

### Findings

The feed consistently delivers fresh regulatory announcements directly from SEBI.

Observed characteristics:

* Stable RSS format
* Reliable publication schedule
* No anti-bot restrictions
* High-quality metadata
* Strong enrichment performance

### Verdict

```text
PRODUCTION APPROVED
```

---

## 2. Economic Times Markets

### Configuration

```text
Name: Economic Times Markets
Slug: economic-times-markets
Type: RSS
```

### Operational Metrics

```text
Health Score: 100
Success Count: 10
Failure Count: 0
Circuit Breaker: CLOSED
```

### Database Contribution

```text
Articles Stored: 106
```

### Findings

This is currently the strongest market-news source in the platform.

Observed characteristics:

* High publication frequency
* Fresh financial content
* Reliable RSS availability
* Strong coverage of Indian equities and capital markets

### Verdict

```text
PRODUCTION APPROVED
```

---

## 3. LiveMint Markets

### Configuration

```text
Name: LiveMint Markets
Slug: livemint-markets
Type: RSS
```

### Operational Metrics

```text
Health Score: 100
Success Count: 10
Failure Count: 0
Circuit Breaker: CLOSED
```

### Database Contribution

```text
Articles Stored: 76
```

### Findings

The feed consistently produces fresh market and business coverage.

Observed characteristics:

* Good publication frequency
* Reliable timestamps
* Consistent RSS structure
* Strong compatibility with enrichment pipeline

### Verdict

```text
PRODUCTION APPROVED
```

---

## 4. Moneycontrol Markets

### Configuration

```text
Name: Moneycontrol Markets
Slug: moneycontrol-markets
Type: RSS
```

### Operational Metrics

```text
Health Score: 100
Success Count: 10
Failure Count: 0
Circuit Breaker: CLOSED
```

### Findings

Although the feed remains technically accessible, the content is stale.

Direct feed inspection revealed:

```text
Last Build Date:
Mon, 03 Jun 2024 23:00:01 +0530
```

Example articles returned by the feed were dated April 2024.

The scheduler currently records successful fetches because the endpoint responds correctly. However, the feed no longer delivers current market information.

### Risk

The existing health scoring mechanism incorrectly classifies this source as healthy because it evaluates transport success rather than content freshness.

### Verdict

```text
STALE SOURCE
NOT PRODUCTION READY
REPLACEMENT RECOMMENDED
```

---

## 5. Business Standard Markets

### Configuration

```text
Name: Business Standard Markets
Slug: business-standard-markets
Type: RSS
```

### Operational Metrics

```text
Health Score: 0
Success Count: 0
Failure Count: 5
Circuit Breaker: OPEN
```

### Findings

Direct validation confirmed that the feed is protected by Akamai anti-bot infrastructure.

Observed response:

```text
HTTP 403 Forbidden
Access Denied
```

The feed is inaccessible to automated collectors.

Repeated failures triggered the circuit breaker and correctly prevented further retries.

### Verdict

```text
FAILED SOURCE
REMOVE OR REPLACE
```

---

# Data Coverage Analysis

Current article distribution:

| Source                    | Articles |
| ------------------------- | -------- |
| Economic Times Markets    | 106      |
| LiveMint Markets          | 76       |
| SEBI Press Releases       | 69       |
| Moneycontrol Markets      | 0 Useful |
| Business Standard Markets | 0        |

Total usable dataset:

```text
251 Articles
```

Effective production sources:

```text
3 of 5
```

Effective source health:

```text
60%
```

---

# Architectural Findings

## Strengths

The ingestion platform successfully demonstrates:

* Scheduler reliability
* Source isolation
* Circuit breaker protection
* Deduplication stability
* Metadata enrichment
* Persistence correctness
* Source attribution integrity

The recently completed source-name propagation fix ensures article provenance is preserved across the entire ingestion lifecycle.

---

## Weaknesses

Current feed health evaluation relies primarily on transport success.

This allows stale feeds to appear healthy.

Example:

```text
Moneycontrol:
HTTP 200
Health Score 100
Content Age > 700 days
```

This creates a mismatch between technical availability and actual usefulness.

---

# Recommendations

## Immediate Actions

### Remove or Disable

```text
Business Standard Markets
```

Reason:

```text
Permanent HTTP 403 blocking.
```

### Replace

```text
Moneycontrol Markets
```

Reason:

```text
Feed no longer publishes current market data.
```

---

## Introduce Freshness Scoring

Current model:

```text
Successful Fetch
=
Healthy Feed
```

Recommended model:

```text
Successful Fetch
+
Recent Articles
+
Usable Content
=
Healthy Feed
```

Suggested thresholds:

| Age of Latest Article | Status   |
| --------------------- | -------- |
| < 7 Days              | Healthy  |
| 7–30 Days             | Degraded |
| > 30 Days             | Stale    |

---

## Candidate Replacement Sources

Priority evaluation:

1. RBI Press Releases
2. NSE Corporate Announcements
3. Hindu BusinessLine Markets
4. CNBC TV18 Markets

Each source should undergo the same audit process before onboarding.

---

# Final Conclusion

The platform architecture is stable and production-capable. The primary bottleneck is no longer ingestion reliability but upstream source quality.

The next release should focus on:

1. Feed replacement
2. Freshness-aware health scoring
3. Research export capabilities

The platform currently operates with three verified production-grade feeds and a validated end-to-end ingestion pipeline.

**Audit Result: PASSED WITH SOURCE QUALITY FINDINGS**
