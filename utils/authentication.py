import time

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication


class CustomTokenAuthentication(TokenAuthentication):
    """Add token expired."""

    keyword = 'Bearer'

    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))

        if time.time() - token.created.timestamp() > settings.TOKEN_EXPIRE_SECONDS:
            raise exceptions.AuthenticationFailed(_('Token expired.'))

        return (token.user, token)
