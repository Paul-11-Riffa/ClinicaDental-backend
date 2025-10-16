# 📱 Documentación Completa para Desarrollo Móvil

## 🎯 Guía de Implementación del Backend API REST

Esta es la documentación oficial para el equipo de desarrollo móvil del sistema de gestión de clínicas dentales.

---

## 📚 Índice de Documentos

### 1. **MOBILE_01_INTRODUCCION.md** 
🏗️ **Fundamentos y Arquitectura**
- Visión general del sistema multi-tenant
- Conceptos fundamentales (Empresa, Usuario, Roles)
- Formato de respuestas y errores
- Configuración inicial
- Flujo típico de usuario

**Cuándo leer**: Primero - Antes de comenzar cualquier implementación

---

### 2. **MOBILE_02_AUTENTICACION.md**
🔐 **Sistema de Autenticación y Tokens**
- Registro de usuarios
- Login y logout
- Gestión de tokens
- Obtener y actualizar perfil
- Preferencias de notificaciones
- Recuperación de contraseña
- Almacenamiento seguro de tokens

**Implementaciones incluidas**:
- ✅ Flutter (SecureStorage)
- ✅ React Native (SecureStore)

**Cuándo leer**: Segundo - Después de entender la arquitectura

---

### 3. **MOBILE_03_ENDPOINTS_CORE.md**
📋 **Endpoints Principales de la API**
- Pacientes (listar, buscar)
- Consultas/Citas (CRUD completo)
- Odontólogos (catálogo)
- Horarios (disponibilidad)
- Tipos de consulta
- Estados de consulta
- Paginación y filtros
- Búsqueda y ordenamiento

**Flujos completos**:
- ✅ Agendar nueva cita
- ✅ Reprogramar cita
- ✅ Cancelar cita

**Cuándo leer**: Tercero - Para implementar funcionalidad core

---

### 4. **MOBILE_04_NOTIFICACIONES_PUSH.md**
🔔 **Sistema FCM Completo**
- Registro de dispositivos móviles
- Configuración de Firebase (Flutter/RN)
- Recordatorios automáticos (24h y 2h)
- Manejo de notificaciones en foreground/background
- Testing y debugging
- Cron jobs para despacho

**Implementaciones completas**:
- ✅ Flutter (firebase_messaging)
- ✅ React Native (@react-native-firebase)

**Cuándo leer**: Cuarto - Después de tener login y citas funcionando

---

### 5. **MOBILE_05_HISTORIAS_CLINICAS.md**
📋 **Historia Clínica Electrónica (HCE)**
- Modelo de datos (episodios múltiples)
- CRUD completo
- Permisos y seguridad
- Datos sensibles y privacidad
- UI/UX recomendada

**Componentes incluidos**:
- ✅ Servicio completo (Flutter)
- ✅ Pantalla de historial
- ✅ Formularios de creación

**Cuándo leer**: Quinto - Feature adicional importante

---

### 6. **MOBILE_06_POLITICAS_NOSHOW.md**
⚠️ **Sistema de Penalizaciones**
- Políticas de No-Show
- Multas automáticas
- Bloqueos de usuarios
- Manejo de deudas
- UX de comunicación de penalizaciones

**Implementaciones**:
- ✅ Verificación de bloqueo en login
- ✅ Pantalla de multas pendientes
- ✅ Cálculo de deuda total

**Cuándo leer**: Sexto - Sistema de penalizaciones

---

### 7. **MOBILE_07_EJEMPLOS_CODIGO.md** *(Próximamente)*
💻 **Código de Producción Completo**
- Arquitectura limpia (Flutter)
- BLoC/Provider patterns
- Servicios HTTP completos
- Manejo global de errores
- Interceptores de autenticación
- Caché local
- Modo offline

**Cuándo leer**: Cuando necesites patrones avanzados

---

### 8. **MOBILE_08_TESTING_DEBUG.md** *(Próximamente)*
🧪 **Testing y Solución de Problemas**
- Pruebas con Postman/Insomnia
- Credenciales de testing
- Problemas comunes y soluciones
- Logs y debugging
- Herramientas recomendadas

**Cuándo leer**: Cuando encuentres problemas o errores

---

## 🚀 Guía de Inicio Rápido

### Para Nuevos Desarrolladores

```
┌─────────────────────────────────────────────────────┐
│  Día 1: Fundamentos                                 │
│  ✅ Leer MOBILE_01_INTRODUCCION.md                 │
│  ✅ Leer MOBILE_02_AUTENTICACION.md                │
│  ✅ Configurar proyecto base                       │
│  ✅ Implementar login/registro                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  Día 2-3: Funcionalidad Core                        │
│  ✅ Leer MOBILE_03_ENDPOINTS_CORE.md               │
│  ✅ Implementar listado de consultas               │
│  ✅ Implementar agendar cita                       │
│  ✅ Implementar cancelar/reprogramar               │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  Día 4: Notificaciones Push                         │
│  ✅ Leer MOBILE_04_NOTIFICACIONES_PUSH.md          │
│  ✅ Configurar Firebase                            │
│  ✅ Implementar registro de dispositivo            │
│  ✅ Probar notificaciones                          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  Día 5: Features Adicionales                        │
│  ✅ Leer MOBILE_05_HISTORIAS_CLINICAS.md           │
│  ✅ Leer MOBILE_06_POLITICAS_NOSHOW.md             │
│  ✅ Implementar según prioridad del negocio        │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Endpoints Esenciales - Referencia Rápida

| Categoría | Endpoint | Método | Autenticación |
|-----------|----------|--------|---------------|
| **Auth** | `/api/auth/register/` | POST | ❌ No |
| | `/api/auth/login/` | POST | ❌ No |
| | `/api/auth/user/` | GET | ✅ Token |
| | `/api/auth/logout/` | POST | ✅ Token |
| **Consultas** | `/api/consultas/` | GET | ✅ Token |
| | `/api/consultas/` | POST | ✅ Token |
| | `/api/consultas/{id}/` | GET | ✅ Token |
| | `/api/consultas/{id}/reprogramar/` | PATCH | ✅ Token |
| | `/api/consultas/{id}/cancelar/` | POST | ✅ Token |
| **Horarios** | `/api/horarios/disponibles/` | GET | ✅ Token |
| **Notif** | `/api/mobile-notif/register-device/` | POST | ✅ Token |
| | `/api/mobile-notif/health/` | GET | ❌ No |
| **HCE** | `/api/historias-clinicas/` | GET/POST | ✅ Token |

---

## 🔧 Tecnologías y Stack

### Backend
- **Framework**: Django 5.2.6 + Django REST Framework
- **Base de Datos**: PostgreSQL (Supabase)
- **Autenticación**: Token Authentication + Supabase Auth
- **Notificaciones**: Firebase Cloud Messaging (FCM)
- **Deployment**: AWS EC2 con Nginx + Gunicorn

### Frontend Móvil Soportado
- ✅ **Flutter** (Dart)
- ✅ **React Native** (JavaScript/TypeScript)
- ✅ **Native iOS** (Swift)
- ✅ **Native Android** (Kotlin/Java)

---

## 🌐 URLs de Ambiente

### Producción
```
Base URL: https://notificct.dpdns.org/api/
Ejemplo con tenant: https://norte.notificct.dpdns.org/api/
```

### Desarrollo Local
```
Base URL: http://localhost:8000/api/
Header requerido: X-Tenant-Subdomain: norte
```

---

## 🔑 Conceptos Clave

### Multi-Tenancy
- Cada **clínica** es una **empresa** (tenant) independiente
- Datos completamente aislados entre empresas
- Identificación por **subdomain** (ej: `norte`, `sur`, `este`)
- En desarrollo: usar header `X-Tenant-Subdomain`
- En producción: subdomain detectado automáticamente

### Autenticación
- Sistema de **tokens** persistentes
- Token válido para **una sola empresa**
- Headers requeridos:
  ```
  Authorization: Token {tu_token_aqui}
  Content-Type: application/json
  ```

### Roles de Usuario
- **Paciente (2)**: Usuario normal de la app móvil
- **Odontólogo (3)**: Profesional que atiende
- **Admin (1)**: Acceso completo al sistema
- **Recepcionista (4)**: Gestiona agenda

---

## 📦 Modelos de Datos Principales

```typescript
// Usuario base
interface Usuario {
  codigo: number;
  nombre: string;
  apellido: string;
  correoelectronico: string;
  telefono: string;
  idtipousuario: TipoUsuario;
  empresa: Empresa;
}

// Paciente (extiende Usuario)
interface Paciente {
  codusuario: Usuario;
  carnetidentidad: string;
  fechanacimiento: string;
  direccion: string;
}

// Consulta (cita médica)
interface Consulta {
  id: number;
  fecha: string;
  codpaciente: Paciente;
  cododontologo: Odontologo;
  idhorario: Horario;
  idtipoconsulta: TipoConsulta;
  idestadoconsulta: EstadoConsulta;
}
```

---

## ⚡ Flujo de Trabajo Típico

```
1. Usuario abre app
   └─> ¿Token guardado?
       ├─ Sí → GET /auth/user/ (verificar validez)
       │       └─ ✅ Válido → Home
       │       └─ ❌ Inválido → Login
       └─ No → Login

2. Login exitoso
   └─> Guardar token en SecureStorage
   └─> POST /mobile-notif/register-device/ (FCM)
   └─> Navegar a Home

3. Agendar cita
   └─> GET /odontologos/ (seleccionar doctor)
   └─> GET /horarios/disponibles/?fecha=X&odontologo_id=Y
   └─> POST /consultas/ (crear cita)
   └─> Backend crea recordatorios automáticos

4. Recibir notificación push
   └─> 24h antes de cita: "Recordatorio de consulta..."
   └─> 2h antes de cita: "Recordatorio de consulta..."

5. Cancelar/Reprogramar
   └─> POST /consultas/{id}/cancelar/
   └─> O PATCH /consultas/{id}/reprogramar/
```

---

## 🛡️ Seguridad y Best Practices

### ✅ Hacer
- Almacenar tokens en **almacenamiento seguro** (Keychain/EncryptedPreferences)
- Validar **certificado SSL** en producción
- Implementar **timeout de sesión**
- Manejar errores **401 globalmente**
- Usar **HTTPS** siempre en producción
- Implementar **retry automático** para errores de red

### ❌ No Hacer
- NO almacenar tokens en SharedPreferences sin encriptar
- NO almacenar contraseñas
- NO ignorar errores de autenticación
- NO hardcodear credenciales
- NO compartir tokens entre dispositivos

---

## 🧪 Credenciales de Testing

```
Email: paciente.test@norte.com
Password: Test1234!
Subdomain: norte
```

**Importante**: Estas credenciales son solo para **desarrollo/testing**.

---

## 📞 Soporte y Recursos

### Documentación Técnica
- **Arquitectura**: Ver `ARCHITECTURE.md`
- **API Reference**: Ver `API_DOCUMENTATION.md`
- **Frontend Web**: Ver `FRONTEND_API_GUIDE.md`

### Endpoints de Diagnóstico
- **Health check**: `GET /api/health/`
- **FCM status**: `GET /api/mobile-notif/health/`
- **DB info**: `GET /api/db/`

### Herramientas Recomendadas
- **API Testing**: Postman, Insomnia
- **Debugging**: Charles Proxy, Proxyman
- **Firebase**: Firebase Console
- **DB**: PostgreSQL Client (DBeaver, pgAdmin)

---

## 🔄 Versionado

**Versión API actual**: `v1`

**Política de cambios**:
- ✅ Nuevos campos opcionales: Sin aviso previo
- ⚠️ Nuevos campos requeridos: 30 días de aviso
- ⚠️ Campos deprecated: 90 días antes de eliminar
- 🚨 Breaking changes: Migración a v2

---

## 📝 Changelog

### v1.0.0 (15 Oct 2025)
- ✅ Documentación completa para móvil
- ✅ Sistema de notificaciones FCM
- ✅ Historias clínicas con episodios múltiples
- ✅ Políticas de no-show automatizadas
- ✅ Multi-tenancy completo

---

## 🎯 Próximos Pasos Recomendados

1. **Leer en orden**: Documentos MOBILE_01 a MOBILE_06
2. **Configurar ambiente**: Firebase, proyecto base
3. **Implementar auth**: Login y gestión de tokens
4. **Probar endpoints**: Con Postman/Insomnia
5. **Implementar features**: Siguiendo los ejemplos de código
6. **Testing**: Usar credenciales de prueba
7. **Deployment**: Configurar para producción

---

## 📚 Documentos Relacionados

- `ARCHITECTURE.md` - Arquitectura completa del backend
- `API_DOCUMENTATION.md` - Referencia detallada de todos los endpoints
- `FRONTEND_API_GUIDE.md` - Guía para frontend web (React)
- `GUIA_ROLES_Y_PERMISOS.md` - Sistema de permisos
- `SOLUCION_EXCEL_OBJECT_OBJECT.md` - Serialización de reportes

---

## 🎓 Recursos de Aprendizaje

### Flutter
- [Flutter HTTP Package](https://pub.dev/packages/http)
- [Flutter Secure Storage](https://pub.dev/packages/flutter_secure_storage)
- [Firebase Messaging](https://pub.dev/packages/firebase_messaging)

### React Native
- [Axios](https://axios-http.com/)
- [React Native Firebase](https://rnfirebase.io/)
- [Expo SecureStore](https://docs.expo.dev/versions/latest/sdk/securestore/)

---

**Última actualización**: 15 de Octubre, 2025  
**Mantenido por**: Equipo Backend - Dental Clinic SaaS  
**Versión de documentación**: 1.0.0

---

## 💬 ¿Preguntas?

Si encuentras algún error en la documentación o tienes preguntas:

1. Revisa los documentos específicos en detalle
2. Prueba con las credenciales de testing
3. Verifica el endpoint `/api/health/`
4. Contacta al equipo backend

**¡Feliz desarrollo! 🚀📱**
