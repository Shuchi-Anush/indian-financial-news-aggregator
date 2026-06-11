# Async Patterns

## Rule 1: Never Block the Event Loop
- Do not use `requests`. Use `httpx.AsyncClient`.
- Do not use `time.sleep`. Use `asyncio.sleep`.

## Rule 2: Concurrency Bounding
- Do not spawn unbounded `asyncio.gather` arrays for thousands of feeds. Use an `asyncio.Semaphore` or chunk the array to prevent TCP port exhaustion and memory spikes.

## Rule 3: AsyncSession Lifecycle
- The `AsyncSession` is strictly scoped per HTTP request or per APScheduler job execution. 
- Use async context managers: `async with session.begin():` to guarantee commit/rollback behaviors automatically.
