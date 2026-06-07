# Scalability Review Prompt

Use this prompt when evaluating whether the system can handle growth.

---

Review this component for scalability concerns in the Indian Financial News Aggregator.

**Current scale assumptions:**
- 8-15 RSS feed sources
- ~200-500 new articles per day
- Single PostgreSQL instance
- Single FastAPI process
- No concurrent users beyond development/demo

**Check:**

1. **Database** — Are queries indexed? Any full table scans on growing tables? Is pagination implemented?
2. **Collection** — Are feeds fetched concurrently? Is there a timeout per feed? Does one slow feed block others?
3. **Memory** — Are large result sets streamed or fully loaded into memory?
4. **Export** — For large exports (10k+ articles), is the file generated in-memory or streamed?
5. **Deduplication** — Does fuzzy matching scale with article count? Is there a windowed approach?

**What we do NOT need to solve yet:**
- Multi-process/multi-node deployment
- Connection pooling beyond asyncpg defaults
- Read replicas
- Full-text search optimization (PostgreSQL built-in is sufficient)
- Rate limiting (no external users)

**Component to review:**
[Describe the component]
