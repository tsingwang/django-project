import datetime

from rest_framework import serializers

from utils.serializers import BaseModelSerializer

from .models import Tag, File, ShareLink


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class FileCreateSerializer(BaseModelSerializer):
    class Meta:
        model = File
        exclude = ['md5sum', 'download_count']


class FileListSerializer(BaseModelSerializer):
    file = serializers.FileField(use_url=False)
    size = serializers.SerializerMethodField()
    can_download = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = '__all__'

    def get_size(self, obj):
        return obj.file.size

    def get_can_download(self, obj):
        #if obj.is_public:
        #    return True
        #if self.context['request'].user.has_perm('filestore.download_file', obj):
        #    return True
        #return False
        return True


class ShareLinkSerializer(BaseModelSerializer):
    link = serializers.CharField(read_only=True)
    file = FileListSerializer(read_only=True)
    is_expired = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ShareLink
        exclude = ['code']

    def get_is_expired(self, obj):
        if not obj.created_at or obj.valid_days < 1:
            return False
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        if obj.created_at + datetime.timedelta(days=obj.valid_days) >= now:
            return False
        return True


class ShareLinkCreateSerializer(BaseModelSerializer):
    link = serializers.CharField(read_only=True)

    class Meta:
        model = ShareLink
        exclude = ['code']


class TagPermUpdateSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True)
    tag_list = serializers.ListField(child=serializers.IntegerField())


class FilePermUpdateSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True)
    file_list = serializers.ListField(child=serializers.IntegerField())
