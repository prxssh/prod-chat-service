from django.http import JsonResponse, HttpResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

ready = True

def healthz(request):
    return JsonResponse({"status": "PING", "version": "1.0.0"})

def readyz(request):
    return JsonResponse(
        {"status": "ready" if ready else "not ready"},
        status=200 if ready else 503
    )

def metrics(request):
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
