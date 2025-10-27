# -*- coding: utf-8 -*-
"""
Permissions personalizadas para Presupuestos Digitales.

SP3-T003: Aceptar Presupuesto Digital por Paciente
Fase 6: Permissions y Seguridad

Define permisos granulares para controlar el acceso a presupuestos digitales
y garantizar que solo los usuarios autorizados puedan realizar acciones.
"""
from rest_framework import permissions
import logging

logger = logging.getLogger(__name__)


class IsPacienteDelPresupuesto(permissions.BasePermission):
    """
    Permiso que verifica que el usuario autenticado sea el paciente
    del presupuesto que está intentando acceder o modificar.
    
    Se usa en acciones como:
    - Aceptar presupuesto
    - Ver detalles del presupuesto
    - Descargar comprobante
    """
    
    message = "No tienes permiso para acceder a este presupuesto. Solo el paciente asociado puede realizar esta acción."
    
    def has_permission(self, request, view):
        """
        Verifica que el usuario esté autenticado.
        La verificación específica del presupuesto se hace en has_object_permission.
        """
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Verifica que el usuario sea el paciente del presupuesto.
        
        Args:
            request: Request object
            view: View object
            obj: Instancia de PresupuestoDigital
        
        Returns:
            bool: True si el usuario es el paciente del presupuesto
        """
        try:
            # obj puede ser PresupuestoDigital o AceptacionPresupuestoDigital
            from api.models import PresupuestoDigital, AceptacionPresupuestoDigital
            
            # Si es una aceptación, obtener el presupuesto
            if isinstance(obj, AceptacionPresupuestoDigital):
                presupuesto = obj.presupuesto_digital
            else:
                presupuesto = obj
            
            # Verificar que el presupuesto tenga plan de tratamiento
            if not hasattr(presupuesto, 'plan_tratamiento') or not presupuesto.plan_tratamiento:
                logger.warning(f"Presupuesto {presupuesto.id} sin plan de tratamiento")
                return False
            
            plan = presupuesto.plan_tratamiento
            
            # Verificar que el plan tenga paciente
            if not hasattr(plan, 'codpaciente') or not plan.codpaciente:
                logger.warning(f"Plan {plan.id} sin paciente asociado")
                return False
            
            paciente = plan.codpaciente
            
            # Verificar que el paciente tenga usuario
            if not hasattr(paciente, 'codusuario') or not paciente.codusuario:
                logger.warning(f"Paciente {paciente.codigo} sin usuario asociado")
                return False
            
            usuario_paciente = paciente.codusuario
            
            # Obtener el Usuario actual por email (mismo patrón que mis-presupuestos)
            usuario_actual = None
            email = getattr(request.user, 'email', None)
            
            if not email:
                logger.warning(f"Django User {request.user.id} no tiene email")
                return False
            
            try:
                from api.models import Usuario
                # Buscar Usuario por email y empresa (tenant)
                usuario_actual = Usuario.objects.get(
                    correoelectronico=email,
                    empresa=request.tenant
                )
                logger.debug(f"Usuario encontrado por email: {usuario_actual.codigo} - {usuario_actual.nombre}")
            except Usuario.DoesNotExist:
                logger.warning(f"No existe Usuario con email {email} en empresa {request.tenant}")
                return False
            except Exception as e:
                logger.error(f"Error buscando Usuario: {e}")
                return False

            # Comparar códigos de usuario
            codigo_paciente = getattr(usuario_paciente, 'codigo', None)
            codigo_actual = getattr(usuario_actual, 'codigo', None)

            logger.debug(f"Comparando usuarios - Paciente: {codigo_paciente}, Actual: {codigo_actual}")

            if codigo_paciente and codigo_actual:
                es_paciente = (codigo_paciente == codigo_actual)

                if not es_paciente:
                    logger.info(
                        f"Acceso denegado: Usuario {codigo_actual} ({getattr(usuario_actual, 'nombreusuario', 'N/A')}) "
                        f"intentó acceder al presupuesto del paciente {codigo_paciente} ({getattr(usuario_paciente, 'nombreusuario', 'N/A')})"
                    )
                else:
                    logger.info(f"Acceso permitido: Usuario {codigo_actual} es el paciente del presupuesto")

                return es_paciente

            logger.warning(f"No se pudieron comparar códigos - codigo_paciente: {codigo_paciente}, codigo_actual: {codigo_actual}")
            return False
            
        except Exception as e:
            logger.error(f"Error verificando permiso IsPacienteDelPresupuesto: {str(e)}", exc_info=True)
            return False


class IsTenantMatch(permissions.BasePermission):
    """
    Permiso que verifica que el presupuesto pertenezca a la misma
    empresa (tenant) del usuario autenticado.
    
    Garantiza aislamiento multi-tenant.
    """
    
    message = "Este presupuesto no pertenece a tu clínica."
    
    def has_permission(self, request, view):
        """
        Verifica que el usuario esté autenticado y tenga empresa asociada.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Verificar que tengamos el tenant del middleware
        if hasattr(request, 'tenant') and request.tenant:
            return True
        
        # Si no hay tenant del middleware, verificar que el usuario tenga empresa
        if hasattr(request.user, 'usuario'):
            usuario = request.user.usuario
            if hasattr(usuario, 'empresa') and usuario.empresa:
                return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Verifica que el presupuesto pertenezca a la empresa del usuario.
        
        Args:
            request: Request object
            view: View object
            obj: Instancia de PresupuestoDigital
        
        Returns:
            bool: True si el presupuesto pertenece a la empresa del usuario
        """
        try:
            from api.models import PresupuestoDigital, AceptacionPresupuestoDigital
            
            # Obtener el presupuesto
            if isinstance(obj, AceptacionPresupuestoDigital):
                presupuesto = obj.presupuesto_digital
            else:
                presupuesto = obj
            
            # Obtener empresa del presupuesto
            empresa_presupuesto = getattr(presupuesto, 'empresa', None)
            if not empresa_presupuesto:
                logger.warning(f"Presupuesto {presupuesto.id} sin empresa asociada")
                return False
            
            # Obtener empresa del usuario (del tenant del middleware)
            if hasattr(request, 'tenant') and request.tenant:
                empresa_usuario = request.tenant
            else:
                # Fallback: obtener empresa del usuario directamente
                usuario = getattr(request.user, 'usuario', None)
                if not usuario:
                    logger.warning("Usuario sin perfil de Usuario model")
                    return False
                empresa_usuario = getattr(usuario, 'empresa', None)
            
            if not empresa_usuario:
                logger.warning("No se pudo determinar empresa del usuario")
                return False
            
            # Comparar empresas
            empresa_presupuesto_id = getattr(empresa_presupuesto, 'id', None)
            empresa_usuario_id = getattr(empresa_usuario, 'id', None)
            
            if empresa_presupuesto_id and empresa_usuario_id:
                es_misma_empresa = (empresa_presupuesto_id == empresa_usuario_id)
                
                if not es_misma_empresa:
                    logger.warning(
                        f"Tenant mismatch: Usuario de empresa {empresa_usuario_id} "
                        f"intentó acceder presupuesto de empresa {empresa_presupuesto_id}"
                    )
                
                return es_misma_empresa
            
            logger.warning("No se pudieron comparar IDs de empresa")
            return False
            
        except Exception as e:
            logger.error(f"Error verificando permiso IsTenantMatch: {str(e)}", exc_info=True)
            return False


class IsOdontologoDelPresupuesto(permissions.BasePermission):
    """
    Permiso que verifica que el usuario sea el odontólogo asociado
    al plan de tratamiento del presupuesto.
    
    Se usa para acciones administrativas como:
    - Emitir presupuesto
    - Anular presupuesto
    - Ver historial de aceptaciones
    """
    
    message = "No tienes permiso para gestionar este presupuesto. Solo el odontólogo asignado puede realizar esta acción."
    
    def has_permission(self, request, view):
        """
        Verifica que el usuario esté autenticado.
        """
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Verifica que el usuario sea el odontólogo del plan de tratamiento.
        """
        try:
            from api.models import PresupuestoDigital, AceptacionPresupuestoDigital
            
            # Obtener el presupuesto
            if isinstance(obj, AceptacionPresupuestoDigital):
                presupuesto = obj.presupuesto_digital
            else:
                presupuesto = obj
            
            # Verificar plan de tratamiento
            if not hasattr(presupuesto, 'plan_tratamiento') or not presupuesto.plan_tratamiento:
                return False
            
            plan = presupuesto.plan_tratamiento
            
            # Verificar odontólogo del plan
            if not hasattr(plan, 'cododontologo') or not plan.cododontologo:
                return False
            
            odontologo = plan.cododontologo
            
            # Verificar usuario del odontólogo
            if not hasattr(odontologo, 'codusuario') or not odontologo.codusuario:
                return False
            
            usuario_odontologo = odontologo.codusuario
            
            # Obtener usuario actual usando el mismo patrón que IsPacienteDelPresupuesto
            try:
                from api.models import Usuario
                usuario_actual = Usuario.objects.get(
                    correoelectronico=request.user.email,
                    empresa=request.tenant
                )
                logger.info(
                    f"✅ Usuario encontrado (IsOdontologoDelPresupuesto): "
                    f"{usuario_actual.codigo} - {usuario_actual.nombre} {usuario_actual.apellido}"
                )
            except Usuario.DoesNotExist:
                logger.warning(
                    f"❌ Usuario no encontrado para Django User: "
                    f"{request.user.email} (ID: {request.user.id})"
                )
                return False
            except Exception as e:
                logger.error(f"❌ Error al obtener Usuario: {str(e)}", exc_info=True)
                return False
            
            # Comparar códigos
            codigo_odontologo = getattr(usuario_odontologo, 'codigo', None)
            codigo_actual = getattr(usuario_actual, 'codigo', None)
            
            if codigo_odontologo and codigo_actual:
                es_odontologo = (codigo_odontologo == codigo_actual)
                if not es_odontologo:
                    logger.info(
                        f"🚫 Acceso denegado: Usuario {codigo_actual} "
                        f"intentó acceder al presupuesto del odontólogo {codigo_odontologo}"
                    )
                else:
                    logger.info(f"✅ Acceso permitido: Usuario {codigo_actual} es el odontólogo")
                return es_odontologo
            
            logger.warning("No se pudieron comparar códigos de usuario/odontólogo")
            return False
            
        except Exception as e:
            logger.error(f"Error verificando permiso IsOdontologoDelPresupuesto: {str(e)}", exc_info=True)
            return False


class CanViewPresupuesto(permissions.BasePermission):
    """
    Permiso compuesto que permite ver un presupuesto si el usuario es:
    - El paciente del presupuesto, O
    - El odontólogo del plan, O
    - Un administrador de la empresa
    """
    
    message = "No tienes permiso para ver este presupuesto."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Permite acceso si el usuario es paciente, odontólogo o admin.
        """
        # Verificar si es paciente
        paciente_permission = IsPacienteDelPresupuesto()
        if paciente_permission.has_object_permission(request, view, obj):
            return True
        
        # Verificar si es odontólogo
        odontologo_permission = IsOdontologoDelPresupuesto()
        if odontologo_permission.has_object_permission(request, view, obj):
            return True
        
        # Verificar si es admin (staff user de Django)
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Verificar si es admin de la empresa (rol Administrador)
        try:
            usuario = getattr(request.user, 'usuario', None)
            if usuario and hasattr(usuario, 'idtipousuario'):
                tipo_usuario = usuario.idtipousuario
                if tipo_usuario and hasattr(tipo_usuario, 'rol'):
                    if 'admin' in tipo_usuario.rol.lower():
                        # Verificar tenant match
                        tenant_permission = IsTenantMatch()
                        return tenant_permission.has_object_permission(request, view, obj)
        except Exception as e:
            logger.error(f"Error verificando si es admin: {str(e)}")
        
        return False


# ============================================================================
# THROTTLING CLASSES (Rate Limiting)
# ============================================================================

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class AceptacionPresupuestoRateThrottle(UserRateThrottle):
    """
    Throttle para limitar la cantidad de aceptaciones de presupuesto
    que un usuario puede hacer en un período de tiempo.
    
    Previene spam y uso abusivo del endpoint de aceptación.
    
    Rate: 10 aceptaciones por hora por usuario.
    """
    scope = 'aceptacion_presupuesto'
    rate = '10/hour'


class PresupuestoListRateThrottle(UserRateThrottle):
    """
    Throttle para limitar consultas a la lista de presupuestos.
    
    Rate: 100 requests por hora por usuario.
    """
    scope = 'presupuesto_list'
    rate = '100/hour'


class PresupuestoAnonRateThrottle(AnonRateThrottle):
    """
    Throttle para usuarios anónimos (sin autenticar).
    Más restrictivo que el de usuarios autenticados.
    
    Rate: 20 requests por día.
    """
    scope = 'presupuesto_anon'
    rate = '20/day'


logger.info("✅ Permissions y throttling classes para presupuestos digitales cargadas")
