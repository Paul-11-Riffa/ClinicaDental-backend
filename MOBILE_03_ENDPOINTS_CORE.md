# 📱 Guía de Desarrollo Móvil - Endpoints Core

## 🎯 Endpoints Principales

Este documento cubre los endpoints esenciales para la funcionalidad básica de la app móvil.

---

## 📋 Tabla de Contenidos

1. [Pacientes](#1-pacientes)
2. [Consultas (Citas)](#2-consultas-citas)
3. [Odontólogos](#3-odontólogos)
4. [Horarios](#4-horarios)
5. [Tipos de Consulta](#5-tipos-de-consulta)
6. [Estados de Consulta](#6-estados-de-consulta)

---

## 1️⃣ Pacientes

### Listar Pacientes

```http
GET /api/pacientes/
Authorization: Token {token}
```

**Query Parameters** (opcionales):
- `search`: Buscar por nombre, apellido o CI
- `ordering`: Ordenar por campo (`nombre`, `-nombre`, `apellido`)
- `page`: Número de página (paginación)

**Response (200 OK)**
```json
{
  "count": 150,
  "next": "https://api.example.com/api/pacientes/?page=2",
  "previous": null,
  "results": [
    {
      "codusuario": {
        "codigo": 1,
        "nombre": "Juan",
        "apellido": "Pérez",
        "correoelectronico": "juan@example.com",
        "telefono": "+591 70123456"
      },
      "carnetidentidad": "1234567",
      "fechanacimiento": "1990-05-15",
      "direccion": "Av. Principal #123",
      "empresa": 1
    }
  ]
}
```

### Obtener Paciente Específico

```http
GET /api/pacientes/{codusuario}/
Authorization: Token {token}
```

**Response (200 OK)**
Retorna objeto paciente individual.

### Buscar Pacientes

```http
GET /api/pacientes/?search=juan
Authorization: Token {token}
```

Busca en: `nombre`, `apellido`, `carnetidentidad`

---

## 2️⃣ Consultas (Citas)

### Listar Consultas del Usuario

```http
GET /api/consultas/
Authorization: Token {token}
```

**Query Parameters**:
- `codpaciente`: Filtrar por paciente (ID)
- `cododontologo`: Filtrar por odontólogo (ID)
- `idestadoconsulta`: Filtrar por estado (1-6)
- `fecha`: Filtrar por fecha específica
  - `hoy`: Consultas de hoy
  - `2025-10-20`: Fecha específica (YYYY-MM-DD)
- `ordering`: `-fecha` (más recientes primero)

**Ejemplos de uso**:
```
# Consultas del paciente actual
GET /api/consultas/?codpaciente=15

# Consultas de hoy
GET /api/consultas/?fecha=hoy

# Consultas pendientes (estado=1)
GET /api/consultas/?idestadoconsulta=1&codpaciente=15

# Consultas futuras ordenadas
GET /api/consultas/?fecha__gte=2025-10-15&ordering=fecha
```

**Response (200 OK)**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 42,
      "fecha": "2025-10-20",
      "codpaciente": {
        "codusuario": {
          "codigo": 15,
          "nombre": "Juan",
          "apellido": "Pérez",
          "correoelectronico": "juan@example.com",
          "telefono": "+591 70123456"
        },
        "carnetidentidad": "1234567"
      },
      "cododontologo": {
        "codigo": 3,
        "codusuario": {
          "codigo": 3,
          "nombre": "María",
          "apellido": "García",
          "correoelectronico": "maria.garcia@clinica.com",
          "telefono": "+591 70999888"
        },
        "especialidad": "Ortodoncia",
        "nromatricula": "ORD-123"
      },
      "codrecepcionista": null,
      "idhorario": {
        "id": 5,
        "hora": "10:00:00"
      },
      "idtipoconsulta": {
        "id": 1,
        "nombreconsulta": "Limpieza dental"
      },
      "idestadoconsulta": {
        "id": 1,
        "estado": "Agendada"
      },
      "empresa": 1
    }
  ]
}
```

### Crear Nueva Consulta

```http
POST /api/consultas/
Authorization: Token {token}
Content-Type: application/json
```

**Request Body**
```json
{
  "fecha": "2025-10-25",
  "codpaciente": 15,
  "cododontologo": 3,
  "idhorario": 8,
  "idtipoconsulta": 1,
  "idestadoconsulta": 1
}
```

**Campos**:
- `fecha` (required): Fecha de la cita en formato `YYYY-MM-DD`
- `codpaciente` (required): ID del paciente (obtenlo del perfil del usuario)
- `cododontologo` (required): ID del odontólogo
- `idhorario` (required): ID del horario
- `idtipoconsulta` (required): ID del tipo de consulta
- `idestadoconsulta` (required): ID del estado (generalmente 1 = Agendada)
- `codrecepcionista` (optional): ID de recepcionista

**Response (201 Created)**
Retorna la consulta creada completa.

**Errores Comunes**:

```json
{
  "detail": "Este horario ya está reservado con el odontólogo seleccionado."
}
```

### Obtener Consulta Específica

```http
GET /api/consultas/{id}/
Authorization: Token {token}
```

### Actualizar Estado de Consulta

```http
PATCH /api/consultas/{id}/
Authorization: Token {token}
Content-Type: application/json
```

**Request Body**
```json
{
  "idestadoconsulta": 2
}
```

**Uso**: Cambiar estado de consulta (ej: 1→2 para confirmar asistencia)

### Reprogramar Consulta

```http
PATCH /api/consultas/{id}/reprogramar/
Authorization: Token {token}
Content-Type: application/json
```

**Request Body**
```json
{
  "fecha": "2025-10-28",
  "idhorario": 10
}
```

**Validaciones**:
- No se puede reprogramar citas pasadas
- Nueva fecha debe ser futura
- Nuevo horario debe estar disponible

**Response (200 OK)**
Retorna la consulta actualizada + recrea notificaciones automáticamente.

**Errores**:
```json
{
  "non_field_errors": [
    "No se puede reprogramar una cita que ya pasó de fecha."
  ]
}
```

```json
{
  "non_field_errors": [
    "El nuevo horario seleccionado no está disponible."
  ]
}
```

### Cancelar Consulta

```http
POST /api/consultas/{id}/cancelar/
Authorization: Token {token}
```

**Response (200 OK)**
```json
{
  "ok": true,
  "detail": "La cita ha sido cancelada y eliminada.",
  "id": 42
}
```

**Importante**: Esta acción **elimina permanentemente** la cita de la base de datos y borra las notificaciones pendientes asociadas.

---

## 3️⃣ Odontólogos

### Listar Odontólogos

```http
GET /api/odontologos/
Authorization: Token {token}
```

**Response (200 OK)**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "codigo": 3,
      "codusuario": {
        "codigo": 3,
        "nombre": "María",
        "apellido": "García",
        "correoelectronico": "maria.garcia@clinica.com",
        "telefono": "+591 70999888"
      },
      "especialidad": "Ortodoncia",
      "nromatricula": "ORD-123"
    },
    {
      "codigo": 4,
      "codusuario": {
        "codigo": 4,
        "nombre": "Carlos",
        "apellido": "Rodríguez",
        "correoelectronico": "carlos.rodriguez@clinica.com",
        "telefono": "+591 70888777"
      },
      "especialidad": "Endodoncia",
      "nromatricula": "END-456"
    }
  ]
}
```

### Obtener Odontólogo Específico

```http
GET /api/odontologos/{codigo}/
Authorization: Token {token}
```

**Uso en la App**:
- Mostrar lista de odontólogos al agendar cita
- Mostrar perfil del odontólogo en detalle de cita
- Filtrar citas por odontólogo específico

---

## 4️⃣ Horarios

### Listar Todos los Horarios

```http
GET /api/horarios/
Authorization: Token {token}
```

**Response (200 OK)**
```json
{
  "count": 16,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "hora": "08:00:00"
    },
    {
      "id": 2,
      "hora": "08:30:00"
    },
    {
      "id": 3,
      "hora": "09:00:00"
    },
    {
      "id": 4,
      "hora": "09:30:00"
    }
  ]
}
```

### Obtener Horarios Disponibles

**⭐ Endpoint más importante para agendar citas**

```http
GET /api/horarios/disponibles/?fecha=2025-10-20&odontologo_id=3
Authorization: Token {token}
```

**Query Parameters** (REQUERIDOS):
- `fecha`: Fecha para verificar disponibilidad (YYYY-MM-DD)
- `odontologo_id`: ID del odontólogo

**Response (200 OK)**
```json
[
  {
    "id": 1,
    "hora": "08:00:00"
  },
  {
    "id": 3,
    "hora": "09:00:00"
  },
  {
    "id": 5,
    "hora": "10:00:00"
  }
]
```

**Nota**: Solo retorna horarios que NO están ocupados para ese odontólogo en esa fecha.

**Errores**:

```json
{
  "detail": "Se requieren los parámetros 'fecha' y 'odontologo_id'."
}
```

```json
{
  "detail": "Formato de fecha inválido. Se esperaba YYYY-MM-DD pero se recibió '20-10-2025'.",
  "error": "time data '20-10-2025' does not match format '%Y-%m-%d'"
}
```

---

## 5️⃣ Tipos de Consulta

### Listar Tipos de Consulta

```http
GET /api/tipos-consulta/
Authorization: Token {token}
```

**Response (200 OK)**
```json
{
  "count": 8,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "nombreconsulta": "Limpieza dental"
    },
    {
      "id": 2,
      "nombreconsulta": "Extracción"
    },
    {
      "id": 3,
      "nombreconsulta": "Ortodoncia - Control"
    },
    {
      "id": 4,
      "nombreconsulta": "Endodoncia"
    },
    {
      "id": 5,
      "nombreconsulta": "Revisión general"
    }
  ]
}
```

**Uso**: Mostrar selector de tipo de consulta al agendar cita.

---

## 6️⃣ Estados de Consulta

### Listar Estados de Consulta

```http
GET /api/estadodeconsultas/
Authorization: Token {token}
```

**Response (200 OK)**
```json
[
  {
    "id": 1,
    "estado": "Agendada"
  },
  {
    "id": 2,
    "estado": "Confirmada"
  },
  {
    "id": 3,
    "estado": "Atendida"
  },
  {
    "id": 4,
    "estado": "Cancelada"
  },
  {
    "id": 5,
    "estado": "No Show"
  },
  {
    "id": 6,
    "estado": "Reprogramada"
  }
]
```

**Significado de Estados**:

| ID | Estado | Descripción | Color Sugerido |
|----|--------|-------------|----------------|
| 1 | Agendada | Cita creada, pendiente | 🔵 Azul |
| 2 | Confirmada | Paciente confirmó asistencia | 🟢 Verde |
| 3 | Atendida | Consulta realizada | ⚫ Gris |
| 4 | Cancelada | Paciente canceló | 🔴 Rojo |
| 5 | No Show | Paciente no asistió ⚠️ | 🟠 Naranja |
| 6 | Reprogramada | Cita movida a otra fecha | 🟡 Amarillo |

**Uso en la App**:
- Mostrar badges de estado con colores
- Permitir cambiar estado a "Confirmada" (botón confirmar asistencia)
- Mostrar alertas especiales para "No Show"

---

## 🔄 Flujo Típico: Agendar Nueva Cita

```
1. GET /api/odontologos/
   └─> Mostrar lista de odontólogos
   
2. Usuario selecciona odontólogo (ej: ID=3)
   └─> Mostrar calendario

3. Usuario selecciona fecha (ej: 2025-10-20)
   └─> GET /api/horarios/disponibles/?fecha=2025-10-20&odontologo_id=3
   
4. Mostrar horarios disponibles
   └─> Usuario selecciona horario (ej: ID=5, 10:00)
   
5. GET /api/tipos-consulta/
   └─> Mostrar selector de tipo de consulta
   
6. Usuario selecciona tipo (ej: ID=1, "Limpieza dental")
   
7. POST /api/consultas/
   Body: {
     "fecha": "2025-10-20",
     "codpaciente": 15,
     "cododontologo": 3,
     "idhorario": 5,
     "idtipoconsulta": 1,
     "idestadoconsulta": 1
   }
   
8. Mostrar confirmación
   └─> Redirigir a "Mis Citas"
```

---

## 🎨 Recomendaciones de UI/UX

### Calendario de Citas
- Deshabilitar fechas pasadas
- Marcar fechas con citas existentes
- Mostrar contador de citas por día

### Horarios Disponibles
- Mostrar en formato 12h (ej: "10:00 AM")
- Deshabilitar horarios ocupados
- Agrupar por mañana/tarde/noche

### Lista de Citas
- Separar por: "Próximas", "Pasadas", "Canceladas"
- Mostrar countdown para citas cercanas
- Permitir filtrar por estado

### Detalle de Cita
- Mostrar mapa con dirección de clínica
- Botón "Agregar a Calendario" (device calendar)
- Botón "Compartir" (WhatsApp, etc)
- Permitir confirmar/cancelar/reprogramar

---

## 📊 Paginación

La mayoría de endpoints retornan datos paginados:

```json
{
  "count": 150,          // Total de registros
  "next": "url?page=2",  // URL de siguiente página (null si es la última)
  "previous": null,      // URL de página anterior
  "results": [...]       // Array de objetos
}
```

**Implementar Infinite Scroll**:

```dart
// Flutter ejemplo
class ConsultasBloc {
  int _currentPage = 1;
  bool _hasMore = true;
  
  Future<void> loadMore() async {
    if (!_hasMore) return;
    
    final response = await api.get('/api/consultas/?page=$_currentPage');
    _currentPage++;
    _hasMore = response['next'] != null;
    
    // Agregar resultados a la lista
  }
}
```

---

## ⚡ Caché y Optimización

### Datos a Cachear (cambian poco)
- ✅ Odontólogos
- ✅ Horarios
- ✅ Tipos de consulta
- ✅ Estados de consulta

### Datos a NO Cachear (cambian frecuentemente)
- ❌ Consultas del usuario
- ❌ Horarios disponibles
- ❌ Perfil de usuario

**Flutter - Ejemplo de Caché Simple**:

```dart
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class CacheManager {
  static Future<void> cacheOdontologos(List<dynamic> data) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('odontologos', jsonEncode(data));
    await prefs.setInt('odontologos_timestamp', DateTime.now().millisecondsSinceEpoch);
  }
  
  static Future<List<dynamic>?> getCachedOdontologos() async {
    final prefs = await SharedPreferences.getInstance();
    final timestamp = prefs.getInt('odontologos_timestamp') ?? 0;
    final now = DateTime.now().millisecondsSinceEpoch;
    
    // Cache válido por 24 horas
    if (now - timestamp > 86400000) {
      return null; // Cache expirado
    }
    
    final data = prefs.getString('odontologos');
    return data != null ? jsonDecode(data) : null;
  }
}
```

---

## 🔍 Búsqueda y Filtros

### Buscar Consultas

```http
# Consultas futuras del paciente
GET /api/consultas/?codpaciente=15&fecha__gte=2025-10-15

# Consultas de hoy confirmadas
GET /api/consultas/?fecha=hoy&idestadoconsulta=2

# Consultas con odontólogo específico
GET /api/consultas/?cododontologo=3&codpaciente=15
```

### Ordenamiento

```http
# Más recientes primero
GET /api/consultas/?ordering=-fecha

# Más antiguas primero
GET /api/consultas/?ordering=fecha

# Por estado, luego fecha
GET /api/consultas/?ordering=idestadoconsulta,fecha
```

---

## 🧪 Testing con Curl

### Crear Consulta
```bash
curl -X POST https://notificct.dpdns.org/api/consultas/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fecha": "2025-10-25",
    "codpaciente": 15,
    "cododontologo": 3,
    "idhorario": 8,
    "idtipoconsulta": 1,
    "idestadoconsulta": 1
  }'
```

### Obtener Horarios Disponibles
```bash
curl -X GET "https://notificct.dpdns.org/api/horarios/disponibles/?fecha=2025-10-20&odontologo_id=3" \
  -H "Authorization: Token YOUR_TOKEN"
```

### Listar Mis Consultas
```bash
curl -X GET "https://notificct.dpdns.org/api/consultas/?codpaciente=15" \
  -H "Authorization: Token YOUR_TOKEN"
```

---

## ⚠️ Errores Comunes

### 400 - Horario Ocupado
```json
{
  "detail": "Este horario ya está reservado con el odontólogo seleccionado."
}
```
**Solución**: Volver a consultar horarios disponibles.

### 400 - Fecha Inválida
```json
{
  "fecha": ["Formato de fecha inválido."]
}
```
**Solución**: Usar formato `YYYY-MM-DD`.

### 401 - Token Inválido
```json
{
  "detail": "Invalid token."
}
```
**Solución**: Reautenticar usuario.

### 404 - Paciente No Encontrado
```json
{
  "detail": "Not found."
}
```
**Solución**: Verificar que el usuario tiene perfil de paciente.

---

## 📱 Próximos Pasos

Continúa con: **MOBILE_04_NOTIFICACIONES_PUSH.md** para implementar el sistema completo de notificaciones Firebase.

---

**Última actualización**: 15 de Octubre, 2025
