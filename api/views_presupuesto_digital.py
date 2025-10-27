# api/views_presupuesto_digital.py
"""
Views para la funcionalidad de generación de presupuestos digitales.
SP3-T002: Generar presupuesto digital (web)
SP3-T003: Aceptar presupuesto digital por paciente

Permite emitir un presupuesto total o por tramos a partir de un plan aprobado.
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

# Configurar logger
logger = logging.getLogger(__name__)

# SP3-T003 Fase 6: Permissions y throttling personalizados
from .permissions_presupuesto import (
    IsPacienteDelPresupuesto,
    IsTenantMatch,
    IsOdontologoDelPresupuesto,
    CanViewPresupuesto,
    AceptacionPresupuestoRateThrottle,
    PresupuestoListRateThrottle,
)

from .models import (
    PresupuestoDigital,
    ItemPresupuestoDigital,
    Plandetratamiento,
    Bitacora,
    AceptacionPresupuestoDigital,
    Usuario,
)
from .serializers_presupuesto_digital import (
    ListarPresupuestosSerializer,
    DetallePresupuestoSerializer,
    CrearPresupuestoSerializer,
    EmitirPresupuestoSerializer,
    ActualizarPresupuestoSerializer,
    PresupuestoDigitalParaPacienteSerializer,
    AceptarPresupuestoDigitalSerializer,
    AceptacionPresupuestoDigitalSerializer,
)



class PresupuestoDigitalViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar presupuestos digitales.
    
    Endpoints disponibles:
    - GET /api/presupuestos-digitales/ - Listar presupuestos
    - POST /api/presupuestos-digitales/ - Crear presupuesto desde plan aprobado
    - GET /api/presupuestos-digitales/{id}/ - Ver detalle de presupuesto
    - PUT/PATCH /api/presupuestos-digitales/{id}/ - Actualizar presupuesto borrador
    - DELETE /api/presupuestos-digitales/{id}/ - Eliminar presupuesto borrador
    - POST /api/presupuestos-digitales/{id}/emitir/ - Emitir presupuesto oficialmente
    - GET /api/presupuestos-digitales/{id}/vigencia/ - Verificar vigencia
    - POST /api/presupuestos-digitales/{id}/generar-pdf/ - Generar PDF del presupuesto
    - GET /api/presupuestos-digitales/planes-disponibles/ - Listar planes aprobados sin presupuesto
    """
    permission_classes = [AllowAny]  # Por defecto AllowAny, se sobrescribe en get_permissions()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'es_tramo', 'plan_tratamiento']
    search_fields = ['codigo_presupuesto', 'notas', 'terminos_condiciones']
    ordering_fields = ['fecha_emision', 'fecha_vigencia', 'total']
    ordering = ['-fecha_emision']
    
    def get_permissions(self):
        """
        Configura permisos según la acción.
        
        - retrieve (ver detalle): Requiere autenticación + CanViewPresupuesto
        - list: AllowAny por ahora (TODO: cambiar a IsAuthenticated)
        - create, update, partial_update, destroy: IsAuthenticated
        - Acciones personalizadas: Cada una define sus propios permisos
        """
        if self.action == 'retrieve':
            # Ver detalle de presupuesto: Solo paciente, odontólogo o admin
            return [IsAuthenticated(), CanViewPresupuesto(), IsTenantMatch()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsTenantMatch()]
        else:
            # Para list y otras acciones no especificadas
            return [AllowAny()]

    
    def get_queryset(self):
        """Filtra presupuestos por empresa del tenant."""
        empresa = self.request.tenant
        
        return PresupuestoDigital.objects.filter(
            empresa=empresa
        ).select_related(
            'plan_tratamiento__codpaciente__codusuario',
            'plan_tratamiento__cododontologo__codusuario',
            'usuario_emite',
        ).prefetch_related(
            'items_presupuesto__item_plan__idservicio',
            'items_presupuesto__item_plan__idpiezadental',
        ).order_by(self.ordering[0])
    
    def get_serializer_class(self):
        """Selecciona el serializer según la acción."""
        if self.action == 'create':
            return CrearPresupuestoSerializer
        elif self.action == 'retrieve':
            return DetallePresupuestoSerializer
        elif self.action in ['update', 'partial_update']:
            return ActualizarPresupuestoSerializer
        elif self.action == 'emitir':
            return EmitirPresupuestoSerializer
        return ListarPresupuestosSerializer
    
    @transaction.atomic
    def perform_destroy(self, instance):
        """Solo permite eliminar presupuestos en borrador."""
        if instance.estado != PresupuestoDigital.ESTADO_BORRADOR:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Solo se pueden eliminar presupuestos en estado borrador.")
        
        # Bitácora
        usuario = getattr(self.request.user, 'usuario', None)
        Bitacora.objects.create(
            empresa=self.request.tenant,
            usuario=usuario,
            accion="PRESUPUESTO_DIGITAL_ELIMINADO",
            tabla_afectada="presupuesto_digital",
            registro_id=instance.id,
            valores_anteriores={
                'codigo_presupuesto': instance.codigo_presupuesto.hex[:8],
                'estado': instance.estado
            },
            ip_address='127.0.0.1',
            user_agent='API'
        )
        
        instance.delete()
    
    @action(detail=True, methods=['post'], url_path='emitir')
    @transaction.atomic
    def emitir(self, request, pk=None):
        """
        Emite oficialmente un presupuesto digital.
        
        POST /api/presupuestos-digitales/{id}/emitir/
        
        Payload:
        {
            "confirmar": true
        }
        
        Response:
        {
            "mensaje": "Presupuesto emitido exitosamente",
            "presupuesto": {...}
        }
        """
        presupuesto = self.get_object()
        
        # Validar que esté en borrador
        if presupuesto.estado != PresupuestoDigital.ESTADO_BORRADOR:
            return Response(
                {"error": "Solo presupuestos en borrador pueden ser emitidos."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(presupuesto, data=request.data)
        serializer.is_valid(raise_exception=True)
        presupuesto = serializer.save()
        
        # Serializar respuesta
        response_serializer = DetallePresupuestoSerializer(presupuesto, context={'request': request})
        
        return Response({
            "mensaje": "Presupuesto emitido exitosamente",
            "presupuesto": response_serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='vigencia')
    def verificar_vigencia(self, request, pk=None):
        """
        Verifica la vigencia del presupuesto.
        
        GET /api/presupuestos-digitales/{id}/vigencia/
        
        Response:
        {
            "esta_vigente": true,
            "fecha_vigencia": "2025-11-25",
            "dias_restantes": 30,
            "mensaje": "El presupuesto está vigente"
        }
        """
        presupuesto = self.get_object()
        
        # Marcar como caducado si corresponde
        presupuesto.marcar_caducado()
        presupuesto.refresh_from_db()
        
        dias_restantes = None
        if presupuesto.fecha_vigencia:
            delta = presupuesto.fecha_vigencia - timezone.now().date()
            dias_restantes = delta.days
        
        esta_vigente = presupuesto.esta_vigente()
        
        if esta_vigente:
            mensaje = f"El presupuesto está vigente. Vence en {dias_restantes} días."
        else:
            mensaje = "El presupuesto ha caducado."
        
        return Response({
            "esta_vigente": esta_vigente,
            "fecha_vigencia": presupuesto.fecha_vigencia,
            "dias_restantes": dias_restantes,
            "estado": presupuesto.estado,
            "mensaje": mensaje
        })
    
    @action(detail=True, methods=['post'], url_path='generar-pdf')
    @transaction.atomic
    def generar_pdf(self, request, pk=None):
        """
        Genera y descarga el PDF del presupuesto.
        
        POST /api/presupuestos-digitales/{id}/generar-pdf/
        
        Retorna: Archivo PDF para descarga directa
        """
        from django.http import HttpResponse
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        from io import BytesIO
        from datetime import datetime
        
        presupuesto = self.get_object()
        
        # Crear buffer de memoria
        buffer = BytesIO()
        
        # Crear documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilo personalizado para título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Estilo para subtítulos
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#475569'),
            spaceAfter=12
        )
        
        # === ENCABEZADO ===
        elements.append(Paragraph("PRESUPUESTO DIGITAL", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Información básica
        codigo = presupuesto.codigo_presupuesto.hex[:8].upper()
        info_data = [
            ['Código:', codigo],
            ['Fecha Emisión:', presupuesto.fecha_emision.strftime('%d/%m/%Y')],
            ['Válido hasta:', presupuesto.fecha_vigencia.strftime('%d/%m/%Y')],
            ['Estado:', presupuesto.estado.estado if hasattr(presupuesto.estado, 'estado') else str(presupuesto.estado)],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # === DATOS DEL PACIENTE Y ODONTÓLOGO ===
        elements.append(Paragraph("Datos del Paciente", subtitle_style))
        
        paciente = presupuesto.plan_tratamiento.codpaciente
        paciente_data = [
            ['Nombre:', f"{paciente.codusuario.nombre} {paciente.codusuario.apellido}"],
            ['CI:', paciente.carnetidentidad or 'No especificado'],
            ['Email:', paciente.codusuario.correoelectronico or 'No especificado'],
        ]
        
        paciente_table = Table(paciente_data, colWidths=[2*inch, 4*inch])
        paciente_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(paciente_table)
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph("Odontólogo Responsable", subtitle_style))
        
        odontologo = presupuesto.plan_tratamiento.cododontologo
        odontologo_data = [
            ['Nombre:', f"{odontologo.codusuario.nombre} {odontologo.codusuario.apellido}"],
            ['Matrícula:', odontologo.codusuario.codigo],
        ]
        
        odontologo_table = Table(odontologo_data, colWidths=[2*inch, 4*inch])
        odontologo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(odontologo_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # === ITEMS DEL PRESUPUESTO ===
        elements.append(Paragraph("Detalle de Servicios", subtitle_style))
        
        # Encabezados de tabla
        items_data = [['#', 'Servicio', 'Precio Unit.', 'Desc.', 'Total']]
        
        # Items del presupuesto
        items = presupuesto.items_presupuesto.all().order_by('orden')
        for idx, item in enumerate(items, 1):
            servicio_nombre = item.item_plan.idservicio.nombre if item.item_plan and item.item_plan.idservicio else 'Servicio'
            items_data.append([
                str(idx),
                servicio_nombre,
                f"${float(item.precio_unitario):.2f}",
                f"${float(item.descuento_item):.2f}",
                f"${float(item.precio_final):.2f}"
            ])
        
        # Totales
        items_data.append(['', '', '', 'Subtotal:', f"${float(presupuesto.subtotal):.2f}"])
        items_data.append(['', '', '', 'Descuento:', f"${float(presupuesto.descuento):.2f}"])
        items_data.append(['', '', '', 'TOTAL:', f"${float(presupuesto.total):.2f}"])
        
        items_table = Table(items_data, colWidths=[0.5*inch, 3*inch, 1.2*inch, 1*inch, 1.3*inch])
        items_table.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Contenido items
            ('ALIGN', (0, 1), (0, -4), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -4), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -4), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -4), 9),
            ('GRID', (0, 0), (-1, -4), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -4), [colors.white, colors.HexColor('#f8fafc')]),
            
            # Totales
            ('ALIGN', (3, -3), (3, -1), 'RIGHT'),
            ('ALIGN', (4, -3), (4, -1), 'RIGHT'),
            ('FONTNAME', (3, -3), (3, -1), 'Helvetica-Bold'),
            ('FONTNAME', (4, -3), (4, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (3, -3), (4, -1), 10),
            ('LINEABOVE', (3, -3), (-1, -3), 1, colors.grey),
            ('LINEABOVE', (3, -1), (-1, -1), 2, colors.black),
            ('BACKGROUND', (3, -1), (-1, -1), colors.HexColor('#dbeafe')),
            
            # Padding general
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(items_table)
        
        # === NOTAS Y TÉRMINOS ===
        if presupuesto.notas:
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph("Notas", subtitle_style))
            elements.append(Paragraph(presupuesto.notas, styles['Normal']))
        
        if presupuesto.terminos_condiciones:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("Términos y Condiciones", subtitle_style))
            elements.append(Paragraph(presupuesto.terminos_condiciones, styles['Normal']))
        
        # === PIE DE PÁGINA ===
        elements.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            f"Documento generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}",
            footer_style
        ))
        
        # Construir PDF
        doc.build(elements)
        
        # Obtener el PDF del buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        # Actualizar registro en BD
        presupuesto.pdf_generado = True
        presupuesto.save(update_fields=['pdf_generado'])
        
        # Bitácora
        usuario = getattr(request.user, 'usuario', None)
        Bitacora.objects.create(
            empresa=request.tenant,
            usuario=usuario,
            accion="PRESUPUESTO_PDF_GENERADO",
            tabla_afectada="presupuesto_digital",
            registro_id=presupuesto.id,
            valores_nuevos={
                'codigo_presupuesto': codigo,
                'pdf_generado': True,
                'fecha_generacion': datetime.now().isoformat()
            },
            ip_address='127.0.0.1',
            user_agent='API'
        )
        
        # Retornar PDF como descarga
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="presupuesto_{codigo}.pdf"'
        return response
    
    @action(detail=False, methods=['post'], url_path='generar-desde-plan')
    @transaction.atomic
    def generar_desde_plan(self, request):
        """
        Genera un presupuesto digital desde un plan de tratamiento aprobado.
        
        POST /api/presupuestos-digitales/generar-desde-plan/
        
        Payload:
        {
            "plan_tratamiento_id": 5,
            "items_ids": [1, 2, 3],  // Opcional, si vacío incluye todos
            "es_tramo": false,
            "numero_tramo": null,
            "fecha_vigencia": "2025-12-31",  // Opcional, default 30 días
            "descuento": "50.00",
            "terminos_condiciones": "Condiciones específicas...",
            "notas": "Notas adicionales...",
            "items_config": [  // Opcional, config por ítem
                {
                    "item_id": 1,
                    "descuento_item": "10.00",
                    "permite_pago_parcial": true,
                    "cantidad_cuotas": 3
                }
            ]
        }
        
        Response (201):
        {
            "id": 10,
            "codigo_presupuesto": "uuid-generado",
            "plan_tratamiento": 5,
            "estado": "Borrador",
            "es_tramo": false,
            "total": "1350.00",
            ...
        }
        """
        serializer = CrearPresupuestoSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        presupuesto = serializer.save()
        
        # Serializar respuesta completa
        response_serializer = DetallePresupuestoSerializer(
            presupuesto,
            context={'request': request}
        )
        
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'], url_path='planes-disponibles')
    def planes_disponibles(self, request):
        """
        Lista planes de tratamiento aprobados que están disponibles
        para generar presupuestos.
        
        GET /api/presupuestos-digitales/planes-disponibles/
        
        Response:
        [
            {
                "id": 1,
                "paciente": "Juan Pérez",
                "odontologo": "Dr. María López",
                "fecha_plan": "2025-10-15",
                "total_items": 5,
                "presupuestos_generados": 0
            }
        ]
        """
        empresa = request.tenant
        
        # Obtener planes aprobados
        planes = Plandetratamiento.objects.filter(
            empresa=empresa,
            estado_plan=Plandetratamiento.ESTADO_PLAN_APROBADO
        ).select_related(
            'codpaciente__codusuario',
            'cododontologo__codusuario'
        ).prefetch_related('presupuestos_digitales')
        
        data = []
        for plan in planes:
            data.append({
                'id': plan.id,
                'paciente': f"{plan.codpaciente.codusuario.nombre} {plan.codpaciente.codusuario.apellido}",
                'odontologo': f"Dr. {plan.cododontologo.codusuario.nombre} {plan.cododontologo.codusuario.apellido}",
                'fecha_plan': plan.fechaplan,
                'fecha_aprobacion': plan.fecha_aprobacion,
                'total_items': plan.itemplandetratamiento_set.count(),
                'monto_total': plan.montototal,
                'presupuestos_generados': plan.presupuestos_digitales.count(),
            })
        
        return Response(data)
    
    @action(detail=True, methods=['get'], url_path='desglose')
    def desglose_detallado(self, request, pk=None):
        """
        Retorna un desglose detallado del presupuesto con cálculos por ítem.
        
        GET /api/presupuestos-digitales/{id}/desglose/
        
        Response:
        {
            "codigo_presupuesto": "A1B2C3D4",
            "items": [...],
            "subtotal": 1000.00,
            "descuento_global": 50.00,
            "total": 950.00,
            "resumen": {...}
        }
        """
        presupuesto = self.get_object()
        
        items_data = []
        for item in presupuesto.items_presupuesto.all():
            items_data.append({
                'servicio': item.item_plan.idservicio.nombre,
                'pieza_dental': item.item_plan.idpiezadental.nombrepieza if item.item_plan.idpiezadental else None,
                'precio_unitario': float(item.precio_unitario),
                'descuento_item': float(item.descuento_item),
                'precio_final': float(item.precio_final),
                'permite_pago_parcial': item.permite_pago_parcial,
                'cantidad_cuotas': item.cantidad_cuotas,
            })
        
        return Response({
            'codigo_presupuesto': presupuesto.codigo_presupuesto.hex[:8].upper(),
            'items': items_data,
            'subtotal': float(presupuesto.subtotal),
            'descuento_global': float(presupuesto.descuento),
            'total': float(presupuesto.total),
            'resumen': {
                'cantidad_items': len(items_data),
                'items_con_pago_parcial': sum(1 for item in presupuesto.items_presupuesto.all() if item.permite_pago_parcial),
                'es_tramo': presupuesto.es_tramo,
                'numero_tramo': presupuesto.numero_tramo,
            }
        })
    
    # =========================================================================
    # ENDPOINTS PARA ACEPTACIÓN DE PRESUPUESTOS (SP3-T003)
    # =========================================================================
    
    @action(
        detail=False,
        methods=['get'],
        url_path='mis-presupuestos',
        permission_classes=[IsAuthenticated, IsTenantMatch],
        throttle_classes=[PresupuestoListRateThrottle]
    )
    def mis_presupuestos(self, request):
        """
        Lista los presupuestos digitales del paciente autenticado.

        Query params:
        - estado_aceptacion: Filtrar por estado (Pendiente, Aceptado, Rechazado, Parcial)
        - esta_vigente: true/false - Filtrar por vigencia
        - plan_tratamiento: ID del plan

        SP3-T003: Permite al paciente ver sus presupuestos disponibles
        """
        
        try:
            # Obtener el Usuario por el email del Django User autenticado
            # El modelo Usuario NO tiene relación con Django User, se relaciona por email
            email = request.user.email
            
            if not email:
                logger.error(f"Django User {request.user.id} no tiene email")
                return Response(
                    {'error': 'El usuario autenticado no tiene email asociado.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                usuario = Usuario.objects.get(correoelectronico=email, empresa=request.tenant)
                logger.info(f"Usuario {usuario.codigo} - {usuario.nombre} solicita sus presupuestos")
            except Usuario.DoesNotExist:
                logger.error(f"No existe Usuario con email {email} en empresa {request.tenant}")
                return Response(
                    {
                        'error': 'Usuario no encontrado',
                        'detalle': f'No existe un usuario con el email {email} en esta clínica. Por favor contacte al administrador.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obtener presupuestos del paciente
            queryset = PresupuestoDigital.objects.filter(
                plan_tratamiento__codpaciente__codusuario=usuario,
                empresa=request.tenant
            ).select_related(
                'plan_tratamiento',
                'plan_tratamiento__codpaciente',
                'plan_tratamiento__cododontologo',
                'usuario_acepta'
            ).prefetch_related('items_presupuesto')
            
            # Filtros opcionales
            estado_aceptacion = request.query_params.get('estado_aceptacion')
            if estado_aceptacion:
                queryset = queryset.filter(estado_aceptacion=estado_aceptacion)
            
            esta_vigente = request.query_params.get('esta_vigente')
            if esta_vigente is not None:
                if esta_vigente.lower() == 'true':
                    queryset = [p for p in queryset if p.esta_vigente()]
                elif esta_vigente.lower() == 'false':
                    queryset = [p for p in queryset if not p.esta_vigente()]
            
            plan_id = request.query_params.get('plan_tratamiento')
            if plan_id:
                queryset = queryset.filter(plan_tratamiento_id=plan_id)
            
            serializer = PresupuestoDigitalParaPacienteSerializer(
                queryset,
                many=True,
                context={'request': request}
            )
            
            logger.info(f"Retornando {len(serializer.data)} presupuestos para usuario {usuario.codigo}")
            
            return Response({
                'count': len(serializer.data) if isinstance(queryset, list) else queryset.count(),
                'results': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error en mis_presupuestos: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Error al obtener presupuestos: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(
        detail=True,
        methods=['get'],
        url_path='puede-aceptar',
        permission_classes=[IsAuthenticated, CanViewPresupuesto, IsTenantMatch]
    )
    def puede_aceptar(self, request, pk=None):
        """
        Verifica si el presupuesto puede ser aceptado por el paciente.
        
        Retorna:
        - puede_aceptar: bool
        - razones: lista de razones si no puede aceptar
        - validaciones: detalle de cada validación
        
        SP3-T003: Pre-validación antes de mostrar UI de aceptación
        """
        presupuesto = self.get_object()
        
        # Obtener usuario usando el patrón correcto de email lookup
        try:
            usuario = Usuario.objects.get(
                correoelectronico=request.user.email,
                empresa=request.tenant
            )
            logger.info(f"puede_aceptar - Usuario encontrado: {usuario.codigo} - {usuario.nombre}")
        except Usuario.DoesNotExist:
            logger.error(f"puede_aceptar - Usuario no encontrado para email: {request.user.email}")
            return Response({
                'puede_aceptar': False,
                'razones': ['Usuario no encontrado en el sistema'],
                'validaciones': {
                    'es_paciente_del_presupuesto': False,
                    'presupuesto_emitido': False,
                    'no_caducado': False,
                    'no_aceptado_previamente': False,
                    'no_rechazado': False,
                },
                'informacion': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validaciones = {
            'es_paciente_del_presupuesto': False,
            'presupuesto_emitido': False,
            'no_caducado': False,
            'no_aceptado_previamente': False,
            'no_rechazado': False,
        }
        razones = []
        
        # Validación 1: Usuario es el paciente del presupuesto
        try:
            if presupuesto.plan_tratamiento and presupuesto.plan_tratamiento.codpaciente:
                usuario_paciente = presupuesto.plan_tratamiento.codpaciente.codusuario
                if usuario_paciente and usuario.codigo == usuario_paciente.codigo:
                    validaciones['es_paciente_del_presupuesto'] = True
                    logger.info(f"✅ Usuario {usuario.codigo} es el paciente del presupuesto")
                else:
                    razones.append("No eres el paciente de este presupuesto")
                    logger.warning(f"❌ Usuario {usuario.codigo} NO es el paciente (paciente: {usuario_paciente.codigo if usuario_paciente else 'N/A'})")
            else:
                razones.append("Presupuesto sin paciente asociado")
        except AttributeError as e:
            razones.append("Error al verificar paciente")
            logger.error(f"Error en validación de paciente: {e}")
        
        # Validación 2: Presupuesto está emitido
        if presupuesto.estado == PresupuestoDigital.ESTADO_EMITIDO:
            validaciones['presupuesto_emitido'] = True
        else:
            razones.append(f"Presupuesto debe estar emitido (estado actual: {presupuesto.estado})")
        
        # Validación 3: No caducado
        if presupuesto.esta_vigente():
            validaciones['no_caducado'] = True
        else:
            razones.append(f"Presupuesto caducado el {presupuesto.fecha_vigencia}")
        
        # Validación 4: No aceptado previamente
        if presupuesto.estado_aceptacion != PresupuestoDigital.ESTADO_ACEPTACION_ACEPTADO:
            validaciones['no_aceptado_previamente'] = True
        else:
            razones.append(f"Presupuesto ya aceptado el {presupuesto.fecha_aceptacion}")
        
        # Validación 5: No rechazado
        if presupuesto.estado_aceptacion != PresupuestoDigital.ESTADO_ACEPTACION_RECHAZADO:
            validaciones['no_rechazado'] = True
        else:
            razones.append("Presupuesto fue rechazado previamente")
        
        puede_aceptar = all(validaciones.values())
        
        return Response({
            'puede_aceptar': puede_aceptar,
            'razones': razones,
            'validaciones': validaciones,
            'informacion': {
                'fecha_vigencia': presupuesto.fecha_vigencia,
                'dias_restantes': (presupuesto.fecha_vigencia - timezone.now().date()).days if presupuesto.fecha_vigencia else None,
                'permite_aceptacion_parcial': presupuesto.items_presupuesto.filter(permite_pago_parcial=True).exists(),
                'items_total': presupuesto.items_presupuesto.count(),
                'items_con_pago_parcial': presupuesto.items_presupuesto.filter(permite_pago_parcial=True).count(),
            }
        })
    
    @action(
        detail=True,
        methods=['post'],
        url_path='aceptar',
        permission_classes=[IsAuthenticated, IsPacienteDelPresupuesto, IsTenantMatch],
        throttle_classes=[AceptacionPresupuestoRateThrottle]
    )
    @transaction.atomic
    def aceptar_presupuesto(self, request, pk=None):
        """
        Acepta el presupuesto digital (total o parcialmente).
        
        Payload:
        {
            "tipo_aceptacion": "Total" | "Parcial",
            "items_aceptados": [1, 2, 3],  // Solo si Parcial
            "firma_digital": {
                "timestamp": "2025-10-25T10:30:00Z",
                "user_id": 123,
                "signature_hash": "abc123...",
                "consent_text": "Acepto términos...",
            },
            "notas": "Comentarios opcionales"
        }
        
        SP3-T003: Endpoint principal de aceptación
        """
        presupuesto = self.get_object()
        
        # Obtener usuario usando el patrón correcto de email lookup
        try:
            usuario = Usuario.objects.get(
                correoelectronico=request.user.email,
                empresa=request.tenant
            )
            logger.info(f"aceptar_presupuesto - Usuario encontrado: {usuario.codigo} - {usuario.nombre}")
        except Usuario.DoesNotExist:
            logger.error(f"aceptar_presupuesto - Usuario no encontrado para email: {request.user.email}")
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar payload
        serializer = AceptarPresupuestoDigitalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        tipo_aceptacion = data['tipo_aceptacion']
        items_aceptados = data.get('items_aceptados', [])
        firma_digital = data['firma_digital']
        notas = data.get('notas', '')
        
        # VALIDACIÓN 1: Usuario es el paciente del presupuesto
        try:
            usuario_paciente = presupuesto.plan_tratamiento.codpaciente.codusuario
            if usuario.codigo != usuario_paciente.codigo:
                logger.warning(f"❌ Usuario {usuario.codigo} intentó aceptar presupuesto del paciente {usuario_paciente.codigo}")
                return Response(
                    {'error': 'No autorizado', 'detalle': 'No eres el paciente de este presupuesto'},
                    status=status.HTTP_403_FORBIDDEN
                )
            logger.info(f"✅ Usuario {usuario.codigo} validado como paciente del presupuesto")
        except AttributeError as e:
            logger.error(f"Error al verificar paciente: {e}")
            return Response(
                {'error': 'Error al verificar paciente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # VALIDACIÓN 2: Presupuesto en estado válido para aceptar
        if presupuesto.estado != PresupuestoDigital.ESTADO_EMITIDO:
            return Response(
                {'error': 'Estado inválido', 'detalle': f'Solo presupuestos emitidos pueden aceptarse (actual: {presupuesto.estado})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # VALIDACIÓN 3: No caducado
        if not presupuesto.esta_vigente():
            return Response(
                {'error': 'Presupuesto caducado', 'detalle': f'El presupuesto caducó el {presupuesto.fecha_vigencia}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # VALIDACIÓN 4: No aceptado previamente
        if presupuesto.estado_aceptacion == PresupuestoDigital.ESTADO_ACEPTACION_ACEPTADO:
            return Response(
                {
                    'error': 'Presupuesto ya aceptado',
                    'detalle': f'Aceptado el {presupuesto.fecha_aceptacion}',
                    'comprobante_url': presupuesto.comprobante_aceptacion_url
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # VALIDACIÓN 5: No rechazado
        if presupuesto.estado_aceptacion == PresupuestoDigital.ESTADO_ACEPTACION_RECHAZADO:
            return Response(
                {'error': 'Presupuesto rechazado', 'detalle': 'Presupuesto fue rechazado previamente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # VALIDACIÓN 6: Items válidos si es parcial
        if tipo_aceptacion == 'Parcial':
            items_presupuesto_ids = list(presupuesto.items_presupuesto.values_list('id', flat=True))
            items_invalidos = set(items_aceptados) - set(items_presupuesto_ids)
            if items_invalidos:
                return Response(
                    {'error': 'Items inválidos', 'detalle': f'Los siguientes items no pertenecen al presupuesto: {items_invalidos}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar que permiten pago parcial
            items_obj = ItemPresupuestoDigital.objects.filter(id__in=items_aceptados)
            items_sin_pago_parcial = items_obj.filter(permite_pago_parcial=False)
            if items_sin_pago_parcial.exists():
                return Response(
                    {'error': 'Items no permiten pago parcial', 'detalle': 'Algunos items seleccionados no permiten aceptación parcial'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Helper para obtener IP real del cliente
        def get_client_ip(req):
            """
            Obtiene la IP real del cliente considerando proxies y balanceadores de carga.

            Orden de prioridad:
            1. X-Forwarded-For (proxies/balanceadores) - toma la primera IP de la cadena
            2. X-Real-IP (nginx/proxy inverso)
            3. REMOTE_ADDR (conexión directa)

            Limpia espacios y valida que la IP no esté vacía.
            """
            # Intentar X-Forwarded-For (puede tener múltiples IPs: "client, proxy1, proxy2")
            x_forwarded_for = req.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                # Tomar la primera IP (la del cliente original)
                ip = x_forwarded_for.split(',')[0].strip()
                if ip:
                    return ip

            # Intentar X-Real-IP (usado por nginx y otros proxies)
            x_real_ip = req.META.get('HTTP_X_REAL_IP')
            if x_real_ip:
                ip = x_real_ip.strip()
                if ip:
                    return ip

            # Fallback: dirección remota directa
            remote_addr = req.META.get('REMOTE_ADDR', '').strip()
            return remote_addr if remote_addr else 'unknown'
        
        # Helper para obtener User Agent
        def get_user_agent(req):
            return req.META.get('HTTP_USER_AGENT', '')
        
        # ACTUALIZACIÓN 1: Actualizar PresupuestoDigital
        presupuesto.estado_aceptacion = (
            PresupuestoDigital.ESTADO_ACEPTACION_ACEPTADO
            if tipo_aceptacion == 'Total'
            else PresupuestoDigital.ESTADO_ACEPTACION_PARCIAL
        )
        presupuesto.fecha_aceptacion = timezone.now()
        presupuesto.usuario_acepta = usuario
        presupuesto.tipo_aceptacion = tipo_aceptacion
        presupuesto.es_editable = False  # BLOQUEAR EDICIÓN
        presupuesto.save()
        
        # ACTUALIZACIÓN 2: Crear registro de auditoría
        aceptacion = AceptacionPresupuestoDigital.objects.create(
            presupuesto_digital=presupuesto,
            usuario_paciente=usuario,
            empresa=request.tenant,
            tipo_aceptacion=tipo_aceptacion,
            items_aceptados=items_aceptados if tipo_aceptacion == 'Parcial' else [],
            firma_digital=firma_digital,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            monto_subtotal=presupuesto.subtotal,
            monto_descuento=presupuesto.descuento,
            monto_total_aceptado=presupuesto.total,
            notas_paciente=notas,
            listo_para_pago=True
        )
        
        # ACTUALIZACIÓN 3: Generar comprobante PDF
        try:
            from .utils_comprobante_aceptacion import generar_comprobante_aceptacion
            comprobante_url = generar_comprobante_aceptacion(aceptacion)
            aceptacion.comprobante_url = comprobante_url
            aceptacion.save(update_fields=['comprobante_url'])
            
            presupuesto.comprobante_aceptacion_url = comprobante_url
            presupuesto.save(update_fields=['comprobante_aceptacion_url'])
        except Exception as e:
            # Log error pero no fallar la aceptación
            logger.error(f"Error generando comprobante PDF: {str(e)}")
        
        # ACTUALIZACIÓN 4: Registrar en Bitácora
        Bitacora.objects.create(
            empresa=request.tenant,
            usuario=usuario,
            accion='ACEPTACION_PRESUPUESTO_DIGITAL',
            tabla_afectada='presupuesto_digital',
            registro_id=presupuesto.id,
            valores_nuevos={
                'comprobante_id': str(aceptacion.comprobante_id),
                'tipo_aceptacion': tipo_aceptacion,
                'monto_total': str(presupuesto.total),
                'items_count': len(items_aceptados) if tipo_aceptacion == 'Parcial' else 'todos',
                'estado_aceptacion': presupuesto.estado_aceptacion,
            },
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        # TODO: ACTUALIZACIÓN 5: Enviar notificaciones (Fase 5)
        # Las signals se encargarán de esto
        
        # Serializar respuesta
        aceptacion_serializer = AceptacionPresupuestoDigitalSerializer(aceptacion)
        presupuesto_serializer = PresupuestoDigitalParaPacienteSerializer(
            presupuesto,
            context={'request': request}
        )
        
        return Response({
            'success': True,
            'mensaje': 'Presupuesto aceptado exitosamente',
            'aceptacion': aceptacion_serializer.data,
            'presupuesto': presupuesto_serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(
        detail=True,
        methods=['get'],
        url_path='historial-aceptaciones',
        permission_classes=[IsAuthenticated, CanViewPresupuesto, IsTenantMatch]
    )
    def historial_aceptaciones(self, request, pk=None):
        """
        Lista el historial de aceptaciones de un presupuesto.
        
        Útil para aceptaciones parciales incrementales donde el paciente
        va aceptando ítems en diferentes momentos.
        
        SP3-T003: Auditoría de aceptaciones
        """
        presupuesto = self.get_object()
        aceptaciones = AceptacionPresupuestoDigital.objects.filter(
            presupuesto_digital=presupuesto
        ).order_by('-fecha_aceptacion')
        
        serializer = AceptacionPresupuestoDigitalSerializer(aceptaciones, many=True)

        return Response({
            'presupuesto_id': presupuesto.id,
            'codigo_presupuesto': presupuesto.codigo_presupuesto.hex[:8].upper(),
            'total_aceptaciones': aceptaciones.count(),
            'aceptaciones': serializer.data
        })

    @action(
        detail=False,
        methods=['get'],
        url_path='aceptaciones/(?P<aceptacion_id>[0-9]+)/descargar-comprobante',
        permission_classes=[IsAuthenticated, CanViewPresupuesto, IsTenantMatch]
    )
    def descargar_comprobante(self, request, aceptacion_id=None):
        """
        Descarga el comprobante PDF de una aceptación de presupuesto.

        GET /api/presupuestos-digitales/aceptaciones/{aceptacion_id}/descargar-comprobante/

        Permisos:
        - Paciente que aceptó el presupuesto
        - Odontólogo del plan de tratamiento
        - Administrador de la empresa

        Retorna:
        - Archivo PDF para descarga directa

        SP3-T003: Endpoint para descarga de comprobante de aceptación
        """
        from django.http import HttpResponse, FileResponse
        import os

        try:
            # Buscar la aceptación
            aceptacion = get_object_or_404(
                AceptacionPresupuestoDigital,
                id=aceptacion_id,
                empresa=request.tenant
            )

            # Verificar permisos de acceso
            presupuesto = aceptacion.presupuesto_digital
            usuario = getattr(request.user, 'usuario', None)

            # Validar que el usuario tenga permiso de ver este comprobante
            es_paciente = False
            es_odontologo = False
            es_admin = request.user.is_staff or request.user.is_superuser

            if usuario:
                try:
                    # Verificar si es el paciente
                    if presupuesto.plan_tratamiento.codpaciente.codusuario == usuario:
                        es_paciente = True

                    # Verificar si es el odontólogo
                    if presupuesto.plan_tratamiento.cododontologo.codusuario == usuario:
                        es_odontologo = True

                    # Verificar si es admin de la empresa
                    if hasattr(usuario, 'idtipousuario') and usuario.idtipousuario:
                        tipo_usuario = usuario.idtipousuario
                        if hasattr(tipo_usuario, 'rol') and 'admin' in tipo_usuario.rol.lower():
                            es_admin = True
                except AttributeError:
                    pass

            if not (es_paciente or es_odontologo or es_admin):
                logger.warning(
                    f"Usuario {usuario.codigo if usuario else 'Unknown'} "
                    f"intentó descargar comprobante {aceptacion_id} sin permisos"
                )
                return Response(
                    {'error': 'No tienes permiso para descargar este comprobante.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Verificar si el comprobante ya existe
            if aceptacion.comprobante_url:
                # Intentar servir el archivo existente
                try:
                    from django.core.files.storage import default_storage

                    # Extraer la ruta del archivo de la URL
                    # Ejemplo: http://domain/media/comprobantes/file.pdf -> comprobantes/file.pdf
                    file_path = aceptacion.comprobante_url.split('/media/')[-1] if '/media/' in aceptacion.comprobante_url else None

                    if file_path and default_storage.exists(file_path):
                        # Abrir el archivo
                        file = default_storage.open(file_path, 'rb')

                        # Retornar como descarga
                        response = FileResponse(
                            file,
                            content_type='application/pdf'
                        )
                        response['Content-Disposition'] = (
                            f'attachment; filename="comprobante_{aceptacion.comprobante_id}.pdf"'
                        )

                        logger.info(
                            f"Comprobante {aceptacion_id} descargado por usuario "
                            f"{usuario.codigo if usuario else 'Unknown'}"
                        )

                        return response
                    else:
                        logger.warning(
                            f"Comprobante {aceptacion_id} tiene URL pero archivo no existe: {file_path}"
                        )
                except Exception as e:
                    logger.error(
                        f"Error al servir comprobante existente {aceptacion_id}: {str(e)}"
                    )

            # Si no existe el comprobante o hubo error, generarlo ahora
            logger.info(f"Generando comprobante para aceptación {aceptacion_id}")

            try:
                from .utils_comprobante_aceptacion import generar_comprobante_aceptacion
                comprobante_url = generar_comprobante_aceptacion(aceptacion)

                # Actualizar la aceptación con la URL del comprobante
                aceptacion.comprobante_url = comprobante_url
                aceptacion.save(update_fields=['comprobante_url'])

                # También actualizar el presupuesto si no tiene
                if not presupuesto.comprobante_aceptacion_url:
                    presupuesto.comprobante_aceptacion_url = comprobante_url
                    presupuesto.save(update_fields=['comprobante_aceptacion_url'])

                # Ahora servir el archivo recién generado
                from django.core.files.storage import default_storage

                file_path = comprobante_url.split('/media/')[-1] if '/media/' in comprobante_url else None

                if file_path and default_storage.exists(file_path):
                    file = default_storage.open(file_path, 'rb')

                    response = FileResponse(
                        file,
                        content_type='application/pdf'
                    )
                    response['Content-Disposition'] = (
                        f'attachment; filename="comprobante_{aceptacion.comprobante_id}.pdf"'
                    )

                    logger.info(
                        f"Comprobante {aceptacion_id} generado y descargado por usuario "
                        f"{usuario.codigo if usuario else 'Unknown'}"
                    )

                    return response
                else:
                    logger.error(
                        f"Comprobante generado pero archivo no encontrado: {file_path}"
                    )
                    return Response(
                        {'error': 'Error al generar el comprobante. Intenta nuevamente.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            except Exception as e:
                logger.error(
                    f"Error al generar comprobante para aceptación {aceptacion_id}: {str(e)}",
                    exc_info=True
                )
                return Response(
                    {'error': f'Error al generar el comprobante: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(
                f"Error en descargar_comprobante para aceptación {aceptacion_id}: {str(e)}",
                exc_info=True
            )
            return Response(
                {'error': 'Error al descargar el comprobante. Verifica que la aceptación exista.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
