# 🔧 SOLUCION: Excel Mostrando "[object Object]"

## ❌ Problema
Al exportar a Excel, aparecía:
```
1,"[object Object]","[object Object]","","[object Object]","[object Object]","[object Object]","2025-10-16","1"
```

**Causa:** El backend devolvía objetos anidados complejos en lugar de valores planos.

---

## ✅ Solución Implementada

### Backend - Nuevo Serializer

Se creó `ConsultaReporteSerializer` en `api/serializers.py` que devuelve valores planos:

```python
class ConsultaReporteSerializer(serializers.ModelSerializer):
    """
    Serializador para reportes y exportación a Excel.
    Devuelve valores planos en lugar de objetos anidados.
    """
    # Paciente
    paciente_nombre = serializers.CharField(
        source='codpaciente.codusuario.nombre', 
        read_only=True
    )
    paciente_apellido = serializers.CharField(
        source='codpaciente.codusuario.apellido', 
        read_only=True
    )
    paciente_rut = serializers.CharField(
        source='codpaciente.codusuario.rut', 
        read_only=True
    )
    
    # Odontólogo
    odontologo_nombre = serializers.CharField(
        source='cododontologo.codusuario.nombre', 
        read_only=True
    )
    odontologo_apellido = serializers.CharField(
        source='cododontologo.codusuario.apellido', 
        read_only=True
    )
    
    # Horario
    hora_inicio = serializers.CharField(
        source='idhorario.hora', 
        read_only=True
    )
    
    # Tipo de consulta
    tipo_consulta = serializers.CharField(
        source='idtipoconsulta.nombreconsulta', 
        read_only=True
    )
    
    # Estado
    estado = serializers.CharField(
        source='idestadoconsulta.estado', 
        read_only=True
    )
```

---

## 📋 Nuevo Formato de Respuesta

### Antes (objetos anidados):
```json
{
  "idconsulta": 1,
  "fecha": "2025-10-16",
  "codpaciente": {
    "codigo": 1,
    "codusuario": {
      "nombre": "Juan",
      "apellido": "Pérez",
      "rut": "12345678-9"
    }
  },
  "cododontologo": {
    "codigo": 2,
    "codusuario": {
      "nombre": "María",
      "apellido": "García"
    }
  },
  "idhorario": {
    "id": 1,
    "hora": "09:00"
  },
  "idtipoconsulta": {
    "id": 1,
    "nombreconsulta": "Revisión"
  },
  "idestadoconsulta": {
    "id": 1,
    "estado": "Confirmada"
  }
}
```

### Ahora (valores planos):
```json
{
  "id": 1,
  "fecha": "2025-10-16",
  "paciente_nombre": "Juan",
  "paciente_apellido": "Pérez",
  "paciente_rut": "12345678-9",
  "odontologo_nombre": "María",
  "odontologo_apellido": "García",
  "hora_inicio": "09:00",
  "tipo_consulta": "Revisión",
  "estado": "Confirmada"
}
```

---

## 🔄 Actualización Requerida en Frontend

### Cambios Necesarios

**1. Actualizar Interfaz TypeScript:**

```typescript
// ANTES
interface Consulta {
  idconsulta: number;
  fecha: string;
  codpaciente: {
    codusuario: {
      nombre: string;
      apellido: string;
      rut: string;
    };
  };
  cododontologo: {
    codusuario: {
      nombre: string;
      apellido: string;
    };
  };
  idhorario: {
    hora: string;
  };
  idtipoconsulta: {
    nombreconsulta: string;
  };
  idestadoconsulta: {
    estado: string;
  };
}

// AHORA
interface ConsultaReporte {
  id: number;  // Cambio: era idconsulta
  fecha: string;
  paciente_nombre: string;
  paciente_apellido: string;
  paciente_rut: string;
  odontologo_nombre: string;
  odontologo_apellido: string;
  hora_inicio: string;
  tipo_consulta: string;
  estado: string;
}
```

**2. Actualizar Tabla de Reportes:**

```typescript
// ANTES
<td>{consulta.codpaciente.codusuario.nombre} {consulta.codpaciente.codusuario.apellido}</td>
<td>{consulta.cododontologo.codusuario.nombre} {consulta.cododontologo.codusuario.apellido}</td>
<td>{consulta.idestadoconsulta.estado}</td>

// AHORA
<td>{consulta.paciente_nombre} {consulta.paciente_apellido}</td>
<td>{consulta.odontologo_nombre} {consulta.odontologo_apellido}</td>
<td>{consulta.estado}</td>
```

**3. Actualizar Función de Exportación a Excel:**

```typescript
// ANTES
const exportarExcel = (consultas: Consulta[]) => {
  const datosExcel = consultas.map(c => ({
    ID: c.idconsulta,
    Fecha: c.fecha,
    Paciente: `${c.codpaciente.codusuario.nombre} ${c.codpaciente.codusuario.apellido}`,
    RUT: c.codpaciente.codusuario.rut,
    Odontólogo: `${c.cododontologo.codusuario.nombre} ${c.cododontologo.codusuario.apellido}`,
    Hora: c.idhorario.hora,
    Tipo: c.idtipoconsulta.nombreconsulta,
    Estado: c.idestadoconsulta.estado
  }));
  
  const ws = XLSX.utils.json_to_sheet(datosExcel);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Consultas');
  XLSX.writeFile(wb, 'reporte_consultas.xlsx');
};

// AHORA (MÁS SIMPLE)
const exportarExcel = (consultas: ConsultaReporte[]) => {
  const datosExcel = consultas.map(c => ({
    ID: c.id,  // Cambio: era c.idconsulta
    Fecha: c.fecha,
    Paciente: `${c.paciente_nombre} ${c.paciente_apellido}`,
    RUT: c.paciente_rut,
    Odontólogo: `${c.odontologo_nombre} ${c.odontologo_apellido}`,
    Hora: c.hora_inicio,
    Tipo: c.tipo_consulta,
    Estado: c.estado
  }));
  
  const ws = XLSX.utils.json_to_sheet(datosExcel);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Consultas');
  XLSX.writeFile(wb, 'reporte_consultas.xlsx');
};
```

---

## 📊 Campos Disponibles en el Nuevo Formato

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `id` | number | ID de la consulta | `1` |
| `fecha` | string | Fecha de la consulta | `"2025-10-16"` |
| `paciente_nombre` | string | Nombre del paciente | `"Juan"` |
| `paciente_apellido` | string | Apellido del paciente | `"Pérez"` |
| `paciente_rut` | string | RUT del paciente | `"12345678-9"` |
| `odontologo_nombre` | string | Nombre del odontólogo | `"María"` |
| `odontologo_apellido` | string | Apellido del odontólogo | `"García"` |
| `hora_inicio` | string | Hora de la consulta | `"09:00"` |
| `tipo_consulta` | string | Tipo de consulta | `"Revisión"` |
| `estado` | string | Estado actual | `"Confirmada"` |

---

## 🧪 Testing

### Probar en el Navegador

```bash
# 1. Obtener reportes
GET http://localhost:8000/api/reportes/?fecha_inicio=12/10/2025&fecha_fin=14/10/2025

# 2. Verificar respuesta en formato plano:
[
  {
    "id": 1,
    "fecha": "2025-10-16",
    "paciente_nombre": "Juan",
    "paciente_apellido": "Pérez",
    "paciente_rut": "12345678-9",
    "odontologo_nombre": "María",
    "odontologo_apellido": "García",
    "hora_inicio": "09:00",
    "tipo_consulta": "Revisión",
    "estado": "Confirmada"
  }
]
```

### Probar Exportación a Excel

1. Cargar reportes en el frontend
2. Click en "Exportar a Excel"
3. Verificar que el archivo Excel muestra:
   ```
   ID | Fecha       | Paciente      | RUT         | Odontólogo     | Hora  | Tipo     | Estado
   1  | 2025-10-16  | Juan Pérez    | 12345678-9  | María García   | 09:00 | Revisión | Confirmada
   ```

---

## ✅ Beneficios del Nuevo Formato

1. **✅ Compatible con Excel:** Valores planos en lugar de objetos
2. **✅ Más simple:** Menos anidación en el frontend
3. **✅ Mejor rendimiento:** Menos procesamiento en el frontend
4. **✅ Código más limpio:** Menos `.codpaciente.codusuario.nombre`
5. **✅ Fácil de exportar:** Directo a CSV/Excel sin transformaciones

---

## 📝 Resumen de Cambios en Frontend

### Archivo: `interfaces/Consulta.ts`
```typescript
// Agregar nueva interfaz
export interface ConsultaReporte {
  id: number;  // PK del modelo
  fecha: string;
  paciente_nombre: string;
  paciente_apellido: string;
  paciente_rut: string;
  odontologo_nombre: string;
  odontologo_apellido: string;
  hora_inicio: string;
  tipo_consulta: string;
  estado: string;
}
```

### Archivo: `services/reportesService.ts`
```typescript
// Cambiar tipo de retorno
export const obtenerConsultasFiltradas = async (
  filtros: FiltrosReporte
): Promise<ConsultaReporte[]> => {  // ← Cambiar aquí
  // ... resto del código igual
};
```

### Archivo: `pages/ReportesPage.tsx`
```typescript
// 1. Cambiar tipo de estado
const [consultas, setConsultas] = useState<ConsultaReporte[]>([]);  // ← Cambiar aquí

# 2. Actualizar renderizado de tabla
<tbody>
  {consultas.map((consulta) => (
    <tr key={consulta.id}>
      <td>{consulta.fecha}</td>
      <td>{consulta.paciente_nombre} {consulta.paciente_apellido}</td>
      <td>{consulta.odontologo_nombre} {consulta.odontologo_apellido}</td>
      <td>{consulta.estado}</td>
    </tr>
  ))}
</tbody>
```

---

## 🚀 Pasos para Implementar

1. **Backend:** ✅ Ya está actualizado (servidor corriendo con cambios)
2. **Frontend:**
   - [ ] Crear interfaz `ConsultaReporte`
   - [ ] Actualizar tipo en `reportesService.ts`
   - [ ] Actualizar tipo en `ReportesPage.tsx`
   - [ ] Actualizar renderizado de tabla (cambiar acceso a propiedades)
   - [ ] Actualizar función de exportación a Excel
   - [ ] Probar que todo funcione

---

## 🎯 Resultado Esperado en Excel

```
ID | Fecha       | Paciente      | RUT         | Odontólogo     | Hora  | Tipo     | Estado
---|-------------|---------------|-------------|----------------|-------|----------|------------
1  | 2025-10-16  | Juan Pérez    | 12345678-9  | María García   | 09:00 | Revisión | Confirmada
2  | 2025-10-16  | Ana López     | 98765432-1  | Carlos Muñoz   | 10:00 | Limpieza | Pendiente
```

**Ya NO más `[object Object]`!** ✅

---

## 📞 Soporte

Si encuentras algún problema:
1. Verifica que el backend esté corriendo
2. Revisa la respuesta en Network Tab (F12)
3. Confirma que los campos tienen los nuevos nombres (`paciente_nombre` en lugar de `codpaciente.codusuario.nombre`)

**Servidor Backend:** ✅ Actualizado y corriendo en `http://0.0.0.0:8000`
