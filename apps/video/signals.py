from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import Video


@receiver(pre_delete, sender=Video)
def handle_video_deleted(instance, **kwargs):
    instance.video.delete(save=False)
    instance.cover.delete(save=False)
