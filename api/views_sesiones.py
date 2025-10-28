"""
ViewSet para Sesiones de Tratamiento
SP3-T008: Registrar procedimiento clínico (web)
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import datetime

from .models import (
    SesionTratamiento, 
    Itemplandetratamiento, 
    Plandetratamiento,
    Historialclinico,
    Bitacora
)
from .serializers_sesiones import (
    SesionTratamientoCreateSerializer,
    SesionTratamientoUpdateSerializer,
    SesionTratamientoListSerializer,
    SesionTratamientoDetailSerializer,
    ProgresoItemSerializer,
    ProgresoPlanSerializer,
)


class SesionTratamientoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar sesiones de tratamiento clínico.
    
    Endpoints:
    - list: Listar sesiones (filtradas por tenant)
    - retrieve: Obtener detalle de una sesión
    - create: Registrar nueva sesión
    - update/partial_update: Modificar sesión
    - destroy: Eliminar sesión
    - progreso_item: Obtener progreso de un ítem específico
    - progreso_plan: Obtener progreso general de un plan
    - marcar_completado: Marcar un ítem como completado
    - sesiones_por_paciente: Listar sesiones de un paciente
    - sesiones_por_plan: Listar sesiones de un plan
    - estadisticas_odontologo: Estadísticas de sesiones por odontólogo
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar sesiones por empresa (multi-tenancy)."""
        # Validar que existe tenant
        if not hasattr(self.request, 'tenant') or not self.request.tenant:
            return SesionTratamiento.objects.none()
        
        queryset = SesionTratamiento.objects.filter(empresa=self.request.tenant)
        
        # Filtros opcionales
        item_plan_id = self.request.query_params.get('item_plan', None)
        plan_id = self.request.query_params.get('plan', None)
        paciente_id = self.request.query_params.get('paciente', None)
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        
        if item_plan_id:
            queryset = queryset.filter(item_plan_id=item_plan_id)
        
        if plan_id:
            queryset = queryset.filter(item_plan__idplantratamiento_id=plan_id)
        
        if paciente_id:
            queryset = queryset.filter(item_plan__idplantratamiento__codpaciente_id=paciente_id)
        
        if fecha_desde:
            queryset = queryset.filter(fecha_sesion__gte=fecha_desde)
        
        if fecha_hasta:
            queryset = queryset.filter(fecha_sesion__lte=fecha_hasta)
        
        return queryset.select_related(
            'item_plan',
            'item_plan__idservicio',
            'item_plan__idplantratamiento',
            'item_plan__idplantratamiento__codpaciente',
            'consulta',
            'usuario_registro'
        ).order_by('-fecha_sesion', '-hora_inicio')
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción."""
        if self.action == 'create':
            return SesionTratamientoCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SesionTratamientoUpdateSerializer
        elif self.action == 'retrieve':
            return SesionTratamientoDetailSerializer
        elif self.action in ['progreso_item']:
            return ProgresoItemSerializer
        elif self.action in ['progreso_plan']:
            return ProgresoPlanSerializer
        return SesionTratamientoListSerializer
    
    def perform_create(self, serializer):
        """Guardar sesión con tenant y usuario actual."""
        # Validar tenant
        if not hasattr(self.request, 'tenant') or not self.request.tenant:
            raise ValidationError({
                'error': 'No se pudo identificar la empresa (tenant). Verifica el header X-Tenant-Subdomain.'
            })
        
        usuario = getattr(self.request.user, 'usuario', None)
        
        sesion = serializer.save(
            empresa=self.request.tenant,
            usuario_registro=usuario
        )
        
        # Registrar en bitácora
        Bitacora.objects.create(
            empresa=self.request.tenant,
            usuario=usuario,
            accion='CREAR_SESION_TRATAMIENTO',
            tabla_afectada='sesion_tratamiento',
            registro_id=sesion.id,
            valores_nuevos={'mensaje': f'Sesión creada para ítem {sesion.item_plan_id} - Progreso: {sesion.progreso_actual}%'},
            ip_address=self.request.META.get('REMOTE_ADDR', '0.0.0.0'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        return sesion
    
    def perform_update(self, serializer):
        """Actualizar sesión con registro en bitácora."""
        usuario = getattr(self.request.user, 'usuario', None)
        sesion = serializer.save()
        
        # Registrar en bitácora
        Bitacora.objects.create(
            empresa=self.request.tenant,
            usuario=usuario,
            accion='ACTUALIZAR_SESION_TRATAMIENTO',
            tabla_afectada='sesion_tratamiento',
            registro_id=sesion.id,
            valores_nuevos={'mensaje': f'Sesión {sesion.id} actualizada - Progreso: {sesion.progreso_actual}%'},
            ip_address=self.request.META.get('REMOTE_ADDR', '0.0.0.0'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        return sesion
    
    def perform_destroy(self, instance):
        """Eliminar sesión con registro en bitácora."""
        usuario = getattr(self.request.user, 'usuario', None)
        sesion_id = instance.id
        item_plan_id = instance.item_plan_id
        
        instance.delete()
        
        # Registrar en bitácora
        Bitacora.objects.create(
            empresa=self.request.tenant,
            usuario=usuario,
            accion='ELIMINAR_SESION_TRATAMIENTO',
            tabla_afectada='sesion_tratamiento',
            registro_id=sesion_id,
            valores_anteriores={'mensaje': f'Sesión {sesion_id} eliminada del ítem {item_plan_id}'},
            ip_address=self.request.META.get('REMOTE_ADDR', '0.0.0.0'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    @action(detail=False, methods=['get'], url_path='progreso-item/(?P<item_id>[0-9]+)')
    def progreso_item(self, request, item_id=None):
        """
        Obtener el progreso actual de un ítem específico.
        
        GET /api/sesiones-tratamiento/progreso-item/123/
        
        Retorna:
        - progreso_actual: Porcentaje de progreso
        - total_sesiones: Número de sesiones registradas
        - ultima_sesion_fecha: Fecha de la última sesión
        - estado_item: Estado actual del ítem
        - puede_facturar: Si el ítem está completado y se puede facturar
        """
        try:
            item = Itemplandetratamiento.objects.get(
                id=item_id,
                idplantratamiento__empresa=request.tenant
            )
        except Itemplandetratamiento.DoesNotExist:
            return Response(
                {'error': 'Ítem no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        sesiones = SesionTratamiento.objects.filter(item_plan=item).order_by('-fecha_sesion')
        ultima_sesion = sesiones.first()
        
        data = {
            'item_plan_id': item.id,
            'progreso_actual': float(ultima_sesion.progreso_actual) if ultima_sesion else 0.0,
            'total_sesiones': sesiones.count(),
            'ultima_sesion_fecha': ultima_sesion.fecha_sesion if ultima_sesion else None,
            'estado_item': item.estado_item,
            'puede_facturar': item.esta_completado()
        }
        
        serializer = ProgresoItemSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='progreso-plan/(?P<plan_id>[0-9]+)')
    def progreso_plan(self, request, plan_id=None):
        """
        Obtener el progreso general de un plan de tratamiento.
        
        GET /api/sesiones-tratamiento/progreso-plan/456/
        
        Retorna:
        - progreso_general: Porcentaje promedio del plan
        - total_items: Total de ítems en el plan
        - items_completados: Ítems completados
        - items_activos: Ítems en progreso
        - items_pendientes: Ítems pendientes
        - plan_completado: Si todos los ítems están completados
        """
        try:
            plan = Plandetratamiento.objects.get(id=plan_id, empresa=request.tenant)
        except Plandetratamiento.DoesNotExist:
            return Response(
                {'error': 'Plan no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        items = plan.itemplandetratamiento_set.all()
        items_activos = items.filter(
            estado_item__in=[
                Itemplandetratamiento.ESTADO_ACTIVO,
                Itemplandetratamiento.ESTADO_COMPLETADO
            ]
        )
        
        # Calcular progreso promedio
        total_progreso = 0
        for item in items_activos:
            ultima_sesion = SesionTratamiento.objects.filter(
                item_plan=item
            ).order_by('-fecha_sesion').first()
            
            if ultima_sesion:
                total_progreso += float(ultima_sesion.progreso_actual)
        
        progreso_general = (total_progreso / items_activos.count()) if items_activos.count() > 0 else 0
        
        items_completados = items.filter(estado_item=Itemplandetratamiento.ESTADO_COMPLETADO).count()
        items_activos_count = items.filter(estado_item=Itemplandetratamiento.ESTADO_ACTIVO).count()
        items_pendientes = items.filter(estado_item=Itemplandetratamiento.ESTADO_PENDIENTE).count()
        
        plan_completado = (items_activos.count() > 0 and 
                          items_activos.count() == items.filter(estado_item=Itemplandetratamiento.ESTADO_COMPLETADO).count())
        
        data = {
            'plan_id': plan.id,
            'progreso_general': round(progreso_general, 2),
            'total_items': items.count(),
            'items_completados': items_completados,
            'items_activos': items_activos_count,
            'items_pendientes': items_pendientes,
            'plan_completado': plan_completado
        }
        
        serializer = ProgresoPlanSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='marcar-completado/(?P<item_id>[0-9]+)')
    def marcar_completado(self, request, item_id=None):
        """
        Marcar un ítem como completado directamente (sin sesión).
        
        POST /api/sesiones-tratamiento/marcar-completado/123/
        Body: {
            "notas": "Tratamiento finalizado anticipadamente"
        }
        
        Útil cuando un ítem se completa sin necesidad de registrar una sesión adicional.
        """
        try:
            item = Itemplandetratamiento.objects.get(
                id=item_id,
                idplantratamiento__empresa=request.tenant
            )
        except Itemplandetratamiento.DoesNotExist:
            return Response(
                {'error': 'Ítem no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validar que no esté ya completado o cancelado
        if item.esta_completado():
            return Response(
                {'error': 'El ítem ya está completado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if item.esta_cancelado():
            return Response(
                {'error': 'No se puede completar un ítem cancelado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Marcar como completado
        item.completar()
        
        # Registrar en bitácora
        usuario = getattr(request.user, 'usuario', None)
        notas = request.data.get('notas', '')
        
        Bitacora.objects.create(
            empresa=request.tenant,
            usuario=usuario,
            accion='COMPLETAR_ITEM_TRATAMIENTO',
            tabla_afectada='itemplandetratamiento',
            registro_id=item.id,
            valores_nuevos={'mensaje': f'Ítem {item.id} marcado como completado. Notas: {notas}'},
            ip_address=request.META.get('REMOTE_ADDR', '0.0.0.0'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'message': 'Ítem marcado como completado exitosamente',
            'item_id': item.id,
            'estado_item': item.estado_item
        })
    
    @action(detail=False, methods=['get'], url_path='por-paciente/(?P<paciente_id>[0-9]+)')
    def sesiones_por_paciente(self, request, paciente_id=None):
        """
        Listar todas las sesiones de tratamiento de un paciente.
        
        GET /api/sesiones-tratamiento/por-paciente/789/
        
        Parámetros opcionales:
        - fecha_desde: Filtrar desde fecha (YYYY-MM-DD)
        - fecha_hasta: Filtrar hasta fecha (YYYY-MM-DD)
        """
        sesiones = self.get_queryset().filter(
            item_plan__idplantratamiento__codpaciente_id=paciente_id
        )
        
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        
        if fecha_desde:
            sesiones = sesiones.filter(fecha_sesion__gte=fecha_desde)
        if fecha_hasta:
            sesiones = sesiones.filter(fecha_sesion__lte=fecha_hasta)
        
        page = self.paginate_queryset(sesiones)
        if page is not None:
            serializer = SesionTratamientoListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = SesionTratamientoListSerializer(sesiones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='por-plan/(?P<plan_id>[0-9]+)')
    def sesiones_por_plan(self, request, plan_id=None):
        """
        Listar todas las sesiones de un plan de tratamiento.
        
        GET /api/sesiones-tratamiento/por-plan/456/
        
        Agrupa las sesiones por ítem y muestra estadísticas.
        """
        try:
            plan = Plandetratamiento.objects.get(id=plan_id, empresa=request.tenant)
        except Plandetratamiento.DoesNotExist:
            return Response(
                {'error': 'Plan no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        sesiones = self.get_queryset().filter(item_plan__idplantratamiento=plan)
        
        # Agrupar por ítem
        items = plan.itemplandetratamiento_set.all()
        resultado = []
        
        for item in items:
            sesiones_item = sesiones.filter(item_plan=item)
            ultima_sesion = sesiones_item.order_by('-fecha_sesion').first()
            
            resultado.append({
                'item_id': item.id,
                'servicio': item.idservicio.nombre,
                'estado_item': item.estado_item,
                'total_sesiones': sesiones_item.count(),
                'progreso_actual': float(ultima_sesion.progreso_actual) if ultima_sesion else 0,
                'ultima_sesion_fecha': ultima_sesion.fecha_sesion if ultima_sesion else None,
                'sesiones': SesionTratamientoListSerializer(sesiones_item, many=True).data
            })
        
        return Response({
            'plan_id': plan.id,
            'items': resultado
        })
    
    @action(detail=False, methods=['get'], url_path='estadisticas-odontologo')
    def estadisticas_odontologo(self, request):
        """
        Estadísticas de sesiones registradas por el odontólogo autenticado.
        
        GET /api/sesiones-tratamiento/estadisticas-odontologo/
        
        Parámetros opcionales:
        - fecha_desde, fecha_hasta: Rango de fechas
        
        Retorna:
        - total_sesiones: Total de sesiones registradas
        - total_pacientes: Pacientes únicos atendidos
        - duracion_promedio: Duración promedio de sesiones (minutos)
        - progreso_promedio: Progreso promedio aplicado por sesión
        - sesiones_por_mes: Distribución mensual
        """
        usuario = getattr(request.user, 'usuario', None)
        if not usuario:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sesiones = self.get_queryset().filter(usuario_registro=usuario)
        
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        
        if fecha_desde:
            sesiones = sesiones.filter(fecha_sesion__gte=fecha_desde)
        if fecha_hasta:
            sesiones = sesiones.filter(fecha_sesion__lte=fecha_hasta)
        
        # Estadísticas
        total_sesiones = sesiones.count()
        pacientes_unicos = sesiones.values('item_plan__idplantratamiento__codpaciente').distinct().count()
        
        estadisticas_agregadas = sesiones.aggregate(
            duracion_promedio=Avg('duracion_minutos'),
            duracion_total=Sum('duracion_minutos'),
        )
        
        # Calcular progreso promedio
        incrementos = [s.get_incremento_progreso() for s in sesiones]
        progreso_promedio = sum(incrementos) / len(incrementos) if incrementos else 0
        
        return Response({
            'total_sesiones': total_sesiones,
            'total_pacientes': pacientes_unicos,
            'duracion_promedio_minutos': round(estadisticas_agregadas['duracion_promedio'] or 0, 2),
            'duracion_total_minutos': estadisticas_agregadas['duracion_total'] or 0,
            'progreso_promedio_incremento': round(progreso_promedio, 2),
            'periodo': {
                'desde': fecha_desde,
                'hasta': fecha_hasta
            }
        })
