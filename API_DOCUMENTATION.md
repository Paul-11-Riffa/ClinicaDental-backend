# 📘 API Documentation - Multi-Tenant Dental Clinic SaaS

## 🌐 Base URLs

### Development
```
Public API:     http://localhost:8000
Tenant Norte:   http://norte.localhost:8000
Tenant Sur:     http://sur.localhost:8000
Tenant Este:    http://este.localhost:8000
```

### Production
```
Public API:     https://notificct.dpdns.org
Tenant Norte:   https://norte.notificct.dpdns.org
Tenant Sur:     https://sur.notificct.dpdns.org
Tenant Este:    https://este.notificct.dpdns.org
```

---

## 🔐 Authentication

### 1. Register User (Supabase Integration)
```http
POST /api/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123",
  "nombre": "Juan",
  "apellido": "Pérez",
  "telefono": "+591 70000000",
  "tipo_usuario": "paciente"  // Options: paciente, odontologo, recepcionista
}
```

**Response (201 Created):**
```json
{
  "user": {
    "id": "uuid-from-supabase",
    "email": "user@example.com"
  },
  "usuario": {
    "codusuario": 1,
    "nombre": "Juan",
    "apellido": "Pérez",
    "correoelectronico": "user@example.com",
    "telefono": "+591 70000000",
    "empresa": {
      "codempresa": 1,
      "nombre": "Clínica Norte",
      "subdomain": "norte"
    }
  },
  "session": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "expires_in": 3600
  }
}
```

### 2. Login
```http
POST /api/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (200 OK):**
```json
{
  "session": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "expires_in": 3600
  },
  "usuario": {
    "codusuario": 1,
    "nombre": "Juan",
    "apellido": "Pérez",
    "empresa": {
      "codempresa": 1,
      "nombre": "Clínica Norte",
      "subdomain": "norte"
    }
  }
}
```

### 3. Using Authentication

**Include in all subsequent requests:**
```http
Authorization: Bearer eyJ...your-access-token
```

---

## 🏥 Multi-Tenancy

### How It Works

1. **Subdomain Detection**: The API automatically detects the tenant from the subdomain
2. **Data Isolation**: Each tenant only sees their own data
3. **Automatic Filtering**: All queries are filtered by `empresa` (tenant)

### For Development (Alternative to Subdomains)

If you can't use subdomains in development, use the header:

```http
X-Tenant-Subdomain: norte
```

---

## 👥 User Management

### Get Current User
```http
GET /api/users/me/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "codusuario": 1,
  "nombre": "Juan",
  "apellido": "Pérez",
  "correoelectronico": "user@example.com",
  "telefono": "+591 70000000",
  "activo": true,
  "empresa": {
    "codempresa": 1,
    "nombre": "Clínica Norte",
    "subdomain": "norte"
  },
  "tipo_usuario": {
    "codtipodeusuario": 1,
    "nombre": "Paciente"
  }
}
```

### Update User Profile
```http
PATCH /api/users/me/
Authorization: Bearer {token}
Content-Type: application/json

{
  "telefono": "+591 71111111",
  "nombre": "Juan Carlos"
}
```

---

## 🦷 Patient Management

### List Patients (Odontologist/Receptionist)
```http
GET /api/clinic/pacientes/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "codpaciente": 1,
      "codusuario": {
        "codusuario": 2,
        "nombre": "María",
        "apellido": "García",
        "correoelectronico": "maria@example.com",
        "telefono": "+591 72000000"
      },
      "carnetidentidad": "1234567-LP",
      "fechanacimiento": "1990-05-15",
      "direccion": "Av. América #123",
      "activo": true
    }
  ]
}
```

### Get Patient Detail
```http
GET /api/clinic/pacientes/{id}/
Authorization: Bearer {token}
```

### Create Patient (Receptionist)
```http
POST /api/clinic/pacientes/
Authorization: Bearer {token}
Content-Type: application/json

{
  "nombre": "María",
  "apellido": "García",
  "correoelectronico": "maria@example.com",
  "telefono": "+591 72000000",
  "carnetidentidad": "1234567-LP",
  "fechanacimiento": "1990-05-15",
  "direccion": "Av. América #123"
}
```

### Update Patient
```http
PATCH /api/clinic/pacientes/{id}/
Authorization: Bearer {token}
Content-Type: application/json

{
  "telefono": "+591 73000000",
  "direccion": "Nueva dirección"
}
```

---

## 📅 Appointment Management (Consultas)

### List Appointments
```http
GET /api/clinic/consultas/
Authorization: Bearer {token}

# Optional filters:
GET /api/clinic/consultas/?estado=Confirmada
GET /api/clinic/consultas/?paciente={codpaciente}
GET /api/clinic/consultas/?odontologo={cododontologo}
GET /api/clinic/consultas/?fecha=2025-10-15
```

**Response:**
```json
{
  "count": 5,
  "results": [
    {
      "codconsulta": 1,
      "paciente": {
        "codpaciente": 1,
        "nombre": "María García"
      },
      "odontologo": {
        "cododontologo": 1,
        "nombre": "Dr. Carlos López"
      },
      "fechahora": "2025-10-20T10:00:00Z",
      "motivoconsulta": "Limpieza dental",
      "estadoconsulta": {
        "codestadoconsulta": 1,
        "nombre": "Confirmada"
      },
      "observaciones": "Primera consulta"
    }
  ]
}
```

### Create Appointment
```http
POST /api/clinic/consultas/
Authorization: Bearer {token}
Content-Type: application/json

{
  "paciente": 1,
  "odontologo": 1,
  "fechahora": "2025-10-20T10:00:00Z",
  "motivoconsulta": "Limpieza dental",
  "observaciones": "Primera consulta"
}
```

### Update Appointment Status
```http
PATCH /api/clinic/consultas/{id}/
Authorization: Bearer {token}
Content-Type: application/json

{
  "estadoconsulta": 2  // ID del estado (Confirmada, Cancelada, Completada, No-Show)
}
```

### Available Appointment States
```http
GET /api/clinic/estados-consulta/
```

**Response:**
```json
[
  {"codestadoconsulta": 1, "nombre": "Pendiente"},
  {"codestadoconsulta": 2, "nombre": "Confirmada"},
  {"codestadoconsulta": 3, "nombre": "Completada"},
  {"codestadoconsulta": 4, "nombre": "Cancelada"},
  {"codestadoconsulta": 5, "nombre": "No-Show"}
]
```

---

## 👨‍⚕️ Odontologist Management

### List Odontologists
```http
GET /api/clinic/odontologos/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "results": [
    {
      "cododontologo": 1,
      "codusuario": {
        "nombre": "Carlos",
        "apellido": "López",
        "correoelectronico": "carlos@clinica.com",
        "telefono": "+591 74000000"
      },
      "especialidad": "Ortodoncia",
      "matricula": "OR-12345",
      "activo": true
    }
  ]
}
```

### Get Odontologist Schedule
```http
GET /api/clinic/odontologos/{id}/disponibilidad/
Authorization: Bearer {token}

# Optional parameters:
?fecha_inicio=2025-10-15
?fecha_fin=2025-10-22
```

---

## 🔔 Push Notifications (FCM)

### Register Device for Notifications
```http
POST /api/notifications/devices/
Authorization: Bearer {token}
Content-Type: application/json

{
  "fcm_token": "fcm-device-token-from-firebase",
  "device_type": "android",  // or "ios", "web"
  "device_name": "Samsung Galaxy S21"
}
```

### Get Notification Preferences
```http
GET /api/notifications/preferences/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "notificaciones_activas": true,
  "recordatorios_citas": true,
  "confirmaciones": true,
  "promociones": false
}
```

### Update Notification Preferences
```http
PATCH /api/notifications/preferences/
Authorization: Bearer {token}
Content-Type: application/json

{
  "recordatorios_citas": false,
  "promociones": true
}
```

### Get Notification History
```http
GET /api/notifications/history/
Authorization: Bearer {token}

# Optional filters:
?tipo=recordatorio_cita
?leida=false
```

---

## 🚫 No-Show Policies & Penalties

### Get Patient Penalties
```http
GET /api/no-show/multas/
Authorization: Bearer {token}

# For specific patient:
GET /api/no-show/multas/?paciente={codpaciente}
```

**Response:**
```json
{
  "results": [
    {
      "codmulta": 1,
      "paciente": {
        "codpaciente": 1,
        "nombre": "María García"
      },
      "consulta": {
        "codconsulta": 5,
        "fechahora": "2025-10-10T10:00:00Z"
      },
      "monto": 50.00,
      "tipo_multa": "no_show",
      "estado": "pendiente",  // pendiente, pagada, condonada
      "fecha_aplicacion": "2025-10-10T11:00:00Z"
    }
  ]
}
```

### Check if Patient is Blocked
```http
GET /api/no-show/bloqueos/activos/
Authorization: Bearer {token}

# For specific patient:
GET /api/no-show/bloqueos/activos/?paciente={codpaciente}
```

**Response:**
```json
{
  "bloqueado": true,
  "bloqueos": [
    {
      "codbloqueousuario": 1,
      "fecha_inicio": "2025-10-10T00:00:00Z",
      "fecha_fin": "2025-10-17T00:00:00Z",
      "motivo": "3 no-shows consecutivos",
      "activo": true
    }
  ]
}
```

---

## 📊 Catalog / Reference Data

### Get All Catalogs
```http
GET /api/catalog/tipos-usuario/
GET /api/catalog/tipos-tratamiento/
GET /api/catalog/especialidades/
GET /api/catalog/estados-consulta/
```

**Example Response (Tipos de Usuario):**
```json
[
  {"codtipodeusuario": 1, "nombre": "Paciente"},
  {"codtipodeusuario": 2, "nombre": "Odontólogo"},
  {"codtipodeusuario": 3, "nombre": "Recepcionista"}
]
```

---

## 🏢 Tenant/Company Management (Admin Only)

### List All Tenants (Public API)
```http
GET /api/tenancy/empresas/
# No authentication required
```

**Response:**
```json
[
  {
    "codempresa": 1,
    "nombre": "Clínica Norte",
    "subdomain": "norte",
    "activo": true,
    "direccion": "Av. América #123",
    "telefono": "+591 2222222"
  },
  {
    "codempresa": 2,
    "nombre": "Clínica Sur",
    "subdomain": "sur",
    "activo": true
  }
]
```

### Get Tenant Details
```http
GET /api/tenancy/empresas/{subdomain}/
```

---

## 📝 Clinical Documents

### Upload Clinical Document
```http
POST /api/clinic/documentos/
Authorization: Bearer {token}
Content-Type: multipart/form-data

{
  "paciente": 1,
  "tipo_documento": "historia_clinica",
  "titulo": "Historia Clínica Inicial",
  "archivo": [binary file data],
  "descripcion": "Primera consulta"
}
```

### Get Patient Documents
```http
GET /api/clinic/documentos/?paciente={codpaciente}
Authorization: Bearer {token}
```

### Download Document
```http
GET /api/clinic/documentos/{id}/download/
Authorization: Bearer {token}
```

---

## 💳 Consent Management

### Get Consent Templates
```http
GET /api/consent/templates/
Authorization: Bearer {token}
```

### Sign Consent
```http
POST /api/consent/sign/
Authorization: Bearer {token}
Content-Type: application/json

{
  "template_id": 1,
  "paciente": 1,
  "firma_digital": "base64-encoded-signature-image"
}
```

---

## ⚠️ Error Responses

### Standard Error Format
```json
{
  "error": "Error message",
  "detail": "Detailed error description",
  "code": "error_code"
}
```

### Common HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created
- `204 No Content` - Successful deletion
- `400 Bad Request` - Invalid data
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource doesn't exist
- `409 Conflict` - Duplicate resource
- `500 Internal Server Error` - Server error

---

## 🔧 Frontend Integration Examples

### React/Next.js Example

```typescript
// api/client.ts
import axios from 'axios';

const isDevelopment = process.env.NODE_ENV === 'development';

// Determine base URL based on subdomain
const getBaseURL = () => {
  if (isDevelopment) {
    const hostname = window.location.hostname;
    const port = ':8000';
    
    // Extract subdomain (e.g., "norte" from "norte.localhost")
    const subdomain = hostname.split('.')[0];
    
    if (subdomain !== 'localhost' && subdomain !== '127') {
      return `http://${hostname}${port}`;
    }
    return `http://localhost${port}`;
  }
  
  // Production
  return `https://${window.location.hostname}`;
};

const apiClient = axios.create({
  baseURL: getBaseURL(),
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### Vue.js Example

```typescript
// plugins/api.ts
import axios from 'axios';

const getBaseURL = () => {
  const hostname = window.location.hostname;
  const isDev = hostname.includes('localhost');
  
  if (isDev) {
    return `http://${hostname}:8000`;
  }
  return `https://${hostname}`;
};

export const api = axios.create({
  baseURL: getBaseURL(),
});

// Add token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Angular Example

```typescript
// services/api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private baseUrl: string;

  constructor(private http: HttpClient) {
    this.baseUrl = this.getBaseURL();
  }

  private getBaseURL(): string {
    const hostname = window.location.hostname;
    const isDev = hostname.includes('localhost');
    return isDev ? `http://${hostname}:8000` : `https://${hostname}`;
  }

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    });
  }

  get(endpoint: string) {
    return this.http.get(`${this.baseUrl}${endpoint}`, {
      headers: this.getHeaders()
    });
  }

  post(endpoint: string, data: any) {
    return this.http.post(`${this.baseUrl}${endpoint}`, data, {
      headers: this.getHeaders()
    });
  }
}
```

---

## 🚀 Quick Start for Frontend

1. **Configure your hosts file** (Development only):
   - Windows: `C:\Windows\System32\drivers\etc\hosts`
   - Mac/Linux: `/etc/hosts`
   
   Add:
   ```
   127.0.0.1 norte.localhost
   127.0.0.1 sur.localhost
   127.0.0.1 este.localhost
   ```

2. **Set environment variables**:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_TENANT_SUBDOMAIN=norte  # or use auto-detection
   ```

3. **Test connection**:
   ```bash
   curl http://norte.localhost:8000/api/tenancy/empresas/
   ```

4. **Implement authentication flow**:
   - Register/Login → Get access token
   - Store token in localStorage/sessionStorage
   - Add token to all requests
   - Handle token refresh/expiration

---

## 📞 Support

For questions or issues:
- Check the Django admin logs
- Review middleware configuration
- Verify tenant isolation
- Check FCM notification logs

---

**Last Updated**: October 15, 2025
**API Version**: 1.0
**Django Version**: 5.2.6
