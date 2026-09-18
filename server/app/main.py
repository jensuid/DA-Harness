from fastapi import FastAPI

app = FastAPI(
    title="DAH Harness Core",
    description="Deterministic core of the Data Analysis Harness.",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe. Confirms the core process is up and answering."""
    return {"status": "ok"}
