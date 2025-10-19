# api/views_presupuestos.py
"""
Views para la funcionalidad de aceptación de presupuestos/planes de tratamiento.
SP3-T003: Implementar Aceptar presupuesto por parte del paciente (web)
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
import json

from .models import (
    Plandetratamiento,
    Itemplandetratamiento,
    AceptacionPresupuesto,
    Paciente,
    Bitacora,
)
from .serializers_presupuestos import (
    PlandetratamientoListSerializer,
    PlandetratamientoDetailSerializer,
    AceptarPresupuestoSerializer,
    AceptacionPresupuestoDetailSerializer,
    VerificarComprobanteSerializer,
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


class PresupuestoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar presupuestos/planes de tratamiento.
    
    El paciente autenticado solo puede ver sus propios presupuestos.
    Los odontólogos y administradores pueden ver todos los presupuestos de su empresa.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtra presupuestos según el usuario y empresa."""
        user = self.request.user
        empresa = self.request.tenant
        
        # Obtener el usuario asociado
        usuario = getattr(user, 'usuario', None)
        if not usuario:
            return Plandetratamiento.objects.none()
        
        # Filtro base por empresa
        queryset = Plandetratamiento.objects.filter(empresa=empresa).select_related(
            'codpaciente__codusuario',
            'cododontologo__codusuario',
            'idestado',
            'usuario_acepta'
        ).prefetch_related('itemplandetratamiento_set', 'aceptaciones')
        
        # Si es paciente, solo sus presupuestos
        try:
            paciente = Paciente.objects.get(codusuario=usuario, empresa=empresa)
            queryset = queryset.filter(codpaciente=paciente)
        except Paciente.DoesNotExist:
            # Si no es paciente, puede ver todos (odontólogo, admin, etc.)
            pass
        
        return queryset.order_by('-fechaplan')
    
    def get_serializer_class(self):
        """Usa serializer detallado para retrieve."""
        if self.action == 'retrieve':
            return PlandetratamientoDetailSerializer
        return PlandetratamientoListSerializer
    
    @action(detail=True, methods=['post'], url_path='aceptar')
    @transaction.atomic
    def aceptar_presupuesto(self, request, pk=None):
        """
        Endpoint para aceptar un presupuesto.
        
        POST /api/presupuestos/{id}/aceptar/
        
        Payload:
        {
            "tipo_aceptacion": "Total" | "Parcial",
            "items_aceptados": [1, 2, 3],  # Opcional si Total
            "firma_digital": {
                "timestamp": "2025-10-19T10:30:00Z",
                "user_id": 123,
                "signature_hash": "abc123..."
            },
            "notas": "Comentarios opcionales"
        }
        
        Responses:
        - 200: Presupuesto aceptado exitosamente
        - 400: Datos inválidos o presupuesto no puede ser aceptado
        - 403: Usuario no autorizado
        - 404: Presupuesto no encontrado
        """
        # Obtener el presupuesto
        presupuesto = self.get_object()
        
        # Validar payload
        serializer = AceptarPresupuestoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        tipo_aceptacion = data['tipo_aceptacion']
        items_aceptados = data.get('items_aceptados', [])
        firma_digital = data['firma_digital']
        notas = data.get('notas', '')
        
        # Obtener usuario actual
        usuario = getattr(request.user, 'usuario', None)
        if not usuario:
            return Response(
                {'error': 'Usuario no encontrado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # **VALIDACIÓN 1: Verificar que el usuario es el paciente del presupuesto**
        try:
            paciente = Paciente.objects.get(
                codusuario=usuario,
                empresa=request.tenant
            )
            if presupuesto.codpaciente.id != paciente.id:
                return Response(
                    {
                        'error': 'No autorizado.',
                        'detalle': 'Solo el paciente del presupuesto puede aceptarlo.'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
        except Paciente.DoesNotExist:
            return Response(
                {
                    'error': 'Usuario no es paciente.',
                    'detalle': 'Solo pacientes pueden aceptar presupuestos.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # **VALIDACIÓN 2: Verificar que el presupuesto no está caducado**
        if presupuesto.esta_caducado():
            return Response(
                {
                    'error': 'Presupuesto caducado.',
                    'detalle': f'El presupuesto venció el {presupuesto.fecha_vigencia}.',
                    'fecha_vigencia': presupuesto.fecha_vigencia
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # **VALIDACIÓN 3: Verificar que no ha sido aceptado previamente**
        if presupuesto.estado_aceptacion == Plandetratamiento.ESTADO_ACEPTADO:
            return Response(
                {
                    'error': 'Presupuesto ya aceptado.',
                    'detalle': f'Este presupuesto fue aceptado el {presupuesto.fecha_aceptacion}.',
                    'fecha_aceptacion': presupuesto.fecha_aceptacion
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if presupuesto.estado_aceptacion == Plandetratamiento.ESTADO_RECHAZADO:
            return Response(
                {
                    'error': 'Presupuesto rechazado.',
                    'detalle': 'Este presupuesto fue rechazado previamente.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # **VALIDACIÓN 4: Si es aceptación parcial, validar items**
        if tipo_aceptacion == 'Parcial':
            # Verificar que todos los items existen y pertenecen al presupuesto
            items_presupuesto = presupuesto.itemplandetratamiento_set.all()
            items_ids_validos = set(items_presupuesto.values_list('id', flat=True))
            items_a_aceptar = set(items_aceptados)
            
            items_invalidos = items_a_aceptar - items_ids_validos
            if items_invalidos:
                return Response(
                    {
                        'error': 'Items inválidos.',
                        'detalle': f'Los siguientes items no pertenecen al presupuesto: {list(items_invalidos)}',
                        'items_invalidos': list(items_invalidos)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not items_a_aceptar:
                return Response(
                    {
                        'error': 'Items requeridos.',
                        'detalle': 'Debe especificar al menos un ítem para aceptación parcial.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # **PROCESAMIENTO: Actualizar presupuesto**
        presupuesto.estado_aceptacion = (
            Plandetratamiento.ESTADO_ACEPTADO if tipo_aceptacion == 'Total'
            else Plandetratamiento.ESTADO_PARCIAL
        )
        presupuesto.aceptacion_tipo = tipo_aceptacion
        presupuesto.fecha_aceptacion = timezone.now()
        presupuesto.usuario_acepta = usuario
        presupuesto.es_editable = False  # Bloquear edición
        presupuesto.firma_digital = json.dumps(firma_digital)
        presupuesto.save()
        
        # **PROCESAMIENTO: Crear registro de aceptación (auditoría)**
        aceptacion = AceptacionPresupuesto.objects.create(
            plandetratamiento=presupuesto,
            usuario_paciente=usuario,
            empresa=request.tenant,
            tipo_aceptacion=tipo_aceptacion,
            items_aceptados=items_aceptados if tipo_aceptacion == 'Parcial' else [],
            firma_digital=firma_digital,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            monto_total_aceptado=presupuesto.montototal or 0,
            notas=notas
        )
        
        # **AUDITORÍA: Registrar en bitácora**
        Bitacora.objects.create(
            empresa=request.tenant,
            usuario=usuario,
            accion='ACEPTACION_PRESUPUESTO',
            tabla_afectada='plandetratamiento',
            detalles=json.dumps({
                'presupuesto_id': presupuesto.id,
                'tipo_aceptacion': tipo_aceptacion,
                'items_aceptados': items_aceptados,
                'fecha_aceptacion': presupuesto.fecha_aceptacion.isoformat(),
                'comprobante_id': str(aceptacion.comprobante_id),
                'monto_total': str(presupuesto.montototal or 0),
                'ip_address': aceptacion.ip_address,
            })
        )
        
        # TODO: Enviar notificaciones (implementar en signals)
        # TODO: Generar PDF de comprobante
        
        # Respuesta exitosa
        response_data = {
            'success': True,
            'mensaje': f'Presupuesto aceptado exitosamente ({tipo_aceptacion.lower()}).',
            'presupuesto': PlandetratamientoDetailSerializer(presupuesto).data,
            'aceptacion': {
                'comprobante_id': str(aceptacion.comprobante_id),
                'fecha_aceptacion': aceptacion.fecha_aceptacion,
                'tipo': aceptacion.tipo_aceptacion,
                'url_verificacion': aceptacion.get_comprobante_verificacion_url(),
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='puede-aceptar')
    def puede_aceptar(self, request, pk=None):
        """
        Verifica si un presupuesto puede ser aceptado.
        
        GET /api/presupuestos/{id}/puede-aceptar/
        
        Retorna información sobre si el presupuesto puede ser aceptado y por qué.
        """
        presupuesto = self.get_object()
        
        # Verificar usuario
        usuario = getattr(request.user, 'usuario', None)
        if not usuario:
            return Response({
                'puede_aceptar': False,
                'razon': 'Usuario no encontrado.'
            })
        
        # Verificar si es el paciente
        try:
            paciente = Paciente.objects.get(codusuario=usuario, empresa=request.tenant)
            es_paciente_del_presupuesto = (presupuesto.codpaciente.id == paciente.id)
        except Paciente.DoesNotExist:
            es_paciente_del_presupuesto = False
        
        # Verificar condiciones
        razones = []
        if not es_paciente_del_presupuesto:
            razones.append('No eres el paciente de este presupuesto.')
        if presupuesto.esta_caducado():
            razones.append(f'El presupuesto caducó el {presupuesto.fecha_vigencia}.')
        if presupuesto.estado_aceptacion == Plandetratamiento.ESTADO_ACEPTADO:
            razones.append(f'Ya fue aceptado el {presupuesto.fecha_aceptacion}.')
        if presupuesto.estado_aceptacion == Plandetratamiento.ESTADO_RECHAZADO:
            razones.append('El presupuesto fue rechazado.')
        
        puede_aceptar = len(razones) == 0
        
        return Response({
            'puede_aceptar': puede_aceptar,
            'razones': razones if not puede_aceptar else [],
            'estado_actual': presupuesto.estado_aceptacion,
            'esta_vigente': presupuesto.esta_vigente(),
            'fecha_vigencia': presupuesto.fecha_vigencia,
            'dias_restantes': (presupuesto.fecha_vigencia - timezone.now().date()).days if presupuesto.fecha_vigencia else None
        })
    
    @action(detail=True, methods=['get'], url_path='comprobantes')
    def listar_comprobantes(self, request, pk=None):
        """
        Lista los comprobantes de aceptación de un presupuesto.
        
        GET /api/presupuestos/{id}/comprobantes/
        """
        presupuesto = self.get_object()
        aceptaciones = presupuesto.aceptaciones.all()
        serializer = AceptacionPresupuestoDetailSerializer(aceptaciones, many=True)
        
        return Response({
            'presupuesto_id': presupuesto.id,
            'cantidad': aceptaciones.count(),
            'comprobantes': serializer.data
        })


class AceptacionPresupuestoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar aceptaciones de presupuestos (solo lectura).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AceptacionPresupuestoDetailSerializer
    
    def get_queryset(self):
        """Filtra aceptaciones según el usuario y empresa."""
        user = self.request.user
        empresa = self.request.tenant
        
        usuario = getattr(user, 'usuario', None)
        if not usuario:
            return AceptacionPresupuesto.objects.none()
        
        queryset = AceptacionPresupuesto.objects.filter(
            empresa=empresa
        ).select_related(
            'plandetratamiento',
            'usuario_paciente',
            'empresa'
        )
        
        # Si es paciente, solo sus aceptaciones
        try:
            paciente = Paciente.objects.get(codusuario=usuario, empresa=empresa)
            queryset = queryset.filter(
                plandetratamiento__codpaciente=paciente
            )
        except Paciente.DoesNotExist:
            # Si no es paciente, puede ver todas
            pass
        
        return queryset.order_by('-fecha_aceptacion')
    
    @action(detail=False, methods=['post'], url_path='verificar')
    def verificar_comprobante(self, request):
        """
        Verifica un comprobante de aceptación.
        
        POST /api/aceptaciones/verificar/
        
        Payload:
        {
            "comprobante_id": "uuid-here"
        }
        """
        serializer = VerificarComprobanteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        comprobante_id = serializer.validated_data['comprobante_id']
        
        try:
            aceptacion = AceptacionPresupuesto.objects.get(comprobante_id=comprobante_id)
            detail_serializer = AceptacionPresupuestoDetailSerializer(aceptacion)
            
            return Response({
                'valido': True,
                'comprobante': detail_serializer.data
            })
        except AceptacionPresupuesto.DoesNotExist:
            return Response({
                'valido': False,
                'mensaje': 'Comprobante no encontrado o inválido.'
            }, status=status.HTTP_404_NOT_FOUND)
