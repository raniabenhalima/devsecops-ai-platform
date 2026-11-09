from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
from pydantic import BaseModel
from fastapi import HTTPException
from app.ai.llm import generate_response

app = FastAPI(
    title="DevSecOps AI Platform",
    description="Cloud-native AI platform running on Kubernetes",
    version="0.1.1",
)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)


@app.middleware("http")
async def prometheus_metrics(request: Request, call_next):
    start_time = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start_time
    endpoint = request.url.path

    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=str(response.status_code),
    ).inc()

    HTTP_REQUEST_DURATION.labels(
        method=request.method,
        endpoint=endpoint,
    ).observe(duration)

    return response


@app.get("/")
def root():
    return {
        "application": "devsecops-ai-platform",
        "status": "running",
        "version": "0.1.1",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


class IncidentRequest(BaseModel):
    logs: str


@app.post("/ai/analyze")
async def analyze_incident(request: IncidentRequest):
    prompt = f"""

You are a Senior DevSecOps and Kubernetes Incident Response Engineer.

Analyze the following incident logs.

STRICT RULES:
- Never invent facts or vulnerabilities.
- Clearly distinguish observed facts from hypotheses.
- Do not claim a root cause without sufficient evidence.
- Do not recommend restarting containers as a generic fix.
- Provide diagnostic commands before remediation.
- All Kubernetes commands must use valid kubectl syntax.
- Never invent Kubernetes resource names.
- If namespace is unknown, explicitly use -n <namespace>.
- Use kubectl logs <pod-name> --previous for previous container logs.
- Use kubectl describe pod <pod-name> for pod events.
- Use kubectl get endpoints or kubectl get endpointslices to inspect service connectivity.
- Never use kubectl scale on a Pod.
- Never recommend destructive actions without evidence.
- Mark commands requiring placeholders clearly.
- Never claim that a diagnostic command proves a root cause.

Use this structure:

1. INCIDENT SUMMARY
2. OBSERVED FACTS
3. POSSIBLE ROOT CAUSES
4. SECURITY RISKS (evidence-based)
5. DIAGNOSTIC COMMANDS
6. RECOMMENDED REMEDIATION
7. CONFIDENCE LEVEL (Low, Medium, High)

Incident logs:
{request.logs}
"""


    try:
        analysis = await generate_response(prompt)
        return {
            "status": "success",
            "analysis": analysis
        }

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=f"AI service unavailable: {str(error)}"
        )
