# 🔍 Análisis de Bitácora - Campos Incorrectos en el Código

## 📊 Estado del Modelo Bitacora

**Modelo correcto** (`api/models.py`):
```python
class Bitacora(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, ...)
    accion = models.CharField(max_length=100)                     # ✅ OK
    tabla_afectada = models.CharField(max_length=100, ...)        # ✅ OK
    registro_id = models.IntegerField(null=True, blank=True)      # ✅ OK
    valores_anteriores = models.JSONField(null=True, blank=True)  # ✅ OK
    valores_nuevos = models.JSONField(null=True, blank=True)      # ✅ OK
    ip_address = models.GenericIPAddressField()                   # ✅ REQUERIDO
    user_agent = models.TextField()                               # ✅ REQUERIDO
    timestamp = models.DateTimeField(auto_now_add=True, ...)
    empresa = models.ForeignKey(Empresa, ...)
```

## ❌ Problemas Encontrados

### 1. api/serializers.py (línea 817) - Función auxiliar incorrecta

**Código actual:**
```python
def crear_registro_bitacora(accion, usuario=None, ip_address='127.0.0.1', descripcion='',
                            modelo_afectado=None, objeto_id=None, datos_adicionales=None):
    return Bitacora.objects.create(
        accion=accion,
        descripcion=descripcion,              # ❌ NO EXISTE
        usuario=usuario,
        ip_address=ip_address,
        modelo_afectado=modelo_afectado,      # ❌ NO EXISTE (debería ser tabla_afectada)
        objeto_id=objeto_id,                  # ❌ NO EXISTE (debería ser registro_id)
        datos_adicionales=datos_adicionales   # ❌ NO EXISTE (debería ser valores_nuevos)
    )
```

**Estado**: ⚠️ **FUNCIÓN NO USABLE** - Fallará si se ejecuta

### 2. api/views.py (línea 427) - Cancelar cita

**Código actual:**
```python
Bitacora.objects.create(
    accion='cancelar_cita',
    descripcion=f'Cita cancelada: {consulta_info}',  # ❌ NO EXISTE
    usuario=usuario,
    ip_address=get_client_ip(request),
    user_agent=request.META.get('HTTP_USER_AGENT', ''),
    modelo_afectado='Consulta',                       # ❌ NO EXISTE
    objeto_id=consulta_id,                            # ❌ NO EXISTE
    datos_adicionales={...}                           # ❌ NO EXISTE
)
```

**Estado**: ⚠️ **FALLA AL EJECUTAR** - Producirá error 500
**Impacto**: No se puede cancelar citas desde el sistema

### 3. api/views.py (línea 492) - Limpiar citas vencidas

**Código similar al anterior**

**Estado**: ⚠️ **FALLA AL EJECUTAR**
**Impacto**: La limpieza de citas vencidas falla

## ✅ Código Correcto Encontrado

### 1. api/views_auth.py (línea 303) - Login ✅
```python
Bitacora.objects.create(
    accion='login',
    tabla_afectada='auth_user',              # ✅ CORRECTO
    usuario=usuario,
    empresa=tenant,
    ip_address=_client_ip(request),
    user_agent=request.META.get('HTTP_USER_AGENT', ''),
    valores_nuevos={'email': email, ...}     # ✅ CORRECTO
)
```

### 2. api/views.py (línea 1589) - Método auxiliar ✅
```python
def _crear_bitacora(self, request, accion, descripcion, modelo, objeto_id):
    Bitacora.objects.create(
        accion=accion,
        tabla_afectada=modelo,               # ✅ CORRECTO
        registro_id=objeto_id,               # ✅ CORRECTO
        usuario=request.user,
        ip_address=self._get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
        empresa=getattr(request, 'tenant', None)
    )
```

### 3. api/middleware.py (línea 275) - Middleware de auditoría ✅
```python
Bitacora.objects.create(
    accion=accion,
    usuario=usuario,
    empresa=empresa,
    ip_address=ip_address,
    user_agent=user_agent,
    tabla_afectada=modelo_afectado,          # ✅ CORRECTO
    registro_id=objeto_id,                   # ✅ CORRECTO
    valores_anteriores={...}                 # ✅ CORRECTO
)
```

### 4. api/views_user_creation.py (línea 132) - ✅ YA CORREGIDO
```python
Bitacora.objects.create(
    empresa=empresa,
    usuario=usuario_actual,
    accion=f"CREAR_USUARIO_{usuario_creado.idtipousuario.rol.upper()}",
    tabla_afectada="usuario",
    registro_id=usuario_creado.codigo,
    valores_nuevos={...},
    ip_address=ip_address,
    user_agent=user_agent
)
```

## 🔧 Fixes Pendientes

### Fix 1: api/serializers.py - Función auxiliar

**REEMPLAZAR:**
```python
def crear_registro_bitacora(accion, usuario=None, ip_address='127.0.0.1', descripcion='',
                            modelo_afectado=None, objeto_id=None, datos_adicionales=None):
    """
    Función auxiliar para crear registros de bitácora desde las vistas
    """
    return Bitacora.objects.create(
        accion=accion,
        descripcion=descripcion,
        usuario=usuario,
        ip_address=ip_address,
        modelo_afectado=modelo_afectado,
        objeto_id=objeto_id,
        datos_adicionales=datos_adicionales or {}
    )
```

**POR:**
```python
def crear_registro_bitacora(accion, usuario=None, ip_address='127.0.0.1', 
                            tabla_afectada=None, registro_id=None, 
                            valores_nuevos=None, valores_anteriores=None,
                            empresa=None, user_agent='Unknown'):
    """
    Función auxiliar para crear registros de bitácora desde las vistas.
    
    Args:
        accion: Descripción de la acción realizada
        usuario: Usuario que realizó la acción
        ip_address: IP del cliente
        tabla_afectada: Nombre de la tabla/modelo afectado
        registro_id: ID del registro afectado
        valores_nuevos: Dict con los valores nuevos (para creaciones/ediciones)
        valores_anteriores: Dict con los valores anteriores (para ediciones/eliminaciones)
        empresa: Empresa/tenant relacionada
        user_agent: User-Agent del cliente
    """
    return Bitacora.objects.create(
        accion=accion,
        usuario=usuario,
        ip_address=ip_address,
        user_agent=user_agent,
        tabla_afectada=tabla_afectada,
        registro_id=registro_id,
        valores_nuevos=valores_nuevos or {},
        valores_anteriores=valores_anteriores,
        empresa=empresa
    )
```

### Fix 2: api/views.py - Cancelar cita (línea ~427)

**REEMPLAZAR:**
```python
from api.middleware import get_client_ip
Bitacora.objects.create(
    accion='cancelar_cita',
    descripcion=f'Cita cancelada: {consulta_info}',
    usuario=usuario,
    ip_address=get_client_ip(request),
    user_agent=request.META.get('HTTP_USER_AGENT', ''),
    modelo_afectado='Consulta',
    objeto_id=consulta_id,
    datos_adicionales={
        'fecha': str(consulta.fecha),
        'horario': consulta.idhorario.hora if consulta.idhorario else 'N/A',
        'odontologo': f"{consulta.cododontologo.codusuario.nombre} {consulta.cododontologo.codusuario.apellido}" if consulta.cododontologo else 'N/A'
    }
)
```

**POR:**
```python
from api.middleware import get_client_ip
Bitacora.objects.create(
    accion='CANCELAR_CITA',
    usuario=usuario,
    ip_address=get_client_ip(request),
    user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown'),
    tabla_afectada='consulta',
    registro_id=consulta_id,
    empresa=getattr(request, 'tenant', None),
    valores_anteriores={
        'estado': consulta.idestadoconsulta.estado if consulta.idestadoconsulta else 'N/A',
        'fecha': str(consulta.fecha),
        'horario': consulta.idhorario.hora if consulta.idhorario else 'N/A',
        'odontologo': f"{consulta.cododontologo.codusuario.nombre} {consulta.cododontologo.codusuario.apellido}" if consulta.cododontologo else 'N/A'
    },
    valores_nuevos={
        'estado': 'Cancelada',
        'info': consulta_info
    }
)
```

### Fix 3: api/views.py - Limpiar citas vencidas (línea ~492)

**REEMPLAZAR:**
```python
from api.middleware import get_client_ip
Bitacora.objects.create(
    accion='limpiar_citas_vencidas',
    descripcion=f'Eliminadas {cantidad} citas vencidas',
    usuario=usuario,
    ip_address=get_client_ip(request),
    user_agent=request.META.get('HTTP_USER_AGENT', ''),
    modelo_afectado='Consulta',
    datos_adicionales={
        'cantidad_eliminadas': cantidad,
        'fecha_limpieza': str(date.today())
    }
)
```

**POR:**
```python
from api.middleware import get_client_ip
Bitacora.objects.create(
    accion='LIMPIAR_CITAS_VENCIDAS',
    usuario=usuario,
    ip_address=get_client_ip(request),
    user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown'),
    tabla_afectada='consulta',
    empresa=getattr(request, 'tenant', None),
    valores_nuevos={
        'cantidad_eliminadas': cantidad,
        'fecha_limpieza': str(date.today())
    }
)
```

## 📋 Resumen de Acciones

| Archivo | Línea | Estado | Prioridad | Impacto |
|---------|-------|--------|-----------|---------|
| api/views_user_creation.py | 132 | ✅ CORREGIDO | ✅ | Crear usuarios |
| api/serializers.py | 817 | ❌ PENDIENTE | 🟡 MEDIA | Función no usada actualmente |
| api/views.py | 427 | ❌ PENDIENTE | 🔴 ALTA | Cancelar citas falla |
| api/views.py | 492 | ❌ PENDIENTE | 🟠 MEDIA-ALTA | Limpieza automática falla |
| api/views_auth.py | 303 | ✅ CORRECTO | - | Login funciona |
| api/middleware.py | 275 | ✅ CORRECTO | - | Auditoría general |
| api/views.py | 1589 | ✅ CORRECTO | - | Método auxiliar bueno |

## 🎯 Próximos Pasos

1. ✅ **COMPLETADO**: Fix en creación de usuarios
2. ⚠️ **URGENTE**: Fix en cancelación de citas (línea 427)
3. ⚠️ **IMPORTANTE**: Fix en limpieza de citas (línea 492)
4. 🟡 **OPCIONAL**: Fix en función auxiliar (línea 817) - no se usa actualmente

## 💡 Recomendación

**Crear una función helper centralizada** que todos los endpoints usen:

```python
# En api/utils_bitacora.py (nuevo archivo)
from api.models import Bitacora

def registrar_en_bitacora(request, accion, tabla_afectada=None, registro_id=None,
                          valores_nuevos=None, valores_anteriores=None):
    """
    Función centralizada para registrar en bitácora.
    Maneja automáticamente IP, User-Agent, empresa y usuario.
    """
    from api.middleware import get_client_ip
    
    try:
        # Obtener usuario
        usuario = None
        if request.user.is_authenticated:
            from api.models import Usuario
            try:
                usuario = Usuario.objects.get(correoelectronico__iexact=request.user.email)
            except Usuario.DoesNotExist:
                pass
        
        # Crear bitácora
        Bitacora.objects.create(
            accion=accion,
            usuario=usuario,
            empresa=getattr(request, 'tenant', None),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown')[:255],
            tabla_afectada=tabla_afectada,
            registro_id=registro_id,
            valores_nuevos=valores_nuevos,
            valores_anteriores=valores_anteriores
        )
    except Exception as e:
        # No fallar la operación principal si falla la bitácora
        import logging
        logging.error(f"Error al registrar bitácora: {e}")
```

Y luego usarla en todos lados:
```python
from api.utils_bitacora import registrar_en_bitacora

# En cualquier vista:
registrar_en_bitacora(
    request,
    accion='CREAR_USUARIO_PACIENTE',
    tabla_afectada='usuario',
    registro_id=usuario.codigo,
    valores_nuevos={'nombre': usuario.nombre, ...}
)
```
