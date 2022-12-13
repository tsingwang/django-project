import os

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from guardian.shortcuts import get_objects_for_user, assign_perm, remove_perm
from rest_framework import permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from apps.system.perms import perm_request
from utils.permissions import ActionModelPermissions, ActionObjectPermissions

from .filters import TagFilter, FileFilter
from .models import Tag, File, ShareLink
from .serializers import (
    TagSerializer,
    FileCreateSerializer,
    FileListSerializer,
    ShareLinkSerializer,
    ShareLinkCreateSerializer,
    TagPermUpdateSerializer,
    FilePermUpdateSerializer,
)

User = get_user_model()


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.order_by('-id')
    serializer_class = TagSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    filterset_class = TagFilter

    @action(detail=False, methods=['POST'])
    def update_user_download_perm(self, request, *args, **kwargs):
        serializer = TagPermUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, username=serializer.validated_data['username'])
        old_list = get_objects_for_user(user, 'filestore.download_tag', Tag)
        for instance in old_list:
            if instance.id not in serializer.validated_data['tag_list']:
                remove_perm('filestore.download_tag', user, instance)
        old_list = [x.id for x in old_list]
        for instance_id in serializer.validated_data['tag_list']:
            if instance_id not in old_list:
                instance = get_object_or_404(Tag, id=instance_id)
                assign_perm('filestore.download_tag', user, instance)
        return Response()


class FileViewSet(ModelViewSet):
    queryset = File.objects.order_by('-id')
    serializer_class = FileListSerializer
    permission_classes = [ActionObjectPermissions]
    filterset_class = FileFilter
    search_fields = ['name', 'desc']
    action_model_perms_map = {
        'download': [],
    }
    action_object_perms_map = {
        'download': ['%(app_label)s.download_%(model_name)s'],
    }

    def get_queryset(self):
        categories = get_objects_for_user(
            self.request.user,
            'filestore.download_tag',
            Tag
        )
        queryset = get_objects_for_user(
            self.request.user,
            'filestore.download_file',
            self.queryset
        )
        return queryset | File.objects.filter(Q(is_public=True) | Q(Tag__in=categories))

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return FileCreateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        if 'icon' in serializer.validated_data:
            serializer.instance.icon.delete(save=False)
        if 'file' in serializer.validated_data:
            serializer.instance.file.delete(save=False)
            serializer.instance.md5sum = None
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['POST'])
    def download(self, request, *args, **kwargs):
        instance = get_object_or_404(File, id=kwargs["pk"])
        if not instance.is_public and \
                not request.user.has_perm('filestore.download_tag', instance.Tag):
            instance = self.get_object()
        instance.download_count += 1
        instance.save()
        resp = FileResponse(instance.file)
        if not resp.headers.get("Content-Length", None):
            resp.headers["Content-Length"] = instance.file.size
        return resp

    @action(detail=True, methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def download_request(self, request, *args, **kwargs):
        instance = self.get_object()
        perm_request('filestore.download_file', request.user, instance)
        return Response()

    @action(detail=False, methods=['POST'])
    def update_user_download_perm(self, request, *args, **kwargs):
        serializer = FilePermUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, username=serializer.validated_data['username'])
        old_list = get_objects_for_user(user, 'filestore.download_file', File)
        for instance in old_list:
            if instance.id not in serializer.validated_data['file_list']:
                remove_perm('filestore.download_file', user, instance)
        old_list = [x.id for x in old_list]
        for instance_id in serializer.validated_data['file_list']:
            if instance_id not in old_list:
                instance = get_object_or_404(File, id=instance_id)
                assign_perm('filestore.download_file', user, instance)
        return Response()


class ShareLinkViewSet(mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.DestroyModelMixin,
                       GenericViewSet):
    queryset = ShareLink.objects.order_by('-created_at')
    serializer_class = ShareLinkSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    search_fields = ['link',]

    def get_serializer_class(self):
        if self.action in ('create',):
            return ShareLinkCreateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['POST'], permission_classes=[permissions.AllowAny])
    def download(self, request, *args, **kwargs):
        sharelink = self.get_object()
        if sharelink.is_expired():
            return Response('链接已过期', status=status.HTTP_404_NOT_FOUND)
        instance = sharelink.file
        instance.download_count += 1
        instance.save()
        resp = FileResponse(instance.file)
        if not resp.headers.get("Content-Length", None):
            resp.headers["Content-Length"] = instance.file.size
        return resp

    @action(detail=False, methods=['GET'], permission_classes=[permissions.IsAdminUser])
    def fetch_all(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
