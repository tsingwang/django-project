from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from . import models


@admin.register(models.Tag)
class TagAdmin(GuardedModelAdmin):
    pass


@admin.register(models.File)
class FileAdmin(GuardedModelAdmin):
    pass
