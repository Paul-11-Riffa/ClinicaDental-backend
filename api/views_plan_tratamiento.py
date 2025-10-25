# api/views_plan_tratamiento.py
"""
Views para la funcionalidad de gestión de planes de tratamiento.
SP3-T001: Crear plan de tratamiento (Web)
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

from .models import (
    Plandetratamiento,
    Itemplandetratamiento,
    Paciente,
    Odontologo,
    Usuario,
    Bitacora,
    Estado,
)
from .serializers_plan_tratamiento import (
    PlanTratamientoListSerializer,
    PlanTratamientoDetailSerializer,
    CrearPlanTratamientoSerializer,
    ActualizarPlanTratamientoSerializer,
    AprobarPlanSerializer,
    ItemPlanTratamientoSerializer,
    CrearItemPlanSerializer,
)


def get_client_ip(request):
    """Obtiene la IP del cliente desde el request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Obtiene el User Agent del cliente."""
    return request.META.get('HTTP_USER_AGENT', '')


class PlanTratamientoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión completa de planes de tratamiento.
    
    Funcionalidades (SP3-T001):
    - a) Crear plan seleccionando paciente y profesional; fecha y notas.
    - b) Agregar/editar/eliminar ítems con pieza, procedimiento, tiempo/costo, fecha objetivo y estado.
    - c) Validar consistencia y totales; cálculo de subtotal, descuentos y total.
    - d) Borrador editable; al aprobar, versión immutable.
    - e) Ítems activos habilitan agenda; cancelados no impactan el total.
    
    Permisos:
    - Odontólogos: Crear, editar (borrador), aprobar sus propios planes
    - Administradores: CRUD completo sobre todos los planes
    - Pacientes: Solo lectura de sus propios planes
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtra planes según el usuario y empresa."""
        user = self.request.user
        empresa = self.request.tenant
        
        # Obtener el usuario asociado
        usuario = getattr(user, 'usuario', None)
        if not usuario:
            try:
                usuario = Usuario.objects.get(correoelectronico__iexact=user.email)
            except Usuario.DoesNotExist:
                return Plandetratamiento.objects.none()
        
        # Filtro base por empresa
        queryset = Plandetratamiento.objects.filter(empresa=empresa).select_related(
            'codpaciente__codusuario',
            'cododontologo__codusuario',
            'idestado',
            'usuario_aprueba',
            'usuario_acepta'
        ).prefetch_related('itemplandetratamiento_set')
        
        # Si es paciente, solo sus planes
        try:
            paciente = Paciente.objects.get(codusuario=usuario, empresa=empresa)
            queryset = queryset.filter(codpaciente=paciente)
        except Paciente.DoesNotExist:
            # Si es odontólogo, solo sus planes (opcional, puede ver todos)
            try:
                odontologo = Odontologo.objects.get(codusuario=usuario, empresa=empresa)
                # Por ahora, odontólogos ven todos los planes de su empresa
                # queryset = queryset.filter(cododontologo=odontologo)
            except Odontologo.DoesNotExist:
                # Admin u otros roles: ven todos
                pass
        
        return queryset.order_by('-fechaplan', '-id')
    
    def get_serializer_class(self):
        """Usa serializer según la acción."""
        if self.action == 'retrieve':
            return PlanTratamientoDetailSerializer
        elif self.action == 'create':
            return CrearPlanTratamientoSerializer
        elif self.action in ['update', 'partial_update']:
            return ActualizarPlanTratamientoSerializer
        return PlanTratamientoListSerializer
    
    def create(self, request, *args, **kwargs):
        """Override create para agregar logging detallado."""
        logger.info(f"=== CREAR PLAN DE TRATAMIENTO ===")
        logger.info(f"Request data: {request.data}")
        logger.info(f"Tenant: {request.tenant}")
        logger.info(f"User: {request.user}")
        
        # Log detallado de items_iniciales
        if 'items_iniciales' in request.data:
            logger.info(f"Items iniciales ({len(request.data['items_iniciales'])} items):")
            for idx, item in enumerate(request.data['items_iniciales']):
                logger.info(f"  Item {idx}: {item}")
                logger.info(f"    - idservicio type: {type(item.get('idservicio'))}")
                logger.info(f"    - idservicio value: {item.get('idservicio')}")
        
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f"❌ Errores de validación: {serializer.errors}")
            logger.error(f"❌ Detalles completos: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        logger.info(f"✅ Plan creado exitosamente: ID {serializer.instance.id}")
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        """Asigna automáticamente la empresa del tenant al crear un plan."""
        serializer.save()
        
        # Registrar en bitácora
        plan = serializer.instance
        usuario = getattr(self.request.user, 'usuario', None)
        
        Bitacora.objects.create(
            empresa=self.request.tenant,
            usuario=usuario,
            accion='CREAR_PLAN_TRATAMIENTO',
            tabla_afectada='plandetratamiento',
            registro_id=plan.id,
            ip_address=get_client_ip(self.request),
            user_agent=get_user_agent(self.request),
            valores_nuevos={
                'plan_id': plan.id,
                'paciente': str(plan.codpaciente),
                'odontologo': str(plan.cododontologo),
                'estado_plan': plan.estado_plan,
            }
        )
    
    def perform_update(self, serializer):
        """Actualiza plan y registra en bitácora."""
        plan_anterior = self.get_object()
        valores_anteriores = {
            'notas_plan': plan_anterior.notas_plan,
            'descuento': str(plan_anterior.descuento or 0),
            'fecha_vigencia': str(plan_anterior.fecha_vigencia) if plan_anterior.fecha_vigencia else None,
        }
        
        serializer.save()
        
        # Registrar en bitácora
        usuario = getattr(self.request.user, 'usuario', None)
        
        Bitacora.objects.create(
            empresa=self.request.tenant,
            usuario=usuario,
            accion='ACTUALIZAR_PLAN_TRATAMIENTO',
            tabla_afectada='plandetratamiento',
            registro_id=plan_anterior.id,
            ip_address=get_client_ip(self.request),
            user_agent=get_user_agent(self.request),
            valores_anteriores=valores_anteriores,
            valores_nuevos={
                'notas_plan': serializer.instance.notas_plan,
                'descuento': str(serializer.instance.descuento or 0),
                'fecha_vigencia': str(serializer.instance.fecha_vigencia) if serializer.instance.fecha_vigencia else None,
            }
        )
    
    def perform_destroy(self, instance):
        """Elimina plan solo si está en borrador."""
        if not instance.es_borrador():
            raise PermissionError("Solo se pueden eliminar planes en estado borrador.")
        
        plan_id = instance.id
        
        # Registrar en bitácora antes de eliminar
        usuario = getattr(self.request.user, 'usuario', None)
        
        Bitacora.objects.create(
            empresa=self.request.tenant,
            usuario=usuario,
            accion='ELIMINAR_PLAN_TRATAMIENTO',
            tabla_afectada='plandetratamiento',
            registro_id=plan_id,
            ip_address=get_client_ip(self.request),
            user_agent=get_user_agent(self.request),
            valores_anteriores={
                'plan_id': plan_id,
                'paciente': str(instance.codpaciente),
                'estado_plan': instance.estado_plan,
            }
        )
        
        instance.delete()
    
    # ========================================================================
    # ACCIÓN: APROBAR PLAN (SP3-T001d)
    # ========================================================================
    
    @action(detail=True, methods=['post'], url_path='aprobar')
    @transaction.atomic
    def aprobar_plan(self, request, pk=None):
        """
        Aprueba un plan de tratamiento, convirtiéndolo en inmutable.
        
        POST /api/planes-tratamiento/{id}/aprobar/
        
        Payload:
        {
            "confirmar": true
        }
        
        Validaciones:
        - Plan debe estar en borrador
        - Debe tener al menos un ítem activo/pendiente
        - Solo odontólogo asignado o admin puede aprobar
        """
        plan = self.get_object()
        
        # Validar permisos (solo odontólogo asignado o admin)
        usuario = getattr(request.user, 'usuario', None)
        if not usuario:
            return Response(
                {'error': 'Usuario no encontrado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si es el odontólogo del plan o admin
        es_odontologo_del_plan = False
        try:
            odontologo = Odontologo.objects.get(codusuario=usuario)
            es_odontologo_del_plan = (plan.cododontologo.codusuario.codigo == odontologo.codusuario.codigo)
        except Odontologo.DoesNotExist:
            pass
        
        es_admin = usuario.idtipousuario and usuario.idtipousuario.rol.lower() == 'administrador'
        
        if not (es_odontologo_del_plan or es_admin):
            return Response(
                {
                    'error': 'No autorizado.',
                    'detalle': 'Solo el odontólogo asignado o un administrador puede aprobar el plan.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar con serializer
        serializer = AprobarPlanSerializer(
            data=request.data,
            context={'plan': plan}
        )
        serializer.is_valid(raise_exception=True)
        
        # Aprobar el plan
        try:
            plan.aprobar_plan(usuario)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Registrar en bitácora
        Bitacora.objects.create(
            empresa=request.tenant,
            usuario=usuario,
            accion='APROBAR_PLAN_TRATAMIENTO',
            tabla_afectada='plandetratamiento',
            registro_id=plan.id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            valores_nuevos={
                'plan_id': plan.id,
                'estado_plan': plan.estado_plan,
                'fecha_aprobacion': plan.fecha_aprobacion.isoformat() if plan.fecha_aprobacion else None,
                'usuario_aprueba': str(usuario),
            }
        )
        
        # Refrescar plan con relaciones
        plan.refresh_from_db()
        
        # Respuesta exitosa
        return Response({
            'success': True,
            'mensaje': 'Plan de tratamiento aprobado exitosamente.',
            'plan': PlanTratamientoDetailSerializer(plan).data
        }, status=status.HTTP_200_OK)
    
    # ========================================================================
    # ACCIÓN: CALCULAR TOTALES (SP3-T001c)
    # ========================================================================
    
    @action(detail=True, methods=['post'], url_path='calcular-totales')
    def calcular_totales(self, request, pk=None):
        """
        Recalcula subtotal y total del plan basándose en ítems activos.
        
        POST /api/planes-tratamiento/{id}/calcular-totales/
        
        Automático, no requiere payload.
        """
        plan = self.get_object()
        
        # Calcular totales
        resultado = plan.calcular_totales()
        
        return Response({
            'success': True,
            'mensaje': 'Totales recalculados exitosamente.',
            'totales': resultado
        }, status=status.HTTP_200_OK)
    
    # ========================================================================
    # ACCIÓN: AGREGAR ÍTEM (SP3-T001b)
    # ========================================================================
    
    @action(detail=True, methods=['post'], url_path='items')
    @transaction.atomic
    def agregar_item(self, request, pk=None):
        """
        Agrega un nuevo ítem al plan de tratamiento.
        
        POST /api/planes-tratamiento/{id}/items/
        
        Payload:
        {
            "idservicio": 1,
            "idpiezadental": 5,  // Opcional
            "idestado": 1,
            "costofinal": 150.00,  // Opcional, usa costo del servicio por defecto
            "fecha_objetivo": "2025-11-15",  // Opcional
            "tiempo_estimado": 60,  // Opcional, usa duración del servicio
            "notas_item": "Nota específica",  // Opcional
            "orden": 1  // Opcional
        }
        """
        plan = self.get_object()
        
        # Validar que el plan esté en borrador
        if not plan.puede_editarse():
            return Response(
                {
                    'error': 'Plan no editable.',
                    'detalle': 'Solo se pueden agregar ítems a planes en borrador.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear ítem
        serializer = CrearItemPlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        item = serializer.save(
            idplantratamiento=plan,
            empresa=request.tenant
        )
        
        # Recalcular totales del plan
        plan.calcular_totales()
        
        # Registrar en bitácora
        usuario = getattr(request.user, 'usuario', None)
        
        Bitacora.objects.create(
            empresa=request.tenant,
            usuario=usuario,
            accion='AGREGAR_ITEM_PLAN',
            tabla_afectada='itemplandetratamiento',
            registro_id=item.id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            valores_nuevos={
                'plan_id': plan.id,
                'item_id': item.id,
                'servicio': str(item.idservicio),
                'costofinal': str(item.costofinal),
            }
        )
        
        # Respuesta exitosa
        return Response({
            'success': True,
            'mensaje': 'Ítem agregado exitosamente.',
            'item': ItemPlanTratamientoSerializer(item).data,
            'totales': {
                'subtotal': str(plan.subtotal_calculado),
                'total': str(plan.montototal)
            }
        }, status=status.HTTP_201_CREATED)
    
    # ========================================================================
    # ACCIÓN: EDITAR ÍTEM (SP3-T001b)
    # ========================================================================
    
    @action(detail=True, methods=['patch'], url_path='items/(?P<item_id>[^/.]+)')
    @transaction.atomic
    def editar_item(self, request, pk=None, item_id=None):
        """
        Edita un ítem existente del plan.
        
        PATCH /api/planes-tratamiento/{id}/items/{item_id}/
        
        Payload (todos los campos son opcionales):
        {
            "costofinal": 200.00,
            "fecha_objetivo": "2025-12-01",
            "tiempo_estimado": 90,
            "notas_item": "Nota actualizada",
            "orden": 2
        }
        """
        plan = self.get_object()
        item = get_object_or_404(Itemplandetratamiento, id=item_id, idplantratamiento=plan)
        
        # Validar que el plan esté en borrador
        if not plan.puede_editarse():
            return Response(
                {
                    'error': 'Plan no editable.',
                    'detalle': 'Solo se pueden editar ítems de planes en borrador.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Guardar valores anteriores para bitácora
        valores_anteriores = {
            'costofinal': str(item.costofinal),
            'fecha_objetivo': str(item.fecha_objetivo) if item.fecha_objetivo else None,
            'tiempo_estimado': item.tiempo_estimado,
            'notas_item': item.notas_item,
            'orden': item.orden,
        }
        
        # Actualizar campos permitidos
        campos_permitidos = ['costofinal', 'fecha_objetivo', 'tiempo_estimado', 'notas_item', 'orden']
        
        for campo in campos_permitidos:
            if campo in request.data:
                setattr(item, campo, request.data[campo])
        
        item.save()
        
        # Recalcular totales si cambió el costo
        if 'costofinal' in request.data:
            plan.calcular_totales()
        
        # Registrar en bitácora
        usuario = getattr(request.user, 'usuario', None)
        
        Bitacora.objects.create(
            empresa=request.tenant,
            usuario=usuario,
            accion='EDITAR_ITEM_PLAN',
            tabla_afectada='itemplandetratamiento',
            registro_id=item.id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            valores_anteriores=valores_anteriores,
            valores_nuevos={
                'costofinal': str(item.costofinal),
                'fecha_objetivo': str(item.fecha_objetivo) if item.fecha_objetivo else None,
                'tiempo_estimado': item.tiempo_estimado,
            }
        )
        
        # Respuesta exitosa
        return Response({
            'success': True,
            'mensaje': 'Ítem actualizado exitosamente.',
            'item': ItemPlanTratamientoSerializer(item).data,
            'totales': {
                'subtotal': str(plan.subtotal_calculado),
                'total': str(plan.montototal)
            }
        }, status=status.HTTP_200_OK)
    
    # ========================================================================
    # ACCIÓN: ELIMINAR ÍTEM (SP3-T001b)
    # ========================================================================
    
    @action(detail=True, methods=['delete'], url_path='items/(?P<item_id>[^/.]+)/eliminar')
    @transaction.atomic
    def eliminar_item(self, request, pk=None, item_id=None):
        """
        Elimina un ítem del plan (solo si está en borrador).
        
        DELETE /api/planes-tratamiento/{id}/items/{item_id}/eliminar/
        """
        plan = self.get_object()
        item = get_object_or_404(Itemplandetratamiento, id=item_id, idplantratamiento=plan)
        
        # Validar que el plan esté en borrador
        if not plan.puede_editarse():
            return Response(
                {
                    'error': 'Plan no editable.',
                    'detalle': 'Solo se pueden eliminar ítems de planes en borrador.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        item_id_original = item.id
        item_info = {
            'servicio': str(item.idservicio),
            'costofinal': str(item.costofinal),
        }
        
        # Eliminar ítem
        item.delete()
        
        # Recalcular totales del plan
        plan.calcular_totales()
        
        # Registrar en bitácora
        usuario = getattr(request.user, 'usuario', None)
        
        Bitacora.objects.create(
            empresa=request.tenant,
            usuario=usuario,
            accion='ELIMINAR_ITEM_PLAN',
            tabla_afectada='itemplandetratamiento',
            registro_id=item_id_original,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            valores_anteriores=item_info
        )
        
        # Respuesta exitosa
        return Response({
            'success': True,
            'mensaje': 'Ítem eliminado exitosamente.',
            'totales': {
                'subtotal': str(plan.subtotal_calculado),
                'total': str(plan.montototal)
            }
        }, status=status.HTTP_200_OK)
    
    # ========================================================================
    # ACCIÓN: ACTIVAR/CANCELAR ÍTEM (SP3-T001e)
    # ========================================================================
    
    @action(detail=True, methods=['post'], url_path='items/(?P<item_id>[^/.]+)/activar')
    @transaction.atomic
    def activar_item(self, request, pk=None, item_id=None):
        """
        Activa un ítem (habilita para agenda y cálculo de totales).
        
        POST /api/planes-tratamiento/{id}/items/{item_id}/activar/
        """
        plan = self.get_object()
        item = get_object_or_404(Itemplandetratamiento, id=item_id, idplantratamiento=plan)
        
        try:
            item.activar()
            plan.calcular_totales()
            
            return Response({
                'success': True,
                'mensaje': 'Ítem activado exitosamente.',
                'item': ItemPlanTratamientoSerializer(item).data
            }, status=status.HTTP_200_OK)
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], url_path='items/(?P<item_id>[^/.]+)/cancelar')
    @transaction.atomic
    def cancelar_item(self, request, pk=None, item_id=None):
        """
        Cancela un ítem (no impacta total ni habilita agenda).
        
        POST /api/planes-tratamiento/{id}/items/{item_id}/cancelar/
        """
        plan = self.get_object()
        item = get_object_or_404(Itemplandetratamiento, id=item_id, idplantratamiento=plan)
        
        item.cancelar()
        
        return Response({
            'success': True,
            'mensaje': 'Ítem cancelado exitosamente. No impacta el total del plan.',
            'item': ItemPlanTratamientoSerializer(item).data,
            'totales': {
                'subtotal': str(plan.subtotal_calculado),
                'total': str(plan.montototal)
            }
        }, status=status.HTTP_200_OK)
