"""
SP3-T009: URLs para Sistema de Pagos en Línea
Rutas para pagos, webhooks de Stripe, comprobantes.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_pagos import (
    PagoEnLineaViewSet,
    stripe_webhook,
    verificar_comprobante
)

# Router para ViewSets
router = DefaultRouter()
router.register(r'pagos', PagoEnLineaViewSet, basename='pago')

urlpatterns = [
    # ViewSet routes
    path('', include(router.urls)),
    
    # Webhook de Stripe (público, sin autenticación)
    path('webhook/stripe/', stripe_webhook, name='stripe-webhook'),
    
    # Verificación de comprobantes (público)
    path('verificar-comprobante-pago/<str:codigo_verificacion>/', 
         verificar_comprobante, 
         name='verificar-comprobante'),
]
