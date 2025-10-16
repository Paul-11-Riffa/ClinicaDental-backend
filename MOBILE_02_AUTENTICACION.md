# 📱 Guía de Desarrollo Móvil - Autenticación

## 🔐 Sistema de Autenticación

El backend utiliza **Token Authentication** de Django Rest Framework con integración de **Supabase Auth**.

---

## 🎯 Endpoints de Autenticación

### Base URL
```
POST /api/auth/login/
POST /api/auth/register/
POST /api/auth/logout/
GET  /api/auth/user/
GET  /api/auth/csrf/
```

---

## 1️⃣ Registro de Usuario

### Endpoint
```http
POST /api/auth/register/
Content-Type: application/json
```

### Request Body

```json
{
  "email": "juan.perez@example.com",
  "password": "Password123!",
  "nombre": "Juan",
  "apellido": "Pérez",
  "telefono": "+591 70123456",
  "sexo": "M",
  "idtipousuario": 2,
  "carnetidentidad": "1234567",
  "fechanacimiento": "1990-05-15",
  "direccion": "Av. Principal #123",
  "subdomain": "norte"
}
```

### Campos Requeridos

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `email` | string | Email único del usuario | "juan@example.com" |
| `password` | string | Contraseña (min 8 caracteres) | "Password123!" |
| `nombre` | string | Nombre del paciente | "Juan" |
| `apellido` | string | Apellido del paciente | "Pérez" |
| `subdomain` | string | Subdomain de la clínica | "norte" |
| `idtipousuario` | int | Tipo de usuario (2=Paciente) | 2 |

### Campos Opcionales

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `telefono` | string | Teléfono de contacto |
| `sexo` | string | "M" o "F" |
| `carnetidentidad` | string | CI/DNI |
| `fechanacimiento` | date | Formato: "YYYY-MM-DD" |
| `direccion` | string | Dirección completa |

### Response (201 Created)

```json
{
  "ok": true,
  "message": "Usuario registrado exitosamente",
  "user": {
    "id": "uuid-here",
    "email": "juan.perez@example.com"
  },
  "token": "abc123def456ghi789jkl012mno345",
  "usuario": {
    "codigo": 15,
    "nombre": "Juan",
    "apellido": "Pérez",
    "correoelectronico": "juan.perez@example.com",
    "telefono": "+591 70123456",
    "sexo": "M",
    "idtipousuario": {
      "id": 2,
      "rol": "Paciente"
    },
    "recibir_notificaciones": true,
    "notificaciones_email": true,
    "notificaciones_push": false
  },
  "paciente": {
    "codusuario": 15,
    "carnetidentidad": "1234567",
    "fechanacimiento": "1990-05-15",
    "direccion": "Av. Principal #123"
  }
}
```

### Errores Comunes

**400 Bad Request - Email duplicado**
```json
{
  "error": "El email ya está registrado",
  "code": "EMAIL_DUPLICADO"
}
```

**400 Bad Request - Subdomain inválido**
```json
{
  "error": "Subdomain no encontrado o inactivo",
  "code": "SUBDOMAIN_INVALIDO"
}
```

**400 Bad Request - Contraseña débil**
```json
{
  "password": [
    "La contraseña debe tener al menos 8 caracteres",
    "La contraseña debe contener al menos una mayúscula"
  ]
}
```

---

## 2️⃣ Login (Inicio de Sesión)

### Endpoint
```http
POST /api/auth/login/
Content-Type: application/json
```

### Request Body

```json
{
  "email": "juan.perez@example.com",
  "password": "Password123!",
  "subdomain": "norte"
}
```

### Response (200 OK)

```json
{
  "ok": true,
  "token": "abc123def456ghi789jkl012mno345",
  "user": {
    "id": "uuid-here",
    "email": "juan.perez@example.com"
  },
  "usuario": {
    "codigo": 15,
    "nombre": "Juan",
    "apellido": "Pérez",
    "correoelectronico": "juan.perez@example.com",
    "telefono": "+591 70123456",
    "sexo": "M",
    "idtipousuario": {
      "id": 2,
      "rol": "Paciente"
    },
    "recibir_notificaciones": true,
    "notificaciones_email": true,
    "notificaciones_push": true
  },
  "rol_info": {
    "es_paciente": true,
    "es_odontologo": false,
    "es_admin": false,
    "es_recepcionista": false
  }
}
```

### Errores Comunes

**401 Unauthorized - Credenciales inválidas**
```json
{
  "error": "Email o contraseña incorrectos",
  "code": "INVALID_CREDENTIALS"
}
```

**403 Forbidden - Usuario bloqueado**
```json
{
  "error": "Usuario bloqueado hasta 2025-10-20",
  "code": "USER_BLOCKED",
  "bloqueado": true,
  "motivo": "Incumplimiento de política de No-Show",
  "fecha_bloqueo": "2025-10-15T10:00:00Z",
  "fecha_fin": "2025-10-20T10:00:00Z"
}
```

**400 Bad Request - Subdomain no proporcionado**
```json
{
  "error": "Subdomain es requerido",
  "code": "SUBDOMAIN_REQUIRED"
}
```

---

## 3️⃣ Obtener Perfil de Usuario

### Endpoint
```http
GET /api/auth/user/
Authorization: Token abc123def456ghi789
```

### Response (200 OK)

```json
{
  "auth_user": {
    "id": 123,
    "username": "juan.perez@example.com",
    "email": "juan.perez@example.com",
    "first_name": "Juan",
    "last_name": "Pérez"
  },
  "usuario": {
    "codigo": 15,
    "nombre": "Juan",
    "apellido": "Pérez",
    "correoelectronico": "juan.perez@example.com",
    "telefono": "+591 70123456",
    "sexo": "M",
    "idtipousuario": {
      "id": 2,
      "rol": "Paciente"
    },
    "recibir_notificaciones": true,
    "notificaciones_email": true,
    "notificaciones_push": true,
    "empresa": {
      "id": 1,
      "nombre": "Clínica Dental Norte",
      "subdomain": "norte"
    }
  },
  "rol_info": {
    "es_paciente": true,
    "es_odontologo": false,
    "es_admin": false,
    "es_recepcionista": false
  },
  "paciente": {
    "codusuario": 15,
    "carnetidentidad": "1234567",
    "fechanacimiento": "1990-05-15",
    "direccion": "Av. Principal #123"
  }
}
```

### Uso
- **Al iniciar la app**: Verifica que el token guardado siga válido
- **Después del login**: Obtén información completa del usuario
- **Para actualizar perfil**: Muestra datos actuales antes de editar

---

## 4️⃣ Actualizar Perfil

### Endpoint
```http
PATCH /api/auth/user/
Authorization: Token abc123def456ghi789
Content-Type: application/json
```

### Request Body (Todos los campos son opcionales)

```json
{
  "nombre": "Juan Carlos",
  "apellido": "Pérez López",
  "telefono": "+591 70999888",
  "direccion": "Nueva Av. #456"
}
```

### Response (200 OK)

Retorna el perfil actualizado (mismo formato que GET).

---

## 5️⃣ Actualizar Preferencias de Notificaciones

### Endpoint
```http
POST /api/auth/user/notifications/
Authorization: Token abc123def456ghi789
Content-Type: application/json
```

### Request Body

```json
{
  "notificaciones_email": true,
  "notificaciones_push": true,
  "recibir_notificaciones": true
}
```

### Response (200 OK)

```json
{
  "ok": true,
  "message": "Preferencias actualizadas",
  "preferencias": {
    "recibir_notificaciones": true,
    "notificaciones_email": true,
    "notificaciones_push": true
  }
}
```

---

## 6️⃣ Logout (Cerrar Sesión)

### Endpoint
```http
POST /api/auth/logout/
Authorization: Token abc123def456ghi789
```

### Response (200 OK)

```json
{
  "ok": true,
  "message": "Sesión cerrada exitosamente"
}
```

**Importante**: Después del logout:
1. Elimina el token del almacenamiento local
2. Elimina el token FCM del dispositivo
3. Redirige al usuario a la pantalla de login

---

## 7️⃣ Recuperación de Contraseña

### Paso 1: Solicitar Reset

```http
POST /api/auth/password-reset/
Content-Type: application/json
```

```json
{
  "email": "juan.perez@example.com"
}
```

**Response (200 OK)**
```json
{
  "ok": true,
  "message": "Se ha enviado un email con instrucciones"
}
```

### Paso 2: Confirmar Nueva Contraseña

```http
POST /api/auth/password-reset-confirm/
Content-Type: application/json
```

```json
{
  "uid": "base64-encoded-user-id",
  "token": "reset-token-from-email",
  "new_password": "NewPassword123!"
}
```

**Response (200 OK)**
```json
{
  "ok": true,
  "message": "Contraseña actualizada exitosamente"
}
```

---

## 🔑 Gestión de Tokens

### Almacenamiento Seguro

**Flutter (iOS/Android)**
```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class TokenStorage {
  static const _storage = FlutterSecureStorage();
  static const _tokenKey = 'auth_token';
  
  static Future<void> saveToken(String token) async {
    await _storage.write(key: _tokenKey, value: token);
  }
  
  static Future<String?> getToken() async {
    return await _storage.read(key: _tokenKey);
  }
  
  static Future<void> deleteToken() async {
    await _storage.delete(key: _tokenKey);
  }
}
```

**React Native**
```javascript
import * as SecureStore from 'expo-secure-store';

export const TokenStorage = {
  async saveToken(token) {
    await SecureStore.setItemAsync('auth_token', token);
  },
  
  async getToken() {
    return await SecureStore.getItemAsync('auth_token');
  },
  
  async deleteToken() {
    await SecureStore.deleteItemAsync('auth_token');
  }
};
```

### Uso del Token en Requests

**Flutter**
```dart
import 'package:http/http.dart' as http;

Future<http.Response> fetchWithAuth(String url) async {
  final token = await TokenStorage.getToken();
  
  return http.get(
    Uri.parse(url),
    headers: {
      'Authorization': 'Token $token',
      'Content-Type': 'application/json',
    },
  );
}
```

**React Native (Axios)**
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://notificct.dpdns.org/api/',
});

api.interceptors.request.use(async (config) => {
  const token = await TokenStorage.getToken();
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

export default api;
```

---

## 🔄 Flujo Completo de Autenticación

```
┌─────────────┐
│  App Start  │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Check Token      │
│ Exists in        │
│ Secure Storage   │
└──────┬───────────┘
       │
       ├─────Yes────▶ ┌──────────────────┐
       │              │ GET /auth/user/  │
       │              └────────┬─────────┘
       │                       │
       │                  ┌────▼─────┐
       │                  │ Success? │
       │                  └────┬─────┘
       │                       │
       │              ┌───Yes──┴──No───┐
       │              ▼                 ▼
       │         ┌─────────┐      ┌─────────┐
       │         │  Home   │      │ Delete  │
       │         │ Screen  │      │ Token   │
       │         └─────────┘      └────┬────┘
       │                               │
       └─────No─────────────────────────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │  Login Screen    │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │ User Enters      │
                              │ Credentials      │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │ POST /auth/login/│
                              └────────┬─────────┘
                                       │
                                  ┌────▼─────┐
                                  │ Success? │
                                  └────┬─────┘
                                       │
                              ┌───Yes──┴──No───┐
                              ▼                 ▼
                         ┌─────────┐      ┌─────────┐
                         │  Save   │      │  Show   │
                         │  Token  │      │  Error  │
                         └────┬────┘      └─────────┘
                              │
                              ▼
                         ┌─────────┐
                         │Register │
                         │FCM Token│
                         └────┬────┘
                              │
                              ▼
                         ┌─────────┐
                         │  Home   │
                         │ Screen  │
                         └─────────┘
```

---

## ⚠️ Manejo de Errores

### Token Inválido (401)

```json
{
  "detail": "Invalid token."
}
```

**Acción**: Eliminar token local y redirigir a login.

### Token Expirado (401)

```json
{
  "detail": "Token has expired."
}
```

**Acción**: Solicitar nuevo login.

### Usuario No Encontrado (404)

```json
{
  "detail": "Usuario de negocio no encontrado"
}
```

**Acción**: El usuario existe en auth pero no en la BD de negocio. Contactar soporte.

---

## 🛡️ Validaciones del Backend

### Email
- Debe ser único en el sistema
- Formato válido de email
- No puede contener espacios

### Contraseña
- Mínimo 8 caracteres
- Al menos una mayúscula
- Al menos un número
- No puede ser muy común (ej: "password123")

### Subdomain
- Debe existir en la tabla `Empresa`
- La empresa debe estar activa (`activo = true`)

### Carnet de Identidad
- Debe ser único por empresa
- Solo letras y números

---

## 🔐 Seguridad - Best Practices

### ✅ Hacer
- Almacenar token en almacenamiento seguro (Keychain/EncryptedPreferences)
- Implementar timeout de sesión (logout automático después de X horas)
- Validar certificado SSL en producción
- Limpiar token al hacer logout
- Manejar errores 401 globalmente

### ❌ No Hacer
- Almacenar token en SharedPreferences/AsyncStorage sin encriptar
- Almacenar contraseña en ningún lado
- Hardcodear tokens en el código
- Ignorar errores de autenticación
- Compartir tokens entre dispositivos

---

## 🧪 Testing

### Credenciales de Prueba

```
Email: paciente.test@norte.com
Password: Test1234!
Subdomain: norte
```

### Curl Examples

**Login**
```bash
curl -X POST https://notificct.dpdns.org/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "paciente.test@norte.com",
    "password": "Test1234!",
    "subdomain": "norte"
  }'
```

**Get Profile**
```bash
curl -X GET https://notificct.dpdns.org/api/auth/user/ \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

---

## 📱 Próximos Pasos

Continúa con: **MOBILE_03_ENDPOINTS_CORE.md** para aprender sobre los endpoints principales de la API.

---

**Última actualización**: 15 de Octubre, 2025
