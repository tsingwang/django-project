import os
import random

import cv2
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models

from utils.model import BaseModel

fs = FileSystemStorage(location=settings.STORAGE_ROOT.joinpath('video'))


def video_path(instance, filename):
    return os.path.join('video', filename)


class Category(models.Model):
    name = models.CharField(max_length=80)


class Video(BaseModel):
    name = models.CharField(max_length=80)
    desc = models.TextField(blank=True, default='')
    cover = models.ImageField(upload_to=video_path)
    video = models.FileField(storage=fs, null=True, blank=True)
    duration = models.IntegerField(default=0)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='videos'
    )
    liked_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_lessons'
    )

    def save(self, *args, **kwargs):
        if not self.id:
            while True:
                self.id = random.randint(10000000, 99999999)
                try:
                    Video.objects.get(id=self.id)
                except Video.DoesNotExist:
                    break
        super().save(*args, **kwargs)
        if self.video and not self.duration:
            self.cover = os.path.join(
                'course', '{}_{}_cover.png'.format(self.course.id, self.id))
            cap = cv2.VideoCapture(self.video.path)
            for i in range(30):
                ok, frame = cap.read()
                if not ok:
                    cap.release()
                    break
            cv2.imwrite(self.cover.path, frame)
            if cap.isOpened():
                rate = cap.get(5)
                frame_num = cap.get(7)
                self.duration = int(frame_num / rate)
                cap.release()
            cv2.destroyAllWindows()
            super().save(*args, **kwargs)
