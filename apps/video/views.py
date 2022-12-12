import binascii
import mimetypes
import os
import re

from django.core.cache import cache
from django.db.models import Max
from django.http import FileResponse, StreamingHttpResponse
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from utils import file_iterator
from utils.permission import ActionModelPermissions

from . import serializers
from .models import Category, Course, Lesson, CourseImage, Comment


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.order_by('id')
    serializer_class = serializers.CategorySerializer
    permission_classes = [ActionModelPermissions]


class VideoViewSet(ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = serializers.VideoSerializer
    permission_classes = [ActionModelPermissions]
    search_fields = ['name', 'content']
    filterset_fields = ['course']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return serializers.VideoCreateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        if 'video' in serializer.validated_data:
            serializer.instance.video.delete(save=False)
            serializer.instance.cover.delete(save=False)
            serializer.instance.duration = 0
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def study(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.read_count += 1
        instance.save()
        instance.learned_users.add(request.user)
        instance.course.learned_users.add(request.user)
        serializer = serializers.VideoDetailSerializer(instance)
        video_token = binascii.hexlify(os.urandom(20)).decode()
        key = 'video.token.' + video_token
        cache.set(key, instance.id, 3600*12)
        ret = dict(serializer.data)
        ret['video_token'] = video_token
        return Response(ret)

    @action(detail=True, methods=['GET'], permission_classes=[permissions.AllowAny])
    def video(self, request, *args, **kwargs):
        video_token = request.query_params.get('token', None)
        key = 'video.token.' + video_token
        instance = self.get_object()
        if video_token is None or cache.get(key) != instance.id:
            return Response(status=status.HTTP_403_FORBIDDEN)

        path = instance.video.path
        range_header = request.META.get('HTTP_RANGE', '').strip()
        range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)
        range_match = range_re.match(range_header)
        size = os.path.getsize(path)
        content_type, encoding = mimetypes.guess_type(path)
        content_type = content_type or 'application/octet-stream'
        if range_match:
            first_byte, last_byte = range_match.groups()
            first_byte = int(first_byte) if first_byte else 0
            last_byte = first_byte + 1024 * 1024 * 16
            if last_byte >= size:
                last_byte = size - 1
            length = last_byte - first_byte + 1
            resp = StreamingHttpResponse(
                file_iterator(path, offset=first_byte, length=length),
                status=206,
                content_type=content_type
            )
            resp['Content-Length'] = str(length)
            resp['Content-Range'] = 'bytes %s-%s/%s' % (first_byte, last_byte, size)
        else:
            resp = FileResponse(instance.video)
            if not resp.headers.get("Content-Length", None):
                resp.headers["Content-Length"] = instance.video.size
        resp['Accept-Ranges'] = 'bytes'
        return resp

    @action(detail=True, methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.liked_users.add(request.user)
        return Response()

    @action(detail=True, methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def unlike(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.liked_users.remove(request.user)
        return Response()
