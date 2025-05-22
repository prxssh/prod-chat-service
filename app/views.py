from typing import Any
from django.http import HttpRequest, JsonResponse, HttpResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.metrics import registry

ready = True

def healthz(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "PING", "version": "1.0.0"})

def readyz(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        {"status": "ready" if ready else "not ready"},
        status=200 if ready else 503
    )

def metrics(request: HttpRequest) -> HttpResponse:
    data = generate_latest(registry)
    return HttpResponse(data, content_type=CONTENT_TYPE_LATEST)
