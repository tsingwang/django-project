from django.urls import include, path
from rest_framework import routers

from . import views


router = routers.DefaultRouter()
router.register(r'tags', views.TagViewSet)
router.register(r'files', views.FileViewSet)
router.register(r'sharelink', views.ShareLinkViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
