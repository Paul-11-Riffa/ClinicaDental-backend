# 📘 API de Catálogo de Servicios - Documentación para Frontend

## 📋 Tabla de Contenidos
- [Introducción](#introducción)
- [Autenticación](#autenticación)
- [Endpoints Disponibles](#endpoints-disponibles)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [Códigos de Estado HTTP](#códigos-de-estado-http)
- [Estructura de Datos](#estructura-de-datos)

---

## 🎯 Introducción

Esta API permite consultar el catálogo de servicios dentales disponibles en el sistema. Incluye funcionalidades de búsqueda, filtrado, ordenamiento y paginación.

**Base URL:** `https://{subdomain}.notificct.dpdns.org/clinic/servicios/`

**Versión:** 1.0  
**Última actualización:** Octubre 2025

---

## 🔐 Autenticación

Todos los endpoints requieren autenticación mediante **Token Authentication**.

### Headers Requeridos

```http
Authorization: Token {tu_token_de_autenticacion}
X-Tenant-Subdomain: {subdomain_de_la_clinica}
Content-Type: application/json
```

### Ejemplo de Header Completo

```javascript
headers: {
  'Authorization': 'Token abc123def456ghi789',
  'X-Tenant-Subdomain': 'norte',
  'Content-Type': 'application/json'
}
```

---

## 📡 Endpoints Disponibles

### 1. Listar Servicios (Con Filtros y Búsqueda)

**GET** `/clinic/servicios/`

Lista todos los servicios activos del catálogo con soporte para filtrado, búsqueda, ordenamiento y paginación.

#### Parámetros Query (Todos Opcionales)

| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `search` | string | Búsqueda por texto en nombre y descripción | `?search=limpieza` |
| `precio_min` | decimal | Precio mínimo del servicio | `?precio_min=100` |
| `precio_max` | decimal | Precio máximo del servicio | `?precio_max=500` |
| `duracion_min` | integer | Duración mínima en minutos | `?duracion_min=30` |
| `duracion_max` | integer | Duración máxima en minutos | `?duracion_max=90` |
| `activo` | boolean | Filtrar por estado activo (omitir para solo activos) | `?activo=true` o `?activo=false` |
| `ordering` | string | Campo para ordenar (nombre, costobase, duracion) | `?ordering=nombre` o `?ordering=-costobase` |
| `page` | integer | Número de página | `?page=2` |
| `page_size` | integer | Cantidad de resultados por página (máx: 100) | `?page_size=20` |

**Nota:** Usar `-` antes del campo de ordenamiento para orden descendente (ej: `-costobase` ordena de mayor a menor precio)

#### Respuesta Exitosa (200 OK)

```json
{
  "count": 25,
  "next": "https://norte.notificct.dpdns.org/clinic/servicios/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "nombre": "Limpieza Dental",
      "costobase": "150.00",
      "precio_vigente": "150.00",
      "duracion": 45,
      "activo": true
    },
    {
      "id": 2,
      "nombre": "Endodoncia",
      "costobase": "800.00",
      "precio_vigente": "800.00",
      "duracion": 90,
      "activo": true
    }
  ]
}
```

---

### 2. Obtener Detalle de Servicio

**GET** `/clinic/servicios/{id}/`

Obtiene la información completa de un servicio específico.

#### Parámetros de URL

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `id` | integer | ID del servicio a consultar |

#### Respuesta Exitosa (200 OK)

```json
{
  "id": 1,
  "nombre": "Limpieza Dental",
  "descripcion": "Limpieza dental profesional completa con ultrasonido, incluye revisión de encías y pulido dental",
  "costobase": "150.00",
  "precio_vigente": "150.00",
  "duracion": 45,
  "activo": true,
  "fecha_creacion": "2025-10-15T10:30:00Z",
  "fecha_modificacion": "2025-10-18T15:45:00Z",
  "empresa": 1
}
```

---

### 3. Obtener Detalle Completo (Endpoint Extendido)

**GET** `/clinic/servicios/{id}/detalle_completo/`

Endpoint alternativo para obtener el detalle completo con toda la información del servicio.

#### Respuesta Exitosa (200 OK)

```json
{
  "id": 1,
  "nombre": "Limpieza Dental",
  "descripcion": "Limpieza dental profesional completa con ultrasonido, incluye revisión de encías y pulido dental",
  "costobase": "150.00",
  "precio_vigente": "150.00",
  "duracion": 45,
  "activo": true,
  "fecha_creacion": "2025-10-15T10:30:00Z",
  "fecha_modificacion": "2025-10-18T15:45:00Z",
  "empresa": 1
}
```

---

### 4. Crear Nuevo Servicio (Admin)

**POST** `/clinic/servicios/`

Crea un nuevo servicio en el catálogo.

#### Request Body

```json
{
  "nombre": "Blanqueamiento Dental",
  "descripcion": "Blanqueamiento profesional con gel de peróxido de hidrógeno",
  "costobase": "400.00",
  "duracion": 60,
  "activo": true
}
```

#### Respuesta Exitosa (201 Created)

```json
{
  "id": 15,
  "nombre": "Blanqueamiento Dental",
  "descripcion": "Blanqueamiento profesional con gel de peróxido de hidrógeno",
  "costobase": "400.00",
  "precio_vigente": "400.00",
  "duracion": 60,
  "activo": true,
  "fecha_creacion": "2025-10-19T12:00:00Z",
  "fecha_modificacion": "2025-10-19T12:00:00Z",
  "empresa": 1
}
```

---

### 5. Actualizar Servicio (Admin)

**PUT** `/clinic/servicios/{id}/`

Actualiza completamente un servicio existente.

#### Request Body

```json
{
  "nombre": "Limpieza Dental Premium",
  "descripcion": "Limpieza dental profesional completa con ultrasonido y fluorización",
  "costobase": "180.00",
  "duracion": 60,
  "activo": true
}
```

#### Respuesta Exitosa (200 OK)

```json
{
  "id": 1,
  "nombre": "Limpieza Dental Premium",
  "descripcion": "Limpieza dental profesional completa con ultrasonido y fluorización",
  "costobase": "180.00",
  "precio_vigente": "180.00",
  "duracion": 60,
  "activo": true,
  "fecha_creacion": "2025-10-15T10:30:00Z",
  "fecha_modificacion": "2025-10-19T14:30:00Z",
  "empresa": 1
}
```

---

### 6. Actualización Parcial (Admin)

**PATCH** `/clinic/servicios/{id}/`

Actualiza solo los campos especificados de un servicio.

#### Request Body (ejemplo: solo precio y estado)

```json
{
  "costobase": "160.00",
  "activo": false
}
```

---

### 7. Eliminar Servicio (Admin)

**DELETE** `/clinic/servicios/{id}/`

Elimina un servicio del catálogo.

#### Respuesta Exitosa (204 No Content)

Sin contenido en el body.

---

## 🚀 Ejemplos de Uso

### Ejemplo 1: Búsqueda de Servicios por Texto

```javascript
// JavaScript/Fetch
const buscarServicios = async (textoBusqueda) => {
  const response = await fetch(
    `https://norte.notificct.dpdns.org/clinic/servicios/?search=${textoBusqueda}`,
    {
      headers: {
        'Authorization': 'Token abc123def456',
        'X-Tenant-Subdomain': 'norte'
      }
    }
  );
  const data = await response.json();
  return data.results;
};

// Uso
buscarServicios('limpieza');
```

```python
# Python/Requests
import requests

def buscar_servicios(texto):
    headers = {
        'Authorization': 'Token abc123def456',
        'X-Tenant-Subdomain': 'norte'
    }
    response = requests.get(
        f'https://norte.notificct.dpdns.org/clinic/servicios/?search={texto}',
        headers=headers
    )
    return response.json()['results']

# Uso
servicios = buscar_servicios('limpieza')
```

---

### Ejemplo 2: Filtrar Servicios por Rango de Precio

```javascript
// JavaScript/Axios
import axios from 'axios';

const obtenerServiciosPorPrecio = async (precioMin, precioMax) => {
  try {
    const response = await axios.get(
      'https://norte.notificct.dpdns.org/clinic/servicios/',
      {
        params: {
          precio_min: precioMin,
          precio_max: precioMax,
          ordering: 'costobase'  // Ordenar por precio ascendente
        },
        headers: {
          'Authorization': 'Token abc123def456',
          'X-Tenant-Subdomain': 'norte'
        }
      }
    );
    return response.data.results;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
};

// Uso: Servicios entre $100 y $500
const servicios = await obtenerServiciosPorPrecio(100, 500);
```

---

### Ejemplo 3: Listar con Paginación y Ordenamiento

```javascript
// React Hooks Example
import { useState, useEffect } from 'react';
import axios from 'axios';

const ServiciosCatalogo = () => {
  const [servicios, setServicios] = useState([]);
  const [pagina, setPagina] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(1);
  const [ordenamiento, setOrdenamiento] = useState('nombre');

  useEffect(() => {
    const cargarServicios = async () => {
      try {
        const response = await axios.get(
          'https://norte.notificct.dpdns.org/clinic/servicios/',
          {
            params: {
              page: pagina,
              page_size: 10,
              ordering: ordenamiento
            },
            headers: {
              'Authorization': `Token ${localStorage.getItem('token')}`,
              'X-Tenant-Subdomain': 'norte'
            }
          }
        );
        
        setServicios(response.data.results);
        setTotalPaginas(Math.ceil(response.data.count / 10));
      } catch (error) {
        console.error('Error cargando servicios:', error);
      }
    };

    cargarServicios();
  }, [pagina, ordenamiento]);

  return (
    <div>
      {/* Selector de ordenamiento */}
      <select onChange={(e) => setOrdenamiento(e.target.value)}>
        <option value="nombre">Nombre (A-Z)</option>
        <option value="-nombre">Nombre (Z-A)</option>
        <option value="costobase">Precio (Menor a Mayor)</option>
        <option value="-costobase">Precio (Mayor a Menor)</option>
        <option value="duracion">Duración (Corta a Larga)</option>
        <option value="-duracion">Duración (Larga a Corta)</option>
      </select>

      {/* Lista de servicios */}
      <ul>
        {servicios.map(servicio => (
          <li key={servicio.id}>
            {servicio.nombre} - ${servicio.precio_vigente} - {servicio.duracion} min
          </li>
        ))}
      </ul>

      {/* Paginación */}
      <button 
        onClick={() => setPagina(p => Math.max(1, p - 1))}
        disabled={pagina === 1}
      >
        Anterior
      </button>
      <span>Página {pagina} de {totalPaginas}</span>
      <button 
        onClick={() => setPagina(p => Math.min(totalPaginas, p + 1))}
        disabled={pagina === totalPaginas}
      >
        Siguiente
      </button>
    </div>
  );
};
```

---

### Ejemplo 4: Filtros Combinados

```javascript
// Vue.js Example
export default {
  data() {
    return {
      filtros: {
        busqueda: '',
        precioMin: null,
        precioMax: null,
        duracionMin: null,
        duracionMax: null,
        soloActivos: true
      },
      servicios: [],
      loading: false
    };
  },
  
  methods: {
    async aplicarFiltros() {
      this.loading = true;
      
      const params = new URLSearchParams();
      
      if (this.filtros.busqueda) params.append('search', this.filtros.busqueda);
      if (this.filtros.precioMin) params.append('precio_min', this.filtros.precioMin);
      if (this.filtros.precioMax) params.append('precio_max', this.filtros.precioMax);
      if (this.filtros.duracionMin) params.append('duracion_min', this.filtros.duracionMin);
      if (this.filtros.duracionMax) params.append('duracion_max', this.filtros.duracionMax);
      if (!this.filtros.soloActivos) params.append('activo', ''); // Incluir inactivos
      
      try {
        const response = await fetch(
          `https://norte.notificct.dpdns.org/clinic/servicios/?${params}`,
          {
            headers: {
              'Authorization': `Token ${this.$store.state.token}`,
              'X-Tenant-Subdomain': 'norte'
            }
          }
        );
        
        const data = await response.json();
        this.servicios = data.results;
      } catch (error) {
        console.error('Error aplicando filtros:', error);
      } finally {
        this.loading = false;
      }
    }
  }
};
```

---

### Ejemplo 5: Crear Nuevo Servicio (Administrador)

```javascript
// TypeScript/Axios Example
import axios from 'axios';

interface NuevoServicio {
  nombre: string;
  descripcion: string;
  costobase: string;
  duracion: number;
  activo: boolean;
}

const crearServicio = async (servicio: NuevoServicio) => {
  try {
    const response = await axios.post(
      'https://norte.notificct.dpdns.org/clinic/servicios/',
      servicio,
      {
        headers: {
          'Authorization': `Token ${getAuthToken()}`,
          'X-Tenant-Subdomain': 'norte',
          'Content-Type': 'application/json'
        }
      }
    );
    
    console.log('Servicio creado:', response.data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Error de validación:', error.response?.data);
    }
    throw error;
  }
};

// Uso
const nuevoServicio = {
  nombre: 'Ortodoncia Invisible',
  descripcion: 'Tratamiento de ortodoncia con alineadores transparentes',
  costobase: '5000.00',
  duracion: 120,
  activo: true
};

crearServicio(nuevoServicio);
```

---

## 📊 Códigos de Estado HTTP

| Código | Descripción | Cuándo Ocurre |
|--------|-------------|---------------|
| 200 OK | Solicitud exitosa | GET, PUT, PATCH exitosos |
| 201 Created | Recurso creado | POST exitoso |
| 204 No Content | Eliminación exitosa | DELETE exitoso |
| 400 Bad Request | Datos inválidos | Validación fallida |
| 401 Unauthorized | No autenticado | Token faltante o inválido |
| 403 Forbidden | Sin permisos | Usuario sin permisos para la acción |
| 404 Not Found | Recurso no encontrado | ID de servicio inexistente |
| 500 Server Error | Error del servidor | Error interno del backend |

---

## 📦 Estructura de Datos

### Objeto Servicio (Completo)

```typescript
interface Servicio {
  id: number;                    // ID único del servicio
  nombre: string;                // Nombre del servicio (max 255 caracteres)
  descripcion: string | null;   // Descripción detallada (opcional)
  costobase: string;             // Precio base en formato decimal "XXX.XX"
  precio_vigente: string;        // Precio actual (igual a costobase)
  duracion: number;              // Duración en minutos (default: 30)
  activo: boolean;               // Si el servicio está disponible (default: true)
  fecha_creacion: string;        // ISO 8601 timestamp
  fecha_modificacion: string;    // ISO 8601 timestamp
  empresa: number;               // ID de la empresa/clínica (asignado automáticamente)
}
```

### Objeto Servicio (Listado Simplificado)

```typescript
interface ServicioListado {
  id: number;
  nombre: string;
  costobase: string;
  precio_vigente: string;
  duracion: number;
  activo: boolean;
}
```

### Respuesta Paginada

```typescript
interface RespuestaPaginada<T> {
  count: number;          // Total de resultados
  next: string | null;    // URL de la siguiente página (null si es la última)
  previous: string | null; // URL de la página anterior (null si es la primera)
  results: T[];           // Array de resultados
}
```

---

## 🎨 Consideraciones de UI/UX

### Filtrado en Tiempo Real

Recomendamos implementar debouncing en la búsqueda por texto para evitar múltiples llamadas al API:

```javascript
import { useState, useEffect } from 'react';
import { debounce } from 'lodash';

const [busqueda, setBusqueda] = useState('');

const buscarConDebounce = debounce((texto) => {
  // Llamada al API
  buscarServicios(texto);
}, 500); // Espera 500ms después de que el usuario deje de escribir

useEffect(() => {
  if (busqueda.length >= 3) {  // Solo buscar con 3+ caracteres
    buscarConDebounce(busqueda);
  }
}, [busqueda]);
```

### Visualización de Servicios Inactivos

Por defecto, la API solo muestra servicios activos. Para mostrar servicios inactivos en una sección de administración:

```javascript
// Para administradores - mostrar todos
const todosLosServicios = await fetch(
  'https://norte.notificct.dpdns.org/clinic/servicios/?activo=',  // Sin valor = mostrar todos
  { headers: authHeaders }
);
```

### Indicadores de Carga

```javascript
const [cargando, setCargando] = useState(false);
const [error, setError] = useState(null);

const cargarServicios = async () => {
  setCargando(true);
  setError(null);
  
  try {
    const response = await fetch(url, { headers });
    if (!response.ok) throw new Error('Error al cargar servicios');
    const data = await response.json();
    setServicios(data.results);
  } catch (err) {
    setError(err.message);
  } finally {
    setCargando(false);
  }
};
```

---

## ⚠️ Notas Importantes

1. **Aislamiento Multi-Tenant**: Cada clínica solo ve sus propios servicios. El sistema filtra automáticamente por tenant.

2. **Servicios Inactivos**: Por defecto, solo se muestran servicios con `activo=true`. Para incluir inactivos, omitir el parámetro `activo` o enviarlo vacío.

3. **Precio Vigente**: Por ahora, `precio_vigente` es igual a `costobase`. Este campo está preparado para futuras implementaciones de precios dinámicos o promociones.

4. **Duración**: Se expresa en minutos. Valores típicos: 30, 45, 60, 90, 120.

5. **Paginación**: El tamaño máximo de página es 100. El default es 10 resultados por página.

6. **Ordenamiento**: Soporta múltiples campos. Usa `-` para orden descendente.

---

## 🔄 Flujo Recomendado para UI

### Vista de Catálogo de Servicios

```
┌─────────────────────────────────────────────┐
│  🔍 Búsqueda: [___________________]         │
│                                             │
│  💰 Precio: [$__] a [$__]                   │
│  ⏱️ Duración: [__] a [__] min               │
│  📊 Ordenar por: [Nombre ▼]                 │
│                                             │
├─────────────────────────────────────────────┤
│  📋 Servicios Disponibles (25 resultados)  │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Limpieza Dental             $150.00 │   │
│  │ 45 minutos                          │   │
│  │ [Ver Detalle]                       │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Endodoncia                  $800.00 │   │
│  │ 90 minutos                          │   │
│  │ [Ver Detalle]                       │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  [◀ Anterior]  Pág 1 de 3  [Siguiente ▶]   │
└─────────────────────────────────────────────┘
```

---

## 📞 Soporte

Para dudas o problemas con la integración, contactar al equipo de backend o consultar el código fuente en:

- **Modelos**: `api/models.py` (clase `Servicio`)
- **Vistas**: `clinic/views.py` (clase `ServicioViewSet`)
- **Serializers**: `clinic/serializers.py`
- **Tests**: `clinic/test_servicios.py`

---

**Fecha de creación**: Octubre 2025  
**Autor**: Backend Team - Dental Clinic SaaS  
**Versión**: 1.0.0
