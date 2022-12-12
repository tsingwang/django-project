import re

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from django.db.models.fields.files import FieldFile
from django.forms.models import model_to_dict
from rest_framework import serializers

from utils.serializers import BasicUserSerializer

from .models import OperationLog, VerificationCode, PermReview

User = get_user_model()


class OperationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationLog
        fields = '__all__'


class CodeCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    code = serializers.CharField(write_only=True)

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        if password != confirm_password:
            msg = '两次输入的密码不一致'
            raise serializers.ValidationError(msg)
        attrs.pop('confirm_password')
        return attrs

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('邮箱不存在')
        if not user.is_active:
            raise serializers.ValidationError('帐号未激活')
        return value


class RegisterSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    fullname = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    mobile = serializers.CharField(write_only=True)

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        if password != confirm_password:
            msg = '两次输入的密码不一致'
            raise serializers.ValidationError(msg)
        attrs.pop('confirm_password')
        return attrs

    def validate_email(self, value):
        if not re.match(r'^\S+@\S+\.\S+$', value):
            raise serializers.ValidationError("邮箱不合法")
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        if username and password:
            user = authenticate(request=self.context.get('request'),
                                username=username, password=password)
            if not user:
                msg = 'Access denied: wrong username or password.'
                raise serializers.ValidationError(msg)
        else:
            msg = 'Both "username" and "password" are required.'
            raise serializers.ValidationError(msg)
        attrs['user'] = user
        return attrs


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name']


class UserSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')

    class Meta:
        model = User
        fields = ['id', 'username', 'fullname', 'email', 'mobile',
                  'is_active', 'date_joined', 'last_login', 'groups']


class PermReviewSerializer(serializers.ModelSerializer):
    requester = BasicUserSerializer(read_only=True)
    reviewer = BasicUserSerializer(read_only=True)
    permission = serializers.SerializerMethodField()
    obj = serializers.SerializerMethodField()

    class Meta:
        model = PermReview
        fields = '__all__'

    def get_permission(self, obj):
        return obj.permission.codename

    def get_obj(self, obj):
        data = model_to_dict(obj.content_object)
        for k in list(data.keys()):
            if isinstance(data[k], FieldFile):
                data.pop(k)
        return data
