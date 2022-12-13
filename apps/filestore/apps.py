from django.apps import AppConfig


class FileStoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.filestore'

    def ready(self):
        import apps.filestore.signals
