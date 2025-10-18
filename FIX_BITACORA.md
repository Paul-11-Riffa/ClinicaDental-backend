# 🔧 Fix: Error en Bitácora - Creación de Usuarios

## 📋 Problema Identificado

El frontend reportó error 500 al crear usuarios, aunque los usuarios **SÍ se estaban creando correctamente** en la base de datos.

### ❌ Error Original
```python
# En api/views_user_creation.py línea 128
Bitacora.objects.create(
    empresa=empresa,
    usuario=usuario_actual,
    accion=f"CREAR_USUARIO_{usuario_creado.idtipousuario.rol.upper()}",
    tabla_afectada="usuario",
    detalles=f"Usuario creado: ..."  # ❌ Campo 'detalles' NO EXISTE
)
```

### 🔍 Causa del Error

El modelo `Bitacora` en `api/models.py` **NO tiene el campo `detalles`** (ni `detalle`).

**Campos correctos del modelo Bitacora:**
```python
class Bitacora(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, ...)
    accion = models.CharField(max_length=100)
    tabla_afectada = models.CharField(max_length=100, null=True, blank=True)
    registro_id = models.IntegerField(null=True, blank=True)
    valores_anteriores = models.JSONField(null=True, blank=True)  # ✅ Para ediciones
    valores_nuevos = models.JSONField(null=True, blank=True)      # ✅ Para creaciones
    ip_address = models.GenericIPAddressField()                   # ⚠️ REQUERIDO
    user_agent = models.TextField()                               # ⚠️ REQUERIDO
    timestamp = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    empresa = models.ForeignKey(Empresa, ...)
```

## ✅ Solución Implementada

### Cambios en `api/views_user_creation.py`

**ANTES (líneas 126-134):**
```python
# Registrar en bitácora
Bitacora.objects.create(
    empresa=empresa,
    usuario=usuario_actual,
    accion=f"CREAR_USUARIO_{usuario_creado.idtipousuario.rol.upper()}",
    tabla_afectada="usuario",
    detalles=f"Usuario creado: {usuario_creado.nombre} {usuario_creado.apellido} "
            f"(ID: {usuario_creado.codigo}, Email: {usuario_creado.correoelectronico}, "
            f"Tipo: {usuario_creado.idtipousuario.rol})"
)
```

**DESPUÉS (líneas 126-148):**
```python
# Obtener IP y User-Agent del request
ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')
user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')

# Registrar en bitácora
Bitacora.objects.create(
    empresa=empresa,
    usuario=usuario_actual,
    accion=f"CREAR_USUARIO_{usuario_creado.idtipousuario.rol.upper()}",
    tabla_afectada="usuario",
    registro_id=usuario_creado.codigo,
    valores_nuevos={
        'codigo': usuario_creado.codigo,
        'nombre': usuario_creado.nombre,
        'apellido': usuario_creado.apellido,
        'correoelectronico': usuario_creado.correoelectronico,
        'tipo_usuario': usuario_creado.idtipousuario.rol,
        'telefono': usuario_creado.telefono,
        'sexo': usuario_creado.sexo,
    },
    ip_address=ip_address,
    user_agent=user_agent
)
```

### Mejoras Implementadas

1. ✅ **Campo `valores_nuevos`**: Ahora se registra un JSON completo con todos los datos del usuario creado
2. ✅ **Campo `registro_id`**: Se guarda el ID del usuario creado para referencia directa
3. ✅ **Campo `ip_address`**: Se obtiene la IP real del cliente desde el request
4. ✅ **Campo `user_agent`**: Se registra el navegador/cliente que hizo la petición
5. ✅ **Datos estructurados**: Uso de JSON en lugar de texto plano para mejor consulta

## 🧪 Pruebas Realizadas

### Test 1: Creación de Usuario con Bitácora
```bash
python test_bitacora_fix.py
```

**Resultado:**
```
✅ Usuario creado: ID 33
✅ Bitácora registrada correctamente
📋 Última bitácora:
   Acción: CREAR_USUARIO_PACIENTE
   Tabla: usuario
   Registro ID: 33
   IP: 192.168.1.100
   User-Agent: Test Script
   Valores Nuevos: {'codigo': 33, 'nombre': 'Test Bitácora', ...}
```

### Test 2: Creación desde Frontend
El frontend ahora puede crear usuarios sin recibir error 500.

## 📊 Verificación de Bitácoras

Para ver todas las bitácoras registradas:
```bash
python ver_bitacoras.py
```

Para ver bitácoras de SmileStudio:
```python
from api.models import Bitacora, Empresa

empresa = Empresa.objects.get(subdomain="smilestudio")
bitacoras = Bitacora.objects.filter(empresa=empresa).order_by('-timestamp')

for b in bitacoras:
    print(f"[{b.id}] {b.accion} - Usuario #{b.registro_id} - {b.timestamp}")
```

## 🎯 Impacto del Fix

### ✅ Beneficios
1. **Frontend funcional**: Ya no hay error 500 al crear usuarios
2. **Auditoría completa**: Se registra quién, cuándo, desde dónde y qué creó
3. **Trazabilidad**: Los datos en formato JSON permiten consultas y reportes
4. **Cumplimiento**: Se registra IP y User-Agent para auditoría de seguridad

### 📈 Datos Registrados Ahora
- **Quién**: Usuario que hizo la acción (o "Sistema" si es automático)
- **Qué**: Tipo de acción (CREAR_USUARIO_PACIENTE, CREAR_USUARIO_ODONTOLOGO, etc.)
- **Cuándo**: Timestamp automático
- **Dónde**: IP address del cliente
- **Cómo**: User-Agent (navegador/app)
- **Detalles**: JSON completo con todos los datos del usuario creado

## 🔄 Próximos Pasos Recomendados

### 1. Aplicar mismo patrón en otras operaciones
Buscar otros lugares donde se use `Bitacora.objects.create()` y verificar:
```bash
grep -r "Bitacora.objects.create" api/
```

### 2. Agregar bitácora en operaciones de edición
Para ediciones de usuarios, usar también `valores_anteriores`:
```python
Bitacora.objects.create(
    ...
    accion="EDITAR_USUARIO",
    registro_id=usuario.codigo,
    valores_anteriores={'nombre': 'Nombre Viejo', ...},
    valores_nuevos={'nombre': 'Nombre Nuevo', ...},
    ip_address=ip_address,
    user_agent=user_agent
)
```

### 3. Agregar bitácora en eliminaciones
```python
Bitacora.objects.create(
    ...
    accion="ELIMINAR_USUARIO",
    registro_id=usuario.codigo,
    valores_anteriores={'nombre': usuario.nombre, 'email': usuario.email, ...},
    ip_address=ip_address,
    user_agent=user_agent
)
```

## 📝 Archivos Modificados

- ✅ `api/views_user_creation.py` - Fix en líneas 126-148
- ✅ `api/serializers_user_creation.py` - Agregado método `create()` en CrearUsuarioRequestSerializer

## 🧪 Archivos de Test Creados

- ✅ `test_bitacora_fix.py` - Test de creación de usuario con bitácora
- ✅ `ver_bitacoras.py` - Script para visualizar bitácoras registradas
- ✅ `test_crear_usuarios_ejemplos.py` - Tests completos de los 4 tipos de usuario

## ✨ Resumen

**Antes**: Error 500 al crear usuarios (campo `detalles` no existe)  
**Después**: ✅ Usuarios se crean correctamente + Auditoría completa en bitácora

**Estado actual**: 🟢 **TODO FUNCIONANDO CORRECTAMENTE**
