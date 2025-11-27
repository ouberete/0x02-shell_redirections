# backend/core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router setup
router = DefaultRouter()
router.register(r'levels', views.LevelViewSet)
router.register(r'classes', views.SchoolClassViewSet)
router.register(r'students', views.StudentViewSet)
router.register(r'parents', views.ParentViewSet)
router.register(r'documents', views.DocumentViewSet)

# URL Patterns
urlpatterns = [
    path('', include(router.urls)),
]
