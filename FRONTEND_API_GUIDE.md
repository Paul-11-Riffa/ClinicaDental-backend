# 📘 API Documentation - Frontend Integration Guide

## 🏗️ **Arquitectura Multi-Tenant**

Este backend implementa una arquitectura **multi-tenant basada en subdominios**, donde cada clínica dental tiene su propio subdominio y datos aislados.

### **URLs Base**
- **Producción**: `https://{subdomain}.notificct.dpdns.org`
- **Desarrollo Local**: Usa header `X-Tenant-Subdomain: {subdomain}` con `http://localhost:8000`
- **Super-Admin**: `http://localhost:8000` (sin subdominio)

### **Empresas/Clínicas Disponibles**
| Subdominio | Nombre | URL Desarrollo |
|------------|--------|----------------|
| `norte` | Clínica Dental Norte | Header: `X-Tenant-Subdomain: norte` |
| `sur` | Clínica Dental Sur | Header: `X-Tenant-Subdomain: sur` |
| `este` | Clínica Dental Este | Header: `X-Tenant-Subdomain: este` |

---

## 👥 **ROLES Y PERMISOS POR CLÍNICA**

### **Estructura de Roles**

Cada clínica tiene 4 tipos de usuarios con diferentes permisos:

| Rol | ID Tipo | Descripción | Permisos Principales |
|-----|---------|-------------|---------------------|
| **Administrador** | 1 | Gestión completa de la clínica | - Gestionar usuarios<br>- Ver reportes<br>- Configurar sistema<br>- Gestionar catálogos |
| **Paciente** | 2 | Usuario final que recibe atención | - Ver sus citas<br>- Ver su historial médico<br>- Agendar citas (limitado)<br>- Ver sus tratamientos |
| **Odontólogo** | 3 | Profesional que atiende pacientes | - Gestionar consultas<br>- Ver/editar historiales clínicos<br>- Gestionar tratamientos<br>- Ver agenda de citas |
| **Recepcionista** | 4 | Personal administrativo | - Agendar citas<br>- Gestionar pacientes<br>- Ver consultas<br>- Gestionar horarios |

### **Detección del Rol en el Login**

Cuando un usuario hace login, el backend devuelve el campo `subtipo` que indica su rol:

```typescript
interface LoginResponse {
  ok: boolean;
  message: string;
  token: string;
  user: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    is_active: boolean;
  };
  usuario: {
    codigo: number;
    nombre: string;
    apellido: string;
    telefono: string;
    sexo: string;
    subtipo: "administrador" | "paciente" | "odontologo" | "recepcionista";  // ← ROL
    idtipousuario: 1 | 2 | 3 | 4;  // ← ID del tipo de usuario
    recibir_notificaciones: boolean;
  };
}
```

### **Ejemplo de Manejo de Roles en React**

```typescript
// AuthContext.tsx
interface UserData {
  codigo: number;
  nombre: string;
  apellido: string;
  subtipo: "administrador" | "paciente" | "odontologo" | "recepcionista";
  idtipousuario: number;
}

// Hook para verificar permisos
const usePermissions = () => {
  const { userData } = useAuth();
  
  return {
    isAdmin: userData?.subtipo === "administrador",
    isPaciente: userData?.subtipo === "paciente",
    isOdontologo: userData?.subtipo === "odontologo",
    isRecepcionista: userData?.subtipo === "recepcionista",
    
    // Permisos combinados
    canManagePatients: ["administrador", "recepcionista"].includes(userData?.subtipo),
    canManageAppointments: ["administrador", "recepcionista", "odontologo"].includes(userData?.subtipo),
    canViewMedicalHistory: ["administrador", "odontologo"].includes(userData?.subtipo),
    canManageUsers: userData?.subtipo === "administrador",
  };
};

// Componente de Routing
const AppRoutes = () => {
  const { isAdmin, isPaciente, isOdontologo, isRecepcionista } = usePermissions();
  
  return (
    <Routes>
      {/* Rutas Públicas */}
      <Route path="/login" element={<Login />} />
      
      {/* Dashboard según el rol */}
      {isAdmin && <Route path="/dashboard" element={<AdminDashboard />} />}
      {isPaciente && <Route path="/dashboard" element={<PatientDashboard />} />}
      {isOdontologo && <Route path="/dashboard" element={<DoctorDashboard />} />}
      {isRecepcionista && <Route path="/dashboard" element={<ReceptionDashboard />} />}
      
      {/* Rutas protegidas por rol */}
      {(isAdmin || isRecepcionista) && (
        <Route path="/pacientes" element={<PatientsList />} />
      )}
      
      {(isAdmin || isOdontologo) && (
        <Route path="/historiales" element={<MedicalRecords />} />
      )}
      
      {isAdmin && (
        <Route path="/usuarios" element={<UsersManagement />} />
      )}
    </Routes>
  );
};
```

### **Redirección Automática por Rol**

```typescript
// Login.tsx - Después del login exitoso
const handleLoginSuccess = (response: LoginResponse) => {
  // Guardar token y datos
  localStorage.setItem('token', response.token);
  localStorage.setItem('userData', JSON.stringify(response.usuario));
  
  // Redirigir según el rol
  const { subtipo } = response.usuario;
  
  switch (subtipo) {
    case 'administrador':
      navigate('/admin/dashboard');
      break;
    case 'paciente':
      navigate('/paciente/mis-citas');
      break;
    case 'odontologo':
      navigate('/doctor/agenda');
      break;
    case 'recepcionista':
      navigate('/recepcion/citas');
      break;
    default:
      navigate('/');
  }
};
```

### **Matriz de Permisos por Endpoint**

| Endpoint | Administrador | Paciente | Odontólogo | Recepcionista |
|----------|--------------|----------|------------|---------------|
| `GET /api/clinic/pacientes/` | ✅ | ❌ (solo propio) | ✅ | ✅ |
| `POST /api/clinic/pacientes/` | ✅ | ❌ | ❌ | ✅ |
| `GET /api/clinic/consultas/` | ✅ | ✅ (solo propias) | ✅ | ✅ |
| `POST /api/clinic/consultas/` | ✅ | ❌ | ✅ | ✅ |
| `GET /api/clinic/odontologos/` | ✅ | ✅ (solo lista) | ✅ | ✅ |
| `GET /api/clinic/historias-clinicas/` | ✅ | ✅ (solo propio) | ✅ | ❌ |
| `POST /api/clinic/historias-clinicas/` | ✅ | ❌ | ✅ | ❌ |
| `GET /api/users/usuarios/` | ✅ | ❌ | ❌ | ❌ |
| `POST /api/users/usuarios/` | ✅ | ❌ | ❌ | ❌ |

### **Credenciales de Prueba por Rol**

#### **Clínica Norte**
```typescript
// Administrador
{ email: "admin@norte.com", password: "norte123" }

// Paciente
{ email: "juan.perez@norte.com", password: "norte123" }
{ email: "maria.gonzalez@norte.com", password: "norte123" }

// Odontólogo
{ email: "pedro.martinez@norte.com", password: "norte123" }

// Recepcionista
{ email: "laura.fernandez@norte.com", password: "norte123" }
```

#### **Clínica Sur**
```typescript
// Administrador
{ email: "admin@sur.com", password: "sur123" }

// Paciente
{ email: "roberto.sanchez@sur.com", password: "sur123" }

// Odontólogo
{ email: "miguel.vargas@sur.com", password: "sur123" }

// Recepcionista
{ email: "sofia.morales@sur.com", password: "sur123" }
```

#### **Clínica Este**
```typescript
// Administrador
{ email: "admin@este.com", password: "este123" }

// Paciente
{ email: "luis.ramirez@este.com", password: "este123" }

// Odontóloga
{ email: "isabel.castro@este.com", password: "este123" }

// Recepcionista
{ email: "andrea.mendez@este.com", password: "este123" }
```

---

## 🔐 **Autenticación**

### **Sistema Dual de Autenticación**

1. **Supabase Auth** - Para registro/login inicial
2. **Django Token Auth** - Para acceso a la API

### **Endpoints de Autenticación**

#### **1. Login** ⭐ **ENDPOINT PRINCIPAL**
```http
POST /api/auth/login/
Content-Type: application/json
X-Tenant-Subdomain: norte  // Header para desarrollo local

{
  "email": "usuario@example.com",
  "password": "contraseña123"
}
```

**Respuesta Exitosa (200)**:
```json
{
  "ok": true,
  "message": "Login exitoso",
  "token": "a1b2c3d4e5f6g7h8i9j0...",
  "user": {
    "id": 1,
    "email": "juan.perez@norte.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "is_active": true
  },
  "usuario": {
    "codigo": 1,
    "nombre": "Juan",
    "apellido": "Pérez",
    "telefono": "+56912345678",
    "sexo": "M",
    "subtipo": "paciente",  // ← ROL DEL USUARIO (clave para routing)
    "idtipousuario": 2,      // ← ID del tipo de usuario
    "recibir_notificaciones": true
  }
}
```

**Ejemplo de Implementación en React:**
```typescript
// api/auth.ts
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export const login = async (email: string, password: string, subdomain: string) => {
  const response = await axios.post(`${API_BASE}/auth/login/`, 
    { email, password },
    {
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-Subdomain': subdomain  // ← Importante para desarrollo
      }
    }
  );
  
  return response.data;
};

// hooks/useAuth.ts
export const useAuth = () => {
  const [user, setUser] = useState<UserData | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const navigate = useNavigate();
  
  const handleLogin = async (email: string, password: string) => {
    try {
      const data = await login(email, password, 'norte');
      
      // Guardar en localStorage
      localStorage.setItem('token', data.token);
      localStorage.setItem('userData', JSON.stringify(data.usuario));
      
      setToken(data.token);
      setUser(data.usuario);
      
      // Redirigir según el rol
      switch (data.usuario.subtipo) {
        case 'administrador':
          navigate('/admin/dashboard');
          break;
        case 'paciente':
          navigate('/paciente/mis-citas');
          break;
        case 'odontologo':
          navigate('/doctor/agenda');
          break;
        case 'recepcionista':
          navigate('/recepcion/citas');
          break;
      }
    } catch (error) {
      console.error('Error en login:', error);
      throw error;
    }
  };
  
  return { user, token, handleLogin };
};
```

#### **2. Registro de Usuario**
```http
POST /api/auth/register/
Content-Type: application/json
X-Tenant-Subdomain: norte

{
  "email": "usuario@example.com",
  "password": "contraseña123",
  "nombre": "Juan",
  "apellido": "Pérez",
  "telefono": "70000000",
  "rol": "Paciente",  // "Paciente", "Odontólogo", "Recepcionista"
  "empresa_subdomain": "norte"  // Subdominio de la clínica
}
```

**Respuesta Exitosa (201)**:
```json
{
  "message": "Usuario registrado exitosamente",
  "user": {
    "codigo": 1,
    "nombre": "Juan",
    "apellido": "Pérez",
    "correoelectronico": "usuario@example.com",
    "subtipo": "paciente"
  }
}
```

#### **3. Cerrar Sesión**
```http
POST /api/auth/logout/
Authorization: Token {tu-token-aqui}
X-Tenant-Subdomain: norte
```

**Respuesta Exitosa (200)**:
```json
{
  "message": "Sesión cerrada exitosamente"
}
```

#### **3. Cerrar Sesión**
```http
POST /api/users/logout/
Authorization: Token {tu-token-aqui}
```

**Respuesta Exitosa (200)**:
```json
{
  "message": "Sesión cerrada exitosamente"
}
```

### **Uso del Token en Requests**

Una vez autenticado, incluye el token en todas las peticiones:

```http
GET /api/clinic/pacientes/
Authorization: Token {tu-token-aqui}
X-Tenant-Subdomain: norte  // Solo para desarrollo sin subdominios
```

---

## 📋 **Endpoints Principales**

### **Base URL para Tenant (Clínica)**
Todos los endpoints de clínica están bajo: `/api/clinic/`

### **1. Pacientes**

#### **Listar Pacientes**
```http
GET http://norte.localhost:8000/api/clinic/pacientes/
Authorization: Token {tu-token}
```

**Respuesta**:
```json
[
  {
    "codusuario": {
      "codigo": 1,
      "nombre": "Juan",
      "apellido": "Pérez",
      "correoelectronico": "juan.perez@norte.com",
      "telefono": "70000001",
      "sexo": "M"
    },
    "carnetidentidad": "1234567-LP",
    "fechanacimiento": "1990-01-01",
    "direccion": "Zona Norte"
  }
]
```

#### **Crear Paciente**
```http
POST http://norte.localhost:8000/api/clinic/pacientes/
Authorization: Token {tu-token}
Content-Type: application/json

{
  "codusuario": {
    "nombre": "María",
    "apellido": "López",
    "correoelectronico": "maria.lopez@norte.com",
    "telefono": "70000002",
    "sexo": "F"
  },
  "carnetidentidad": "9876543-LP",
  "fechanacimiento": "1995-06-15",
  "direccion": "Calle Ejemplo #123"
}
```

#### **Obtener Paciente por ID**
```http
GET http://norte.localhost:8000/api/clinic/pacientes/{id}/
Authorization: Token {tu-token}
```

#### **Actualizar Paciente**
```http
PUT http://norte.localhost:8000/api/clinic/pacientes/{id}/
Authorization: Token {tu-token}
Content-Type: application/json

{
  "codusuario": {
    "nombre": "Juan Actualizado",
    "telefono": "71111111"
  },
  "direccion": "Nueva dirección"
}
```

#### **Eliminar Paciente**
```http
DELETE http://norte.localhost:8000/api/clinic/pacientes/{id}/
Authorization: Token {tu-token}
```

---

### **2. Odontólogos**

#### **Listar Odontólogos**
```http
GET http://norte.localhost:8000/api/clinic/odontologos/
Authorization: Token {tu-token}
```

**Respuesta**:
```json
[
  {
    "codusuario": {
      "codigo": 3,
      "nombre": "Dr. Pedro",
      "apellido": "Martínez",
      "correoelectronico": "pedro.martinez@norte.com",
      "telefono": "71000001"
    },
    "especialidad": "Odontología General",
    "nromatricula": "ODO-001-LP",
    "experienciaprofesional": "5 años"
  }
]
```

#### **Crear Odontólogo**
```http
POST http://norte.localhost:8000/api/clinic/odontologos/
Authorization: Token {tu-token}
Content-Type: application/json

{
  "codusuario": {
    "nombre": "Dra. Ana",
    "apellido": "García",
    "correoelectronico": "ana.garcia@norte.com",
    "telefono": "71000002",
    "sexo": "F"
  },
  "especialidad": "Ortodoncia",
  "nromatricula": "ODO-002-LP",
  "experienciaprofesional": "10 años de experiencia en ortodoncia"
}
```

---

### **3. Consultas (Citas)**

#### **Listar Consultas**
```http
GET http://norte.localhost:8000/api/clinic/consultas/
Authorization: Token {tu-token}
```

**Filtros disponibles**:
```http
GET /api/clinic/consultas/?fecha=2025-10-15
GET /api/clinic/consultas/?codpaciente=1
GET /api/clinic/consultas/?cododontologo=3
GET /api/clinic/consultas/?idestadoconsulta=1
```

**Respuesta**:
```json
[
  {
    "id": 1,
    "fecha": "2025-10-16",
    "codpaciente": {
      "codusuario": {
        "nombre": "Juan",
        "apellido": "Pérez"
      }
    },
    "cododontologo": {
      "codusuario": {
        "nombre": "Dr. Pedro",
        "apellido": "Martínez"
      }
    },
    "idhorario": {
      "hora": "08:00:00"
    },
    "idtipoconsulta": {
      "nombreconsulta": "Consulta General"
    },
    "idestadoconsulta": {
      "estado": "Confirmada"
    }
  }
]
```

#### **Crear Consulta**
```http
POST http://norte.localhost:8000/api/clinic/consultas/
Authorization: Token {tu-token}
Content-Type: application/json

{
  "fecha": "2025-10-20",
  "codpaciente": 1,
  "cododontologo": 3,
  "codrecepcionista": 4,
  "idhorario": 1,
  "idtipoconsulta": 1,
  "idestadoconsulta": 1
}
```

#### **Actualizar Estado de Consulta**
```http
PATCH http://norte.localhost:8000/api/clinic/consultas/{id}/
Authorization: Token {tu-token}
Content-Type: application/json

{
  "idestadoconsulta": 2  // Cambiar a otro estado
}
```

#### **Cancelar Consulta**
```http
DELETE http://norte.localhost:8000/api/clinic/consultas/{id}/
Authorization: Token {tu-token}
```

---

### **4. Horarios Disponibles**

#### **Listar Horarios**
```http
GET http://norte.localhost:8000/api/clinic/horarios/
Authorization: Token {tu-token}
```

**Respuesta**:
```json
[
  {"id": 1, "hora": "08:00:00"},
  {"id": 2, "hora": "09:00:00"},
  {"id": 3, "hora": "10:00:00"},
  {"id": 4, "hora": "11:00:00"},
  {"id": 5, "hora": "14:00:00"}
]
```

---

### **5. Tipos de Consulta**

#### **Listar Tipos de Consulta**
```http
GET http://norte.localhost:8000/api/clinic/tipos-consulta/
Authorization: Token {tu-token}
```

**Respuesta**:
```json
[
  {"id": 1, "nombreconsulta": "Consulta General"},
  {"id": 2, "nombreconsulta": "Limpieza Dental"},
  {"id": 3, "nombreconsulta": "Ortodoncia"},
  {"id": 4, "nombreconsulta": "Endodoncia"}
]
```

---

### **6. Estados de Consulta**

#### **Listar Estados**
```http
GET http://norte.localhost:8000/api/clinic/estadodeconsultas/
Authorization: Token {tu-token}
```

**Respuesta**:
```json
[
  {"id": 1, "estado": "Pendiente"},
  {"id": 2, "estado": "Confirmada"},
  {"id": 3, "estado": "En Atención"},
  {"id": 4, "estado": "Completada"},
  {"id": 5, "estado": "Cancelada"}
]
```

---

### **7. Tratamientos**

#### **Listar Tratamientos**
```http
GET http://norte.localhost:8000/api/clinic/tratamientos/
Authorization: Token {tu-token}
```

**Respuesta**:
```json
[
  {
    "id": 1,
    "nombretratamiento": "Limpieza Dental",
    "precio": "150.00"
  },
  {
    "id": 2,
    "nombretratamiento": "Blanqueamiento",
    "precio": "500.00"
  }
]
```

---

### **8. Historial Clínico**

#### **Listar Historiales**
```http
GET http://norte.localhost:8000/api/clinic/historias-clinicas/
Authorization: Token {tu-token}
```

#### **Historial por Paciente**
```http
GET http://norte.localhost:8000/api/clinic/historias-clinicas/?pacientecodigo=1
Authorization: Token {tu-token}
```

#### **Crear Historial**
```http
POST http://norte.localhost:8000/api/clinic/historias-clinicas/
Authorization: Token {tu-token}
Content-Type: application/json

{
  "pacientecodigo": 1,
  "descripcion": "Consulta general, paciente sin problemas",
  "diagnostico": "Salud dental buena",
  "tratamientorealizado": "Limpieza dental profunda"
}
```

---

### **9. Recepcionistas**

#### **Listar Recepcionistas**
```http
GET http://norte.localhost:8000/api/clinic/recepcionistas/
Authorization: Token {tu-token}
```

**Respuesta**:
```json
[
  {
    "codusuario": {
      "codigo": 4,
      "nombre": "Laura",
      "apellido": "Fernández",
      "correoelectronico": "laura.fernandez@norte.com"
    },
    "habilidadessoftware": "Microsoft Office"
  }
]
```

---

## 🔔 **Notificaciones Push (FCM)**

### **Registrar Token FCM**
```http
POST /api/notifications/register-device/
Authorization: Token {tu-token}
Content-Type: application/json

{
  "fcm_token": "token-fcm-del-dispositivo",
  "device_type": "android",  // "android" o "ios"
  "device_name": "Xiaomi Redmi Note 9"
}
```

### **Actualizar Preferencias de Notificaciones**
```http
PUT /api/clinic/usuarios/{id}/
Authorization: Token {tu-token}
Content-Type: application/json

{
  "notificaciones_push": true,
  "notificaciones_email": true,
  "recibir_notificaciones": true
}
```

---

## 🏥 **Endpoints de Super-Admin**

Estos endpoints solo están disponibles en `localhost:8000` (sin subdominio):

### **Listar Todas las Empresas**
```http
GET http://localhost:8000/api/tenancy/empresas/
Authorization: Token {token-super-admin}
```

### **Crear Nueva Empresa**
```http
POST http://localhost:8000/api/tenancy/empresas/
Authorization: Token {token-super-admin}
Content-Type: application/json

{
  "nombre": "Clínica Dental Oeste",
  "subdomain": "oeste",
  "activo": true
}
```

---

## ⚠️ **Manejo de Errores**

### **Códigos de Estado HTTP**

| Código | Significado | Descripción |
|--------|-------------|-------------|
| 200 | OK | Operación exitosa |
| 201 | Created | Recurso creado exitosamente |
| 400 | Bad Request | Datos inválidos en la petición |
| 401 | Unauthorized | No autenticado o token inválido |
| 403 | Forbidden | Sin permisos para esta acción |
| 404 | Not Found | Recurso no encontrado |
| 500 | Server Error | Error interno del servidor |

### **Formato de Errores**

```json
{
  "error": "Descripción del error",
  "details": {
    "campo": ["Mensaje de error específico"]
  }
}
```

**Ejemplo**:
```json
{
  "error": "Datos inválidos",
  "details": {
    "correoelectronico": ["Este campo debe ser único."],
    "telefono": ["Ingrese un número de teléfono válido."]
  }
}
```

---

## 🧪 **Datos de Prueba Disponibles**

### **Clínica Norte**

**Pacientes**:
- Juan Pérez García (CI: 1234567-LP)
- María González (CI: 2345678-LP)

**Odontólogos**:
- Dr. Pedro Martínez (Matrícula: ODO-001-LP)

**Recepcionista**:
- Laura Fernández

### **Clínica Sur**

**Pacientes**:
- Roberto Sánchez (CI: 4567890-CB)

**Odontólogos**:
- Dr. Miguel Vargas (Matrícula: ODO-001-CB)

**Recepcionista**:
- Sofia Morales

### **Clínica Este**

**Pacientes**:
- Luis Ramírez (CI: 6789012-SC)

**Odontólogos**:
- Dra. Isabel Castro (Matrícula: ODO-001-SC)

**Recepcionista**:
- Andrea Méndez

---

## 💻 **Desarrollo Local**

### **Configuración de Subdominios**

Para desarrollo local, necesitas configurar Acrylic DNS Proxy o usar headers HTTP:

#### **Opción 1: Con Acrylic DNS Proxy** (Recomendado)
Acceso directo desde el navegador:
```
http://norte.localhost:8000/api/clinic/pacientes/
```

#### **Opción 2: Con Headers HTTP**
Si no usas Acrylic, incluye el header `X-Tenant-Subdomain`:
```javascript
fetch('http://localhost:8000/api/clinic/pacientes/', {
  headers: {
    'Authorization': 'Token tu-token-aqui',
    'X-Tenant-Subdomain': 'norte'
  }
})
```

---

## 📦 **Ejemplo de Integración en React**

### **Service de API**

```javascript
// api.service.js
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  constructor(subdomain) {
    this.subdomain = subdomain;
    this.baseURL = `http://${subdomain}.localhost:8000`;
  }

  async request(endpoint, options = {}) {
    const token = localStorage.getItem('authToken');
    
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Token ${token}` }),
        'X-Tenant-Subdomain': this.subdomain, // Para desarrollo sin subdominios
        ...options.headers,
      },
    };

    const response = await fetch(`${this.baseURL}${endpoint}`, config);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Error en la petición');
    }
    
    return response.json();
  }

  // Pacientes
  async getPacientes() {
    return this.request('/api/clinic/pacientes/');
  }

  async createPaciente(data) {
    return this.request('/api/clinic/pacientes/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Consultas
  async getConsultas(filters = {}) {
    const queryString = new URLSearchParams(filters).toString();
    return this.request(`/api/clinic/consultas/?${queryString}`);
  }

  async createConsulta(data) {
    return this.request('/api/clinic/consultas/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Autenticación
  async login(email, password) {
    const response = await this.request('/api/users/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    
    if (response.token) {
      localStorage.setItem('authToken', response.token);
      localStorage.setItem('currentUser', JSON.stringify(response.user));
    }
    
    return response;
  }

  async logout() {
    await this.request('/api/users/logout/', { method: 'POST' });
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
  }
}

export default ApiService;
```

### **Uso en Componentes**

```javascript
// PacientesPage.jsx
import { useState, useEffect } from 'react';
import ApiService from './api.service';

const api = new ApiService('norte'); // Subdominio de la clínica

function PacientesPage() {
  const [pacientes, setPacientes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPacientes();
  }, []);

  const loadPacientes = async () => {
    try {
      const data = await api.getPacientes();
      setPacientes(data);
    } catch (error) {
      console.error('Error cargando pacientes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePaciente = async (formData) => {
    try {
      await api.createPaciente(formData);
      loadPacientes(); // Recargar lista
    } catch (error) {
      console.error('Error creando paciente:', error);
    }
  };

  return (
    <div>
      <h1>Pacientes</h1>
      {loading ? (
        <p>Cargando...</p>
      ) : (
        <ul>
          {pacientes.map(p => (
            <li key={p.codusuario.codigo}>
              {p.codusuario.nombre} {p.codusuario.apellido} - CI: {p.carnetidentidad}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default PacientesPage;
```

---

## 📝 **Notas Importantes**

1. **Aislamiento de Datos**: Cada clínica solo puede ver sus propios datos. El sistema filtra automáticamente por empresa.

2. **Tokens**: Los tokens de autenticación son específicos por usuario, no por empresa. Un usuario puede pertenecer a una sola empresa.

3. **CORS**: El backend acepta peticiones desde cualquier origen en desarrollo. En producción, solo desde dominios autorizados.

4. **Rate Limiting**: No implementado actualmente, pero recomendado para producción.

5. **Paginación**: Los endpoints que retornan listas soportan paginación:
   ```
   GET /api/clinic/pacientes/?page=2&page_size=20
   ```

6. **Ordenamiento**: Usa el parámetro `ordering`:
   ```
   GET /api/clinic/pacientes/?ordering=-fecha
   ```

---

## 🆘 **Soporte**

Para problemas o preguntas:
- Verificar la documentación del modelo en `api/models.py`
- Revisar los serializadores en `api/serializers.py`
- Consultar logs del servidor Django

---

**Última actualización**: Octubre 15, 2025
