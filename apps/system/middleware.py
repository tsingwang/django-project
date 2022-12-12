from datetime import datetime, timezone
import json
import time

from django.utils.deprecation import MiddlewareMixin

from .models import OperationLog


class OperationLogMiddleware(MiddlewareMixin):

    exclude_urls = []

    def __init__(self, get_response):
        super().__init__(get_response)
        self.action_time = None

    def process_request(self, request):
        self.action_time = time.time()

    def process_response(self, request, response):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return response

        for url in self.exclude_urls:
            if url in request.path:
                return response

        latency = round((time.time() - self.action_time)*1000)

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(",")[0] if x_forwarded_for \
                else request.META.get('REMOTE_ADDR')

        content = ""
        if request.POST:
            data = dict(request.POST)
            self.clean_secret(data)
            content = json.dumps(data, ensure_ascii=False)
        elif hasattr(response, 'renderer_context'):
            data = response.renderer_context["request"].data
            self.clean_secret(data)
            try:
                content = json.dumps(data, ensure_ascii=False)
            except:
                pass

        OperationLog.objects.create(
            action_time=datetime.fromtimestamp(self.action_time, tz=timezone.utc),
            operator=request.user.username,
            ip=ip,
            path=request.path,
            method=request.method,
            content=content,
            latency=latency,
            status_code=response.status_code
        )
        return response

    def clean_secret(self, data):
        for k in list(data.keys()):
            for key in ["password", "token"]:
                if key in k:
                    data.pop(k)
