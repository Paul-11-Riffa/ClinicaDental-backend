# Fix: 404 Error en /api/clinic/servicios/

## Problema Resuelto ✅

Frontend estaba obteniendo 404 en:
```
GET /api/clinic/servicios/?page=1&page_size=10&ordering=nombre HTTP/1.1" 404
```

Backend solo servía en: `/clinic/servicios/`

## Solución Implementada

**Archivo modificado**: `api/urls.py`

Se agregó un alias para que el catálogo esté disponible en ambas rutas:

```python
# api/urls.py (línea ~73)
# Rutas de los ViewSets
path("", include(router.urls)),

# Clinic app - Alias para /api/clinic/servicios/
path("clinic/", include("clinic.urls")),  # ← AGREGADO

# Notificaciones mobile
path("mobile-notif/", include("api.notifications_mobile.urls")),
```

## URLs Disponibles

El catálogo ahora responde en **ambas rutas**:

1. ✅ `/clinic/servicios/` (original)
2. ✅ `/api/clinic/servicios/` (nuevo alias)

### Ejemplos de URLs Completas

```bash
# Ambas funcionan igual
http://smilestudio.localhost:8000/clinic/servicios/
http://smilestudio.localhost:8000/api/clinic/servicios/

# En producción
https://norte.notificct.dpdns.org/clinic/servicios/
https://norte.notificct.dpdns.org/api/clinic/servicios/
```

## Pruebas Realizadas

### Test con PowerShell

```powershell
$headers = @{ "X-Tenant-Subdomain" = "smilestudio" }
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/clinic/servicios/?page=1&page_size=10&ordering=nombre" -Headers $headers

# Resultado:
# ✅ Count: 8 servicios
# ✅ Results: Array con los 8 servicios creados
# ✅ Ordenados por nombre
```

### Servicios de Ejemplo Creados

Para la empresa **SmileStudio** (`subdomain=smilestudio`):

| Servicio | Precio | Duración | Estado |
|----------|--------|----------|--------|
| Limpieza Dental Profesional | $150.00 | 45 min | ✅ Activo |
| Blanqueamiento Dental | $400.00 | 60 min | ✅ Activo |
| Consulta General | $50.00 | 30 min | ✅ Activo |
| Endodoncia | $800.00 | 90 min | ✅ Activo |
| Ortodoncia Mensual | $200.00 | 30 min | ✅ Activo |
| Extracción Simple | $150.00 | 30 min | ✅ Activo |
| Corona Dental | $1200.00 | 60 min | ✅ Activo |
| Implante Dental | $2500.00 | 120 min | ✅ Activo |

## Acceso Público

El endpoint **NO requiere autenticación** para operaciones GET:

```javascript
// Frontend puede llamar sin token
fetch('https://smilestudio.notificct.dpdns.org/api/clinic/servicios/')
  .then(res => res.json())
  .then(data => console.log(data.results))
```

## Filtros Disponibles

```bash
# Búsqueda por texto
?busqueda=limpieza

# Rango de precio
?precio_min=100&precio_max=500

# Rango de duración
?duracion_min=30&duracion_max=60

# Solo activos (default: true)
?activo=true

# Ordenamiento
?ordering=nombre          # Alfabético
?ordering=-nombre         # Inverso
?ordering=costobase       # Más barato primero
?ordering=-costobase      # Más caro primero
?ordering=duracion        # Más corto primero

# Paginación
?page=1&page_size=10
```

## Recomendación Frontend

Usar la ruta `/api/clinic/servicios/` para consistencia con otras rutas API:

```javascript
const API_BASE = 'https://smilestudio.notificct.dpdns.org/api';
const SERVICIOS_URL = `${API_BASE}/clinic/servicios/`;
```

## Verificación

Para confirmar que funciona en tu ambiente:

```bash
# Con curl (Linux/Mac)
curl -H "X-Tenant-Subdomain: smilestudio" http://localhost:8000/api/clinic/servicios/

# Con PowerShell (Windows)
$headers = @{ "X-Tenant-Subdomain" = "smilestudio" }
Invoke-RestMethod -Uri "http://localhost:8000/api/clinic/servicios/" -Headers $headers
```

## Estado del Branch

✅ Branch: `SI2-Consultar-Catalogos-de-Servicios`
✅ Archivos modificados:
  - `api/urls.py` - Agregado alias clinic/
  - `crear_servicios_ejemplo.py` - Script para crear datos de ejemplo

✅ Listo para merge o deploy
