from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class BasicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'mobile', 'avatar']


class BaseModelSerializer(serializers.ModelSerializer):
    created_by = BasicUserSerializer(read_only=True)
    updated_by = BasicUserSerializer(read_only=True)
