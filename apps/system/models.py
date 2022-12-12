import datetime
import random

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

User = get_user_model()

GENDERS = (
    ('male', 'Male'),
    ('female', 'Female'),
)

STATUS_CHOICES = (
    (0, 'Pending'),
    (1, 'Approve'),
    (2, 'Reject'),
)


class OperationLog(models.Model):
    action_time = models.DateTimeField()
    operator = models.CharField(max_length=64)
    ip = models.CharField(max_length=32)
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=11)
    content = models.TextField(null=True)
    latency = models.IntegerField(verbose_name='响应耗时/ms')
    status_code = models.IntegerField()

    class Meta:
        db_table = 'system_operation_log'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    full_name = models.CharField(max_length=64)
    gender = models.CharField(choices=GENDERS, max_length=8, null=True, blank=True)
    avatar = models.CharField(max_length=256, null=True, blank=True)
    mobile = models.CharField(max_length=15, unique=True, null=True, blank=True)


class VerificationCode(models.Model):
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='codes')

    class Meta:
        db_table = 'system_verification_code'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = '{:0>6}'.format(random.randint(0, 999999))
        return super().save(*args, **kwargs)

    def is_expired(self):
        if not self.created_at:
            return False
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        if self.created_at + datetime.timedelta(hours=1) >= now:
            return False
        return True


class PermReview(models.Model):
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='perm_request',
    )
    reviewer = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='perm_review',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_perm_review'
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
