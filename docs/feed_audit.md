# Feed Audit

## Purpose

This document tracks the operational status, validation results, onboarding requirements, and expansion roadmap for all news sources used by the Indian Financial News Aggregator.

---

# Current Production Sources

| Source                 | Slug                   | Status | Evidence                        |
| ---------------------- | ---------------------- | ------ | ------------------------------- |
| SEBI Press Releases    | sebi-press-releases    | ACTIVE | Successfully ingesting articles |
| Economic Times Markets | economic-times-markets | ACTIVE | Successfully ingesting articles |
| LiveMint Markets       | livemint-markets       | ACTIVE | Successfully ingesting articles |

### Current Database Distribution

| Source                 | Articles |
| ---------------------- | -------- |
| Economic Times Markets | 106      |
| LiveMint Markets       | 76       |
| SEBI Press Releases    | 69       |

Total Articles: 251

---

# Rejected Sources

## Business Standard Markets

### Status

REJECTED

### Evidence

```bash
curl https://www.business-standard.com/rss/markets-106.rss
```

Response:

```text
HTTP 403 Forbidden
```

### Root Cause

Akamai anti-bot protection prevents reliable automated ingestion.

### Recommendation

Do not use in production RSS pipeline.

---

## Moneycontrol Markets

### Status

REJECTED

### Evidence

Feed returns stale content from 2024.

### Root Cause

RSS endpoint appears abandoned or no longer maintained.

### Recommendation

Do not use in production RSS pipeline.

---

# Candidate Sources

## Priority P0

### RBI Press Releases

Status: Pending Validation

Expected Complexity: Low

Expected Onboarding Method:

* feed_sources entry
* RSS collector registration

---

### RBI Notifications

Status: Pending Validation

Expected Complexity: Low

Expected Onboarding Method:

* feed_sources entry
* RSS collector registration

---

### PIB Finance

Status: Pending Validation

Expected Complexity: Low

Expected Onboarding Method:

* feed_sources entry
* RSS collector registration

---

## Priority P2

### NSE RSS

Status: Pending Validation

Expected Complexity: High

Risks:

* Akamai
* Anti-bot protections
* Possible cookie requirements
* Possible custom header requirements

---

# Collector Architecture Audit

## Finding

Current RSS onboarding is not fully configuration-driven.

### Existing Design

feed_sources
→ ingestion_jobs.py
→ hardcoded slug mapping
→ collector instantiation

New feeds currently require factory registration.

### Collector Audit Result

All source-specific RSS collectors are empty wrappers around BaseRSSCollector.

Examples:

* BusinessStandardRSSCollector
* EconomicTimesRSSCollector
* LiveMintRSSCollector
* MoneycontrolRSSCollector
* SEBIRSSCollector

Each contains only:

```python
class SomeCollector(BaseRSSCollector):
    pass
```

### Architectural Conclusion

BaseRSSCollector already provides:

* HTTP fetching
* Retry handling
* Feed parsing
* Entry mapping
* Metadata propagation

The collector subclasses add no source-specific behavior.

### Recommended Future Refactor

Replace hardcoded slug-based collector instantiation with source_type-based instantiation.

Example:

```python
if source_type == "RSS":
    return BaseRSSCollector(metadata)
```

Result:

Future RSS feeds can be onboarded through database configuration alone.

No code changes required.

---

# Validation Protocol

Every new feed must pass:

1. HTTP accessibility
2. XML validity
3. Feed parsing
4. Timestamp parsing
5. Deduplication compatibility
6. Persistence validation
7. Scheduler execution
8. 24-hour stability monitoring

---

# Recommended v1.3.2 Scope

Include:

* RBI Press Releases
* RBI Notifications
* PIB Finance

Exclude:

* NSE RSS

until live validation confirms operational stability.

---

# Release Recommendation

Current Release:

v1.3.1-source-name-fix

Next Release:

v1.3.2-feed-expansion-validation

Goals:

* Validate RBI feeds
* Validate PIB feed
* Expand source coverage
* Improve dataset breadth

Future Release:

v1.4.0-research-exports

Goals:

* XLSX export
* Date-range export
* Source-filtered export
* Keyword export
* Research workflows

# Architectural Finding

## Current State

New RSS feeds require:

1. feed_sources database row
2. hardcoded slug registration
3. collector instantiation mapping

## Audit Result

All RSS collectors currently contain no source-specific logic.

Examples:

- LiveMintRSSCollector
- EconomicTimesRSSCollector
- SEBIRSSCollector
- MoneycontrolRSSCollector

Each inherits BaseRSSCollector without overriding behavior.

## Recommendation

Refactor collector instantiation to become source-type driven.

Current:

feed_source
→ slug mapping
→ collector class

Future:

feed_source
→ source_type
→ BaseRSSCollector

Result:

New RSS feeds can be onboarded entirely through database configuration.

No application code changes required.

Priority: Medium

Target Release: v1.4.0
