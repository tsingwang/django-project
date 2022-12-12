from rest_framework import serializers

from utils.serializers import BaseModelSerializer, BasicUserSerializer
from .models import Category, Video


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class VideoSerializer(BaseModelSerializer):
    video = serializers.FileField(use_url=False)

    class Meta:
        model = Video
        fields = '__all__'


class VideoCreateSerializer(BaseModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Video
        exclude = ['liked_users']


class VideoDetailSerializer(BaseModelSerializer):
    video = serializers.FileField(use_url=False)
    liked_users = BasicUserSerializer(many=True, read_only=True)

    class Meta:
        model = Video
        fields = '__all__'
