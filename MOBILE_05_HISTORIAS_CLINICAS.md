# 📱 Guía de Desarrollo Móvil - Historias Clínicas

## 📋 Historia Clínica Electrónica (HCE)

El sistema permite gestionar episodios múltiples de historias clínicas por paciente, con trazabilidad completa de cambios.

---

## 🎯 Características

✅ Múltiples episodios por paciente  
✅ Campos clínicos completos (alergias, enfermedades, diagnóstico)  
✅ Timestamps automáticos (creación y actualización)  
✅ Aislamiento por empresa (multi-tenancy)  
✅ Consulta de historial completo  

---

## 📊 Modelo de Datos

```typescript
interface HistoriaClinica {
  id: number;
  pacientecodigo: number;
  episodio: number;              // Número de episodio (1, 2, 3...)
  alergias: string | null;
  enfermedades: string | null;
  motivoconsulta: string | null;
  diagnostico: string | null;
  fecha: string;                 // ISO 8601 timestamp
  updated_at: string;            // ISO 8601 timestamp
  empresa: number;
}
```

### Relación con Paciente

- Un paciente puede tener **múltiples episodios** de historia clínica
- Cada episodio tiene un número consecutivo (1, 2, 3...)
- Constraint único: `(pacientecodigo, episodio)`

---

## 🔗 Endpoints

### Base URL
```
/api/historias-clinicas/
```

---

## 1️⃣ Crear Historia Clínica

```http
POST /api/historias-clinicas/
Authorization: Token {token}
Content-Type: application/json
```

### Request Body

```json
{
  "pacientecodigo": 15,
  "alergias": "Penicilina, Polen",
  "enfermedades": "Diabetes tipo 2 controlada",
  "motivoconsulta": "Dolor en muela inferior derecha",
  "diagnostico": "Caries profunda en pieza 46"
}
```

### Campos

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `pacientecodigo` | integer | ✅ | ID del paciente (código de usuario) |
| `alergias` | string | ❌ | Alergias conocidas del paciente |
| `enfermedades` | string | ❌ | Enfermedades preexistentes |
| `motivoconsulta` | string | ❌ | Motivo de la consulta actual |
| `diagnostico` | string | ❌ | Diagnóstico médico |

**Nota**: El sistema asigna automáticamente:
- `episodio`: Siguiente número disponible para ese paciente
- `fecha`: Timestamp actual
- `empresa`: Empresa del tenant actual

### Response (201 Created)

```json
{
  "id": 42,
  "pacientecodigo": 15,
  "episodio": 3,
  "alergias": "Penicilina, Polen",
  "enfermedades": "Diabetes tipo 2 controlada",
  "motivoconsulta": "Dolor en muela inferior derecha",
  "diagnostico": "Caries profunda en pieza 46",
  "fecha": "2025-10-15T14:30:00.123456Z",
  "updated_at": "2025-10-15T14:30:00.123456Z",
  "empresa": 1
}
```

### Errores Comunes

**400 Bad Request - Paciente no encontrado**
```json
{
  "pacientecodigo": ["Paciente inválido"]
}
```

**400 Bad Request - Campo requerido**
```json
{
  "pacientecodigo": ["Este campo es requerido."]
}
```

---

## 2️⃣ Listar Historias Clínicas

### Todas las Historias del Usuario Autenticado

```http
GET /api/historias-clinicas/
Authorization: Token {token}
```

**Filtros automáticos**:
- Solo historias del paciente autenticado
- Ordenadas por fecha (más reciente primero)

### Response (200 OK)

```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 45,
      "pacientecodigo": 15,
      "episodio": 5,
      "alergias": "Penicilina, Polen",
      "enfermedades": "Diabetes tipo 2 controlada, Hipertensión",
      "motivoconsulta": "Control de rutina",
      "diagnostico": "Estado general bueno",
      "fecha": "2025-10-15T10:00:00Z",
      "updated_at": "2025-10-15T10:00:00Z",
      "empresa": 1
    },
    {
      "id": 42,
      "pacientecodigo": 15,
      "episodio": 4,
      "alergias": "Penicilina",
      "enfermedades": "Diabetes tipo 2",
      "motivoconsulta": "Dolor en muela",
      "diagnostico": "Caries profunda en pieza 46",
      "fecha": "2025-09-20T14:30:00Z",
      "updated_at": "2025-09-20T14:30:00Z",
      "empresa": 1
    }
  ]
}
```

### Filtrar por Paciente (Solo Admin/Odontólogo)

```http
GET /api/historias-clinicas/?pacientecodigo=15
Authorization: Token {admin_token}
```

---

## 3️⃣ Obtener Historia Específica

```http
GET /api/historias-clinicas/{id}/
Authorization: Token {token}
```

### Response (200 OK)

Retorna objeto individual de historia clínica.

**Restricción**: Solo puedes acceder a tus propias historias (o si eres admin/odontólogo).

---

## 4️⃣ Actualizar Historia Clínica

```http
PATCH /api/historias-clinicas/{id}/
Authorization: Token {token}
Content-Type: application/json
```

### Request Body (Todos los campos son opcionales)

```json
{
  "alergias": "Penicilina, Polen, Nueces",
  "enfermedades": "Diabetes tipo 2 controlada, Hipertensión",
  "diagnostico": "Caries profunda en pieza 46 - Tratamiento completado"
}
```

### Response (200 OK)

Retorna la historia actualizada con `updated_at` actualizado.

**Nota**: El campo `episodio` NO se puede modificar.

---

## 5️⃣ Eliminar Historia Clínica

```http
DELETE /api/historias-clinicas/{id}/
Authorization: Token {token}
```

### Response (204 No Content)

**Importante**: Esta acción es permanente. Considera desactivar en lugar de eliminar.

---

## 🎨 Implementación en la App Móvil

### Flutter - Servicio de Historias Clínicas

```dart
// historia_clinica_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class HistoriaClinicaService {
  static const String baseUrl = 'https://notificct.dpdns.org/api';
  
  Future<List<HistoriaClinica>> obtenerHistorias() async {
    final token = await TokenStorage.getToken();
    
    final response = await http.get(
      Uri.parse('$baseUrl/historias-clinicas/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return (data['results'] as List)
          .map((json) => HistoriaClinica.fromJson(json))
          .toList();
    } else {
      throw Exception('Error al cargar historias');
    }
  }
  
  Future<HistoriaClinica> crearHistoria({
    required int pacientecodigo,
    String? alergias,
    String? enfermedades,
    String? motivoconsulta,
    String? diagnostico,
  }) async {
    final token = await TokenStorage.getToken();
    
    final response = await http.post(
      Uri.parse('$baseUrl/historias-clinicas/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'pacientecodigo': pacientecodigo,
        if (alergias != null) 'alergias': alergias,
        if (enfermedades != null) 'enfermedades': enfermedades,
        if (motivoconsulta != null) 'motivoconsulta': motivoconsulta,
        if (diagnostico != null) 'diagnostico': diagnostico,
      }),
    );
    
    if (response.statusCode == 201) {
      return HistoriaClinica.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Error al crear historia: ${response.body}');
    }
  }
  
  Future<HistoriaClinica> actualizarHistoria(
    int id, 
    Map<String, dynamic> cambios,
  ) async {
    final token = await TokenStorage.getToken();
    
    final response = await http.patch(
      Uri.parse('$baseUrl/historias-clinicas/$id/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode(cambios),
    );
    
    if (response.statusCode == 200) {
      return HistoriaClinica.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Error al actualizar historia');
    }
  }
}

// Modelo
class HistoriaClinica {
  final int id;
  final int pacientecodigo;
  final int episodio;
  final String? alergias;
  final String? enfermedades;
  final String? motivoconsulta;
  final String? diagnostico;
  final DateTime fecha;
  final DateTime updatedAt;
  
  HistoriaClinica({
    required this.id,
    required this.pacientecodigo,
    required this.episodio,
    this.alergias,
    this.enfermedades,
    this.motivoconsulta,
    this.diagnostico,
    required this.fecha,
    required this.updatedAt,
  });
  
  factory HistoriaClinica.fromJson(Map<String, dynamic> json) {
    return HistoriaClinica(
      id: json['id'],
      pacientecodigo: json['pacientecodigo'],
      episodio: json['episodio'],
      alergias: json['alergias'],
      enfermedades: json['enfermedades'],
      motivoconsulta: json['motivoconsulta'],
      diagnostico: json['diagnostico'],
      fecha: DateTime.parse(json['fecha']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }
}
```

---

### Flutter - Pantalla de Historial

```dart
// historial_screen.dart
import 'package:flutter/material.dart';

class HistorialScreen extends StatefulWidget {
  @override
  _HistorialScreenState createState() => _HistorialScreenState();
}

class _HistorialScreenState extends State<HistorialScreen> {
  final _service = HistoriaClinicaService();
  List<HistoriaClinica> _historias = [];
  bool _loading = true;
  
  @override
  void initState() {
    super.initState();
    _cargarHistorias();
  }
  
  Future<void> _cargarHistorias() async {
    setState(() => _loading = true);
    try {
      final historias = await _service.obtenerHistorias();
      setState(() {
        _historias = historias;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error al cargar historias: $e')),
      );
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Mi Historial Clínico'),
      ),
      body: _loading
          ? Center(child: CircularProgressIndicator())
          : _historias.isEmpty
              ? Center(child: Text('No hay historias clínicas'))
              : ListView.builder(
                  itemCount: _historias.length,
                  itemBuilder: (context, index) {
                    final historia = _historias[index];
                    return Card(
                      margin: EdgeInsets.all(8),
                      child: ListTile(
                        title: Text('Episodio ${historia.episodio}'),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            SizedBox(height: 8),
                            if (historia.motivoconsulta != null)
                              Text('Motivo: ${historia.motivoconsulta}'),
                            if (historia.diagnostico != null)
                              Text('Diagnóstico: ${historia.diagnostico}'),
                            SizedBox(height: 4),
                            Text(
                              'Fecha: ${_formatFecha(historia.fecha)}',
                              style: TextStyle(fontSize: 12, color: Colors.grey),
                            ),
                          ],
                        ),
                        onTap: () => _mostrarDetalle(historia),
                      ),
                    );
                  },
                ),
      floatingActionButton: FloatingActionButton(
        onPressed: _crearNuevaHistoria,
        child: Icon(Icons.add),
      ),
    );
  }
  
  String _formatFecha(DateTime fecha) {
    return '${fecha.day}/${fecha.month}/${fecha.year}';
  }
  
  void _mostrarDetalle(HistoriaClinica historia) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Episodio ${historia.episodio}'),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildCampo('Alergias', historia.alergias),
              _buildCampo('Enfermedades', historia.enfermedades),
              _buildCampo('Motivo', historia.motivoconsulta),
              _buildCampo('Diagnóstico', historia.diagnostico),
              SizedBox(height: 8),
              Text(
                'Creado: ${_formatFecha(historia.fecha)}',
                style: TextStyle(fontSize: 12, color: Colors.grey),
              ),
              Text(
                'Actualizado: ${_formatFecha(historia.updatedAt)}',
                style: TextStyle(fontSize: 12, color: Colors.grey),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cerrar'),
          ),
        ],
      ),
    );
  }
  
  Widget _buildCampo(String label, String? valor) {
    if (valor == null || valor.isEmpty) return SizedBox.shrink();
    return Padding(
      padding: EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
          ),
          SizedBox(height: 4),
          Text(valor),
        ],
      ),
    );
  }
  
  void _crearNuevaHistoria() {
    // Navegar a pantalla de creación
    // Navigator.push(...);
  }
}
```

---

### React Native - Servicio

```javascript
// historiaClinicaService.js
import api from './api';

export const HistoriaClinicaService = {
  async obtenerHistorias() {
    const response = await api.get('/historias-clinicas/');
    return response.data.results;
  },

  async crearHistoria(data) {
    const response = await api.post('/historias-clinicas/', data);
    return response.data;
  },

  async actualizarHistoria(id, cambios) {
    const response = await api.patch(`/historias-clinicas/${id}/`, cambios);
    return response.data;
  },

  async eliminarHistoria(id) {
    await api.delete(`/historias-clinicas/${id}/`);
  },
};
```

---

## 🔒 Permisos y Seguridad

### Reglas de Acceso

1. **Paciente**: 
   - ✅ Puede ver sus propias historias
   - ✅ Puede crear nuevas historias
   - ✅ Puede actualizar sus historias
   - ❌ No puede ver historias de otros pacientes

2. **Odontólogo**:
   - ✅ Puede ver historias de sus pacientes
   - ✅ Puede crear/actualizar historias
   
3. **Admin**:
   - ✅ Acceso completo a todas las historias

### Filtrado Automático

El backend filtra automáticamente por:
- **Empresa**: Solo historias de la empresa del tenant
- **Usuario**: Pacientes solo ven sus propias historias

---

## 📊 Casos de Uso Comunes

### 1. Ver Historial Completo

```dart
final historias = await HistoriaClinicaService().obtenerHistorias();
// Ordenadas por fecha descendente
```

### 2. Registrar Nueva Consulta

```dart
await HistoriaClinicaService().crearHistoria(
  pacientecodigo: miCodigoUsuario,
  motivoconsulta: 'Dolor de muelas',
  alergias: 'Ninguna conocida',
);
```

### 3. Actualizar Información Médica

```dart
await HistoriaClinicaService().actualizarHistoria(
  historiaId,
  {
    'alergias': 'Penicilina (nueva)',
    'enfermedades': 'Diabetes tipo 2',
  },
);
```

---

## 🎯 Recomendaciones de UI/UX

### Pantalla de Historial
- **Timeline view**: Mostrar episodios en orden cronológico
- **Tarjetas expandibles**: Mostrar resumen, expandir para detalle
- **Indicadores visuales**: Iconos para alergias, enfermedades graves
- **Búsqueda**: Filtrar por fecha, diagnóstico

### Formulario de Creación
- **Campos separados**: Un campo por tipo de información
- **Autocompletado**: Sugerir alergias/enfermedades comunes
- **Validación**: Alertar si campos importantes están vacíos
- **Confirmación**: Mostrar resumen antes de guardar

### Alertas de Alergias
- **Banner prominente**: Si el paciente tiene alergias
- **Color de advertencia**: Rojo/naranja para alergias graves
- **Mostrar en todas las pantallas**: Recordatorio constante

---

## 🧪 Testing

### Crear Historia de Prueba

```bash
curl -X POST https://notificct.dpdns.org/api/historias-clinicas/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pacientecodigo": 15,
    "alergias": "Penicilina",
    "enfermedades": "Ninguna",
    "motivoconsulta": "Control de rutina",
    "diagnostico": "Estado general bueno"
  }'
```

### Listar Historias

```bash
curl -X GET https://notificct.dpdns.org/api/historias-clinicas/ \
  -H "Authorization: Token YOUR_TOKEN"
```

---

## ⚠️ Consideraciones Importantes

### Datos Sensibles
- Las historias clínicas son **datos médicos sensibles**
- Implementa **encriptación** en tránsito (HTTPS)
- NO almacenes historias en caché local sin encriptar
- Cumple con regulaciones locales (HIPAA, GDPR equivalente)

### Privacidad
- Solo muestra historias del usuario autenticado
- Implementa timeout de sesión
- Requiere re-autenticación para acciones sensibles

### Trazabilidad
- El backend registra automáticamente `fecha` y `updated_at`
- Considera agregar bitácora de cambios para auditoría

---

## 📱 Próximos Pasos

Continúa con: **MOBILE_06_POLITICAS_NOSHOW.md** para entender el sistema de penalizaciones por inasistencias.

---

**Última actualización**: 15 de Octubre, 2025
