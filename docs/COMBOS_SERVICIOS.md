# Combos/Paquetes de Servicios Dentales

## 📋 Descripción

Módulo para la gestión completa de combos o paquetes de servicios dentales con precios especiales. Implementa el requisito **SP3-T007: Crear paquete o combo de servicios (web)**.

## ✨ Funcionalidades Implementadas

### a) Crear Combo
- Nombre y descripción del combo
- Selección de servicios con cantidades
- Tres tipos de reglas de precio:
  - **PORCENTAJE**: Descuento porcentual sobre el total de servicios
  - **MONTO_FIJO**: Precio fijo del combo (independiente del total de servicios)
  - **PROMOCION**: Precio promocional especial

### b) Editar y Previsualizar
- Editar datos básicos del combo
- Modificar servicios incluidos y cantidades
- **Previsualizar precio final** antes de guardar
- Validación automática: rechaza totales negativos

### c) Desactivar Combo
- Desactivar combo para bloquear uso futuro
- No se elimina, solo se marca como inactivo
- Posibilidad de reactivar si es necesario

### d) Validaciones de Consistencia
- Cantidades deben ser positivas (> 0)
- No se permiten servicios duplicados en un combo
- El precio final no puede ser negativo
- Porcentajes de descuento no pueden superar 100%

### e) Guardar desde Edición
- Operación PUT/PATCH para actualizar combos existentes
- Todos los cambios se persisten correctamente

## 🔧 Arquitectura

### Modelos

#### `ComboServicio`
Representa el combo/paquete principal.

```python
{
    "nombre": "Paquete Blanqueamiento Completo",
    "descripcion": "Incluye limpieza + blanqueamiento + consulta",
    "tipo_precio": "PORCENTAJE",  # PORCENTAJE | MONTO_FIJO | PROMOCION
    "valor_precio": 25.00,  # 25% descuento
    "activo": true,
    "fecha_creacion": "2025-10-27T14:00:00Z",
    "empresa": 1
}
```

#### `ComboServicioDetalle`
Representa cada servicio incluido en el combo.

```python
{
    "combo": 1,
    "servicio": 5,
    "cantidad": 2,
    "orden": 1
}
```

### Serializers

- **`ComboServicioSerializer`**: Lectura completa con cálculos
- **`ComboServicioCreateUpdateSerializer`**: Crear/editar con detalles anidados
- **`ComboServicioListSerializer`**: Listado simplificado
- **`ComboServicioPrevisualizacionSerializer`**: Previsualizar sin guardar

### ViewSet

**`ComboServicioViewSet`** - Endpoints principales:

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/combos-servicios/` | Listar combos activos |
| POST | `/api/combos-servicios/` | Crear nuevo combo |
| GET | `/api/combos-servicios/{id}/` | Detalle de combo |
| PUT/PATCH | `/api/combos-servicios/{id}/` | Actualizar combo |
| DELETE | `/api/combos-servicios/{id}/` | Eliminar combo |
| POST | `/api/combos-servicios/previsualizar/` | Previsualizar precio |
| POST | `/api/combos-servicios/{id}/activar/` | Activar combo |
| POST | `/api/combos-servicios/{id}/desactivar/` | Desactivar combo |
| GET | `/api/combos-servicios/{id}/detalle_completo/` | Detalle con cálculos |
| GET | `/api/combos-servicios/estadisticas/` | Estadísticas generales |

## 📡 Ejemplos de Uso

### 1. Crear Combo con Descuento Porcentual

```bash
POST /api/combos-servicios/
Authorization: Token abc123...
X-Tenant-Subdomain: norte

{
    "nombre": "Paquete Básico",
    "descripcion": "Limpieza + Consulta con 20% descuento",
    "tipo_precio": "PORCENTAJE",
    "valor_precio": "20.00",
    "activo": true,
    "detalles": [
        {
            "servicio": 1,
            "cantidad": 1,
            "orden": 1
        },
        {
            "servicio": 3,
            "cantidad": 1,
            "orden": 2
        }
    ]
}
```

**Respuesta:**
```json
{
    "mensaje": "Combo creado exitosamente",
    "combo": {
        "id": 1,
        "nombre": "Paquete Básico",
        "descripcion": "Limpieza + Consulta con 20% descuento",
        "tipo_precio": "PORCENTAJE",
        "valor_precio": "20.00",
        "activo": true,
        "precio_total_servicios": "200.00",
        "precio_final": "160.00",
        "ahorro": "40.00",
        "duracion_total": 75,
        "cantidad_servicios": 2,
        "detalles": [
            {
                "id": 1,
                "servicio": 1,
                "servicio_nombre": "Limpieza Dental",
                "servicio_precio": "150.00",
                "cantidad": 1,
                "subtotal": "150.00"
            },
            {
                "id": 2,
                "servicio": 3,
                "servicio_nombre": "Consulta General",
                "servicio_precio": "50.00",
                "cantidad": 1,
                "subtotal": "50.00"
            }
        ]
    }
}
```

### 2. Previsualizar Precio (Sin Guardar)

```bash
POST /api/combos-servicios/previsualizar/
Authorization: Token abc123...
X-Tenant-Subdomain: norte

{
    "tipo_precio": "PORCENTAJE",
    "valor_precio": "30.00",
    "servicios": [
        {"servicio_id": 1, "cantidad": 1},
        {"servicio_id": 2, "cantidad": 1}
    ]
}
```

**Respuesta:**
```json
{
    "precio_total_servicios": "650.00",
    "precio_final": "455.00",
    "ahorro": "195.00",
    "tipo_precio": "PORCENTAJE",
    "valor_precio": "30.00",
    "mensaje": "Previsualización calculada exitosamente"
}
```

### 3. Editar Combo Existente

```bash
PUT /api/combos-servicios/1/
Authorization: Token abc123...

{
    "nombre": "Paquete Básico Plus",
    "descripcion": "Ahora con mayor descuento",
    "tipo_precio": "PORCENTAJE",
    "valor_precio": "25.00",
    "activo": true,
    "detalles": [
        {
            "servicio": 1,
            "cantidad": 2,
            "orden": 1
        }
    ]
}
```

### 4. Desactivar Combo

```bash
POST /api/combos-servicios/1/desactivar/
Authorization: Token abc123...
```

**Respuesta:**
```json
{
    "mensaje": "Combo desactivado exitosamente. Ya no estará disponible para nuevas ventas.",
    "combo": {
        "id": 1,
        "nombre": "Paquete Básico",
        "activo": false,
        ...
    }
}
```

### 5. Listar Combos con Filtros

```bash
# Solo activos (por defecto)
GET /api/combos-servicios/

# Incluir inactivos
GET /api/combos-servicios/?activo=false

# Buscar por nombre
GET /api/combos-servicios/?search=Premium

# Filtrar por tipo de precio
GET /api/combos-servicios/?tipo_precio=PORCENTAJE

# Ordenar por fecha
GET /api/combos-servicios/?ordering=-fecha_creacion
```

## 🧪 Tests

Se incluyen **25+ tests comprehensivos** que cubren:

- ✅ Creación de combos con diferentes tipos de precio
- ✅ Cálculo correcto de precios finales
- ✅ Validación de cantidades positivas
- ✅ Rechazo de precios negativos
- ✅ Edición de combos existentes
- ✅ Previsualización de precios
- ✅ Activación/desactivación
- ✅ Aislamiento multi-tenant
- ✅ Validación de servicios duplicados
- ✅ Búsqueda y filtrado
- ✅ Autenticación requerida

**Ejecutar tests:**
```bash
python manage.py test api.tests_combos
```

## 🔒 Seguridad

### Multi-Tenancy
- Todos los combos están aislados por `empresa` (tenant)
- Filtrado automático por subdomain
- Un tenant no puede ver/editar combos de otro

### Autenticación
- Se requiere autenticación para todas las operaciones
- Token authentication + Session authentication
- Validación de permisos por tenant

### Auditoría (Bitácora)
Todas las operaciones importantes se registran:
- `CREAR_COMBO`: Al crear un nuevo combo
- `ACTUALIZAR_COMBO`: Al editar un combo
- `ELIMINAR_COMBO`: Al eliminar un combo
- `ACTIVAR_COMBO`: Al activar un combo
- `DESACTIVAR_COMBO`: Al desactivar un combo

## 💾 Base de Datos

### Tablas

**`combo_servicio`**
```sql
CREATE TABLE combo_servicio (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    tipo_precio VARCHAR(20) NOT NULL,
    valor_precio NUMERIC(10, 2) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL,
    fecha_modificacion TIMESTAMP NOT NULL,
    empresa_id INTEGER REFERENCES api_empresa(id),
    CONSTRAINT combo_valor_precio_no_negativo CHECK (valor_precio >= 0)
);
```

**`combo_servicio_detalle`**
```sql
CREATE TABLE combo_servicio_detalle (
    id SERIAL PRIMARY KEY,
    combo_id INTEGER REFERENCES combo_servicio(id) ON DELETE CASCADE,
    servicio_id INTEGER REFERENCES servicio(id) ON DELETE PROTECT,
    cantidad INTEGER NOT NULL,
    orden INTEGER DEFAULT 0,
    CONSTRAINT unique_combo_servicio UNIQUE (combo_id, servicio_id),
    CONSTRAINT combo_detalle_cantidad_positiva CHECK (cantidad > 0)
);
```

### Índices Recomendados

```sql
CREATE INDEX idx_combo_servicio_empresa ON combo_servicio(empresa_id);
CREATE INDEX idx_combo_servicio_activo ON combo_servicio(activo);
CREATE INDEX idx_combo_detalle_combo ON combo_servicio_detalle(combo_id);
CREATE INDEX idx_combo_detalle_servicio ON combo_servicio_detalle(servicio_id);
```

## 📊 Admin Panel

Los combos son completamente gestionables desde el Django Admin:

- Vista de listado con precios calculados
- Inline de servicios incluidos
- Campos de solo lectura para cálculos automáticos
- Filtros por estado, tipo de precio y fecha
- Búsqueda por nombre y descripción

## 🚀 Próximas Mejoras

- [ ] Restricción de uso por fechas (vigencia del combo)
- [ ] Límite de usos por paciente
- [ ] Tracking de combos más vendidos
- [ ] Reportes de rendimiento de combos
- [ ] Notificaciones de combos próximos a vencer
- [ ] Generación automática de códigos promocionales

## 📝 Notas Importantes

1. **Precio Negativo**: Si el descuento porcentual o el precio fijo resulta en un total negativo, se rechaza automáticamente.

2. **Servicios Duplicados**: No se permite agregar el mismo servicio dos veces en un combo (se controla por constraint de BD).

3. **Eliminación de Servicios**: Los servicios incluidos en combos tienen protección `ON DELETE PROTECT` - no se pueden eliminar si están en un combo activo.

4. **Soft Delete**: Se recomienda usar desactivación en lugar de eliminación física para mantener historial.

## 🤝 Contribuir

Para agregar nuevas funcionalidades:

1. Agregar métodos en los modelos (`ComboServicio`, `ComboServicioDetalle`)
2. Crear/actualizar serializers según necesidad
3. Agregar actions en `ComboServicioViewSet`
4. Escribir tests en `tests_combos.py`
5. Documentar en este README

---

**Desarrollado para**: Clínica Dental SaaS  
**Versión**: 1.0.0  
**Fecha**: Octubre 2025  
**Branch**: `combo-de-servicios`
