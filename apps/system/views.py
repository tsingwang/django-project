import time
import traceback

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet, ModelViewSet, ReadOnlyModelViewSet

from utils.permissions import ActionModelWithReadPermissions

from .models import VerificationCode, OperationLog, PermReview
from .notification import notify_register, send_email_code, notify_active, notify_inactive
from .perms import perm_approve, perm_reject
from .serializers import (
    CodeCreateSerializer,
    ResetPasswordSerializer,
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    GroupSerializer,
    OperationLogSerializer,
    PermReviewSerializer,
)

User = get_user_model()


class OperationLogViewSet(ReadOnlyModelViewSet):
    queryset = OperationLog.objects.order_by('-id')
    serializer_class = OperationLogSerializer
    permission_classes = [ActionModelWithReadPermissions]
    search_fields = ['operator', 'ip', 'path']
    filterset_fields = ['operator', 'ip', 'path', 'method', 'status_code']


class AuthViewSet(ViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def send_code(self, request, *args, **kwargs):
        serializer = CodeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = get_object_or_404(User, email=email)
        code, created = VerificationCode.objects.get_or_create(user=user)
        if not created and code.is_expired():
            code.delete()
            code, created = VerificationCode.objects.get_or_create(user=user)
        send_email_code(code)
        return Response()

    @action(detail=False, methods=['post'])
    def register(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['email']
        serializer.validated_data['is_active'] = False
        try:
            user = User.objects.create_user(username, **serializer.validated_data)
        except Exception as e:
            print(traceback.format_exc())
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        notify_register(user)
        return Response()

    @action(detail=False, methods=['post'])
    def login(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        if time.time() - token.created.timestamp() > settings.TOKEN_EXPIRE_SECONDS:
            Token.objects.filter(user_id=user.id).delete()
            token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key,
                         'userId': user.username,})

    @action(detail=False, methods=['post'])
    def logout(self, request, *args, **kwargs):
        user = request.user
        if user:
            Token.objects.filter(user_id=user.id).delete()
        return Response()

    @action(detail=False, methods=['post'])
    def reset_password(self, request, *args, **kwargs):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = get_object_or_404(User, email=email)
        code = get_object_or_404(VerificationCode, user=user)
        if code.is_expired():
            code.delete()
            return Response('验证码已过期', status=status.HTTP_400_BAD_REQUEST)
        if code.code != serializer.validated_data['code']:
            return Response('验证码不正确', status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['password'])
        user.save()
        return Response()


class UserViewSet(ModelViewSet):
    queryset = User.objects.exclude(is_superuser=True).\
            exclude(username='AnonymousUser').order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [ActionModelWithReadPermissions]
    search_fields = ['fullname', 'email', 'mobile',]
    filterset_fields = ['is_active']

    @action(detail=False, permission_classes=[permissions.IsAuthenticated])
    def info(self, request, pk=None):
        user = request.user
        serializer = self.get_serializer(user)
        ret = dict(serializer.data)
        ret.update({'userId': user.username, 'realName': user.profile.fullname,
                    'roles': ret['groups']})
        return Response(ret)

    @action(detail=True, methods=['post'])
    def active(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_active:
            return Response()
        instance.is_active = True
        instance.save()
        notify_active(instance)
        return Response()

    @action(detail=True, methods=['post'])
    def inactive(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_active:
            return Response('帐号已经激活了', status=status.HTTP_400_BAD_REQUEST)
        instance.delete()
        notify_inactive(instance)
        return Response()


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [ActionModelWithReadPermissions]


class PermReviewViewSet(ModelViewSet):
    queryset = PermReview.objects.order_by('-id')
    serializer_class = PermReviewSerializer
    permission_classes = [ActionModelWithReadPermissions]
    filterset_fields = ['status']

    @action(detail=True, methods=['post'])
    def approve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != 0:
            return Response()
        perm_approve(instance.permission, instance.requester, instance.content_object)
        instance.status = 1
        instance.reviewer = request.user
        instance.save()
        return Response()

    @action(detail=True, methods=['post'])
    def reject(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != 0:
            return Response()
        perm_reject(instance.permission, instance.requester, instance.content_object)
        instance.status = 2
        instance.reviewer = request.user
        instance.save()
        return Response()
