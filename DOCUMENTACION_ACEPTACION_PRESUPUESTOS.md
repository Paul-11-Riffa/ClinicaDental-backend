# SP3-T003: API de Aceptación de Presupuestos por Paciente

## 📋 Descripción General

Esta funcionalidad permite que un paciente autenticado acepte un presupuesto dental, ya sea en su totalidad o seleccionando ítems específicos, registrando su consentimiento con firma electrónica simple y sello de tiempo.

---

## 🎯 Criterios de Aceptación Implementados

| ID | Criterio | Estado | Implementación |
|----|----------|--------|----------------|
| **a** | El paciente puede ver el presupuesto completo con servicios y costos | ✅ | `GET /api/presupuestos/{id}/` |
| **b** | Puede aceptar el presupuesto completo o solo algunos servicios | ✅ | Parámetro `tipo_aceptacion: Total\|Parcial` |
| **c** | Registro de firma digital, timestamp y generación de comprobante | ✅ | Modelo `AceptacionPresupuesto` con `comprobante_id` UUID |
| **d** | Bloqueo de edición del presupuesto y notificaciones a ambas partes | ✅ | Campo `es_editable=False` + Signals para FCM |
| **e** | Validación de fecha de vigencia y no aceptado previamente | ✅ | Métodos `esta_vigente()` y `puede_ser_aceptado()` |

---

## 📡 Endpoints Disponibles

### 1. **Listar Presupuestos del Paciente**

```http
GET /api/presupuestos/
```

**Headers:**
```http
Authorization: Token <token>
X-Tenant-Subdomain: <subdomain>
```

**Response 200 OK:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "fechaplan": "2025-10-15",
      "paciente_nombre": "Juan Pérez",
      "odontologo_nombre": "Dr. María González",
      "estado_nombre": "Pendiente",
      "montototal": "1500.00",
      "descuento": "0.00",
      "cantidad_items": 3,
      "estado_aceptacion": "Pendiente",
      "aceptacion_tipo": null,
      "fecha_vigencia": "2025-11-15",
      "fecha_aceptacion": null,
      "esta_vigente": true,
      "puede_aceptar": true
    }
  ]
}
```

---

### 2. **Ver Detalle de un Presupuesto**

```http
GET /api/presupuestos/{id}/
```

**Response 200 OK:**
```json
{
  "id": 1,
  "fechaplan": "2025-10-15",
  "paciente": {
    "id": 1,
    "usuario_id": 5,
    "nombre": "Juan",
    "apellido": "Pérez",
    "email": "juan.perez@example.com"
  },
  "odontologo": {
    "id": 2,
    "usuario_id": 10,
    "nombre": "Dr. María González"
  },
  "estado_nombre": "Pendiente",
  "montototal": "1500.00",
  "descuento": "0.00",
  "items": [
    {
      "id": 1,
      "servicio_nombre": "Limpieza Dental",
      "servicio_descripcion": "Limpieza completa con ultrasonido",
      "pieza_dental": null,
      "estado_nombre": "Pendiente",
      "costofinal": "150.00"
    },
    {
      "id": 2,
      "servicio_nombre": "Endodoncia",
      "servicio_descripcion": "Tratamiento de conducto",
      "pieza_dental": "Molar 6",
      "estado_nombre": "Pendiente",
      "costofinal": "800.00"
    },
    {
      "id": 3,
      "servicio_nombre": "Corona Dental",
      "servicio_descripcion": "Corona de porcelana",
      "pieza_dental": "Molar 6",
      "estado_nombre": "Pendiente",
      "costofinal": "550.00"
    }
  ],
  "estado_aceptacion": "Pendiente",
  "aceptacion_tipo": null,
  "fecha_vigencia": "2025-11-15",
  "fecha_aceptacion": null,
  "usuario_acepta_nombre": null,
  "es_editable": true,
  "esta_vigente": true,
  "puede_aceptar": true,
  "dias_para_vencimiento": 31,
  "aceptaciones_historial": []
}
```

---

### 3. **Aceptar Presupuesto (Principal)** ⭐

```http
POST /api/presupuestos/{id}/aceptar/
```

**Headers:**
```http
Authorization: Token <token>
X-Tenant-Subdomain: <subdomain>
Content-Type: application/json
```

#### **Payload para Aceptación Total:**

```json
{
  "tipo_aceptacion": "Total",
  "firma_digital": {
    "timestamp": "2025-10-19T10:30:00Z",
    "user_id": 5,
    "signature_hash": "a1b2c3d4e5f6...",
    "client_info": {
      "browser": "Chrome 120",
      "device": "Desktop"
    }
  },
  "notas": "Acepto el presupuesto completo. Proceder con todos los tratamientos."
}
```

#### **Payload para Aceptación Parcial:**

```json
{
  "tipo_aceptacion": "Parcial",
  "items_aceptados": [1, 2],
  "firma_digital": {
    "timestamp": "2025-10-19T10:30:00Z",
    "user_id": 5,
    "signature_hash": "a1b2c3d4e5f6..."
  },
  "notas": "Solo acepto limpieza y endodoncia por ahora."
}
```

#### **Response 200 OK - Aceptación Exitosa:**

```json
{
  "success": true,
  "mensaje": "Presupuesto aceptado exitosamente (total).",
  "presupuesto": {
    "id": 1,
    "estado_aceptacion": "Aceptado",
    "fecha_aceptacion": "2025-10-19T10:30:15.123Z",
    "es_editable": false,
    "usuario_acepta_nombre": "Juan Pérez",
    ...
  },
  "aceptacion": {
    "comprobante_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "fecha_aceptacion": "2025-10-19T10:30:15.123Z",
    "tipo": "Total",
    "url_verificacion": "/verificar-comprobante/a1b2c3d4-e5f6-7890-abcd-ef1234567890/"
  }
}
```

#### **Response 400 BAD REQUEST - Presupuesto Caducado:**

```json
{
  "error": "Presupuesto caducado.",
  "detalle": "El presupuesto venció el 2025-10-10.",
  "fecha_vigencia": "2025-10-10"
}
```

#### **Response 400 BAD REQUEST - Ya Aceptado:**

```json
{
  "error": "Presupuesto ya aceptado.",
  "detalle": "Este presupuesto fue aceptado el 2025-10-18T14:25:00Z.",
  "fecha_aceptacion": "2025-10-18T14:25:00Z"
}
```

#### **Response 400 BAD REQUEST - Items Inválidos:**

```json
{
  "error": "Items inválidos.",
  "detalle": "Los siguientes items no pertenecen al presupuesto: [999, 888]",
  "items_invalidos": [999, 888]
}
```

#### **Response 403 FORBIDDEN - Usuario No Autorizado:**

```json
{
  "error": "No autorizado.",
  "detalle": "Solo el paciente del presupuesto puede aceptarlo."
}
```

---

### 4. **Verificar Si Puede Aceptar**

```http
GET /api/presupuestos/{id}/puede-aceptar/
```

**Response 200 OK - Puede Aceptar:**
```json
{
  "puede_aceptar": true,
  "razones": [],
  "estado_actual": "Pendiente",
  "esta_vigente": true,
  "fecha_vigencia": "2025-11-15",
  "dias_restantes": 27
}
```

**Response 200 OK - No Puede Aceptar:**
```json
{
  "puede_aceptar": false,
  "razones": [
    "El presupuesto caducó el 2025-10-10."
  ],
  "estado_actual": "Caducado",
  "esta_vigente": false,
  "fecha_vigencia": "2025-10-10",
  "dias_restantes": null
}
```

---

### 5. **Listar Comprobantes de Aceptación**

```http
GET /api/presupuestos/{id}/comprobantes/
```

**Response 200 OK:**
```json
{
  "presupuesto_id": 1,
  "cantidad": 1,
  "comprobantes": [
    {
      "id": 1,
      "comprobante_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "fecha_aceptacion": "2025-10-19T10:30:15.123Z",
      "tipo_aceptacion": "Total",
      "monto_total_aceptado": "1500.00",
      "paciente": {
        "id": 5,
        "nombre": "Juan Pérez",
        "email": "juan.perez@example.com"
      },
      "items_detalle": [],
      "ip_address": "192.168.1.100",
      "url_verificacion": "/verificar-comprobante/a1b2c3d4-e5f6-7890-abcd-ef1234567890/"
    }
  ]
}
```

---

### 6. **Verificar Comprobante**

```http
POST /api/aceptaciones/verificar/
```

**Payload:**
```json
{
  "comprobante_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Response 200 OK - Comprobante Válido:**
```json
{
  "valido": true,
  "comprobante": {
    "comprobante_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "fecha_aceptacion": "2025-10-19T10:30:15.123Z",
    "tipo_aceptacion": "Total",
    "monto_total_aceptado": "1500.00",
    "presupuesto": { ... },
    "paciente": { ... }
  }
}
```

**Response 404 NOT FOUND - Comprobante Inválido:**
```json
{
  "valido": false,
  "mensaje": "Comprobante no encontrado o inválido."
}
```

---

## 🔐 Validaciones Implementadas

### Validación 1: Usuario Autorizado
- Solo el **paciente del presupuesto** puede aceptarlo
- Otros pacientes reciben `403 FORBIDDEN`
- Odontólogos y administradores **no pueden** aceptar en nombre del paciente

### Validación 2: Vigencia del Presupuesto
- Se verifica `fecha_vigencia > fecha_actual`
- Presupuestos caducados retornan `400 BAD REQUEST`
- Sin `fecha_vigencia` = siempre vigente

### Validación 3: Estado de Aceptación
- No se puede aceptar presupuestos con estado:
  - `Aceptado` (ya aceptado)
  - `Rechazado` (previamente rechazado)
- Estado `Pendiente` o `null` = aceptable

### Validación 4: Items en Aceptación Parcial
- Todos los IDs deben existir en el presupuesto
- No se permiten IDs duplicados
- Items inválidos retornan `400 BAD REQUEST` con lista de IDs inválidos

### Validación 5: Firma Digital
- Campos requeridos: `timestamp`, `user_id`
- Formato JSON válido
- Timestamp debe ser reciente (opcional implementar)

---

## 🗄️ Modelos de Base de Datos

### Modelo: Plandetratamiento (Extendido)

**Nuevos Campos:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `fecha_vigencia` | DateField | Fecha hasta la cual el presupuesto es válido |
| `fecha_aceptacion` | DateTimeField | Timestamp de aceptación |
| `usuario_acepta` | FK(Usuario) | Usuario paciente que aceptó |
| `estado_aceptacion` | CharField | Pendiente, Aceptado, Rechazado, Caducado, Parcial |
| `aceptacion_tipo` | CharField | Total o Parcial |
| `es_editable` | BooleanField | False cuando se acepta (bloqueo) |
| `firma_digital` | TextField | JSON con datos de firma |

**Métodos del Modelo:**
```python
presupuesto.esta_vigente()  # → bool
presupuesto.esta_caducado()  # → bool
presupuesto.puede_ser_aceptado()  # → bool
presupuesto.marcar_como_caducado()  # Actualiza estado
```

---

### Modelo: AceptacionPresupuesto (Nuevo)

**Tabla de Auditoría Completa:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | BigAutoField | PK |
| `plandetratamiento` | FK | Presupuesto aceptado |
| `usuario_paciente` | FK(Usuario) | Paciente que aceptó |
| `empresa` | FK(Empresa) | Tenant |
| `fecha_aceptacion` | DateTimeField | Timestamp (auto_now_add) |
| `tipo_aceptacion` | CharField | Total o Parcial |
| `items_aceptados` | JSONField | Lista de IDs de items (si parcial) |
| `firma_digital` | JSONField | Datos de firma completos |
| `ip_address` | GenericIPAddressField | IP del cliente |
| `user_agent` | TextField | User Agent del navegador |
| `comprobante_id` | UUIDField | ID único del comprobante ⭐ |
| `comprobante_url` | URLField | URL del PDF (futuro) |
| `monto_total_aceptado` | DecimalField | Monto al momento de aceptación |
| `notas` | TextField | Comentarios del paciente |

**Características:**
- **Registro inmutable** (no se elimina ni edita)
- **Comprobante UUID único** para verificación
- **Captura metadata** (IP, User Agent) automáticamente
- **Histórico completo** de todas las aceptaciones

---

## 🔔 Sistema de Notificaciones

### Implementación con Signals

**Archivo:** `api/signals_presupuestos.py`

```python
@receiver(post_save, sender=AceptacionPresupuesto)
def notificar_aceptacion_presupuesto(sender, instance, created, **kwargs):
    if not created:
        return
    
    # Notificación al paciente (confirmación)
    queue_notification(
        empresa=instance.empresa,
        usuario_destino=instance.usuario_paciente,
        titulo='✅ Presupuesto Aceptado',
        mensaje=f'Has aceptado el presupuesto #{instance.plandetratamiento.id}...',
        tipo='presupuesto_aceptado_paciente',
        datos_extra={'comprobante_id': str(instance.comprobante_id)}
    )
    
    # Notificación al odontólogo (nueva aceptación)
    queue_notification(
        empresa=instance.empresa,
        usuario_destino=instance.plandetratamiento.cododontologo.codusuario,
        titulo='🔔 Presupuesto Aceptado por Paciente',
        mensaje=f'El paciente {paciente_nombre} ha aceptado el presupuesto...',
        tipo='presupuesto_aceptado_odontologo',
        datos_extra={'presupuesto_id': instance.plandetratamiento.id}
    )
```

**Integración:**
- Conectado automáticamente en `api/apps.py → ready()`
- Usa el sistema FCM existente (`api/notifications_mobile/`)
- Encola notificaciones de forma asíncrona

---

## 📊 Bitácora de Auditoría

Cada aceptación registra en `Bitacora`:

```json
{
  "empresa": "Clínica Test",
  "usuario": "Juan Pérez (ID: 5)",
  "accion": "ACEPTACION_PRESUPUESTO",
  "tabla_afectada": "plandetratamiento",
  "detalles": {
    "presupuesto_id": 1,
    "tipo_aceptacion": "Total",
    "items_aceptados": [],
    "fecha_aceptacion": "2025-10-19T10:30:15.123Z",
    "comprobante_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "monto_total": "1500.00",
    "ip_address": "192.168.1.100"
  },
  "fecha": "2025-10-19T10:30:15.123Z"
}
```

---

## 🧪 Ejemplos de Uso

### Ejemplo 1: Aceptación Total con cURL

```bash
curl -X POST https://test.notificct.dpdns.org/api/presupuestos/1/aceptar/ \
  -H "Authorization: Token abc123xyz" \
  -H "X-Tenant-Subdomain: test" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_aceptacion": "Total",
    "firma_digital": {
      "timestamp": "2025-10-19T10:30:00Z",
      "user_id": 5,
      "signature_hash": "a1b2c3d4e5f6"
    },
    "notas": "Acepto todo el tratamiento propuesto."
  }'
```

---

### Ejemplo 2: Aceptación Parcial con JavaScript (Fetch)

```javascript
const aceptarPresupuesto = async (presupuestoId, itemsSeleccionados) => {
  const firma = {
    timestamp: new Date().toISOString(),
    user_id: currentUser.id,
    signature_hash: generateHash(currentUser.id + Date.now()),
    client_info: {
      browser: navigator.userAgent,
      screen: `${screen.width}x${screen.height}`
    }
  };
  
  const response = await fetch(
    `https://test.notificct.dpdns.org/api/presupuestos/${presupuestoId}/aceptar/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Token ${userToken}`,
        'X-Tenant-Subdomain': 'test',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        tipo_aceptacion: 'Parcial',
        items_aceptados: itemsSeleccionados,  // [1, 2]
        firma_digital: firma,
        notas: 'Solo estos tratamientos por ahora.'
      })
    }
  );
  
  if (response.ok) {
    const data = await response.json();
    console.log('✅ Presupuesto aceptado:', data.aceptacion.comprobante_id);
    mostrarComprobante(data.aceptacion.url_verificacion);
  } else {
    const error = await response.json();
    console.error('❌ Error:', error.error, error.detalle);
  }
};

// Uso
aceptarPresupuesto(1, [1, 2]);  // Acepta items 1 y 2 del presupuesto 1
```

---

### Ejemplo 3: Verificar si Puede Aceptar

```javascript
const verificarAceptacion = async (presupuestoId) => {
  const response = await fetch(
    `https://test.notificct.dpdns.org/api/presupuestos/${presupuestoId}/puede-aceptar/`,
    {
      headers: {
        'Authorization': `Token ${userToken}`,
        'X-Tenant-Subdomain': 'test'
      }
    }
  );
  
  const data = await response.json();
  
  if (data.puede_aceptar) {
    console.log(`✅ Puede aceptar. Días restantes: ${data.dias_restantes}`);
    habilitarBotonAceptar();
  } else {
    console.log('❌ No puede aceptar:', data.razones.join(', '));
    deshabilitarBotonAceptar();
    mostrarRazones(data.razones);
  }
};
```

---

## 🔒 Consideraciones de Seguridad

### 1. **Autorización Multi-Nivel**
- **Token Authentication**: Usuario debe estar autenticado
- **Tenant Isolation**: Solo datos de su empresa (`request.tenant`)
- **Patient Ownership**: Solo el paciente del presupuesto puede aceptarlo

### 2. **Firma Digital**
- Se almacena **metadata completa**: timestamp, user_id, IP, user agent
- Permite **auditoría forense** de cada aceptación
- **Inmutable**: Registro en tabla separada no se puede modificar

### 3. **Protección de Datos**
- **IP Address**: Se registra para trazabilidad legal
- **User Agent**: Identifica dispositivo/navegador usado
- **Timestamp**: Momento exacto de aceptación (zona horaria UTC)

### 4. **Bloqueo de Edición**
- `es_editable = False` al aceptar
- Previene modificaciones post-aceptación
- Protege integridad del consentimiento

### 5. **Validación de Vigencia**
- Presupuestos caducados **no se pueden aceptar**
- Evita aceptaciones de presupuestos obsoletos
- Fecha de vigencia configurable por el odontólogo

---

## 📝 Códigos de Error Completos

| Código | Escenario | Mensaje |
|--------|-----------|---------|
| `200` | Aceptación exitosa | `"Presupuesto aceptado exitosamente (total)."` |
| `400` | Presupuesto caducado | `"Presupuesto caducado."` |
| `400` | Ya aceptado | `"Presupuesto ya aceptado."` |
| `400` | Presupuesto rechazado | `"Presupuesto rechazado."` |
| `400` | Items inválidos (parcial) | `"Items inválidos."` |
| `400` | Sin items (parcial) | `"Items requeridos."` |
| `400` | Firma incompleta | `"El campo 'user_id' es requerido en la firma digital."` |
| `403` | Usuario no autorizado | `"Solo el paciente del presupuesto puede aceptarlo."` |
| `403` | No es paciente | `"Solo pacientes pueden aceptar presupuestos."` |
| `404` | Presupuesto no existe | `"Not found."` |

---

## 🚀 Estado de Implementación

| Componente | Estado | Notas |
|------------|--------|-------|
| **Modelos** | ✅ Completo | `Plandetratamiento` extendido + `AceptacionPresupuesto` |
| **Migración** | ✅ Aplicada | `0003_aceptacion_presupuestos.py` |
| **Serializers** | ✅ Completo | 9 serializers (list, detail, write, verify) |
| **ViewSets** | ✅ Completo | `PresupuestoViewSet` + `AceptacionPresupuestoViewSet` |
| **Validaciones** | ✅ Completo | 5 validaciones críticas implementadas |
| **Notificaciones** | ✅ Completo | Signals + integración FCM |
| **Bitácora** | ✅ Completo | Registro automático en auditoría |
| **Tests** | ⚠️ Creados | 24 tests (requieren ajustes de fixtures) |
| **Comprobante PDF** | ⏳ Pendiente | Futuro: reportlab/weasyprint |
| **Documentación** | ✅ Completo | Este archivo |

---

## 📂 Archivos Creados/Modificados

### Creados:
- `api/models.py` - Modelos extendidos (Plandetratamiento + AceptacionPresupuesto)
- `api/serializers_presupuestos.py` - 9 serializers
- `api/views_presupuestos.py` - 2 ViewSets con 5 actions
- `api/signals_presupuestos.py` - Notificaciones automáticas
- `api/tests_presupuestos.py` - Suite de 24 tests
- `api/migrations/0003_aceptacion_presupuestos.py` - Migración de BD

### Modificados:
- `api/apps.py` - Registro de signals
- `api/urls.py` - Registro de routers

---

## 🔮 Próximas Mejoras (Futuras)

1. **Generación de PDF del Comprobante**
   - Usar `reportlab` o `weasyprint`
   - Incluir QR code con `comprobante_id`
   - Subir a S3 y actualizar `comprobante_url`

2. **Email de Confirmación**
   - Enviar email al paciente con PDF adjunto
   - Copia al odontólogo

3. **Dashboard de Aceptaciones**
   - Vista para odontólogos: estadísticas de aceptación
   - Gráficos de tasa de aceptación por período

4. **Recordatorios de Vigencia**
   - Notificar al paciente X días antes de vencer
   - Tarea programada para marcar caducados

5. **Firma Digital Avanzada**
   - Integrar con proveedores de firma electrónica legal
   - Captura de firma manuscrita (canvas HTML5)

---

## 🤝 Soporte

Para preguntas sobre esta implementación:
- **Branch**: `SP3-T003-Aceptar-Presupuesto-Paciente`
- **Documentación adicional**: Ver código fuente en archivos mencionados

---

**Versión**: 1.0  
**Fecha**: Octubre 2025  
**Autor**: Implementación SP3-T003
