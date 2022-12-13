from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import File


@receiver(pre_delete, sender=File)
def handle_file_deleted(instance: File, **kwargs):
    instance.file.delete(save=False)
    instance.icon.delete(save=False)
