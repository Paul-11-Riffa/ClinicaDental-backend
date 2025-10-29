"""
ViewSets para el Flujo Cl�nico
Paso 3: APIs RESTful para gesti�n del flujo de consultas, planes e items
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Consulta, Plandetratamiento, Itemplandetratamiento, Bitacora
from .serializers_flujo_clinico import (
    ConsultaFlujoClincoSerializer,
    PlanTratamientoFlujoClincoSerializer,
    PlanTratamientoCreateSerializer,
    ItemEjecucionSerializer,
    ItemEjecucionCreateSerializer,
    ItemReprogramarSerializer
)


def log_to_bitacora(request, accion, tabla_afectada, valores_nuevos=None, registro_id=None):
    """
    Helper para crear registro de bit�cora con todos los campos requeridos.
    
    Args:
        request: Request object de Django/DRF
        accion: Descripci�n de la acci�n realizada
        tabla_afectada: Nombre de la tabla afectada
        valores_nuevos: Datos nuevos (opcional)
        registro_id: ID del registro afectado (opcional)
    """
    # Obtener IP del cliente
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')
    
    # Obtener User Agent
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    
    # Crear registro de bit�cora
    Bitacora.objects.create(
        empresa=request.tenant,
        usuario=getattr(request.user, 'usuario', None),
        accion=accion,
        tabla_afectada=tabla_afectada,
        registro_id=registro_id,
        valores_nuevos=valores_nuevos,
        ip_address=ip_address,
        user_agent=user_agent
    )


class ConsultaFlujoClincoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gesti�n de Consultas en el flujo cl�nico.
    
    Endpoints:
    - GET /api/flujo-clinico/consultas/ - Listar consultas
    - GET /api/flujo-clinico/consultas/{id}/ - Detalle de consulta
    - POST /api/flujo-clinico/consultas/ - Crear consulta
    - PUT/PATCH /api/flujo-clinico/consultas/{id}/ - Actualizar consulta
    - DELETE /api/flujo-clinico/consultas/{id}/ - Eliminar consulta
    
    Acciones custom:
    - POST /api/flujo-clinico/consultas/{id}/generar_plan/ - Generar plan desde consulta
    - GET /api/flujo-clinico/consultas/{id}/validar_flujo/ - Validar datos del flujo
    - GET /api/flujo-clinico/consultas/diagnosticas/ - Listar solo consultas diagn�sticas
    """
    serializer_class = ConsultaFlujoClincoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['codpaciente', 'cododontologo', 'idestadoconsulta', 'fecha']
    search_fields = ['motivoconsulta', 'diagnostico', 'tratamiento']
    ordering_fields = ['fecha', 'idconsulta']
    ordering = ['-fecha']
    
    def get_queryset(self):
        """Filtrar por empresa del tenant actual"""
        return Consulta.objects.filter(
            empresa=self.request.tenant
        ).select_related(
            'codpaciente', 'cododontologo', 'idestadoconsulta', 
            'idtipoconsulta', 'plan_tratamiento'
        )
    
    def perform_create(self, serializer):
        """Asignar empresa al crear"""
        consulta = serializer.save(empresa=self.request.tenant)
        
        # Registrar en bit�cora
        log_to_bitacora(
            request=self.request,
            accion="CONSULTA_CREADA",
            tabla_afectada="consulta",
            registro_id=consulta.id,
            valores_nuevos="Consulta creada en flujo cl�nico"
        )
    
    @action(detail=True, methods=['post'], url_path='generar-plan')
    def generar_plan(self, request, pk=None):
        """
        Generar un plan de tratamiento desde esta consulta diagn�stica.
        
        POST /api/flujo-clinico/consultas/{id}/generar-plan/
        Body:
        {
            "descripcionplan": "Plan de tratamiento para...",
            "cododontologo": 1,
            "idestado": 1
        }
        
        Returns: Plan creado con estado 'Propuesto'
        """
        consulta = self.get_object()
        
        # Validar que pueda generar plan
        puede, mensaje = consulta.puede_generar_plan()
        if not puede:
            return Response(
                {'error': mensaje},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear plan con datos del request
        serializer = PlanTratamientoCreateSerializer(data={
            **request.data,
            'codpaciente': consulta.codpaciente.pk,
            'consulta_diagnostico': consulta.id,
            'fechaplan': timezone.now().date(),
            'empresa': self.request.tenant.pk
        })
        
        if serializer.is_valid():
            with transaction.atomic():
                plan = serializer.save()
                
                # Vincular plan a consulta
                consulta.vincular_plan(plan)
                
                # Registrar en bit�cora
                log_to_bitacora(
                    request=request,
                    accion="PLAN_GENERADO_DESDE_CONSULTA",
                    tabla_afectada="plandetratamiento",
                    registro_id=plan.id,
                    valores_nuevos=f"Plan {plan.id} generado desde consulta {consulta.id}"
                )
                
                # Retornar plan completo
                plan_serializer = PlanTratamientoFlujoClincoSerializer(plan)
                return Response(
                    {
                        'mensaje': 'Plan de tratamiento generado exitosamente',
                        'plan': plan_serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='validar-flujo')
    def validar_flujo(self, request, pk=None):
        """
        Validar la consistencia de datos del flujo cl�nico.
        
        GET /api/flujo-clinico/consultas/{id}/validar-flujo/
        
        Returns: Estado de validaci�n con lista de errores
        """
        consulta = self.get_object()
        es_valido, errores = consulta.validar_datos_flujo()
        
        return Response({
            'es_valido': es_valido,
            'errores': errores,
            'consulta_id': consulta.id,
            'es_diagnostico': consulta.es_consulta_diagnostico()
        })
    
    @action(detail=False, methods=['get'], url_path='diagnosticas')
    def diagnosticas(self, request):
        """
        Listar solo consultas diagn�sticas (sin plan vinculado).
        
        GET /api/flujo-clinico/consultas/diagnosticas/
        
        Returns: Lista de consultas diagn�sticas
        """
        queryset = self.get_queryset().filter(
            plan_tratamiento__isnull=True
        )
        
        # Aplicar filtros
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PlanTratamientoFlujoClincoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gesti�n de Planes de Tratamiento con flujo cl�nico.
    
    Endpoints:
    - GET /api/flujo-clinico/planes/ - Listar planes
    - GET /api/flujo-clinico/planes/{id}/ - Detalle de plan
    - POST /api/flujo-clinico/planes/ - Crear plan
    - PUT/PATCH /api/flujo-clinico/planes/{id}/ - Actualizar plan
    
    Acciones custom de transiciones de estado:
    - POST /api/flujo-clinico/planes/{id}/iniciar_ejecucion/ - Iniciar ejecuci�n
    - POST /api/flujo-clinico/planes/{id}/pausar/ - Pausar ejecuci�n
    - POST /api/flujo-clinico/planes/{id}/reanudar/ - Reanudar ejecuci�n
    - POST /api/flujo-clinico/planes/{id}/cancelar/ - Cancelar plan
    - POST /api/flujo-clinico/planes/{id}/completar/ - Marcar como completado
    
    Acciones de informaci�n:
    - GET /api/flujo-clinico/planes/{id}/progreso/ - Calcular progreso
    - GET /api/flujo-clinico/planes/{id}/siguiente_item/ - Obtener siguiente item
    - GET /api/flujo-clinico/planes/{id}/validar_consistencia/ - Validar datos
    """
    serializer_class = PlanTratamientoFlujoClincoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['codpaciente', 'cododontologo', 'estado_tratamiento', 'idestado']
    search_fields = ['descripcionplan', 'notas_plan']
    ordering_fields = ['fechaplan', 'idplantratamiento', 'fecha_inicio_ejecucion']
    ordering = ['-fechaplan']
    
    def get_queryset(self):
        """Filtrar por empresa del tenant actual"""
        return Plandetratamiento.objects.filter(
            empresa=self.request.tenant
        ).select_related(
            'codpaciente', 'cododontologo', 'idestado', 'consulta_diagnostico'
        ).prefetch_related('itemplandetratamiento_set__idservicio')
    
    def perform_create(self, serializer):
        """Asignar empresa al crear"""
        plan = serializer.save(empresa=self.request.tenant)
        
        log_to_bitacora(
            request=self.request,
            accion="PLAN_TRATAMIENTO_CREADO",
            tabla_afectada="plandetratamiento",
            registro_id=plan.id,
            valores_nuevos="Plan de tratamiento creado desde API flujo cl�nico"
        )
    
    @action(detail=True, methods=['post'], url_path='iniciar-ejecucion')
    def iniciar_ejecucion(self, request, pk=None):
        """
        Iniciar la ejecuci�n del plan (Aceptado ? En Ejecuci�n).
        
        POST /api/flujo-clinico/planes/{id}/iniciar-ejecucion/
        
        Returns: Plan actualizado con estado 'En Ejecuci�n'
        """
        plan = self.get_object()
        
        resultado = plan.iniciar_ejecucion()
        
        if resultado:
            log_to_bitacora(
                request=request,
                accion="PLAN_INICIADO",
                tabla_afectada="plandetratamiento",
                registro_id=plan.id,
                valores_nuevos=f"Plan {plan.id} iniciado. Estado: {plan.estado_tratamiento}"
            )
            
            serializer = self.get_serializer(plan)
            return Response({
                'mensaje': 'Plan iniciado exitosamente',
                'plan': serializer.data
            })
        
        return Response(
            {'error': 'No se pudo iniciar el plan. Verifica que est� en estado Aceptado.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def pausar(self, request, pk=None):
        """
        Pausar la ejecuci�n del plan (En Ejecuci�n ? Pausado).
        
        POST /api/flujo-clinico/planes/{id}/pausar/
        Body: { "motivo": "Raz�n de la pausa" }
        
        Returns: Plan actualizado con estado 'Pausado'
        """
        plan = self.get_object()
        motivo = request.data.get('motivo', 'Pausado por solicitud')
        
        resultado = plan.pausar(motivo)
        
        if resultado:
            log_to_bitacora(
                request=request,
                accion="PLAN_PAUSADO",
                tabla_afectada="plandetratamiento",
                registro_id=plan.id,
                valores_nuevos=f"Plan {plan.id} pausado. Motivo: {motivo}"
            )
            
            serializer = self.get_serializer(plan)
            return Response({
                'mensaje': 'Plan pausado exitosamente',
                'plan': serializer.data
            })
        
        return Response(
            {'error': 'No se pudo pausar el plan. Verifica que est� En Ejecuci�n.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def reanudar(self, request, pk=None):
        """
        Reanudar la ejecuci�n del plan (Pausado ? En Ejecuci�n).
        
        POST /api/flujo-clinico/planes/{id}/reanudar/
        
        Returns: Plan actualizado con estado 'En Ejecuci�n'
        """
        plan = self.get_object()
        
        resultado = plan.reanudar()
        
        if resultado:
            log_to_bitacora(
                request=request,
                accion="PLAN_REANUDADO",
                tabla_afectada="plandetratamiento",
                registro_id=plan.id,
                valores_nuevos=f"Plan {plan.id} reanudado"
            )
            
            serializer = self.get_serializer(plan)
            return Response({
                'mensaje': 'Plan reanudado exitosamente',
                'plan': serializer.data
            })
        
        return Response(
            {'error': 'No se pudo reanudar el plan. Verifica que est� Pausado.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """
        Cancelar el plan (cualquier estado ? Cancelado).
        
        POST /api/flujo-clinico/planes/{id}/cancelar/
        Body: { "motivo": "Raz�n de cancelaci�n" }
        
        Returns: Plan actualizado con estado 'Cancelado'
        """
        plan = self.get_object()
        motivo = request.data.get('motivo', 'Cancelado por solicitud')
        
        if not motivo:
            return Response(
                {'error': 'Debe proporcionar un motivo de cancelaci�n'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        resultado = plan.cancelar(motivo)
        
        if resultado:
            log_to_bitacora(
                request=request,
                accion="PLAN_CANCELADO",
                tabla_afectada="plandetratamiento",
                registro_id=plan.id,
                valores_nuevos=f"Plan {plan.id} cancelado. Motivo: {motivo}"
            )
            
            serializer = self.get_serializer(plan)
            return Response({
                'mensaje': 'Plan cancelado exitosamente',
                'plan': serializer.data
            })
        
        return Response(
            {'error': 'No se pudo cancelar el plan'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def completar(self, request, pk=None):
        """
        Marcar el plan como completado (En Ejecuci�n ? Completado).
        Requiere que todos los items activos est�n ejecutados.
        
        POST /api/flujo-clinico/planes/{id}/completar/
        
        Returns: Plan actualizado con estado 'Completado'
        """
        plan = self.get_object()
        
        resultado = plan.marcar_completado()
        
        if resultado:
            log_to_bitacora(
                request=request,
                accion="PLAN_COMPLETADO",
                tabla_afectada="plandetratamiento",
                registro_id=plan.id,
                valores_nuevos=f"Plan {plan.id} completado manualmente"
            )
            
            serializer = self.get_serializer(plan)
            return Response({
                'mensaje': 'Plan completado exitosamente',
                'plan': serializer.data
            })
        
        return Response(
            {'error': 'No se pudo completar el plan. Verifica que todos los items est�n ejecutados.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['get'])
    def progreso(self, request, pk=None):
        """
        Calcular el progreso de ejecuci�n del plan (0-100%).
        
        GET /api/flujo-clinico/planes/{id}/progreso/
        
        Returns: Porcentaje de progreso e informaci�n de items
        """
        plan = self.get_object()
        progreso = plan.calcular_progreso_ejecucion()
        
        items = plan.itemplandetratamiento_set.filter(estado_item='Activo')
        total = items.count()
        ejecutados = items.filter(fecha_ejecucion__isnull=False).count()
        pendientes = total - ejecutados
        
        return Response({
            'plan_id': plan.id,
            'estado_tratamiento': plan.estado_tratamiento,
            'progreso_porcentaje': round(progreso, 2),
            'items_total': total,
            'items_ejecutados': ejecutados,
            'items_pendientes': pendientes,
            'fecha_inicio': plan.fecha_inicio_ejecucion,
            'fecha_finalizacion': plan.fecha_finalizacion
        })
    
    @action(detail=True, methods=['get'], url_path='siguiente-item')
    def siguiente_item(self, request, pk=None):
        """
        Obtener el siguiente item pendiente por ejecutar.
        
        GET /api/flujo-clinico/planes/{id}/siguiente-item/
        
        Returns: Pr�ximo item seg�n orden_ejecucion
        """
        plan = self.get_object()
        item = plan.get_siguiente_item_por_ejecutar()
        
        if item:
            serializer = ItemEjecucionSerializer(item)
            return Response({
                'tiene_siguiente': True,
                'item': serializer.data
            })
        
        return Response({
            'tiene_siguiente': False,
            'mensaje': 'No hay items pendientes por ejecutar'
        })
    
    @action(detail=True, methods=['get'], url_path='validar-consistencia')
    def validar_consistencia(self, request, pk=None):
        """
        Validar la consistencia del flujo cl�nico del plan.
        
        GET /api/flujo-clinico/planes/{id}/validar-consistencia/
        
        Returns: Estado de validaci�n con lista de errores
        """
        plan = self.get_object()
        es_valido, errores = plan.validar_consistencia_flujo()
        
        return Response({
            'es_valido': es_valido,
            'errores': errores,
            'plan_id': plan.id,
            'estado_tratamiento': plan.estado_tratamiento
        })


class ItemPlanTratamientoFlujoClincoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gesti�n de Items de Plan de Tratamiento.
    
    Endpoints:
    - GET /api/flujo-clinico/items/ - Listar items
    - GET /api/flujo-clinico/items/{id}/ - Detalle de item
    - POST /api/flujo-clinico/items/ - Crear item
    - PUT/PATCH /api/flujo-clinico/items/{id}/ - Actualizar item
    
    Acciones custom:
    - POST /api/flujo-clinico/items/{id}/ejecutar/ - Ejecutar item en consulta
    - POST /api/flujo-clinico/items/{id}/marcar_ejecutado/ - Marcar como ejecutado
    - POST /api/flujo-clinico/items/{id}/reprogramar/ - Cambiar orden de ejecuci�n
    - GET /api/flujo-clinico/items/{id}/validar_ejecucion/ - Validar si puede ejecutarse
    """
    serializer_class = ItemEjecucionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['idplantratamiento', 'estado_item', 'odontologo_ejecutor']
    ordering_fields = ['orden_ejecucion', 'fecha_ejecucion', 'iditemplan']
    ordering = ['orden_ejecucion']
    
    def get_queryset(self):
        """Filtrar por empresa del tenant actual"""
        return Itemplandetratamiento.objects.filter(
            empresa=self.request.tenant
        ).select_related(
            'idplantratamiento', 'idservicio', 'odontologo_ejecutor', 'consulta_ejecucion'
        )
    
    def perform_create(self, serializer):
        """Asignar empresa al crear"""
        item = serializer.save(empresa=self.request.tenant)
        
        log_to_bitacora(
            request=self.request,
            accion="ITEM_PLAN_CREADO",
            tabla_afectada="itemplandetratamiento",
            registro_id=item.id,
            valores_nuevos="Item de plan creado desde API flujo cl�nico"
        )
    
    @action(detail=True, methods=['post'])
    def ejecutar(self, request, pk=None):
        """
        Ejecutar el item en una consulta espec�fica.
        
        POST /api/flujo-clinico/items/{id}/ejecutar/
        Body:
        {
            "consulta_ejecucion": 123,
            "odontologo_ejecutor": 45,
            "notas_ejecucion": "Procedimiento realizado sin complicaciones"
        }
        
        Returns: Item actualizado con fecha_ejecucion
        """
        item = self.get_object()
        
        serializer = ItemEjecucionCreateSerializer(
            instance=item,
            data=request.data,
            context={'item': item}
        )
        
        if serializer.is_valid():
            with transaction.atomic():
                resultado = item.ejecutar_en_consulta(
                    consulta=serializer.validated_data['consulta_ejecucion'],
                    odontologo=serializer.validated_data['odontologo_ejecutor'],
                    notas=serializer.validated_data.get('notas_ejecucion', '')
                )
                
                if resultado:
                    log_to_bitacora(
                        request=request,
                        accion="ITEM_EJECUTADO",
                        tabla_afectada="itemplandetratamiento",
                        registro_id=item.id,
                        valores_nuevos=f"Item {item.id} ejecutado en consulta {item.consulta_ejecucion_id}"
                    )
                    
                    result_serializer = self.get_serializer(item)
                    return Response({
                        'mensaje': 'Item ejecutado exitosamente',
                        'item': result_serializer.data
                    })
                
                return Response(
                    {'error': 'No se pudo ejecutar el item'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='marcar-ejecutado')
    def marcar_ejecutado(self, request, pk=None):
        """
        Marcar el item como ejecutado (simplificado, sin consulta).
        
        POST /api/flujo-clinico/items/{id}/marcar-ejecutado/
        Body:
        {
            "odontologo_ejecutor": 45,
            "notas_ejecucion": "Notas opcionales"
        }
        
        Returns: Item actualizado
        """
        item = self.get_object()
        
        odontologo_id = request.data.get('odontologo_ejecutor')
        notas = request.data.get('notas_ejecucion', '')
        
        if not odontologo_id:
            return Response(
                {'error': 'Debe proporcionar odontologo_ejecutor'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener odontologo object
        try:
            from .models import Odontologo
            odontologo = Odontologo.objects.get(pk=odontologo_id, empresa=self.request.tenant)
        except Odontologo.DoesNotExist:
            return Response(
                {'error': 'Odontólogo no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        with transaction.atomic():
            resultado = item.marcar_ejecutado(
                odontologo=odontologo,
                notas=notas
            )
            
            if resultado:
                log_to_bitacora(
                    request=request,
                    accion="ITEM_MARCADO_EJECUTADO",
                    tabla_afectada="itemplandetratamiento",
                    registro_id=item.id,
                    valores_nuevos=f"Item {item.id} marcado como ejecutado"
                )
                
                serializer = self.get_serializer(item)
                return Response({
                    'mensaje': 'Item marcado como ejecutado',
                    'item': serializer.data
                })
            
            return Response(
                {'error': 'No se pudo marcar el item como ejecutado'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reprogramar(self, request, pk=None):
        """
        Reprogramar el orden de ejecuci�n del item.
        
        POST /api/flujo-clinico/items/{id}/reprogramar/
        Body: { "nuevo_orden": 3 }
        
        Returns: Item actualizado con nuevo orden
        """
        item = self.get_object()
        
        serializer = ItemReprogramarSerializer(
            data=request.data,
            context={'item': item}
        )
        
        if serializer.is_valid():
            nuevo_orden = serializer.validated_data['nuevo_orden']
            
            with transaction.atomic():
                resultado = item.reprogramar_orden(nuevo_orden)
                
                if resultado:
                    log_to_bitacora(
                        request=request,
                        accion="ITEM_REPROGRAMADO",
                        tabla_afectada="itemplandetratamiento",
                        registro_id=item.id,
                        valores_nuevos=f"Item {item.id} reprogramado a orden {nuevo_orden}"
                    )
                    
                    result_serializer = self.get_serializer(item)
                    return Response({
                        'mensaje': 'Item reprogramado exitosamente',
                        'item': result_serializer.data
                    })
                
                return Response(
                    {'error': 'No se pudo reprogramar el item'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='validar-ejecucion')
    def validar_ejecucion(self, request, pk=None):
        """
        Validar si el item puede ejecutarse ahora.
        
        GET /api/flujo-clinico/items/{id}/validar-ejecucion/
        
        Returns: Estado de validaci�n con mensaje
        """
        item = self.get_object()
        puede, mensaje = item.puede_ejecutarse()
        
        return Response({
            'puede_ejecutarse': puede,
            'mensaje': mensaje,
            'item_id': item.id,
            'orden_ejecucion': item.orden_ejecucion,
            'estado_item': item.estado_item,
            'esta_ejecutado': item.esta_ejecutado()
        })
