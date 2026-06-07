from fastapi import FastAPI

app = FastAPI(
    title="Indian Financial News Aggregator",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}