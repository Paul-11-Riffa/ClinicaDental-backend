# 📱 Guía de Desarrollo Móvil - Políticas de No-Show

## ⚠️ Sistema de Penalizaciones por Inasistencia

El backend incluye un sistema automatizado de penalizaciones cuando un paciente no asiste a una cita sin previo aviso ("No-Show").

---

## 🎯 ¿Qué es una Política de No-Show?

Una **Política de No-Show** es una regla de negocio configurada por la clínica que se activa automáticamente cuando una cita cambia a cierto estado (generalmente "No Show").

**Acciones automáticas**:
- 💰 Multa económica
- 🚫 Bloqueo temporal del usuario
- 📧 Notificación al paciente
- 📊 Registro en bitácora

---

## 📊 Modelos Relacionados

### 1. PoliticaNoShow

```typescript
interface PoliticaNoShow {
  id: number;
  nombre: string;
  descripcion: string;
  estado_consulta: number;           // ID del estado que activa la política
  accion: string;                    // "MULTA" | "BLOQUEO" | "NOTIFICACION"
  monto_multa: string | null;        // Decimal (ej: "50.00")
  dias_bloqueo: number | null;       // Días de bloqueo
  mensaje_notificacion: string | null;
  activo: boolean;
  empresa: number;
  fecha_creacion: string;
}
```

### 2. Multa

```typescript
interface Multa {
  id: number;
  paciente: number;                  // ID del paciente
  consulta: number | null;           // ID de la consulta (opcional)
  monto: string;                     // Decimal
  motivo: string;
  fecha_creacion: string;
  pagada: boolean;
  fecha_pago: string | null;
  empresa: number;
}
```

### 3. BloqueoUsuario

```typescript
interface BloqueoUsuario {
  id: number;
  usuario: number;                   // ID del usuario
  motivo: string;
  fecha_inicio: string;
  fecha_fin: string | null;          // null = bloqueo indefinido
  activo: boolean;
  empresa: number;
}
```

---

## 🔗 Endpoints

### Base URL
```
/api/politicas-no-show/
```

---

## 1️⃣ Listar Políticas Activas

```http
GET /api/politicas-no-show/
Authorization: Token {token}
```

**Query Parameters**:
- `activo`: Filtrar por estado (`true` o `false`)
- `estado_consulta`: Filtrar por estado de consulta

### Response (200 OK)

```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "nombre": "Multa por Primera Inasistencia",
      "descripcion": "Se aplica una multa de Bs. 50 en la primera inasistencia",
      "estado_consulta": 5,
      "accion": "MULTA",
      "monto_multa": "50.00",
      "dias_bloqueo": null,
      "mensaje_notificacion": "Se ha aplicado una multa de Bs. 50 por inasistencia",
      "activo": true,
      "empresa": 1,
      "fecha_creacion": "2025-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "nombre": "Bloqueo por Segunda Inasistencia",
      "descripcion": "Bloqueo de 7 días después de la segunda inasistencia",
      "estado_consulta": 5,
      "accion": "BLOQUEO",
      "monto_multa": null,
      "dias_bloqueo": 7,
      "mensaje_notificacion": "Usuario bloqueado por 7 días debido a reincidencia",
      "activo": true,
      "empresa": 1,
      "fecha_creacion": "2025-01-01T00:00:00Z"
    }
  ]
}
```

---

## 2️⃣ ¿Cómo se Activa una Política?

Las políticas se ejecutan **automáticamente** cuando:

1. Una consulta cambia de estado (ej: PATCH `/api/consultas/{id}/`)
2. El nuevo estado coincide con `estado_consulta` de una política activa
3. El backend ejecuta las acciones configuradas

**Ejemplo de flujo**:

```
Consulta #42 → Estado cambia a "No Show" (ID=5)
       ↓
Backend detecta políticas activas con estado_consulta=5
       ↓
Ejecuta acción "MULTA": Crea registro en tabla Multa
       ↓
Ejecuta acción "BLOQUEO": Crea registro en BloqueoUsuario
       ↓
Ejecuta acción "NOTIFICACION": Envía email/push al paciente
```

---

## 3️⃣ Consultar Multas del Usuario

**Endpoint no documentado oficialmente pero accesible:**

```http
GET /api/multas/?paciente={codusuario}
Authorization: Token {token}
```

### Response Esperada

```json
{
  "count": 1,
  "results": [
    {
      "id": 10,
      "paciente": 15,
      "consulta": 42,
      "monto": "50.00",
      "motivo": "Multa por Primera Inasistencia",
      "fecha_creacion": "2025-10-15T10:00:00Z",
      "pagada": false,
      "fecha_pago": null,
      "empresa": 1
    }
  ]
}
```

---

## 4️⃣ Verificar Bloqueo del Usuario

El sistema verifica automáticamente si un usuario está bloqueado al hacer **login**.

### Response de Login con Usuario Bloqueado

```json
{
  "error": "Usuario bloqueado hasta 2025-10-22",
  "code": "USER_BLOCKED",
  "bloqueado": true,
  "motivo": "Bloqueo por Segunda Inasistencia",
  "fecha_bloqueo": "2025-10-15T10:00:00Z",
  "fecha_fin": "2025-10-22T10:00:00Z"
}
```

### ¿Cómo Manejar un Bloqueo?

1. **Detectar el bloqueo** en respuesta de login
2. **Mostrar mensaje** al usuario con motivo y fecha de fin
3. **Deshabilitar acciones** (agendar citas, etc.)
4. **Permitir ver historial** (solo lectura)

---

## 📱 Implementación en la App Móvil

### Flutter - Verificar Estado de Bloqueo

```dart
// auth_service.dart
class AuthResponse {
  final bool success;
  final String? token;
  final String? error;
  final bool bloqueado;
  final String? motivoBloqueo;
  final DateTime? fechaFinBloqueo;
  
  AuthResponse({
    required this.success,
    this.token,
    this.error,
    this.bloqueado = false,
    this.motivoBloqueo,
    this.fechaFinBloqueo,
  });
  
  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    if (json.containsKey('error') && json['bloqueado'] == true) {
      return AuthResponse(
        success: false,
        error: json['error'],
        bloqueado: true,
        motivoBloqueo: json['motivo'],
        fechaFinBloqueo: json['fecha_fin'] != null 
            ? DateTime.parse(json['fecha_fin'])
            : null,
      );
    }
    
    return AuthResponse(
      success: true,
      token: json['token'],
    );
  }
}

Future<AuthResponse> login(String email, String password, String subdomain) async {
  final response = await http.post(
    Uri.parse('$baseUrl/auth/login/'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'email': email,
      'password': password,
      'subdomain': subdomain,
    }),
  );
  
  final data = jsonDecode(response.body);
  
  if (response.statusCode == 403 || data['bloqueado'] == true) {
    return AuthResponse.fromJson(data);
  }
  
  if (response.statusCode == 200) {
    return AuthResponse.fromJson(data);
  }
  
  return AuthResponse(
    success: false,
    error: data['error'] ?? 'Error desconocido',
  );
}
```

### Mostrar Diálogo de Bloqueo

```dart
void _handleLoginResponse(AuthResponse response) {
  if (response.bloqueado) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(Icons.block, color: Colors.red),
            SizedBox(width: 8),
            Text('Usuario Bloqueado'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              response.motivoBloqueo ?? 'Usuario bloqueado temporalmente',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 16),
            if (response.fechaFinBloqueo != null)
              Text(
                'Bloqueo activo hasta: ${_formatFecha(response.fechaFinBloqueo!)}',
                style: TextStyle(color: Colors.grey[700]),
              )
            else
              Text(
                'Bloqueo indefinido. Contacte a la clínica.',
                style: TextStyle(color: Colors.red),
              ),
            SizedBox(height: 16),
            Text(
              'Por favor, comuníquese con la clínica para más información.',
              style: TextStyle(fontSize: 12),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              // Opcional: abrir pantalla de contacto
            },
            child: Text('Contactar Clínica'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Entendido'),
          ),
        ],
      ),
    );
  } else if (response.success) {
    // Login exitoso
    _saveToken(response.token!);
    _navigateToHome();
  } else {
    // Error de credenciales
    _showError(response.error ?? 'Error al iniciar sesión');
  }
}
```

---

### Consultar Multas Pendientes

```dart
// multa_service.dart
class MultaService {
  static const String baseUrl = 'https://notificct.dpdns.org/api';
  
  Future<List<Multa>> obtenerMultasPendientes(int pacienteId) async {
    final token = await TokenStorage.getToken();
    
    final response = await http.get(
      Uri.parse('$baseUrl/multas/?paciente=$pacienteId&pagada=false'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return (data['results'] as List)
          .map((json) => Multa.fromJson(json))
          .toList();
    } else {
      throw Exception('Error al cargar multas');
    }
  }
  
  Future<double> calcularDeudaTotal(int pacienteId) async {
    final multas = await obtenerMultasPendientes(pacienteId);
    return multas.fold(0.0, (sum, multa) => sum + double.parse(multa.monto));
  }
}

class Multa {
  final int id;
  final int paciente;
  final int? consulta;
  final String monto;
  final String motivo;
  final DateTime fechaCreacion;
  final bool pagada;
  final DateTime? fechaPago;
  
  Multa({
    required this.id,
    required this.paciente,
    this.consulta,
    required this.monto,
    required this.motivo,
    required this.fechaCreacion,
    required this.pagada,
    this.fechaPago,
  });
  
  factory Multa.fromJson(Map<String, dynamic> json) {
    return Multa(
      id: json['id'],
      paciente: json['paciente'],
      consulta: json['consulta'],
      monto: json['monto'],
      motivo: json['motivo'],
      fechaCreacion: DateTime.parse(json['fecha_creacion']),
      pagada: json['pagada'],
      fechaPago: json['fecha_pago'] != null 
          ? DateTime.parse(json['fecha_pago']) 
          : null,
    );
  }
}
```

### Pantalla de Multas

```dart
class MultasScreen extends StatefulWidget {
  final int pacienteId;
  
  MultasScreen({required this.pacienteId});
  
  @override
  _MultasScreenState createState() => _MultasScreenState();
}

class _MultasScreenState extends State<MultasScreen> {
  final _service = MultaService();
  List<Multa> _multas = [];
  bool _loading = true;
  double _deudaTotal = 0.0;
  
  @override
  void initState() {
    super.initState();
    _cargarMultas();
  }
  
  Future<void> _cargarMultas() async {
    setState(() => _loading = true);
    try {
      final multas = await _service.obtenerMultasPendientes(widget.pacienteId);
      final total = await _service.calcularDeudaTotal(widget.pacienteId);
      
      setState(() {
        _multas = multas;
        _deudaTotal = total;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error al cargar multas: $e')),
      );
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Multas Pendientes'),
        backgroundColor: Colors.red,
      ),
      body: _loading
          ? Center(child: CircularProgressIndicator())
          : Column(
              children: [
                // Header con total
                Container(
                  width: double.infinity,
                  padding: EdgeInsets.all(16),
                  color: Colors.red[50],
                  child: Column(
                    children: [
                      Text(
                        'Deuda Total',
                        style: TextStyle(fontSize: 16, color: Colors.grey[700]),
                      ),
                      SizedBox(height: 8),
                      Text(
                        'Bs. ${_deudaTotal.toStringAsFixed(2)}',
                        style: TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                          color: Colors.red,
                        ),
                      ),
                    ],
                  ),
                ),
                
                // Lista de multas
                Expanded(
                  child: _multas.isEmpty
                      ? Center(child: Text('No tienes multas pendientes'))
                      : ListView.builder(
                          itemCount: _multas.length,
                          itemBuilder: (context, index) {
                            final multa = _multas[index];
                            return Card(
                              margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                              child: ListTile(
                                leading: CircleAvatar(
                                  backgroundColor: Colors.red,
                                  child: Icon(Icons.warning, color: Colors.white),
                                ),
                                title: Text(multa.motivo),
                                subtitle: Text(
                                  'Fecha: ${_formatFecha(multa.fechaCreacion)}',
                                ),
                                trailing: Text(
                                  'Bs. ${multa.monto}',
                                  style: TextStyle(
                                    fontSize: 18,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.red,
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                ),
                
                // Botón de pago
                if (_deudaTotal > 0)
                  Padding(
                    padding: EdgeInsets.all(16),
                    child: ElevatedButton(
                      onPressed: _procesarPago,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        minimumSize: Size(double.infinity, 50),
                      ),
                      child: Text(
                        'Pagar Bs. ${_deudaTotal.toStringAsFixed(2)}',
                        style: TextStyle(fontSize: 18),
                      ),
                    ),
                  ),
              ],
            ),
    );
  }
  
  String _formatFecha(DateTime fecha) {
    return '${fecha.day}/${fecha.month}/${fecha.year}';
  }
  
  void _procesarPago() {
    // Implementar integración con pasarela de pago
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Pago de Multas'),
        content: Text('Funcionalidad de pago en desarrollo'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('OK'),
          ),
        ],
      ),
    );
  }
}
```

---

## 🎯 Flujo Completo del Sistema

```
1. Paciente agenda cita
   └─> Estado: "Agendada" (ID=1)
   
2. Paciente no asiste
   └─> Admin cambia estado a "No Show" (ID=5)
   
3. Backend detecta cambio de estado
   └─> Busca políticas activas con estado_consulta=5
   
4. Encuentra política "Multa por Primera Inasistencia"
   └─> Acción: MULTA, Monto: Bs. 50
   
5. Crea registro en tabla Multa
   └─> {paciente: 15, monto: "50.00", pagada: false}
   
6. Envía notificación al paciente
   └─> Email + Push (si está configurado)
   
7. Próximo login del paciente
   └─> App muestra badge: "1 multa pendiente"
   
8. Usuario revisa multas
   └─> GET /api/multas/?paciente=15&pagada=false
   └─> Muestra: Bs. 50 pendientes
   
9. Usuario paga multa (fuera del sistema actual)
   └─> Admin marca multa como pagada
   
10. Si hay segunda inasistencia
    └─> Se activa política "Bloqueo por 7 días"
    └─> Usuario no puede agendar nuevas citas
```

---

## ⚠️ Consideraciones de UX

### 1. Comunicación Clara
- **Antes de la cita**: Recordar política de no-show
- **Al agendar**: Mostrar advertencia sobre multas
- **Después de multa**: Explicar cómo pagar

### 2. Prevención
- **Permitir cancelación**: Hasta X horas antes
- **Confirmación de asistencia**: Botón "Confirmar" 24h antes
- **Recordatorios múltiples**: 24h, 2h, 30min antes

### 3. Transparencia
- **Mostrar políticas**: Pantalla de "Términos y Condiciones"
- **Historial de multas**: Permitir ver multas pagadas
- **Contador de inasistencias**: "Tienes 1 inasistencia en los últimos 6 meses"

---

## 🧪 Testing

### Simular No-Show

```bash
# 1. Crear consulta
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

# 2. Cambiar estado a No Show (requiere admin)
curl -X PATCH https://notificct.dpdns.org/api/consultas/42/ \
  -H "Authorization: Token ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "idestadoconsulta": 5
  }'

# 3. Verificar multa creada
curl -X GET "https://notificct.dpdns.org/api/multas/?paciente=15" \
  -H "Authorization: Token YOUR_TOKEN"
```

---

## 📱 Próximos Pasos

Continúa con: **MOBILE_07_EJEMPLOS_CODIGO.md** para ver implementaciones completas en Flutter y React Native.

---

**Última actualización**: 15 de Octubre, 2025
