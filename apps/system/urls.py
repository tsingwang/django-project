from django.urls import include, path
from rest_framework import routers

from . import views


router = routers.DefaultRouter()
router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'perm_review', views.PermReviewViewSet)
router.register(r'operationlog', views.OperationLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
