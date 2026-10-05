from fastapi import FastAPI

app = FastAPI(
    title="DevSecOps AI Platform",
    description="Cloud-native AI platform running on Kubernetes",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "application": "devsecops-ai-platform",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }