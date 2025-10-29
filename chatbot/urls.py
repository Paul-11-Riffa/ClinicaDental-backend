"""
URLs del chatbot.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatbotViewSet, PreConsultaViewSet

router = DefaultRouter()
router.register(r'chatbot', ChatbotViewSet, basename='chatbot')
router.register(r'pre-consultas', PreConsultaViewSet, basename='pre-consultas')

urlpatterns = [
    path('', include(router.urls)),
]
