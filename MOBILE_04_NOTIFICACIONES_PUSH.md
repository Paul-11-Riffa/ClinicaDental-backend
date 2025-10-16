# 📱 Guía de Desarrollo Móvil - Notificaciones Push FCM

## 🔔 Sistema de Notificaciones Push

El backend implementa un sistema completo de notificaciones push usando **Firebase Cloud Messaging (FCM)** con gestión automática de recordatorios de citas.

---

## 🎯 Funcionalidades

✅ Registro de dispositivos móviles  
✅ Envío de notificaciones push  
✅ Recordatorios automáticos (24h y 2h antes de cita)  
✅ Notificaciones de reprogramación  
✅ Gestión de preferencias de usuario  
✅ Historial de notificaciones  
✅ Soporte multi-dispositivo (1 dispositivo activo por usuario)  

---

## 📋 Endpoints de Notificaciones

### Base URL
```
/api/mobile-notif/
```

### Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/register-device/` | POST | Registrar token FCM del dispositivo |
| `/register-lite/` | POST | Registro rápido (testing) |
| `/health/` | GET | Verificar estado del sistema FCM |
| `/test-push/` | POST | Enviar notificación de prueba |
| `/dispatch/{id}/` | POST | Ejecutar notificación pendiente (interno) |
| `/dispatch-due/` | POST | Procesar notificaciones vencidas (cron) |

---

## 1️⃣ Registrar Dispositivo

**Endpoint más importante para la app móvil**

```http
POST /api/mobile-notif/register-device/
Authorization: Token {token}
Content-Type: application/json
```

### Request Body

```json
{
  "token_fcm": "fXn4kP7qR8sH2jK9...",
  "plataforma": "android",
  "modelo_dispositivo": "Samsung Galaxy S21",
  "version_app": "1.0.5"
}
```

### Campos

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `token_fcm` | string | ✅ | Token FCM del dispositivo |
| `plataforma` | string | ❌ | "android" o "ios" (default: "android") |
| `modelo_dispositivo` | string | ❌ | Modelo del dispositivo |
| `version_app` | string | ❌ | Versión de la app |

### Response (200 OK)

```json
{
  "ok": true,
  "created": false,
  "device_id": 42,
  "usuario_codigo": 15,
  "plataforma": "android",
  "modelo_dispositivo": "Samsung Galaxy S21",
  "version_app": "1.0.5"
}
```

**Campos de respuesta**:
- `created`: `true` si es un dispositivo nuevo, `false` si se actualizó existente
- `device_id`: ID del dispositivo registrado
- `usuario_codigo`: Código del usuario (para referencia)

### Comportamiento del Sistema

1. **Si el token ya existe en BD**: 
   - Reasigna el token al usuario actual
   - Actualiza plataforma, modelo y versión
   - Activa el dispositivo

2. **Si el token NO existe**:
   - Busca dispositivo existente del usuario
   - Si existe: actualiza con nuevo token
   - Si no existe: crea nuevo registro

3. **Desactiva otros dispositivos del mismo usuario** (solo 1 activo)

### Errores Comunes

```json
{
  "ok": false,
  "detail": "Usuario sin email/username"
}
```

```json
{
  "ok": false,
  "detail": "Usuario de negocio no encontrado"
}
```

---

## 2️⃣ Verificar Estado del Sistema FCM

```http
GET /api/mobile-notif/health/
```

**No requiere autenticación**

### Response (200 OK)

```json
{
  "status": "ok",
  "fcm_configured": true,
  "fcm_project_id": "dental-clinic-app",
  "service_account_loaded": true,
  "timestamp": "2025-10-15T14:30:00Z"
}
```

**Uso**: Verificar que el backend tiene FCM correctamente configurado.

---

## 3️⃣ Enviar Notificación de Prueba

```http
POST /api/mobile-notif/test-push/
Content-Type: application/json
```

**No requiere autenticación (solo para desarrollo)**

### Request Body

```json
{
  "tokens": ["fXn4kP7qR8sH2jK9...", "aB3cD4eF5gH6iJ7k..."],
  "title": "Prueba de Notificación",
  "body": "Este es un mensaje de prueba desde el backend",
  "data": {
    "tipo": "test",
    "custom_field": "valor"
  }
}
```

### Response (200 OK)

```json
{
  "success_count": 2,
  "failure_count": 0,
  "responses": [
    {
      "success": true,
      "message_id": "projects/dental-clinic/messages/0:1234567890"
    },
    {
      "success": true,
      "message_id": "projects/dental-clinic/messages/0:1234567891"
    }
  ]
}
```

---

## 🔔 Sistema de Recordatorios Automáticos

### ¿Cuándo se Crean Notificaciones?

El sistema crea automáticamente recordatorios al:

1. **Crear una consulta nueva** (POST `/api/consultas/`)
2. **Reprogramar una consulta** (PATCH `/api/consultas/{id}/reprogramar/`)

### Tipos de Recordatorios

| Tipo | Cuándo se envía | Título | Mensaje |
|------|-----------------|--------|---------|
| 24h | 24 horas antes de la cita | "Recordatorio de consulta" | "Tienes una consulta el DD/MM HH:MM. Recordatorio 24h." |
| 2h | 2 horas antes de la cita | "Recordatorio de consulta" | "Tienes una consulta el DD/MM HH:MM. Recordatorio 2h." |

### Estados de Notificaciones

| Estado | Descripción |
|--------|-------------|
| `PENDIENTE` | Notificación programada, aún no enviada |
| `ENVIADO` | Notificación enviada exitosamente |
| `ERROR` | Error al enviar notificación |
| `LEIDA` | Usuario abrió la notificación (requiere implementación en app) |

### Ejemplo de Notificación Creada

Cuando creas una cita para el **2025-10-20 a las 10:00**, el sistema crea:

```json
// Recordatorio 24h (se envía 2025-10-19 10:00)
{
  "id": 100,
  "titulo": "Recordatorio de consulta",
  "mensaje": "Tienes una consulta el 20/10 10:00. Recordatorio 24h.",
  "estado": "PENDIENTE",
  "fecha_creacion": "2025-10-15T14:00:00Z",
  "fecha_envio": "2025-10-19T10:00:00Z",
  "codusuario": 15,
  "idtiponotificacion": 1,
  "idcanalnotificacion": 1,
  "datos_adicionales": {
    "consulta_id": 42,
    "empresa_id": 1,
    "reminder": "24h"
  }
}

// Recordatorio 2h (se envía 2025-10-20 08:00)
{
  "id": 101,
  "titulo": "Recordatorio de consulta",
  "mensaje": "Tienes una consulta el 20/10 10:00. Recordatorio 2h.",
  "estado": "PENDIENTE",
  "fecha_creacion": "2025-10-15T14:00:00Z",
  "fecha_envio": "2025-10-20T08:00:00Z",
  "codusuario": 15,
  "idtiponotificacion": 1,
  "idcanalnotificacion": 1,
  "datos_adicionales": {
    "consulta_id": 42,
    "empresa_id": 1,
    "reminder": "2h"
  }
}
```

### ¿Cómo se Envían las Notificaciones?

El backend tiene un **endpoint de despacho** que debe ser llamado periódicamente (cron job):

```http
POST /api/mobile-notif/dispatch-due/
```

Este endpoint:
1. Busca todas las notificaciones con estado `PENDIENTE` y `fecha_envio <= now()`
2. Obtiene el token FCM del dispositivo del usuario
3. Envía la notificación vía FCM
4. Actualiza el estado a `ENVIADO` o `ERROR`

**Configuración recomendada**: Ejecutar cada 5-15 minutos.

---

## 📱 Implementación en la App Móvil

### Flutter - Configuración Inicial

#### 1. Instalar Dependencias

```yaml
dependencies:
  firebase_core: ^2.24.0
  firebase_messaging: ^14.7.0
  flutter_local_notifications: ^16.2.0
```

#### 2. Inicializar Firebase

```dart
// main.dart
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

// Handler de notificaciones en background
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  print('Background message: ${message.messageId}');
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Inicializar Firebase
  await Firebase.initializeApp();
  
  // Configurar handler de background
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
  
  runApp(MyApp());
}
```

#### 3. Solicitar Permisos y Obtener Token

```dart
// notification_service.dart
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotificationService {
  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications = 
      FlutterLocalNotificationsPlugin();
  
  Future<void> initialize() async {
    // 1. Solicitar permisos
    NotificationSettings settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
    
    if (settings.authorizationStatus != AuthorizationStatus.authorized) {
      print('Usuario denegó permisos de notificaciones');
      return;
    }
    
    // 2. Obtener token FCM
    String? token = await _messaging.getToken();
    if (token != null) {
      print('FCM Token: $token');
      // Registrar en backend
      await _registerDeviceInBackend(token);
    }
    
    // 3. Configurar listeners
    _setupListeners();
    
    // 4. Configurar notificaciones locales
    await _setupLocalNotifications();
  }
  
  Future<void> _registerDeviceInBackend(String token) async {
    try {
      final authToken = await TokenStorage.getToken();
      
      final response = await http.post(
        Uri.parse('https://notificct.dpdns.org/api/mobile-notif/register-device/'),
        headers: {
          'Authorization': 'Token $authToken',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'token_fcm': token,
          'plataforma': Platform.isIOS ? 'ios' : 'android',
          'modelo_dispositivo': await _getDeviceModel(),
          'version_app': '1.0.5',
        }),
      );
      
      if (response.statusCode == 200) {
        print('Dispositivo registrado exitosamente');
      } else {
        print('Error al registrar dispositivo: ${response.body}');
      }
    } catch (e) {
      print('Error al registrar dispositivo: $e');
    }
  }
  
  void _setupListeners() {
    // Foreground messages
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      print('Mensaje recibido en foreground');
      _showLocalNotification(message);
    });
    
    // Mensaje clickeado (app en background)
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      print('Notificación clickeada');
      _handleNotificationClick(message);
    });
    
    // Verificar si la app se abrió desde notificación
    _messaging.getInitialMessage().then((message) {
      if (message != null) {
        _handleNotificationClick(message);
      }
    });
  }
  
  Future<void> _setupLocalNotifications() async {
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings();
    
    const settings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );
    
    await _localNotifications.initialize(
      settings,
      onDidReceiveNotificationResponse: (details) {
        // Manejar click en notificación local
      },
    );
  }
  
  Future<void> _showLocalNotification(RemoteMessage message) async {
    const androidDetails = AndroidNotificationDetails(
      'citas_channel',
      'Notificaciones de Citas',
      channelDescription: 'Recordatorios de consultas dentales',
      importance: Importance.high,
      priority: Priority.high,
    );
    
    const iosDetails = DarwinNotificationDetails();
    
    const details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );
    
    await _localNotifications.show(
      message.hashCode,
      message.notification?.title ?? 'Notificación',
      message.notification?.body ?? '',
      details,
      payload: jsonEncode(message.data),
    );
  }
  
  void _handleNotificationClick(RemoteMessage message) {
    final data = message.data;
    
    if (data.containsKey('consulta_id')) {
      // Navegar al detalle de la cita
      final consultaId = data['consulta_id'];
      // NavigationService.navigateToConsulta(consultaId);
    }
  }
  
  Future<String> _getDeviceModel() async {
    // Implementar con device_info_plus
    return 'Unknown Device';
  }
}
```

#### 4. Llamar al Servicio al Login

```dart
// Después del login exitoso
await NotificationService().initialize();
```

---

### React Native - Configuración

#### 1. Instalar Dependencias

```bash
npm install @react-native-firebase/app @react-native-firebase/messaging
npx pod-install # iOS only
```

#### 2. Configurar Servicio

```javascript
// notificationService.js
import messaging from '@react-native-firebase/messaging';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from './api';

export const NotificationService = {
  async initialize() {
    // Solicitar permisos
    const authStatus = await messaging().requestPermission();
    const enabled =
      authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
      authStatus === messaging.AuthorizationStatus.PROVISIONAL;

    if (!enabled) {
      console.log('Permisos de notificaciones denegados');
      return;
    }

    // Obtener token
    const token = await messaging().getToken();
    console.log('FCM Token:', token);

    // Registrar en backend
    await this.registerDevice(token);

    // Configurar listeners
    this.setupListeners();
  },

  async registerDevice(token) {
    try {
      const response = await api.post('/mobile-notif/register-device/', {
        token_fcm: token,
        plataforma: Platform.OS,
        modelo_dispositivo: await this.getDeviceModel(),
        version_app: '1.0.5',
      });

      console.log('Dispositivo registrado:', response.data);
    } catch (error) {
      console.error('Error al registrar dispositivo:', error);
    }
  },

  setupListeners() {
    // Foreground
    messaging().onMessage(async (remoteMessage) => {
      console.log('Mensaje en foreground:', remoteMessage);
      // Mostrar notificación local
    });

    // Background/Quit
    messaging().setBackgroundMessageHandler(async (remoteMessage) => {
      console.log('Mensaje en background:', remoteMessage);
    });

    // Click en notificación
    messaging().onNotificationOpenedApp((remoteMessage) => {
      console.log('Notificación clickeada:', remoteMessage);
      this.handleNotificationClick(remoteMessage);
    });

    // App abierta desde notificación (quit state)
    messaging()
      .getInitialNotification()
      .then((remoteMessage) => {
        if (remoteMessage) {
          this.handleNotificationClick(remoteMessage);
        }
      });
  },

  handleNotificationClick(message) {
    const { consulta_id } = message.data;
    if (consulta_id) {
      // Navegar al detalle de la cita
    }
  },

  async getDeviceModel() {
    // Usar react-native-device-info
    return 'Unknown Device';
  },
};
```

---

## 🔕 Gestión de Preferencias de Notificaciones

### Actualizar Preferencias

```http
POST /api/auth/user/notifications/
Authorization: Token {token}
Content-Type: application/json
```

```json
{
  "notificaciones_push": true,
  "notificaciones_email": false,
  "recibir_notificaciones": true
}
```

**Importante**: Si `notificaciones_push` es `false`, el backend NO creará recordatorios automáticos.

---

## 🧪 Testing y Debugging

### 1. Verificar Token FCM

```bash
# Android - Logcat
adb logcat | grep FCM

# iOS - Console
# Buscar "FCM Token" en Xcode console
```

### 2. Probar Envío Manual

```bash
curl -X POST https://notificct.dpdns.org/api/mobile-notif/test-push/ \
  -H "Content-Type: application/json" \
  -d '{
    "tokens": ["TU_TOKEN_FCM_AQUI"],
    "title": "Test",
    "body": "Mensaje de prueba"
  }'
```

### 3. Verificar Registro del Dispositivo

```bash
curl -X GET https://notificct.dpdns.org/api/auth/user/ \
  -H "Authorization: Token YOUR_TOKEN"
```

Verifica que `notificaciones_push: true`.

---

## ⚠️ Problemas Comunes

### Token no se registra

**Síntoma**: `registerDevice()` falla con 400/401

**Soluciones**:
- Verificar que el token de autenticación sea válido
- Asegurar que el usuario tenga perfil de paciente
- Revisar logs del backend

### Notificaciones no llegan

**Posibles causas**:
1. **Permisos denegados**: Revisar configuración del dispositivo
2. **Token inválido**: Refrescar token FCM
3. **Backend no configurado**: Verificar `/mobile-notif/health/`
4. **App en doze mode** (Android): Deshabilitar optimización de batería
5. **Cron job no ejecutándose**: El endpoint `/dispatch-due/` debe ejecutarse periódicamente

### Notificaciones se envían tarde

**Causa**: Cron job ejecutándose con poca frecuencia

**Solución**: Configurar cron para ejecutar cada 5 minutos.

---

## 📊 Monitoreo y Logs

### Ver Notificaciones Pendientes (Admin)

```http
GET /api/notificaciones/?estado=PENDIENTE
Authorization: Token {admin_token}
```

### Ver Historial de Notificaciones del Usuario

```http
GET /api/notificaciones/?codusuario=15
Authorization: Token {token}
```

---

## 🚀 Configuración de Producción

### Cron Job para Despachar Notificaciones

```bash
# Agregar a crontab (ejecutar cada 5 minutos)
*/5 * * * * curl -X POST https://notificct.dpdns.org/api/mobile-notif/dispatch-due/
```

O usando systemd timer, GitHub Actions, etc.

---

## 📱 Próximos Pasos

Continúa con: **MOBILE_05_HISTORIAS_CLINICAS.md** para implementar el módulo de historias clínicas electrónicas.

---

**Última actualización**: 15 de Octubre, 2025
