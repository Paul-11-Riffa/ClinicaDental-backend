"""
Signals para gestión automática de roles de usuarios
Cuando un Usuario cambia su idtipousuario (rol), este signal:
1. Elimina el registro del rol anterior (Paciente/Odontologo/Recepcionista)
2. Crea el registro del nuevo rol
3. Mantiene la consistencia de la base de datos
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
import logging

from .models import Usuario, Paciente, Odontologo, Recepcionista, Tipodeusuario

logger = logging.getLogger(__name__)


# Mapeo de IDs de roles según inicializar_datos.py
# 1 = Administrador, 2 = Paciente, 3 = Odontologo, 4 = Recepcionista
ROLE_MAPPING = {
    'administrador': 1,
    'paciente': 2,
    'odontologo': 3,
    'recepcionista': 4,
}


def _es_creacion_inicial(usuario):
    """
    Verifica si el usuario está siendo creado inicialmente (no es un cambio de rol)
    Detecta el flag especial _skip_signals que se establece durante la creación
    """
    return getattr(usuario, '_skip_signals', False)


def _obtener_rol_nombre(tipo_usuario_id):
    """Obtiene el nombre del rol basado en el ID del tipo de usuario"""
    try:
        tipo = Tipodeusuario.objects.get(id=tipo_usuario_id)
        return tipo.rol.lower().strip()
    except Tipodeusuario.DoesNotExist:
        return None


def _verificar_relaciones(usuario):
    """
    Verifica si el usuario tiene relaciones que impidan eliminar su perfil
    Retorna: (tiene_relaciones, descripcion)
    """
    from .models import Consulta, Plandetratamiento, Recetamedica
    
    relaciones = []
    
    # Verificar si tiene Paciente con relaciones
    try:
        paciente = Paciente.objects.get(codusuario=usuario)
        
        # Consultas como paciente
        consultas_count = Consulta.objects.filter(codpaciente=paciente).count()
        if consultas_count > 0:
            relaciones.append(f"{consultas_count} consulta(s) como paciente")
        
        # Planes de tratamiento
        planes_count = Plandetratamiento.objects.filter(codpaciente=paciente).count()
        if planes_count > 0:
            relaciones.append(f"{planes_count} plan(es) de tratamiento")
        
        # Recetas médicas
        recetas_count = Recetamedica.objects.filter(codpaciente=paciente).count()
        if recetas_count > 0:
            relaciones.append(f"{recetas_count} receta(s) médica(s)")
    except Paciente.DoesNotExist:
        pass
    
    # Verificar si tiene Odontologo con relaciones
    try:
        odontologo = Odontologo.objects.get(codusuario=usuario)
        
        # Consultas como odontólogo
        consultas_count = Consulta.objects.filter(cododontologo=odontologo).count()
        if consultas_count > 0:
            relaciones.append(f"{consultas_count} consulta(s) como odontólogo")
        
        # Planes de tratamiento
        planes_count = Plandetratamiento.objects.filter(cododontologo=odontologo).count()
        if planes_count > 0:
            relaciones.append(f"{planes_count} plan(es) de tratamiento como odontólogo")
        
        # Recetas médicas
        recetas_count = Recetamedica.objects.filter(cododontologo=odontologo).count()
        if recetas_count > 0:
            relaciones.append(f"{recetas_count} receta(s) como odontólogo")
    except Odontologo.DoesNotExist:
        pass
    
    # Verificar si tiene Recepcionista con relaciones
    try:
        recepcionista = Recepcionista.objects.get(codusuario=usuario)
        
        # Consultas como recepcionista
        consultas_count = Consulta.objects.filter(codrecepcionista=recepcionista).count()
        if consultas_count > 0:
            relaciones.append(f"{consultas_count} consulta(s) como recepcionista")
    except Recepcionista.DoesNotExist:
        pass
    
    if relaciones:
        return True, ", ".join(relaciones)
    return False, None


def _eliminar_perfil_antiguo(usuario):
    """
    Elimina todos los perfiles específicos del usuario (Paciente, Odontologo, Recepcionista)
    Solo elimina si no hay relaciones que lo impidan
    """
    from django.db import IntegrityError
    
    eliminados = []
    errores = []
    
    # Intentar eliminar perfil de Paciente
    try:
        paciente = Paciente.objects.get(codusuario=usuario)
        try:
            paciente.delete()
            eliminados.append('Paciente')
            logger.info(f"🗑️ Perfil de Paciente eliminado para usuario {usuario.codigo}")
        except IntegrityError as e:
            error_msg = f"No se puede eliminar perfil de Paciente (tiene datos relacionados)"
            errores.append(error_msg)
            logger.warning(f"⚠️ {error_msg} para usuario {usuario.codigo}")
    except Paciente.DoesNotExist:
        pass
    
    # Intentar eliminar perfil de Odontologo
    try:
        odontologo = Odontologo.objects.get(codusuario=usuario)
        try:
            odontologo.delete()
            eliminados.append('Odontologo')
            logger.info(f"🗑️ Perfil de Odontologo eliminado para usuario {usuario.codigo}")
        except IntegrityError as e:
            error_msg = f"No se puede eliminar perfil de Odontologo (tiene datos relacionados)"
            errores.append(error_msg)
            logger.warning(f"⚠️ {error_msg} para usuario {usuario.codigo}")
    except Odontologo.DoesNotExist:
        pass
    
    # Intentar eliminar perfil de Recepcionista
    try:
        recepcionista = Recepcionista.objects.get(codusuario=usuario)
        try:
            recepcionista.delete()
            eliminados.append('Recepcionista')
            logger.info(f"🗑️ Perfil de Recepcionista eliminado para usuario {usuario.codigo}")
        except IntegrityError as e:
            error_msg = f"No se puede eliminar perfil de Recepcionista (tiene datos relacionados)"
            errores.append(error_msg)
            logger.warning(f"⚠️ {error_msg} para usuario {usuario.codigo}")
    except Recepcionista.DoesNotExist:
        pass
    
    return eliminados, errores


def _crear_perfil_nuevo(usuario, nuevo_rol):
    """Crea el perfil específico según el nuevo rol"""
    empresa = usuario.empresa
    
    if nuevo_rol == 'paciente':
        # Verificar que no exista ya
        if not Paciente.objects.filter(codusuario=usuario).exists():
            Paciente.objects.create(
                codusuario=usuario,
                empresa=empresa,
                carnetidentidad=None,
                fechanacimiento=None,
                direccion=None
            )
            logger.info(f"✅ Perfil de Paciente creado para usuario {usuario.codigo}")
            return 'Paciente'
    
    elif nuevo_rol == 'odontologo':
        # Verificar que no exista ya
        if not Odontologo.objects.filter(codusuario=usuario).exists():
            Odontologo.objects.create(
                codusuario=usuario,
                empresa=empresa,
                especialidad='',
                experienciaprofesional='',
                nromatricula=None
            )
            logger.info(f"✅ Perfil de Odontologo creado para usuario {usuario.codigo}")
            return 'Odontologo'
    
    elif nuevo_rol == 'recepcionista':
        # Verificar que no exista ya
        if not Recepcionista.objects.filter(codusuario=usuario).exists():
            Recepcionista.objects.create(
                codusuario=usuario,
                empresa=empresa,
                habilidadessoftware=''
            )
            logger.info(f"✅ Perfil de Recepcionista creado para usuario {usuario.codigo}")
            return 'Recepcionista'
    
    elif nuevo_rol == 'administrador':
        # Administrador no requiere perfil específico
        logger.info(f"ℹ️ Usuario {usuario.codigo} es ahora Administrador (sin perfil específico)")
        return 'Administrador'
    
    return None


@receiver(pre_save, sender=Usuario)
def guardar_rol_anterior(sender, instance, **kwargs):
    """
    Pre-save signal para guardar el rol anterior del usuario
    Solo se ejecuta si el usuario ya existe (update)
    """
    if instance.pk:  # Solo si es un update (el usuario ya existe)
        try:
            # Obtener el usuario actual de la base de datos
            usuario_anterior = Usuario.objects.get(pk=instance.pk)
            # Guardar el rol anterior como atributo temporal
            instance._rol_anterior_id = usuario_anterior.idtipousuario_id
        except Usuario.DoesNotExist:
            instance._rol_anterior_id = None
    else:
        instance._rol_anterior_id = None


@receiver(post_save, sender=Usuario)
def sincronizar_perfil_rol(sender, instance, created, **kwargs):
    """
    Post-save signal para sincronizar el perfil específico cuando cambia el rol
    
    Casos:
    1. Creación de usuario nuevo → crear perfil según el rol
    2. Cambio de rol → eliminar perfil anterior y crear nuevo (si es posible)
    3. Sin cambio de rol → no hacer nada
    
    IMPORTANTE: Si el usuario tiene datos relacionados (consultas, planes, etc.),
    NO se elimina el perfil anterior para mantener la integridad referencial.
    En este caso, el usuario tendrá múltiples perfiles hasta que se limpien los datos.
    """
    
    # Si tiene el flag _skip_signals, omitir completamente el signal
    # Esto se usa durante la creación inicial desde serializers de creación
    if _es_creacion_inicial(instance):
        logger.info(f"⏭️ Saltando signal para usuario {instance.codigo} (creación inicial)")
        return
    
    # Evitar recursión infinita
    if hasattr(instance, '_sincronizando_perfil'):
        return
    
    try:
        instance._sincronizando_perfil = True
        
        with transaction.atomic():
            nuevo_rol_id = instance.idtipousuario_id
            nuevo_rol = _obtener_rol_nombre(nuevo_rol_id)
            
            if not nuevo_rol:
                logger.warning(f"⚠️ No se pudo determinar el rol para tipo_usuario_id={nuevo_rol_id}")
                return
            
            if created:
                # CASO 1: Usuario recién creado
                logger.info(f"🆕 Creando usuario {instance.codigo} con rol {nuevo_rol}")
                perfil_creado = _crear_perfil_nuevo(instance, nuevo_rol)
                if perfil_creado:
                    logger.info(f"✅ Usuario {instance.codigo} creado con perfil {perfil_creado}")
            
            else:
                # CASO 2: Usuario existente - verificar si cambió el rol
                rol_anterior_id = getattr(instance, '_rol_anterior_id', None)
                
                if rol_anterior_id and rol_anterior_id != nuevo_rol_id:
                    # El rol SÍ cambió
                    rol_anterior = _obtener_rol_nombre(rol_anterior_id)
                    
                    logger.info(f"🔄 Cambiando rol de usuario {instance.codigo}: {rol_anterior} → {nuevo_rol}")
                    
                    # Verificar si tiene relaciones que impidan el cambio
                    tiene_relaciones, descripcion_relaciones = _verificar_relaciones(instance)
                    
                    if tiene_relaciones:
                        logger.warning(
                            f"⚠️ Usuario {instance.codigo} tiene datos relacionados: {descripcion_relaciones}"
                        )
                        logger.warning(
                            f"⚠️ NO se eliminará el perfil anterior. El usuario tendrá múltiples perfiles."
                        )
                        logger.warning(
                            f"⚠️ Para eliminar el perfil antiguo, primero elimina o reasigna: {descripcion_relaciones}"
                        )
                        
                        # Solo crear el nuevo perfil, NO eliminar el anterior
                        perfil_creado = _crear_perfil_nuevo(instance, nuevo_rol)
                        
                        logger.warning(
                            f"⚠️ Cambio de rol parcial para usuario {instance.codigo}: "
                            f"Perfil anterior mantenido, Creado: {perfil_creado or 'ninguno'}"
                        )
                    else:
                        # No tiene relaciones, se puede eliminar el perfil anterior
                        eliminados, errores = _eliminar_perfil_antiguo(instance)
                        
                        if errores:
                            logger.error(
                                f"❌ Errores al eliminar perfiles de usuario {instance.codigo}: {errores}"
                            )
                            # Aun con errores, intentar crear el nuevo perfil
                        
                        # Crear nuevo perfil según el nuevo rol
                        perfil_creado = _crear_perfil_nuevo(instance, nuevo_rol)
                        
                        logger.info(
                            f"✅ Cambio de rol completado para usuario {instance.codigo}: "
                            f"Eliminados: {eliminados or 'ninguno'}, Creado: {perfil_creado or 'ninguno'}"
                        )
                
                # Si no cambió el rol, no hacer nada
    
    except Exception as e:
        logger.error(f"❌ Error sincronizando perfil de usuario {instance.codigo}: {str(e)}")
        # NO hacer raise para evitar que falle el guardado del usuario
        # El usuario se guardará pero sin sincronización de perfil
    
    finally:
        # Limpiar flag de sincronización
        if hasattr(instance, '_sincronizando_perfil'):
            delattr(instance, '_sincronizando_perfil')
        if hasattr(instance, '_rol_anterior_id'):
            delattr(instance, '_rol_anterior_id')


# ============================
# Función auxiliar para uso manual
# ============================

def reparar_inconsistencias_roles():
    """
    Función auxiliar para reparar usuarios con roles inconsistentes
    Útil para ejecutar una vez y limpiar datos históricos
    
    IMPORTANTE: No forzará la eliminación de perfiles con datos relacionados.
    """
    logger.info("🔧 Iniciando reparación de inconsistencias de roles...")
    
    usuarios = Usuario.objects.all()
    reparados = 0
    advertencias = 0
    
    for usuario in usuarios:
        rol = _obtener_rol_nombre(usuario.idtipousuario_id)
        if not rol:
            continue
        
        # Verificar consistencia
        tiene_paciente = Paciente.objects.filter(codusuario=usuario).exists()
        tiene_odontologo = Odontologo.objects.filter(codusuario=usuario).exists()
        tiene_recepcionista = Recepcionista.objects.filter(codusuario=usuario).exists()
        
        # Contar cuántos perfiles tiene
        perfiles_count = sum([tiene_paciente, tiene_odontologo, tiene_recepcionista])
        
        # Caso 1: Tiene múltiples perfiles (inconsistencia)
        if perfiles_count > 1:
            logger.warning(f"⚠️ Usuario {usuario.codigo} tiene múltiples perfiles. Verificando relaciones...")
            
            # Verificar si tiene relaciones
            tiene_relaciones, descripcion = _verificar_relaciones(usuario)
            
            if tiene_relaciones:
                logger.warning(
                    f"⚠️ Usuario {usuario.codigo} tiene datos relacionados: {descripcion}"
                )
                logger.warning(
                    f"⚠️ NO se pueden eliminar perfiles automáticamente. Requiere intervención manual."
                )
                advertencias += 1
            else:
                # Intentar corregir
                eliminados, errores = _eliminar_perfil_antiguo(usuario)
                if not errores:
                    _crear_perfil_nuevo(usuario, rol)
                    reparados += 1
                else:
                    advertencias += 1
        
        # Caso 2: Tiene perfil que no corresponde con su rol
        elif (rol == 'paciente' and not tiene_paciente) or \
             (rol == 'odontologo' and not tiene_odontologo) or \
             (rol == 'recepcionista' and not tiene_recepcionista):
            logger.warning(f"⚠️ Usuario {usuario.codigo} no tiene el perfil correcto. Creando...")
            _crear_perfil_nuevo(usuario, rol)
            reparados += 1
        
        # Caso 3: Es admin/otro pero tiene perfiles específicos
        elif rol in ['administrador'] and perfiles_count > 0:
            logger.warning(f"⚠️ Usuario {usuario.codigo} es {rol} pero tiene perfiles.")
            
            # Verificar si tiene relaciones
            tiene_relaciones, descripcion = _verificar_relaciones(usuario)
            
            if tiene_relaciones:
                logger.warning(
                    f"⚠️ Usuario {usuario.codigo} tiene datos relacionados: {descripcion}"
                )
                logger.warning(
                    f"⚠️ NO se pueden eliminar perfiles. Requiere intervención manual."
                )
                advertencias += 1
            else:
                eliminados, errores = _eliminar_perfil_antiguo(usuario)
                if not errores:
                    reparados += 1
                else:
                    advertencias += 1
    
    logger.info(f"✅ Reparación completada. {reparados} usuarios corregidos, {advertencias} con advertencias.")
    return reparados
