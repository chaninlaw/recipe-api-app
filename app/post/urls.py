"""
URL mappings for the post app.
"""

from django.urls import path, include

from rest_framework.routers import DefaultRouter

from post import views


router = DefaultRouter()
router.register('post', views.PostViewSet)

app_name = 'post'

urlpatterns = [
    path('', include(router.urls)),
]
