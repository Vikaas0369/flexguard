from fastapi import FastAPI

app = FastAPI(
    title="FieldSync API",
    description="Demo field inspection API used by FlexGuard.",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "FieldSync API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }