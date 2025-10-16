# 📱 Guía de Desarrollo Móvil - Introducción

## 🎯 Propósito de esta Documentación

Esta serie de documentos está diseñada específicamente para el **equipo de desarrollo móvil** que consumirá la API REST del backend de la clínica dental. Aquí encontrarás toda la información necesaria para integrar tu aplicación móvil (iOS/Android) con nuestro backend Django.

---

## 📚 Estructura de la Documentación

La documentación está dividida en módulos especializados:

1. **MOBILE_01_INTRODUCCION.md** (este documento)
   - Visión general del sistema
   - Arquitectura multi-tenant
   - Conceptos fundamentales

2. **MOBILE_02_AUTENTICACION.md**
   - Sistema de autenticación
   - Login y registro
   - Gestión de tokens
   - Perfiles de usuario

3. **MOBILE_03_ENDPOINTS_CORE.md**
   - Endpoints principales (Pacientes, Consultas, Odontólogos)
   - Parámetros y respuestas
   - Ejemplos de uso

4. **MOBILE_04_NOTIFICACIONES_PUSH.md**
   - Sistema FCM completo
   - Registro de dispositivos
   - Gestión de notificaciones
   - Testing y debugging

5. **MOBILE_05_HISTORIAS_CLINICAS.md**
   - Historia clínica electrónica
   - CRUD completo
   - Episodios múltiples

6. **MOBILE_06_POLITICAS_NOSHOW.md**
   - Sistema de penalizaciones
   - Bloqueos de usuarios
   - Multas automáticas

7. **MOBILE_07_EJEMPLOS_CODIGO.md**
   - Código ejemplo para Flutter/React Native
   - Servicios HTTP
   - Manejo de errores
   - Buenas prácticas

8. **MOBILE_08_TESTING_DEBUG.md**
   - Cómo probar endpoints
   - Herramientas recomendadas
   - Solución de problemas comunes

---

## 🏗️ Arquitectura del Sistema

### Multi-Tenancy (Multi-Inquilino)

El sistema está diseñado para manejar **múltiples clínicas dentales** en una sola instancia:

```
┌─────────────────────────────────────────────────────┐
│                  DOMINIO BASE                        │
│            notificct.dpdns.org                       │
└─────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
   ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
   │ norte.  │    │  sur.   │    │ este.   │
   │         │    │         │    │         │
   └────┬────┘    └────┬────┘    └────┬────┘
        │              │              │
   Clínica A      Clínica B      Clínica C
```

**¿Qué significa esto para el desarrollo móvil?**

- Cada clínica tiene su propio **subdomain** (ej: `norte`, `sur`, `este`)
- Los datos están **completamente aislados** entre clínicas
- Debes **identificar la clínica** al hacer login/registro

---

## 🔑 Conceptos Fundamentales

### 1. Empresa (Tenant)

```json
{
  "id": 1,
  "nombre": "Clínica Dental Norte",
  "subdomain": "norte",
  "activo": true,
  "fecha_creacion": "2025-01-15T10:00:00Z"
}
```

- Representa una **clínica dental**
- Cada empresa es un "tenant" independiente
- Todas las consultas deben filtrarse por empresa

### 2. Usuario

El modelo base para todos los usuarios del sistema:

```json
{
  "codigo": 1,
  "nombre": "Juan",
  "apellido": "Pérez",
  "correoelectronico": "juan@example.com",
  "telefono": "+591 70123456",
  "sexo": "M",
  "idtipousuario": 2,
  "recibir_notificaciones": true,
  "notificaciones_email": true,
  "notificaciones_push": true
}
```

### 3. Roles de Usuario

| ID | Rol            | Descripción                          |
|----|----------------|--------------------------------------|
| 1  | Administrador  | Acceso total al sistema              |
| 2  | Paciente       | Usuario que agenda citas             |
| 3  | Odontólogo     | Profesional que atiende              |
| 4  | Recepcionista  | Gestiona agenda y citas              |

**Para la app móvil, normalmente trabajarás con rol `Paciente` (2)**

### 4. Paciente

Extiende `Usuario` con información médica:

```json
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
  "direccion": "Av. Principal #123"
}
```

### 5. Consulta (Cita Médica)

La entidad principal del sistema:

```json
{
  "id": 42,
  "fecha": "2025-10-20",
  "codpaciente": { /* objeto paciente */ },
  "cododontologo": { /* objeto odontólogo */ },
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
  }
}
```

### 6. Estados de Consulta

| ID | Estado        | Descripción                              |
|----|---------------|------------------------------------------|
| 1  | Agendada      | Cita creada, pendiente                   |
| 2  | Confirmada    | Paciente confirmó asistencia             |
| 3  | Atendida      | Consulta realizada                       |
| 4  | Cancelada     | Paciente canceló                         |
| 5  | No Show       | Paciente no asistió (⚠️ puede generar multa) |
| 6  | Reprogramada  | Cita movida a otra fecha                 |

---

## 🌐 URL Base de la API

### Producción
```
https://notificct.dpdns.org/api/
```

### Desarrollo Local
```
http://localhost:8000/api/
```

---

## 🔐 Autenticación

El sistema usa **Token Authentication** de Django Rest Framework:

### Headers Requeridos

```http
Authorization: Token abc123def456ghi789
Content-Type: application/json
X-Tenant-Subdomain: norte
```

**Importante:**
- `Authorization`: Token obtenido en login
- `X-Tenant-Subdomain`: Subdomain de la clínica (solo en desarrollo)

En producción, el tenant se detecta automáticamente del subdomain de la URL.

---

## 📦 Formato de Respuestas

### Respuesta Exitosa (200 OK)

```json
{
  "id": 1,
  "nombre": "Juan",
  "apellido": "Pérez",
  "correoelectronico": "juan@example.com"
}
```

### Lista Paginada

```json
{
  "count": 150,
  "next": "https://api.example.com/pacientes/?page=2",
  "previous": null,
  "results": [
    { /* objeto 1 */ },
    { /* objeto 2 */ },
    { /* ... */ }
  ]
}
```

### Error (400 Bad Request)

```json
{
  "detail": "Este horario ya está reservado.",
  "error_code": "HORARIO_OCUPADO"
}
```

### Error de Validación

```json
{
  "fecha": ["Este campo es requerido."],
  "codpaciente": ["Este campo no puede ser nulo."]
}
```

---

## ⚙️ Configuración Inicial

### 1. Obtener Credenciales de Acceso

Contacta al administrador del sistema para:
- URL base de la API
- Subdomain de tu clínica
- Credenciales de prueba

### 2. Configurar Variables de Entorno

```dart
// Flutter ejemplo
class ApiConfig {
  static const String baseUrl = 'https://notificct.dpdns.org/api/';
  static const String subdomain = 'norte'; // Tu clínica
}
```

```javascript
// React Native ejemplo
export const API_CONFIG = {
  baseUrl: 'https://notificct.dpdns.org/api/',
  subdomain: 'norte'
};
```

### 3. Instalar Dependencias HTTP

**Flutter:**
```yaml
dependencies:
  http: ^1.1.0
  shared_preferences: ^2.2.2
```

**React Native:**
```bash
npm install axios @react-native-async-storage/async-storage
```

---

## 🎨 Flujo Típico de Usuario Móvil

```
┌─────────────────┐
│  1. App Launch  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Token Saved?   │─No──▶│  Login Screen    │
└────────┬────────┘      └────────┬─────────┘
         │                        │
        Yes                       │
         │                        ▼
         │              ┌──────────────────┐
         │              │  POST /auth/login│
         │              └────────┬─────────┘
         │                       │
         │                       ▼
         │              ┌──────────────────┐
         │              │  Save Token      │
         │              └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
         ┌──────────────────────┐
         │  GET /auth/user/     │  (Obtener perfil)
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Register FCM Token  │
         │  POST /mobile-notif/ │
         │     register-device/ │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   Main Screen        │
         │   - Mis Citas        │
         │   - Agendar Nueva    │
         │   - Historial        │
         └──────────────────────┘
```

---

## 🚀 Primeros Pasos

1. **Lee el documento de autenticación**: `MOBILE_02_AUTENTICACION.md`
2. **Implementa el login**: Prueba con credenciales de test
3. **Explora los endpoints core**: `MOBILE_03_ENDPOINTS_CORE.md`
4. **Configura notificaciones push**: `MOBILE_04_NOTIFICACIONES_PUSH.md`
5. **Revisa los ejemplos de código**: `MOBILE_07_EJEMPLOS_CODIGO.md`

---

## 📞 Soporte

- **Documentación API**: Ver archivos `MOBILE_*.md`
- **Endpoint de salud**: `GET /api/health/`
- **Contacto técnico**: [Agregar email del equipo backend]

---

## 🔄 Versionado de la API

**Versión actual**: `v1` (incluida en todas las rutas)

Cambios que requieren atención:
- Nuevos campos obligatorios se notificarán con 30 días de anticipación
- Campos deprecated se marcarán pero seguirán funcionando por 90 días
- Breaking changes requieren migración a v2

---

## ⚠️ Consideraciones Importantes

### Multi-Tenancy
- **SIEMPRE** filtra por empresa/tenant
- Un token solo funciona para UNA clínica
- No compartas datos entre clínicas

### Seguridad
- **NUNCA** almacenes tokens en texto plano
- Usa `Keychain` (iOS) o `EncryptedSharedPreferences` (Android)
- Implementa refresh de tokens si la sesión expira

### Performance
- Implementa **caché local** para catálogos (horarios, tipos de consulta)
- Usa **paginación** en listas grandes
- Implementa **pull-to-refresh** para actualizar datos

### UX/UI
- Muestra **loaders** durante llamadas HTTP
- Implementa **retry** automático para errores de red
- Almacena datos offline cuando sea posible

---

## 📱 Plataformas Soportadas

- ✅ **Flutter** (iOS & Android)
- ✅ **React Native** (iOS & Android)
- ✅ **Native iOS** (Swift)
- ✅ **Native Android** (Kotlin/Java)

Todas las plataformas consumen la misma API REST.

---

## 🎓 Próximos Pasos

Continúa con: **MOBILE_02_AUTENTICACION.md** para implementar el sistema de login y gestión de tokens.

---

**Última actualización**: 15 de Octubre, 2025
**Versión**: 1.0.0
