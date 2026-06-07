# Architecture Review Prompt

Use this prompt when proposing new modules, changing layer boundaries, or adding new technology.

---

Review this architectural change for the Indian Financial News Aggregator.

**Evaluate against:**

1. **Necessity** — Does this solve a concrete problem we have *right now*, or is it speculative?
2. **Scope** — Does this stay within current constraints? (no K8s, no microservices, no event buses, no paid dependencies for core flow)
3. **Dependency direction** — Does this maintain `routes → services → {processors, collectors, db}`?
4. **Complexity budget** — Is this the simplest solution that works? What's the cheaper alternative?
5. **Reversibility** — If this turns out to be wrong, how hard is it to undo?
6. **ADR needed?** — If this changes a settled decision, should a new ADR be written in `docs/decisions/`?

**Proposed change:**
[Describe what's changing and why]

**Files affected:**
[List files]
