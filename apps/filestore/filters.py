from django.contrib.auth import get_user_model
from django_filters import CharFilter
from django_filters import rest_framework as filters
from guardian.shortcuts import get_objects_for_user

from .models import Tag, File

User = get_user_model()


class TagFilter(filters.FilterSet):
    download_by_user = CharFilter(method='filter_download_by_user')

    class Meta:
        model = Tag
        fields = ['download_by_user']

    def filter_download_by_user(self, queryset, name, value):
        try:
            user = User.objects.get(username=value)
        except User.DoesNotExist:
            return queryset
        return get_objects_for_user(
            user,
            'filestore.download_tag',
            queryset
        )


class FileFilter(filters.FilterSet):
    download_by_user = CharFilter(method='filter_download_by_user')

    class Meta:
        model = File
        fields = ['tag', 'download_by_user']

    def filter_download_by_user(self, queryset, name, value):
        try:
            user = User.objects.get(username=value)
        except User.DoesNotExist:
            return queryset
        return get_objects_for_user(
            user,
            'filestore.download_file',
            queryset
        )
