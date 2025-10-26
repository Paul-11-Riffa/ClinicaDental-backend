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
            # Intentar obtener usuario por email
            try:
                usuario = Usuario.objects.get(correoelectronico__iexact=request.user.email)
            except Usuario.DoesNotExist:
                return Response(
                    {
                        'error': 'Usuario no encontrado.',
                        'detalle': f'No existe usuario con email {request.user.email}'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Verificar si es el odontólogo del plan o admin
        es_odontologo_del_plan = False
        try:
            odontologo = Odontologo.objects.get(codusuario=usuario)
            # Comparar directamente los objetos Odontologo (más simple y seguro)
            es_odontologo_del_plan = (plan.cododontologo == odontologo)
        except Odontologo.DoesNotExist:
            pass
        
        # Verificar si es admin usando ID de tipo de usuario (más confiable que string)
        es_admin = usuario.idtipousuario and usuario.idtipousuario.id == 1
        
        # Logging para debugging (temporal)
        logger.info(f"=== APROBAR PLAN: Validación de permisos ===")
        logger.info(f"Plan ID: {plan.id}")
        logger.info(f"Usuario: {usuario.nombre} {usuario.apellido} (código: {usuario.codigo})")
        logger.info(f"Usuario.idtipousuario: {usuario.idtipousuario.id} ({usuario.idtipousuario.rol})")
        logger.info(f"Plan.cododontologo: {plan.cododontologo}")
        logger.info(f"es_odontologo_del_plan: {es_odontologo_del_plan}")
        logger.info(f"es_admin: {es_admin}")
        
        if not (es_odontologo_del_plan or es_admin):
            logger.warning(f"ACCESO DENEGADO: Usuario {usuario.codigo} intentó aprobar plan {plan.id}")
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
    # ACCIÓN: VALIDAR APROBACIÓN (Endpoint de diagnóstico)
    # ========================================================================
    
    @action(detail=True, methods=['get'], url_path='validar-aprobacion')
    def validar_aprobacion(self, request, pk=None):
        """
        Valida si un plan puede ser aprobado sin intentar aprobarlo.
        Útil para mostrar mensajes al usuario antes de aprobar.
        
        GET /api/planes-tratamiento/{id}/validar-aprobacion/
        
        Respuesta:
        {
            "puede_aprobar": true/false,
            "motivos": [...],
            "detalles": {
                "es_borrador": true/false,
                "items_activos": 5,
                "items_pendientes": 2,
                "items_totales": 10,
                "es_editable": true/false,
                "usuario_puede_aprobar": true/false
            }
        }
        """
        plan = self.get_object()
        usuario = getattr(request.user, 'usuario', None)
        
        # Fallback: intentar obtener usuario por email (igual que en aprobar_plan)
        if not usuario:
            try:
                usuario = Usuario.objects.get(correoelectronico__iexact=request.user.email)
            except Usuario.DoesNotExist:
                # Si no hay usuario, retornar que no puede aprobar
                return Response({
                    'puede_aprobar': False,
                    'motivos': ['Usuario no encontrado en el sistema.'],
                    'detalles': {
                        'error': 'No se pudo identificar al usuario',
                        'email': request.user.email
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Inicializar resultado
        motivos = []
        detalles = {
            'es_borrador': plan.es_borrador(),
            'items_totales': plan.itemplandetratamiento_set.count(),
            'items_activos': plan.itemplandetratamiento_set.filter(estado_item='Activo').count(),
            'items_pendientes': plan.itemplandetratamiento_set.filter(estado_item='Pendiente').count(),
            'items_cancelados': plan.itemplandetratamiento_set.filter(estado_item='Cancelado').count(),
            'items_completados': plan.itemplandetratamiento_set.filter(estado_item='Completado').count(),
            'es_editable': plan.es_editable,
            'estado_plan': plan.estado_plan,
        }
        
        # Validar permisos de usuario (MISMA LÓGICA que aprobar_plan)
        usuario_puede_aprobar = False
        es_odontologo_del_plan = False
        es_admin = False
        
        try:
            odontologo = Odontologo.objects.get(codusuario=usuario)
            # Comparar directamente los objetos Odontologo (igual que aprobar_plan)
            es_odontologo_del_plan = (plan.cododontologo == odontologo)
            usuario_puede_aprobar = es_odontologo_del_plan
        except Odontologo.DoesNotExist:
            pass
        
        # Verificar si es admin usando ID (más confiable que string)
        es_admin = usuario.idtipousuario and usuario.idtipousuario.id == 1
        if es_admin:
            usuario_puede_aprobar = True
        
        # Agregar info de debugging
        detalles['usuario_puede_aprobar'] = usuario_puede_aprobar
        detalles['debug'] = {
            'usuario_codigo': usuario.codigo,
            'usuario_tipo_id': usuario.idtipousuario.id,
            'usuario_tipo_rol': usuario.idtipousuario.rol,
            'plan_odontologo_id': plan.cododontologo.codusuario.codigo if plan.cododontologo else None,
            'es_odontologo_del_plan': es_odontologo_del_plan,
            'es_admin': es_admin,
        }
        
        # Validaciones
        if not plan.es_borrador():
            motivos.append(f"El plan ya está en estado '{plan.estado_plan}', solo se pueden aprobar planes en borrador.")
        
        items_activos_o_pendientes = detalles['items_activos'] + detalles['items_pendientes']
        if items_activos_o_pendientes == 0:
            motivos.append("El plan debe tener al menos un ítem activo o pendiente para ser aprobado.")
        
        if not usuario_puede_aprobar:
            motivos.append("Solo el odontólogo asignado al plan o un administrador puede aprobarlo.")
        
        puede_aprobar = len(motivos) == 0
        
        return Response({
            'puede_aprobar': puede_aprobar,
            'motivos': motivos,
            'detalles': detalles,
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
        
        # Validar items duplicados (mismo servicio + pieza dental)
        servicio_id = serializer.validated_data.get('idservicio').id
        pieza_id = serializer.validated_data.get('idpiezadental')
        pieza_id = pieza_id.id if pieza_id else None
        
        existe_duplicado = Itemplandetratamiento.objects.filter(
            idplantratamiento=plan,
            idservicio_id=servicio_id,
            idpiezadental_id=pieza_id,
            estado_item__in=['Pendiente', 'Activo']
        ).exists()
        
        if existe_duplicado:
            return Response(
                {
                    'error': 'Ítem duplicado.',
                    'detalle': 'Ya existe un ítem activo/pendiente con este servicio y pieza dental. Considere editarlo en lugar de crear uno nuevo.',
                    'advertencia': True  # Flag para que el frontend pueda mostrar diálogo de confirmación
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
        
        # Registrar en bitácora
        usuario = getattr(request.user, 'usuario', None)
        
        Bitacora.objects.create(
            empresa=request.tenant,
            usuario=usuario,
            accion='CANCELAR_ITEM_PLAN',
            tabla_afectada='itemplandetratamiento',
            registro_id=item.id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            valores_nuevos={
                'plan_id': plan.id,
                'item_id': item.id,
                'estado_item': item.estado_item,
            }
        )
        
        return Response({
            'success': True,
            'mensaje': 'Ítem cancelado exitosamente. No impacta el total del plan.',
            'item': ItemPlanTratamientoSerializer(item).data,
            'totales': {
                'subtotal': str(plan.subtotal_calculado),
                'total': str(plan.montototal)
            }
        }, status=status.HTTP_200_OK)
    
    # ========================================================================
    # ACCIÓN: ESTADÍSTICAS POR PACIENTE (Mejora UX)
    # ========================================================================
    
    @action(detail=False, methods=['get'], url_path='estadisticas-paciente/(?P<paciente_id>[^/.]+)')
    def estadisticas_paciente(self, request, paciente_id=None):
        """
        Retorna estadísticas agregadas de todos los planes de un paciente.
        
        GET /api/planes-tratamiento/estadisticas-paciente/{paciente_id}/
        
        Response:
        {
            "paciente": {...},
            "estadisticas": {
                "total_planes": 3,
                "planes_borrador": 1,
                "planes_aprobados": 2,
                "total_invertido": "4500.00",
                "items_completados": 8,
                "items_pendientes": 3,
                "progreso_global": 72.7
            },
            "planes": [...]
        }
        """
        # Validar paciente
        try:
            paciente = Paciente.objects.get(
                codusuario__codigo=paciente_id,
                empresa=request.tenant
            )
        except Paciente.DoesNotExist:
            return Response(
                {'error': 'Paciente no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener todos los planes del paciente
        planes = Plandetratamiento.objects.filter(
            codpaciente=paciente,
            empresa=request.tenant
        ).prefetch_related('itemplandetratamiento_set')
        
        # Calcular estadísticas
        total_planes = planes.count()
        planes_borrador = planes.filter(estado_plan=Plandetratamiento.ESTADO_PLAN_BORRADOR).count()
        planes_aprobados = planes.filter(estado_plan=Plandetratamiento.ESTADO_PLAN_APROBADO).count()
        planes_cancelados = planes.filter(estado_plan=Plandetratamiento.ESTADO_PLAN_CANCELADO).count()
        
        total_invertido = sum(
            float(plan.montototal or 0) 
            for plan in planes.filter(estado_plan=Plandetratamiento.ESTADO_PLAN_APROBADO)
        )
        
        # Estadísticas de ítems
        items_completados = 0
        items_pendientes = 0
        items_activos = 0
        items_total = 0
        
        for plan in planes:
            items = plan.itemplandetratamiento_set.all()
            items_total += items.count()
            items_completados += items.filter(estado_item='Completado').count()
            items_pendientes += items.filter(estado_item='Pendiente').count()
            items_activos += items.filter(estado_item='Activo').count()
        
        # Progreso global (% de items completados sobre items no cancelados)
        items_no_cancelados = items_total - sum(
            plan.itemplandetratamiento_set.filter(estado_item='Cancelado').count()
            for plan in planes
        )
        progreso_global = (
            round((items_completados / items_no_cancelados) * 100, 1) 
            if items_no_cancelados > 0 else 0
        )
        
        # Datos de los planes
        planes_data = []
        for plan in planes.order_by('-fechaplan'):
            items = plan.itemplandetratamiento_set.exclude(estado_item='Cancelado')
            completados = items.filter(estado_item='Completado').count()
            total = items.count()
            progreso = round((completados / total) * 100, 1) if total > 0 else 0
            
            planes_data.append({
                'id': plan.id,
                'fechaplan': plan.fechaplan,
                'estado_plan': plan.estado_plan,
                'montototal': str(plan.montototal or 0),
                'cantidad_items': total,
                'items_completados': completados,
                'progreso_porcentaje': progreso,
                'fecha_aprobacion': plan.fecha_aprobacion.isoformat() if plan.fecha_aprobacion else None,
            })
        
        # Respuesta
        return Response({
            'paciente': {
                'id': paciente.codusuario.codigo,
                'nombre': paciente.codusuario.nombre,
                'apellido': paciente.codusuario.apellido,
                'email': paciente.codusuario.correoelectronico,
            },
            'estadisticas': {
                'total_planes': total_planes,
                'planes_borrador': planes_borrador,
                'planes_aprobados': planes_aprobados,
                'planes_cancelados': planes_cancelados,
                'total_invertido': f"{total_invertido:.2f}",
                'items_completados': items_completados,
                'items_pendientes': items_pendientes,
                'items_activos': items_activos,
                'items_total': items_total,
                'progreso_global': progreso_global,
            },
            'planes': planes_data
        })
    
    # ========================================================================
    # ACCIÓN: CLONAR PLAN (Mejora UX)
    # ========================================================================
    
    @action(detail=True, methods=['post'], url_path='clonar')
    @transaction.atomic
    def clonar_plan(self, request, pk=None):
        """
        Clona un plan de tratamiento existente para reutilizar su estructura.
        
        POST /api/planes-tratamiento/{id}/clonar/
        
        Payload:
        {
            "codpaciente": 10,  // Nuevo paciente (o el mismo)
            "cododontologo": 3, // Nuevo odontólogo (opcional, usa el original)
            "clonar_items": true, // Si se copian los ítems (default: true)
            "notas_adicionales": "Plan clonado del plan #{id_original}"
        }
        
        Response:
        {
            "success": true,
            "mensaje": "Plan clonado exitosamente",
            "plan_original_id": 5,
            "plan_nuevo": {
                "id": 15,
                "estado_plan": "Borrador",
                "cantidad_items": 5,
                ...
            }
        }
        """
        plan_original = self.get_object()
        
        # Validar permisos
        usuario = getattr(request.user, 'usuario', None)
        if not usuario:
            return Response(
                {'error': 'Usuario no encontrado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener datos del payload
        codpaciente_id = request.data.get('codpaciente')
        cododontologo_id = request.data.get('cododontologo', plan_original.cododontologo.codusuario.codigo)
        clonar_items = request.data.get('clonar_items', True)
        notas_adicionales = request.data.get('notas_adicionales', '')
        
        # Validar paciente y odontólogo
        try:
            paciente = Paciente.objects.get(codusuario__codigo=codpaciente_id, empresa=request.tenant)
            odontologo = Odontologo.objects.get(codusuario__codigo=cododontologo_id, empresa=request.tenant)
        except (Paciente.DoesNotExist, Odontologo.DoesNotExist):
            return Response(
                {'error': 'Paciente u odontólogo no encontrado o no pertenece a esta empresa.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear nuevo plan (clon)
        plan_nuevo = Plandetratamiento.objects.create(
            codpaciente=paciente,
            cododontologo=odontologo,
            empresa=request.tenant,
            idestado=plan_original.idestado,
            fechaplan=timezone.now().date(),
            estado_plan=Plandetratamiento.ESTADO_PLAN_BORRADOR,
            descuento=plan_original.descuento or 0,
            notas_plan=f"{plan_original.notas_plan or ''}\n\n{notas_adicionales}".strip(),
            fecha_vigencia=plan_original.fecha_vigencia,
            version=1,  # Nuevo plan independiente
            montototal=0,
            subtotal_calculado=0,
        )
        
        # Clonar ítems si se solicita
        items_clonados = 0
        if clonar_items:
            items_originales = plan_original.itemplandetratamiento_set.exclude(
                estado_item__in=['Cancelado', 'cancelado']
            )
            
            for item_orig in items_originales:
                Itemplandetratamiento.objects.create(
                    idplantratamiento=plan_nuevo,
                    idservicio=item_orig.idservicio,
                    idpiezadental=item_orig.idpiezadental,
                    idestado=item_orig.idestado,
                    empresa=request.tenant,
                    costofinal=item_orig.costofinal,
                    costo_base_servicio=item_orig.costo_base_servicio,
                    fecha_objetivo=None,  # Resetear fecha
                    tiempo_estimado=item_orig.tiempo_estimado,
                    estado_item=Itemplandetratamiento.ESTADO_PENDIENTE,  # Resetear a pendiente
                    notas_item=item_orig.notas_item,
                    orden=item_orig.orden,
                )
                items_clonados += 1
            
            # Recalcular totales
            plan_nuevo.calcular_totales()
        
        # Registrar en bitácora
        Bitacora.objects.create(
            empresa=request.tenant,
            usuario=usuario,
            accion='CLONAR_PLAN_TRATAMIENTO',
            tabla_afectada='plandetratamiento',
            registro_id=plan_nuevo.id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            valores_nuevos={
                'plan_original_id': plan_original.id,
                'plan_nuevo_id': plan_nuevo.id,
                'items_clonados': items_clonados,
                'paciente_nuevo': str(paciente.codusuario),
            }
        )
        
        # Respuesta exitosa
        return Response({
            'success': True,
            'mensaje': f'Plan clonado exitosamente. {items_clonados} ítems copiados.',
            'plan_original_id': plan_original.id,
            'plan_nuevo': PlanTratamientoDetailSerializer(plan_nuevo, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)
    
    # ========================================================================
    # ACCIÓN: COMPLETAR ÍTEM (SP3-T001e)
    # ========================================================================
    
    @action(detail=True, methods=['post'], url_path='items/(?P<item_id>[^/.]+)/completar')
    @transaction.atomic
    def completar_item(self, request, pk=None, item_id=None):
        """
        Marca un ítem como completado (tratamiento finalizado).
        
        POST /api/planes-tratamiento/{id}/items/{item_id}/completar/
        
        Validaciones:
        - El item debe estar activo (no cancelado)
        - El plan puede estar aprobado o en borrador
        
        Response:
        {
            "success": true,
            "mensaje": "Ítem completado exitosamente.",
            "item": {...}
        }
        """
        plan = self.get_object()
        item = get_object_or_404(Itemplandetratamiento, id=item_id, idplantratamiento=plan)
        
        try:
            # Completar el ítem
            item.completar()
            
            # Registrar en bitácora
            usuario = getattr(request.user, 'usuario', None)
            
            Bitacora.objects.create(
                empresa=request.tenant,
                usuario=usuario,
                accion='COMPLETAR_ITEM_PLAN',
                tabla_afectada='itemplandetratamiento',
                registro_id=item.id,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                valores_nuevos={
                    'plan_id': plan.id,
                    'item_id': item.id,
                    'servicio': str(item.idservicio),
                    'estado_item': item.estado_item,
                }
            )
            
            return Response({
                'success': True,
                'mensaje': 'Ítem completado exitosamente.',
                'item': ItemPlanTratamientoSerializer(item).data
            }, status=status.HTTP_200_OK)
        
        except ValueError as e:
            return Response(
                {
                    'error': str(e),
                    'detalle': 'Solo items activos pueden marcarse como completados.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
