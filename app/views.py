from django.http import JsonResponse

def ping(request):
    return JsonResponse({"status": "PONG", "version": "1.0.0"})
