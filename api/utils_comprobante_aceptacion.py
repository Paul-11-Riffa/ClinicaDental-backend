# api/utils_comprobante_aceptacion.py
"""
Utilidad para generar comprobantes de aceptación de presupuestos digitales en PDF.

SP3-T003: Aceptar presupuesto digital por paciente
Genera PDF profesional con logo, datos del presupuesto, firma digital y QR code.
"""
from io import BytesIO
from decimal import Decimal
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF

from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

import os
import hashlib


def generar_comprobante_aceptacion(aceptacion):
    """
    Genera un PDF del comprobante de aceptación de presupuesto.
    
    Args:
        aceptacion (AceptacionPresupuestoDigital): Instancia del modelo de aceptación
    
    Returns:
        str: URL del PDF generado
    """
    buffer = BytesIO()
    
    # Crear documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
        title=f"Comprobante de Aceptación {aceptacion.comprobante_id}"
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para título
    estilo_titulo = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulos
    estilo_subtitulo = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para texto normal
    estilo_normal = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=6
    )
    
    # Estilo para texto pequeño
    estilo_pequeno = ParagraphStyle(
        'CustomSmall',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=4
    )
    
    # Contenido del PDF
    story = []
    
    # =========================================================================
    # HEADER - Logo y Empresa (si existe)
    # =========================================================================
    try:
        empresa = aceptacion.empresa
        if empresa:
            # TODO: Agregar logo si existe
            # if empresa.logo:
            #     logo = Image(empresa.logo.path, width=2*inch, height=1*inch)
            #     story.append(logo)
            
            empresa_nombre = Paragraph(
                f"<b>{empresa.nombre}</b>",
                estilo_subtitulo
            )
            story.append(empresa_nombre)
    except AttributeError:
        pass
    
    story.append(Spacer(1, 0.3*inch))
    
    # =========================================================================
    # TÍTULO PRINCIPAL
    # =========================================================================
    titulo = Paragraph(
        "COMPROBANTE DE ACEPTACIÓN DE PRESUPUESTO",
        estilo_titulo
    )
    story.append(titulo)
    story.append(Spacer(1, 0.2*inch))
    
    # =========================================================================
    # CÓDIGO DE COMPROBANTE (destacado)
    # =========================================================================
    codigo_comprobante = Table(
        [[Paragraph(
            f"<b>Código de Comprobante:</b><br/>"
            f"<font size=12 color='#e74c3c'>{aceptacion.comprobante_id}</font>",
            estilo_normal
        )]],
        colWidths=[6.5*inch]
    )
    codigo_comprobante.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecf0f1')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#bdc3c7')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(codigo_comprobante)
    story.append(Spacer(1, 0.3*inch))
    
    # =========================================================================
    # INFORMACIÓN GENERAL
    # =========================================================================
    presupuesto = aceptacion.presupuesto_digital
    paciente = presupuesto.plan_tratamiento.codpaciente
    odontologo = presupuesto.plan_tratamiento.cododontologo
    
    fecha_aceptacion_str = aceptacion.fecha_aceptacion.strftime('%d/%m/%Y %H:%M:%S')
    
    info_general_data = [
        ['Fecha y Hora de Aceptación:', fecha_aceptacion_str],
        ['Tipo de Aceptación:', aceptacion.get_tipo_aceptacion_display()],
        ['Código de Presupuesto:', presupuesto.codigo_presupuesto.hex[:8].upper()],
        ['Estado:', 'ACEPTADO ✓' if aceptacion.tipo_aceptacion == 'Total' else 'ACEPTACIÓN PARCIAL ⚠'],
    ]
    
    info_general = Table(info_general_data, colWidths=[2.5*inch, 4*inch])
    info_general.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#d5dbdb')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(info_general)
    story.append(Spacer(1, 0.2*inch))
    
    # =========================================================================
    # DATOS DEL PACIENTE
    # =========================================================================
    story.append(Paragraph("DATOS DEL PACIENTE", estilo_subtitulo))
    
    paciente_data = [
        ['Nombre Completo:', f"{paciente.codusuario.nombre} {paciente.codusuario.apellido}"],
        ['Carnet de Identidad:', paciente.carnetidentidad or 'N/A'],
        ['Email:', paciente.codusuario.correoelectronico or 'N/A'],
        ['Teléfono:', paciente.codusuario.telefono or 'N/A'],
    ]
    
    paciente_table = Table(paciente_data, colWidths=[2.5*inch, 4*inch])
    paciente_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f5e9')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1b5e20')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#a5d6a7')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(paciente_table)
    story.append(Spacer(1, 0.2*inch))
    
    # =========================================================================
    # DATOS DEL ODONTÓLOGO
    # =========================================================================
    story.append(Paragraph("ODONTÓLOGO TRATANTE", estilo_subtitulo))
    
    odontologo_data = [
        ['Nombre:', f"Dr(a). {odontologo.codusuario.nombre} {odontologo.codusuario.apellido}"],
        ['Especialidad:', odontologo.especialidad or 'General'],
    ]
    
    odontologo_table = Table(odontologo_data, colWidths=[2.5*inch, 4*inch])
    odontologo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0d47a1')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#90caf9')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(odontologo_table)
    story.append(Spacer(1, 0.2*inch))
    
    # =========================================================================
    # ÍTEMS ACEPTADOS
    # =========================================================================
    story.append(Paragraph("DETALLE DEL PRESUPUESTO ACEPTADO", estilo_subtitulo))
    
    items_data = [['#', 'Servicio', 'Pieza Dental', 'Precio', 'Estado']]
    
    if aceptacion.tipo_aceptacion == 'Total':
        # Todos los items
        items = presupuesto.items_presupuesto.all()
        for idx, item in enumerate(items, 1):
            servicio = item.item_plan.idservicio.nombre if item.item_plan.idservicio else 'N/A'
            pieza = item.item_plan.idpiezadental.nombrepieza if item.item_plan.idpiezadental else 'N/A'
            precio = f"Bs. {item.precio_final}"
            items_data.append([str(idx), servicio, pieza, precio, '✓ ACEPTADO'])
    else:
        # Solo items aceptados
        from .models import ItemPresupuestoDigital
        items = ItemPresupuestoDigital.objects.filter(id__in=aceptacion.items_aceptados)
        for idx, item in enumerate(items, 1):
            servicio = item.item_plan.idservicio.nombre if item.item_plan.idservicio else 'N/A'
            pieza = item.item_plan.idpiezadental.nombrepieza if item.item_plan.idpiezadental else 'N/A'
            precio = f"Bs. {item.precio_final}"
            items_data.append([str(idx), servicio, pieza, precio, '✓ ACEPTADO'])
    
    items_table = Table(
        items_data,
        colWidths=[0.4*inch, 2.5*inch, 1.5*inch, 1.2*inch, 1*inch]
    )
    items_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Body
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # #
        ('ALIGN', (1, 1), (2, -1), 'LEFT'),     # Servicio, Pieza
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),    # Precio
        ('ALIGN', (4, 1), (4, -1), 'CENTER'),   # Estado
        
        # Alternating rows
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.2*inch))
    
    # =========================================================================
    # MONTOS
    # =========================================================================
    montos_data = [
        ['Subtotal:', f"Bs. {aceptacion.monto_subtotal}"],
        ['Descuento:', f"Bs. {aceptacion.monto_descuento}"],
        ['TOTAL ACEPTADO:', f"Bs. {aceptacion.monto_total_aceptado}"],
    ]
    
    montos_table = Table(montos_data, colWidths=[5*inch, 1.5*inch])
    montos_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        
        # Última fila (TOTAL) destacada
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.whitesmoke),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 12),
        
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#bdc3c7')),
        ('LINEABOVE', (0, 2), (-1, 2), 2, colors.HexColor('#27ae60')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(montos_table)
    story.append(Spacer(1, 0.3*inch))
    
    # =========================================================================
    # FIRMA DIGITAL
    # =========================================================================
    story.append(Paragraph("FIRMA DIGITAL ELECTRÓNICA", estilo_subtitulo))
    
    firma = aceptacion.firma_digital
    firma_hash = firma.get('signature_hash', 'N/A')[:32] + '...'  # Primeros 32 caracteres
    
    firma_data = [
        ['Timestamp:', firma.get('timestamp', 'N/A')],
        ['Usuario ID:', str(firma.get('user_id', 'N/A'))],
        ['Hash de Firma:', firma_hash],
        ['IP de Origen:', aceptacion.ip_address or 'N/A'],
        ['Consentimiento:', firma.get('consent_text', 'N/A')[:50] + '...'],
    ]
    
    firma_table = Table(firma_data, colWidths=[2*inch, 4.5*inch])
    firma_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fff3cd')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#856404')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ffc107')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(firma_table)
    story.append(Spacer(1, 0.2*inch))
    
    # =========================================================================
    # QR CODE PARA VERIFICACIÓN
    # =========================================================================
    story.append(Paragraph("VERIFICACIÓN DEL COMPROBANTE", estilo_subtitulo))
    
    # Generar URL de verificación (ajustar según tu dominio)
    verification_url = f"https://notificct.dpdns.org/api/verificar-comprobante/{aceptacion.comprobante_id}/"
    
    # Crear QR code
    qr_code = QrCodeWidget(verification_url)
    qr_drawing = Drawing(1.5*inch, 1.5*inch)
    qr_drawing.add(qr_code)
    
    # Centrar QR code
    qr_table = Table([[qr_drawing]], colWidths=[6.5*inch])
    qr_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(qr_table)
    
    verification_text = Paragraph(
        f"<i>Escanea el código QR para verificar la autenticidad de este comprobante</i><br/>"
        f"<font size=7>{verification_url}</font>",
        estilo_pequeno
    )
    story.append(verification_text)
    story.append(Spacer(1, 0.2*inch))
    
    # =========================================================================
    # NOTAS (si existen)
    # =========================================================================
    if aceptacion.notas_paciente:
        story.append(Paragraph("NOTAS DEL PACIENTE", estilo_subtitulo))
        notas = Paragraph(aceptacion.notas_paciente, estilo_normal)
        story.append(notas)
        story.append(Spacer(1, 0.2*inch))
    
    # =========================================================================
    # FOOTER
    # =========================================================================
    footer_text = Paragraph(
        f"<i>Documento generado electrónicamente el {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}</i><br/>"
        f"<font size=7>Este comprobante tiene validez legal según la normativa vigente de firmas electrónicas.</font>",
        estilo_pequeno
    )
    story.append(Spacer(1, 0.3*inch))
    story.append(footer_text)
    
    # =========================================================================
    # GENERAR PDF
    # =========================================================================
    doc.build(story)
    
    # Obtener el PDF del buffer
    pdf_content = buffer.getvalue()
    buffer.close()
    
    # Guardar el PDF
    filename = f"comprobante_aceptacion_{aceptacion.comprobante_id}.pdf"
    
    # Guardar en media/comprobantes/
    file_path = f"comprobantes/{filename}"
    
    # Usar default_storage para compatibilidad con S3 o almacenamiento local
    saved_path = default_storage.save(file_path, ContentFile(pdf_content))
    
    # Retornar URL
    url = default_storage.url(saved_path)
    
    return url
