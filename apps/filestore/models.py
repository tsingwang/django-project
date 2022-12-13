import datetime
import hashlib
import random
import string

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models

from utils.model import BaseModel

fs = FileSystemStorage(location=settings.STORAGE_ROOT.joinpath('filestore'))


class Tag(models.Model):
    name = models.CharField(max_length=80)

    class Meta:
        permissions = (
            ("download_tag", "Can download tag files"),
        )

    def __str__(self):
        return self.name


class File(BaseModel):
    name = models.CharField(max_length=80)
    desc = models.TextField(default='', blank=True)
    is_public = models.BooleanField(default=True)
    icon = models.ImageField(upload_to='filestore/icon', null=True, blank=True)
    file = models.FileField(storage=fs)
    md5sum = models.CharField(max_length=36, blank=True)
    download_count = models.IntegerField(default=0)
    tag = models.ForeignKey(Tag, null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name='files')

    class Meta:
        permissions = (
            ("download_file", "Can download file"),
        )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.md5sum:
            md5 = hashlib.md5()
            for chunk in self.file.chunks():
                md5.update(chunk)
            self.md5sum = md5.hexdigest()
        super().save(*args, **kwargs)


class ShareLink(BaseModel):
    link = models.CharField(max_length=32, primary_key=True)
    code = models.CharField(max_length=8)
    valid_days = models.IntegerField()
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='sharelinks')

    def save(self, *args, **kwargs):
        s = string.digits + string.ascii_uppercase + string.ascii_lowercase
        if not self.link:
            while True:
                self.link = ''.join(random.sample(s, 24))
                try:
                    ShareLink.objects.get(link=self.link)
                except ShareLink.DoesNotExist:
                    break
        if not self.code:
            self.code = ''.join(random.sample(s, 4))
        return super().save(*args, **kwargs)

    def is_expired(self):
        if not self.created_at or self.valid_days < 1:
            return False
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        if self.created_at + datetime.timedelta(days=self.valid_days) >= now:
            return False
        return True
