# api/views_presupuesto_digital.py
"""
Views para la funcionalidad de generación de presupuestos digitales.
SP3-T002: Generar presupuesto digital (web)

Permite emitir un presupuesto total o por tramos a partir de un plan aprobado.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import (
    PresupuestoDigital,
    ItemPresupuestoDigital,
    Plandetratamiento,
    Bitacora,
)
from .serializers_presupuesto_digital import (
    ListarPresupuestosSerializer,
    DetallePresupuestoSerializer,
    CrearPresupuestoSerializer,
    EmitirPresupuestoSerializer,
    ActualizarPresupuestoSerializer,
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
    permission_classes = [AllowAny]  # TODO: Cambiar a IsAuthenticated en producción
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'es_tramo', 'plan_tratamiento']
    search_fields = ['codigo_presupuesto', 'notas', 'terminos_condiciones']
    ordering_fields = ['fecha_emision', 'fecha_vigencia', 'total']
    ordering = ['-fecha_emision']
    
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
