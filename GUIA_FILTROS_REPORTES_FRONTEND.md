# 📊 Guía de Integración de Filtros de Reportes - Frontend

## ✅ Cambios Implementados en Backend

El endpoint `/api/reportes/` ahora **SÍ aplica los filtros** correctamente:

- ✅ **Filtro por rango de fechas**: `fecha_inicio` y `fecha_fin`
- ✅ **Filtro por odontólogo**: búsqueda por nombre o apellido
- ✅ **Multi-tenant**: automático por subdomain

---

## 🔧 API - Cómo Usar los Filtros

### Endpoint Principal
```
GET /api/reportes/?fecha_inicio=12/10/2025&fecha_fin=14/10/2025&odontologo=juan
```

### Parámetros de Query String

| Parámetro | Tipo | Formato | Descripción | Ejemplo |
|-----------|------|---------|-------------|---------|
| `fecha_inicio` | string | `DD/MM/YYYY` | Fecha inicio del rango (inclusive) | `12/10/2025` |
| `fecha_fin` | string | `DD/MM/YYYY` | Fecha fin del rango (inclusive) | `14/10/2025` |
| `odontologo` | string | texto | Nombre o apellido del odontólogo (case-insensitive) | `juan` o `Juan Pérez` |

### Ejemplos de URLs

```bash
# Filtrar solo por fechas
GET /api/reportes/?fecha_inicio=01/10/2025&fecha_fin=31/10/2025

# Filtrar solo por odontólogo
GET /api/reportes/?odontologo=María

# Combinar todos los filtros
GET /api/reportes/?fecha_inicio=12/10/2025&fecha_fin=14/10/2025&odontologo=Juan
```

---

## 💻 Código Frontend - React/TypeScript

### 1. Función para Construir la URL con Filtros

```typescript
// utils/reportes.ts
interface FiltrosReporte {
  fecha_inicio?: string;  // Formato: DD/MM/YYYY
  fecha_fin?: string;     // Formato: DD/MM/YYYY
  odontologo?: string;
}

/**
 * Construye la URL del endpoint de reportes con los filtros aplicados
 */
export const buildReportesURL = (filtros: FiltrosReporte): string => {
  const baseURL = '/api/reportes/';
  const params = new URLSearchParams();

  // Agregar parámetros solo si tienen valor
  if (filtros.fecha_inicio?.trim()) {
    params.append('fecha_inicio', filtros.fecha_inicio.trim());
  }
  
  if (filtros.fecha_fin?.trim()) {
    params.append('fecha_fin', filtros.fecha_fin.trim());
  }
  
  if (filtros.odontologo?.trim()) {
    params.append('odontologo', filtros.odontologo.trim());
  }

  // Retornar URL completa
  const queryString = params.toString();
  return queryString ? `${baseURL}?${queryString}` : baseURL;
};
```

### 2. Hook para Manejar Filtros

```typescript
// hooks/useReportesFiltros.ts
import { useState, useCallback } from 'react';

interface FiltrosReporte {
  fecha_inicio: string;
  fecha_fin: string;
  odontologo: string;
}

export const useReportesFiltros = () => {
  const [filtros, setFiltros] = useState<FiltrosReporte>({
    fecha_inicio: '',
    fecha_fin: '',
    odontologo: ''
  });

  // Actualizar un filtro específico
  const actualizarFiltro = useCallback((campo: keyof FiltrosReporte, valor: string) => {
    setFiltros(prev => ({
      ...prev,
      [campo]: valor
    }));
  }, []);

  // Limpiar todos los filtros
  const limpiarFiltros = useCallback(() => {
    setFiltros({
      fecha_inicio: '',
      fecha_fin: '',
      odontologo: ''
    });
  }, []);

  return {
    filtros,
    actualizarFiltro,
    limpiarFiltros
  };
};
```

### 3. Servicio API con Filtros

```typescript
// services/reportesService.ts
import api from './axiosConfig';
import { buildReportesURL } from '../utils/reportes';

interface FiltrosReporte {
  fecha_inicio?: string;
  fecha_fin?: string;
  odontologo?: string;
}

interface Consulta {
  idconsulta: number;
  fecha: string;
  codpaciente: {
    codigo: number;
    codusuario: {
      nombre: string;
      apellido: string;
    };
  };
  cododontologo: {
    codigo: number;
    codusuario: {
      nombre: string;
      apellido: string;
    };
  };
  idestadoconsulta: {
    idestado: number;
    estado: string;
  };
  idtipoconsulta: {
    idtipo: number;
    tipo: string;
  };
  idhorario: {
    idhorario: number;
    horainicio: string;
    horafin: string;
  };
}

/**
 * Obtiene las consultas filtradas del backend
 */
export const obtenerConsultasFiltradas = async (
  filtros: FiltrosReporte
): Promise<Consulta[]> => {
  try {
    const url = buildReportesURL(filtros);
    const response = await api.get<Consulta[]>(url);
    
    // Validar que la respuesta sea un array
    if (!Array.isArray(response.data)) {
      console.error('❌ Backend no devolvió un array:', response.data);
      throw new Error('Formato de respuesta inválido');
    }
    
    return response.data;
  } catch (error) {
    console.error('❌ Error al obtener consultas filtradas:', error);
    throw error;
  }
};
```

### 4. Componente de Filtros

```typescript
// components/FiltrosReporte.tsx
import React from 'react';

interface FiltrosReporteProps {
  fechaInicio: string;
  fechaFin: string;
  odontologo: string;
  onChangeFechaInicio: (fecha: string) => void;
  onChangeFechaFin: (fecha: string) => void;
  onChangeOdontologo: (nombre: string) => void;
  onAplicarFiltros: () => void;
  onLimpiarFiltros: () => void;
}

export const FiltrosReporte: React.FC<FiltrosReporteProps> = ({
  fechaInicio,
  fechaFin,
  odontologo,
  onChangeFechaInicio,
  onChangeFechaFin,
  onChangeOdontologo,
  onAplicarFiltros,
  onLimpiarFiltros
}) => {
  return (
    <div className="filtros-container">
      <h3>Filtros</h3>
      
      <div className="filtros-grid">
        {/* Fecha Inicio */}
        <div className="filtro-campo">
          <label htmlFor="fecha-inicio">Fecha Inicio</label>
          <input
            id="fecha-inicio"
            type="date"
            value={fechaInicio}
            onChange={(e) => onChangeFechaInicio(e.target.value)}
            placeholder="DD/MM/YYYY"
          />
        </div>

        {/* Fecha Fin */}
        <div className="filtro-campo">
          <label htmlFor="fecha-fin">Fecha Fin</label>
          <input
            id="fecha-fin"
            type="date"
            value={fechaFin}
            onChange={(e) => onChangeFechaFin(e.target.value)}
            placeholder="DD/MM/YYYY"
          />
        </div>

        {/* Odontólogo */}
        <div className="filtro-campo">
          <label htmlFor="odontologo">Odontólogo (nombre completo)</label>
          <input
            id="odontologo"
            type="text"
            value={odontologo}
            onChange={(e) => onChangeOdontologo(e.target.value)}
            placeholder="Ej: Juan o Juan Pérez"
          />
        </div>
      </div>

      {/* Botones */}
      <div className="filtros-actions">
        <button 
          className="btn-aplicar"
          onClick={onAplicarFiltros}
        >
          Aplicar Filtros
        </button>
        
        <button 
          className="btn-limpiar"
          onClick={onLimpiarFiltros}
        >
          Limpiar Filtros
        </button>
      </div>
    </div>
  );
};
```

### 5. Página Completa de Reportes

```typescript
// pages/ReportesPage.tsx
import React, { useState, useEffect } from 'react';
import { FiltrosReporte } from '../components/FiltrosReporte';
import { obtenerConsultasFiltradas } from '../services/reportesService';
import { useReportesFiltros } from '../hooks/useReportesFiltros';

interface Consulta {
  idconsulta: number;
  fecha: string;
  codpaciente: {
    codusuario: {
      nombre: string;
      apellido: string;
    };
  };
  cododontologo: {
    codusuario: {
      nombre: string;
      apellido: string;
    };
  };
  idestadoconsulta: {
    estado: string;
  };
}

export const ReportesPage: React.FC = () => {
  const { filtros, actualizarFiltro, limpiarFiltros } = useReportesFiltros();
  const [consultas, setConsultas] = useState<Consulta[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Cargar consultas iniciales
  useEffect(() => {
    cargarConsultas();
  }, []);

  // Función para cargar consultas con filtros actuales
  const cargarConsultas = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Convertir fechas de YYYY-MM-DD a DD/MM/YYYY
      const filtrosFormateados = {
        fecha_inicio: filtros.fecha_inicio 
          ? convertirFechaParaBackend(filtros.fecha_inicio)
          : undefined,
        fecha_fin: filtros.fecha_fin 
          ? convertirFechaParaBackend(filtros.fecha_fin)
          : undefined,
        odontologo: filtros.odontologo || undefined
      };

      const data = await obtenerConsultasFiltradas(filtrosFormateados);
      
      if (!Array.isArray(data)) {
        throw new Error('La respuesta del backend no es un array');
      }
      
      setConsultas(data);
    } catch (err) {
      console.error('Error al cargar consultas:', err);
      setError('Error al cargar los datos. Por favor intente nuevamente.');
    } finally {
      setLoading(false);
    }
  };

  // Aplicar filtros
  const handleAplicarFiltros = () => {
    cargarConsultas();
  };

  // Limpiar filtros y recargar
  const handleLimpiarFiltros = () => {
    limpiarFiltros();
    // Cargar consultas sin filtros
    setTimeout(() => cargarConsultas(), 100);
  };

  // Convertir fecha de input (YYYY-MM-DD) a formato backend (DD/MM/YYYY)
  const convertirFechaParaBackend = (fecha: string): string => {
    const [year, month, day] = fecha.split('-');
    return `${day}/${month}/${year}`;
  };

  return (
    <div className="reportes-page">
      <h1>Reportes de Consultas</h1>

      {/* Filtros */}
      <FiltrosReporte
        fechaInicio={filtros.fecha_inicio}
        fechaFin={filtros.fecha_fin}
        odontologo={filtros.odontologo}
        onChangeFechaInicio={(fecha) => actualizarFiltro('fecha_inicio', fecha)}
        onChangeFechaFin={(fecha) => actualizarFiltro('fecha_fin', fecha)}
        onChangeOdontologo={(nombre) => actualizarFiltro('odontologo', nombre)}
        onAplicarFiltros={handleAplicarFiltros}
        onLimpiarFiltros={handleLimpiarFiltros}
      />

      {/* Indicador de carga */}
      {loading && (
        <div className="loading">
          <p>Cargando consultas...</p>
        </div>
      )}

      {/* Mensaje de error */}
      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}

      {/* Tabla de resultados */}
      {!loading && !error && (
        <div className="resultados">
          <h2>Resultados ({consultas.length} consultas)</h2>
          
          {consultas.length === 0 ? (
            <p className="no-resultados">
              No se encontraron consultas con los filtros aplicados.
            </p>
          ) : (
            <table className="tabla-consultas">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Paciente</th>
                  <th>Odontólogo</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {consultas.map((consulta) => (
                  <tr key={consulta.idconsulta}>
                    <td>{consulta.fecha}</td>
                    <td>
                      {consulta.codpaciente.codusuario.nombre}{' '}
                      {consulta.codpaciente.codusuario.apellido}
                    </td>
                    <td>
                      {consulta.cododontologo.codusuario.nombre}{' '}
                      {consulta.cododontologo.codusuario.apellido}
                    </td>
                    <td>{consulta.idestadoconsulta.estado}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
};
```

---

## 🎨 Estilos CSS Recomendados

```css
/* styles/reportes.css */

.reportes-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.filtros-container {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.filtros-container h3 {
  margin-top: 0;
  color: #333;
  font-size: 1.3rem;
}

.filtros-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.filtro-campo {
  display: flex;
  flex-direction: column;
}

.filtro-campo label {
  font-weight: 600;
  margin-bottom: 8px;
  color: #555;
  font-size: 0.9rem;
}

.filtro-campo input {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.filtro-campo input:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.1);
}

.filtros-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.btn-aplicar,
.btn-limpiar {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-aplicar {
  background: #4CAF50;
  color: white;
}

.btn-aplicar:hover {
  background: #45a049;
}

.btn-limpiar {
  background: #f44336;
  color: white;
}

.btn-limpiar:hover {
  background: #da190b;
}

.resultados h2 {
  color: #333;
  margin-bottom: 20px;
}

.no-resultados {
  text-align: center;
  padding: 40px;
  color: #888;
  font-size: 1.1rem;
}

.tabla-consultas {
  width: 100%;
  border-collapse: collapse;
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.tabla-consultas th,
.tabla-consultas td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.tabla-consultas th {
  background: #4CAF50;
  color: white;
  font-weight: 600;
}

.tabla-consultas tbody tr:hover {
  background: #f5f5f5;
}

.loading,
.error-message {
  padding: 20px;
  text-align: center;
  border-radius: 4px;
  margin: 20px 0;
}

.loading {
  background: #e3f2fd;
  color: #1976d2;
}

.error-message {
  background: #ffebee;
  color: #c62828;
}
```

---

## 🧪 Testing - Pruebas Paso a Paso

### Prueba 1: Filtro por Fechas
```bash
# 1. Aplicar filtro de fechas en frontend:
#    Fecha Inicio: 12/10/2025
#    Fecha Fin: 14/10/2025
#    Click "Aplicar Filtros"

# 2. Verificar en Network tab la URL generada:
GET /api/reportes/?fecha_inicio=12/10/2025&fecha_fin=14/10/2025

# 3. Verificar que solo aparecen consultas entre esas fechas
```

### Prueba 2: Filtro por Odontólogo
```bash
# 1. Escribir en el campo Odontólogo: "juan"
# 2. Click "Aplicar Filtros"

# 3. Verificar URL:
GET /api/reportes/?odontologo=juan

# 4. Verificar que solo aparecen consultas de odontólogos con "juan" en nombre/apellido
```

### Prueba 3: Filtros Combinados
```bash
# 1. Aplicar todos los filtros:
#    Fecha Inicio: 12/10/2025
#    Fecha Fin: 14/10/2025
#    Odontólogo: juan

# 2. Verificar URL:
GET /api/reportes/?fecha_inicio=12/10/2025&fecha_fin=14/10/2025&odontologo=juan

# 3. Verificar que aparecen solo consultas que cumplen TODOS los criterios
```

### Prueba 4: Limpiar Filtros
```bash
# 1. Click "Limpiar Filtros"
# 2. Verificar que los campos se vacían
# 3. Verificar URL sin parámetros:
GET /api/reportes/

# 4. Verificar que aparecen TODAS las consultas del tenant
```

---

## 🔍 Debugging - Solución de Problemas

### Problema 1: Los filtros no se aplican

**Síntomas:**
- Los filtros se llenan pero la tabla muestra todos los datos

**Solución:**
```typescript
// Verificar en consola del navegador:
console.log('Filtros actuales:', filtros);
console.log('URL generada:', buildReportesURL(filtros));

// Verificar en Network tab (F12) la URL de la petición
// Debe incluir los parámetros: ?fecha_inicio=...&fecha_fin=...
```

### Problema 2: Error "consultasData.map is not a function"

**Síntomas:**
- Error en consola del navegador

**Solución:**
```typescript
// Agregar validación antes de usar .map()
if (!Array.isArray(consultas)) {
  console.error('❌ Los datos no son un array:', consultas);
  return;
}

consultas.map(...) // Ahora es seguro
```

### Problema 3: Fechas en formato incorrecto

**Síntomas:**
- Backend no filtra por fechas correctamente

**Causa:**
- Input tipo `date` en HTML devuelve formato `YYYY-MM-DD`
- Backend espera formato `DD/MM/YYYY`

**Solución:**
```typescript
// Función de conversión:
const convertirFechaParaBackend = (fecha: string): string => {
  const [year, month, day] = fecha.split('-');
  return `${day}/${month}/${year}`;
};

// Usar antes de enviar al backend:
const filtrosFormateados = {
  fecha_inicio: convertirFechaParaBackend(filtros.fecha_inicio),
  fecha_fin: convertirFechaParaBackend(filtros.fecha_fin),
  odontologo: filtros.odontologo
};
```

### Problema 4: Odontólogo no filtra correctamente

**Síntomas:**
- Escribir "juan" no muestra resultados esperados

**Verificar:**
```typescript
// 1. Verificar que el nombre se envía correctamente:
console.log('Odontólogo buscado:', filtros.odontologo);

// 2. Verificar en backend que el nombre existe:
// Revisar en admin Django o base de datos

// 3. Probar búsqueda case-insensitive:
// Backend usa icontains (insensible a mayúsculas/minúsculas)
```

---

## 📝 Checklist de Implementación

- [ ] ✅ Backend actualizado con lógica de filtros en `ReporteViewSet.list()`
- [ ] Crear función `buildReportesURL()` para construir URLs con query params
- [ ] Crear hook `useReportesFiltros()` para manejar estado de filtros
- [ ] Actualizar servicio API para usar `buildReportesURL()`
- [ ] Crear componente `FiltrosReporte` con inputs de fecha y odontólogo
- [ ] Implementar función de conversión de fechas (`YYYY-MM-DD` → `DD/MM/YYYY`)
- [ ] Agregar botones "Aplicar Filtros" y "Limpiar Filtros"
- [ ] Implementar validación `Array.isArray()` antes de usar `.map()`
- [ ] Agregar estilos CSS para filtros y tabla
- [ ] Probar cada filtro individualmente
- [ ] Probar filtros combinados
- [ ] Verificar comportamiento al limpiar filtros

---

## 🚀 Resumen Rápido para el Frontend

### Pasos de Integración:

1. **Crear función para construir URL con filtros**
   ```typescript
   buildReportesURL({ fecha_inicio, fecha_fin, odontologo })
   ```

2. **Actualizar servicio API**
   ```typescript
   const url = buildReportesURL(filtros);
   const response = await api.get(url);
   ```

3. **Convertir fechas antes de enviar**
   ```typescript
   // Input HTML date: "2025-10-12"
   // Backend espera: "12/10/2025"
   const fechaBackend = convertirFechaParaBackend(fechaInput);
   ```

4. **Validar respuesta es array**
   ```typescript
   if (!Array.isArray(response.data)) {
     throw new Error('Formato inválido');
   }
   ```

5. **Aplicar filtros al hacer click en botón**
   ```typescript
   const handleAplicarFiltros = () => {
     cargarConsultas(); // Llama API con filtros actuales
   };
   ```

---

## 🎯 URLs de Ejemplo para Testing

```bash
# Sin filtros (todas las consultas del tenant)
http://localhost:8000/api/reportes/

# Solo fecha inicio
http://localhost:8000/api/reportes/?fecha_inicio=12/10/2025

# Solo fecha fin
http://localhost:8000/api/reportes/?fecha_fin=14/10/2025

# Rango de fechas
http://localhost:8000/api/reportes/?fecha_inicio=12/10/2025&fecha_fin=14/10/2025

# Solo odontólogo
http://localhost:8000/api/reportes/?odontologo=juan

# Todos los filtros
http://localhost:8000/api/reportes/?fecha_inicio=12/10/2025&fecha_fin=14/10/2025&odontologo=juan
```

---

**¡Listo!** El backend ahora filtra correctamente. Sigue esta guía para integrar los filtros en el frontend. 🎉
