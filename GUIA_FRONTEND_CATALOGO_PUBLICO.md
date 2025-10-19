# 🌐 Catálogo Público de Servicios - Guía para Frontend

## 📋 Resumen Ejecutivo

Esta API permite a **pacientes y visitantes** consultar el catálogo de servicios dentales **sin necesidad de autenticación**. Es ideal para mostrar en la página pública de la clínica, permitiendo que cualquier persona vea los servicios disponibles antes de agendar una cita.

---

## 🎯 Características Principales

✅ **Acceso Público** - No requiere autenticación para consultar servicios  
✅ **Búsqueda en Tiempo Real** - Busca por nombre o descripción  
✅ **Filtros Inteligentes** - Por precio y duración  
✅ **Ordenamiento Flexible** - Por nombre, precio o duración  
✅ **Paginación Automática** - Para mejor rendimiento  
✅ **Solo Servicios Activos** - Oculta servicios descontinuados  
✅ **Multi-Tenant** - Cada clínica ve sus propios servicios  

---

## 🚀 Quick Start

### Ejemplo Básico - JavaScript/Fetch

```javascript
// Listar servicios de una clínica (sin autenticación)
const cargarServicios = async () => {
  try {
    const response = await fetch(
      'https://norte.notificct.dpdns.org/clinic/servicios/',
      {
        headers: {
          'X-Tenant-Subdomain': 'norte'
        }
      }
    );
    
    const data = await response.json();
    console.log('Servicios disponibles:', data.results);
    return data;
  } catch (error) {
    console.error('Error cargando servicios:', error);
  }
};

cargarServicios();
```

**Respuesta:**
```json
{
  "count": 8,
  "next": null,
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

## 📡 Endpoints Disponibles (Acceso Público)

### 1. 🔍 Listar Servicios

**GET** `/clinic/servicios/`

**Autenticación:** ❌ No requerida

#### Parámetros de Consulta

| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `search` | string | Buscar en nombre y descripción | `?search=limpieza` |
| `precio_min` | decimal | Precio mínimo | `?precio_min=100` |
| `precio_max` | decimal | Precio máximo | `?precio_max=500` |
| `duracion_min` | integer | Duración mínima (minutos) | `?duracion_min=30` |
| `duracion_max` | integer | Duración máxima (minutos) | `?duracion_max=90` |
| `ordering` | string | Ordenar resultados | `?ordering=costobase` |
| `page` | integer | Número de página | `?page=2` |
| `page_size` | integer | Resultados por página (max: 100) | `?page_size=20` |

#### Opciones de Ordenamiento

- `nombre` - Alfabético A-Z
- `-nombre` - Alfabético Z-A
- `costobase` - Precio menor a mayor
- `-costobase` - Precio mayor a menor
- `duracion` - Duración corta a larga
- `-duracion` - Duración larga a corta

---

### 2. 📄 Detalle de Servicio

**GET** `/clinic/servicios/{id}/`

**Autenticación:** ❌ No requerida

```javascript
// Obtener detalle de un servicio específico
const obtenerDetalle = async (servicioId) => {
  const response = await fetch(
    `https://norte.notificct.dpdns.org/clinic/servicios/${servicioId}/`,
    {
      headers: {
        'X-Tenant-Subdomain': 'norte'
      }
    }
  );
  
  return await response.json();
};

// Uso
const detalle = await obtenerDetalle(1);
```

**Respuesta:**
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

## 💻 Ejemplos Prácticos de Integración

### 🎨 React - Componente de Catálogo

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const CatalogoServicios = () => {
  const [servicios, setServicios] = useState([]);
  const [busqueda, setBusqueda] = useState('');
  const [precioMax, setPrecioMax] = useState('');
  const [ordenamiento, setOrdenamiento] = useState('nombre');
  const [cargando, setCargando] = useState(false);

  const BASE_URL = 'https://norte.notificct.dpdns.org/clinic/servicios/';
  const HEADERS = {
    'X-Tenant-Subdomain': 'norte'
  };

  useEffect(() => {
    cargarServicios();
  }, [busqueda, precioMax, ordenamiento]);

  const cargarServicios = async () => {
    setCargando(true);
    
    try {
      const params = new URLSearchParams();
      if (busqueda) params.append('search', busqueda);
      if (precioMax) params.append('precio_max', precioMax);
      params.append('ordering', ordenamiento);

      const response = await axios.get(`${BASE_URL}?${params}`, {
        headers: HEADERS
      });

      setServicios(response.data.results);
    } catch (error) {
      console.error('Error cargando servicios:', error);
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="catalogo-servicios">
      <h1>Nuestros Servicios</h1>
      
      {/* Filtros */}
      <div className="filtros">
        <input
          type="text"
          placeholder="Buscar servicio..."
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
        />
        
        <input
          type="number"
          placeholder="Precio máximo"
          value={precioMax}
          onChange={(e) => setPrecioMax(e.target.value)}
        />
        
        <select 
          value={ordenamiento} 
          onChange={(e) => setOrdenamiento(e.target.value)}
        >
          <option value="nombre">Nombre A-Z</option>
          <option value="-nombre">Nombre Z-A</option>
          <option value="costobase">Precio: Menor a Mayor</option>
          <option value="-costobase">Precio: Mayor a Menor</option>
          <option value="duracion">Duración: Corta a Larga</option>
        </select>
      </div>

      {/* Lista de Servicios */}
      {cargando ? (
        <p>Cargando servicios...</p>
      ) : (
        <div className="servicios-grid">
          {servicios.map(servicio => (
            <ServicioCard key={servicio.id} servicio={servicio} />
          ))}
        </div>
      )}
    </div>
  );
};

const ServicioCard = ({ servicio }) => (
  <div className="servicio-card">
    <h3>{servicio.nombre}</h3>
    <p className="precio">${servicio.precio_vigente}</p>
    <p className="duracion">⏱️ {servicio.duracion} minutos</p>
    <button onClick={() => verDetalle(servicio.id)}>
      Ver Detalles
    </button>
  </div>
);

const verDetalle = (id) => {
  // Navegar a página de detalle o abrir modal
  window.location.href = `/servicios/${id}`;
};

export default CatalogoServicios;
```

---

### 🎭 Vue.js - Catálogo con Filtros

```vue
<template>
  <div class="catalogo-container">
    <h1>Servicios Disponibles</h1>
    
    <!-- Búsqueda y Filtros -->
    <div class="filtros-panel">
      <input 
        v-model="filtros.busqueda" 
        @input="debounceCargar"
        placeholder="Buscar servicio..."
        type="text"
      />
      
      <div class="rango-precio">
        <label>Precio:</label>
        <input 
          v-model="filtros.precioMin" 
          @change="cargarServicios"
          type="number" 
          placeholder="Mín"
        />
        <span>-</span>
        <input 
          v-model="filtros.precioMax" 
          @change="cargarServicios"
          type="number" 
          placeholder="Máx"
        />
      </div>
      
      <select v-model="filtros.ordenamiento" @change="cargarServicios">
        <option value="nombre">Ordenar por Nombre</option>
        <option value="costobase">Precio Menor</option>
        <option value="-costobase">Precio Mayor</option>
        <option value="duracion">Duración</option>
      </select>
    </div>
    
    <!-- Resultados -->
    <div v-if="cargando" class="loading">
      <p>Cargando servicios...</p>
    </div>
    
    <div v-else class="servicios-lista">
      <div 
        v-for="servicio in servicios" 
        :key="servicio.id"
        class="servicio-item"
      >
        <h3>{{ servicio.nombre }}</h3>
        <p class="precio">${{ servicio.precio_vigente }}</p>
        <p class="duracion">{{ servicio.duracion }} minutos</p>
        <button @click="verDetalle(servicio.id)">Ver Más</button>
      </div>
    </div>
    
    <!-- Sin Resultados -->
    <div v-if="!cargando && servicios.length === 0" class="sin-resultados">
      <p>No se encontraron servicios que coincidan con tu búsqueda.</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { debounce } from 'lodash';

export default {
  name: 'CatalogoServicios',
  
  data() {
    return {
      servicios: [],
      cargando: false,
      filtros: {
        busqueda: '',
        precioMin: '',
        precioMax: '',
        ordenamiento: 'nombre'
      },
      baseURL: 'https://norte.notificct.dpdns.org/clinic/servicios/',
      subdomain: 'norte'
    };
  },
  
  mounted() {
    this.cargarServicios();
  },
  
  methods: {
    async cargarServicios() {
      this.cargando = true;
      
      try {
        const params = {};
        if (this.filtros.busqueda) params.search = this.filtros.busqueda;
        if (this.filtros.precioMin) params.precio_min = this.filtros.precioMin;
        if (this.filtros.precioMax) params.precio_max = this.filtros.precioMax;
        params.ordering = this.filtros.ordenamiento;
        
        const response = await axios.get(this.baseURL, {
          params,
          headers: {
            'X-Tenant-Subdomain': this.subdomain
          }
        });
        
        this.servicios = response.data.results;
      } catch (error) {
        console.error('Error:', error);
        this.$toast.error('Error al cargar servicios');
      } finally {
        this.cargando = false;
      }
    },
    
    debounceCargar: debounce(function() {
      this.cargarServicios();
    }, 500),
    
    verDetalle(id) {
      this.$router.push(`/servicios/${id}`);
    }
  }
};
</script>
```

---

### 🍦 JavaScript Vanilla - Landing Page

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Nuestros Servicios</title>
  <style>
    .servicios-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: 20px;
      padding: 20px;
    }
    
    .servicio-card {
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
      transition: transform 0.2s;
    }
    
    .servicio-card:hover {
      transform: translateY(-5px);
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .precio {
      font-size: 24px;
      color: #2c3e50;
      font-weight: bold;
    }
    
    .filtros {
      padding: 20px;
      background: #f5f5f5;
      border-radius: 8px;
      margin: 20px;
    }
    
    .filtros input, .filtros select {
      margin: 10px;
      padding: 8px;
      border-radius: 4px;
      border: 1px solid #ddd;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Servicios Dentales Disponibles</h1>
    
    <div class="filtros">
      <input 
        type="text" 
        id="busqueda" 
        placeholder="Buscar servicio..."
        onkeyup="buscarServicios()"
      />
      
      <input 
        type="number" 
        id="precioMax" 
        placeholder="Precio máximo"
        onchange="cargarServicios()"
      />
      
      <select id="ordenamiento" onchange="cargarServicios()">
        <option value="nombre">Nombre A-Z</option>
        <option value="costobase">Precio Menor</option>
        <option value="-costobase">Precio Mayor</option>
      </select>
    </div>
    
    <div id="servicios-container" class="servicios-grid">
      <!-- Los servicios se cargarán aquí -->
    </div>
  </div>

  <script>
    const BASE_URL = 'https://norte.notificct.dpdns.org/clinic/servicios/';
    const SUBDOMAIN = 'norte';
    
    // Cargar servicios al iniciar
    window.addEventListener('DOMContentLoaded', cargarServicios);
    
    async function cargarServicios() {
      const container = document.getElementById('servicios-container');
      container.innerHTML = '<p>Cargando servicios...</p>';
      
      try {
        const params = new URLSearchParams();
        
        const busqueda = document.getElementById('busqueda').value;
        if (busqueda) params.append('search', busqueda);
        
        const precioMax = document.getElementById('precioMax').value;
        if (precioMax) params.append('precio_max', precioMax);
        
        const ordenamiento = document.getElementById('ordenamiento').value;
        params.append('ordering', ordenamiento);
        
        const response = await fetch(`${BASE_URL}?${params}`, {
          headers: {
            'X-Tenant-Subdomain': SUBDOMAIN
          }
        });
        
        const data = await response.json();
        mostrarServicios(data.results);
        
      } catch (error) {
        container.innerHTML = '<p>Error al cargar servicios</p>';
        console.error('Error:', error);
      }
    }
    
    function mostrarServicios(servicios) {
      const container = document.getElementById('servicios-container');
      
      if (servicios.length === 0) {
        container.innerHTML = '<p>No se encontraron servicios</p>';
        return;
      }
      
      container.innerHTML = servicios.map(servicio => `
        <div class="servicio-card">
          <h3>${servicio.nombre}</h3>
          <p class="precio">$${servicio.precio_vigente}</p>
          <p>⏱️ ${servicio.duracion} minutos</p>
          <button onclick="verDetalle(${servicio.id})">
            Ver Detalle
          </button>
        </div>
      `).join('');
    }
    
    // Debounce para búsqueda
    let searchTimeout;
    function buscarServicios() {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(cargarServicios, 500);
    }
    
    async function verDetalle(id) {
      try {
        const response = await fetch(`${BASE_URL}${id}/`, {
          headers: {
            'X-Tenant-Subdomain': SUBDOMAIN
          }
        });
        
        const servicio = await response.json();
        
        // Mostrar en modal o navegar a página de detalle
        alert(`
          ${servicio.nombre}
          
          ${servicio.descripcion}
          
          Precio: $${servicio.precio_vigente}
          Duración: ${servicio.duracion} minutos
        `);
        
      } catch (error) {
        console.error('Error:', error);
      }
    }
  </script>
</body>
</html>
```

---

## 🔐 Importante: Operaciones que SÍ Requieren Autenticación

Solo las operaciones de **lectura** son públicas. Las operaciones de **administración** requieren autenticación:

### ❌ Requiere Autenticación (Admin)

- **POST** `/clinic/servicios/` - Crear servicio
- **PUT** `/clinic/servicios/{id}/` - Actualizar servicio
- **PATCH** `/clinic/servicios/{id}/` - Actualización parcial
- **DELETE** `/clinic/servicios/{id}/` - Eliminar servicio

```javascript
// Ejemplo: Intentar crear sin autenticación - Fallará
const intentarCrear = async () => {
  const response = await fetch('https://norte.notificct.dpdns.org/clinic/servicios/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Tenant-Subdomain': 'norte'
    },
    body: JSON.stringify({
      nombre: 'Nuevo Servicio',
      costobase: '100.00',
      duracion: 30
    })
  });
  
  console.log(response.status); // 401 Unauthorized
};
```

---

## 📱 Casos de Uso Comunes

### 1. Página de Servicios Pública

**Objetivo:** Mostrar todos los servicios en la página web de la clínica

```javascript
// Cargar todos los servicios
fetch('https://miClinica.notificct.dpdns.org/clinic/servicios/', {
  headers: { 'X-Tenant-Subdomain': 'miClinica' }
})
  .then(res => res.json())
  .then(data => mostrarEnPagina(data.results));
```

### 2. Buscador en Tiempo Real

**Objetivo:** Búsqueda mientras el usuario escribe

```javascript
const buscarEnTiempoReal = debounce(async (texto) => {
  if (texto.length < 3) return; // Mínimo 3 caracteres
  
  const response = await fetch(
    `https://miClinica.notificct.dpdns.org/clinic/servicios/?search=${texto}`,
    { headers: { 'X-Tenant-Subdomain': 'miClinica' } }
  );
  
  const data = await response.json();
  actualizarResultados(data.results);
}, 300);
```

### 3. Filtro por Presupuesto

**Objetivo:** Mostrar servicios dentro del presupuesto del paciente

```javascript
const serviciosPorPresupuesto = async (presupuesto) => {
  const response = await fetch(
    `https://miClinica.notificct.dpdns.org/clinic/servicios/?precio_max=${presupuesto}&ordering=costobase`,
    { headers: { 'X-Tenant-Subdomain': 'miClinica' } }
  );
  
  return await response.json();
};

// Uso
const servicios = await serviciosPorPresupuesto(500);
```

### 4. Comparador de Servicios

**Objetivo:** Comparar múltiples servicios lado a lado

```javascript
const compararServicios = async (ids) => {
  const promesas = ids.map(id => 
    fetch(`https://miClinica.notificct.dpdns.org/clinic/servicios/${id}/`, {
      headers: { 'X-Tenant-Subdomain': 'miClinica' }
    }).then(res => res.json())
  );
  
  const servicios = await Promise.all(promesas);
  return servicios;
};

// Uso
const comparacion = await compararServicios([1, 2, 3]);
```

---

## 🎨 Mejores Prácticas de UI/UX

### 1. Indicadores de Carga

```javascript
const ServiciosSkeleton = () => (
  <div className="skeleton">
    {[1,2,3,4].map(i => (
      <div key={i} className="skeleton-card animate-pulse">
        <div className="h-6 bg-gray-200 rounded mb-2"></div>
        <div className="h-4 bg-gray-200 rounded mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    ))}
  </div>
);
```

### 2. Manejo de Errores

```javascript
const cargarConErrorHandling = async () => {
  try {
    const response = await fetch(url, { headers });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    return data;
    
  } catch (error) {
    if (error.message.includes('Failed to fetch')) {
      mostrarError('Sin conexión a internet');
    } else {
      mostrarError('Error al cargar servicios');
    }
    console.error('Error detallado:', error);
  }
};
```

### 3. Caché para Mejor Rendimiento

```javascript
const cache = new Map();
const CACHE_TIME = 5 * 60 * 1000; // 5 minutos

const cargarConCache = async (url) => {
  const now = Date.now();
  const cached = cache.get(url);
  
  if (cached && (now - cached.timestamp) < CACHE_TIME) {
    return cached.data;
  }
  
  const response = await fetch(url, headers);
  const data = await response.json();
  
  cache.set(url, {
    data,
    timestamp: now
  });
  
  return data;
};
```

---

## 🌐 Multi-Tenant: Configuración por Clínica

Cada clínica tiene su propio subdominio y solo ve sus propios servicios:

```javascript
// Clínica Norte
const serviciosNorte = await fetch(
  'https://norte.notificct.dpdns.org/clinic/servicios/',
  { headers: { 'X-Tenant-Subdomain': 'norte' } }
);

// Clínica Sur
const serviciosSur = await fetch(
  'https://sur.notificct.dpdns.org/clinic/servicios/',
  { headers: { 'X-Tenant-Subdomain': 'sur' } }
);

// Cada una verá solo sus servicios
```

---

## ⚡ Optimizaciones de Performance

### Paginación Eficiente

```javascript
const cargarPagina = async (numeroPagina, tamano = 10) => {
  const response = await fetch(
    `${BASE_URL}?page=${numeroPagina}&page_size=${tamano}`,
    { headers }
  );
  
  const data = await response.json();
  
  return {
    servicios: data.results,
    totalPaginas: Math.ceil(data.count / tamano),
    siguiente: data.next,
    anterior: data.previous
  };
};
```

### Infinite Scroll

```javascript
const InfiniteScrollServicios = () => {
  const [servicios, setServicios] = useState([]);
  const [pagina, setPagina] = useState(1);
  const [cargando, setCargando] = useState(false);
  const [hayMas, setHayMas] = useState(true);
  
  const cargarMas = async () => {
    if (cargando || !hayMas) return;
    
    setCargando(true);
    const data = await cargarPagina(pagina);
    
    setServicios(prev => [...prev, ...data.servicios]);
    setPagina(prev => prev + 1);
    setHayMas(!!data.siguiente);
    setCargando(false);
  };
  
  useEffect(() => {
    cargarMas();
  }, []);
  
  return (
    <InfiniteScroll
      dataLength={servicios.length}
      next={cargarMas}
      hasMore={hayMas}
      loader={<h4>Cargando...</h4>}
    >
      {servicios.map(servicio => (
        <ServicioCard key={servicio.id} servicio={servicio} />
      ))}
    </InfiniteScroll>
  );
};
```

---

## 📊 TypeScript Interfaces

```typescript
interface Servicio {
  id: number;
  nombre: string;
  descripcion: string | null;
  costobase: string;
  precio_vigente: string;
  duracion: number;
  activo: boolean;
  fecha_creacion: string;
  fecha_modificacion: string;
  empresa: number;
}

interface ServicioListado {
  id: number;
  nombre: string;
  costobase: string;
  precio_vigente: string;
  duracion: number;
  activo: boolean;
}

interface RespuestaPaginada<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Uso
const cargarServicios = async (): Promise<RespuestaPaginada<ServicioListado>> => {
  const response = await fetch(BASE_URL, { headers });
  return await response.json();
};
```

---

## 🚨 Manejo de Errores HTTP

| Código | Descripción | Acción Recomendada |
|--------|-------------|-------------------|
| 200 OK | Éxito | Mostrar resultados |
| 404 Not Found | Servicio no existe | Mostrar mensaje "Servicio no encontrado" |
| 500 Server Error | Error del servidor | Mostrar "Error temporal, intenta más tarde" |
| Network Error | Sin conexión | Mostrar "Verifica tu conexión a internet" |

---

## ✅ Checklist de Integración

- [ ] Configurar subdomain correcto en headers
- [ ] Implementar búsqueda con debounce
- [ ] Agregar indicadores de carga
- [ ] Manejar estado vacío (sin resultados)
- [ ] Implementar paginación o infinite scroll
- [ ] Caché de resultados para mejor UX
- [ ] Manejo de errores de red
- [ ] Responsive design para móviles
- [ ] Accesibilidad (ARIA labels, keyboard navigation)
- [ ] SEO optimization (meta tags, structured data)

---

## 📞 Soporte y Recursos

- **Documentación Técnica Completa**: `DOCUMENTACION_API_SERVICIOS_FRONTEND.md`
- **Código Fuente**: 
  - Modelos: `api/models.py`
  - Vistas: `clinic/views.py`
  - Tests: `clinic/test_servicios.py`
- **Tests**: 22/22 passing ✅

---

**Última actualización**: Octubre 2025  
**Versión API**: 1.1.0 (Acceso Público)  
**Estado**: ✅ Producción - Acceso Público Habilitado
