from django.http import HttpResponse


count = 0

def index(request):
    global count
    if request.GET.get('add', None):
        import time
        count += int(request.GET.get('add', 0))
        time.sleep(10)
        return HttpResponse(count)
    return HttpResponse(count)
