# 🧪 Ejemplos de Creación de Usuarios - Testing Manual

## 📋 Datos de Prueba para cada Tipo de Usuario

### 1. Crear Paciente

**Request:**
```http
POST /api/crear-usuario/
Content-Type: application/json
Authorization: Token <tu_token_admin>
X-Tenant-Subdomain: smilestudio

{
  "tipo_usuario": 2,
  "datos": {
    "nombre": "María",
    "apellido": "González",
    "correoelectronico": "maria.gonzalez@test.com",
    "sexo": "F",
    "telefono": "71234567",
    "carnetidentidad": "9876543",
    "fechanacimiento": "1995-03-15",
    "direccion": "Av. Arce #2345, La Paz"
  }
}
```

**Respuesta Esperada (201):**
```json
{
  "mensaje": "Usuario creado exitosamente como Paciente",
  "usuario": {
    "codigo": 27,
    "nombre": "María",
    "apellido": "González",
    "correoelectronico": "maria.gonzalez@test.com",
    "sexo": "F",
    "telefono": "71234567",
    "idtipousuario": 2,
    "tipo_usuario_nombre": "Paciente",
    "recibir_notificaciones": true,
    "notificaciones_email": true,
    "notificaciones_push": false,
    "paciente": {
      "carnetidentidad": "9876543",
      "fechanacimiento": "1995-03-15",
      "direccion": "Av. Arce #2345, La Paz"
    },
    "odontologo": null,
    "recepcionista": null
  }
}
```

---

### 2. Crear Odontólogo

**Request:**
```http
POST /api/crear-usuario/
Content-Type: application/json
Authorization: Token <tu_token_admin>
X-Tenant-Subdomain: smilestudio

{
  "tipo_usuario": 3,
  "datos": {
    "nombre": "Dr. Carlos",
    "apellido": "Rodríguez",
    "correoelectronico": "carlos.rodriguez@test.com",
    "sexo": "M",
    "telefono": "72345678",
    "especialidad": "Ortodoncia",
    "experienciaprofesional": "10 años de experiencia en ortodoncia y rehabilitación oral",
    "nromatricula": "ODONT-2024-001"
  }
}
```

**Respuesta Esperada (201):**
```json
{
  "mensaje": "Usuario creado exitosamente como Odontologo",
  "usuario": {
    "codigo": 28,
    "nombre": "Dr. Carlos",
    "apellido": "Rodríguez",
    "correoelectronico": "carlos.rodriguez@test.com",
    "sexo": "M",
    "telefono": "72345678",
    "idtipousuario": 3,
    "tipo_usuario_nombre": "Odontologo",
    "recibir_notificaciones": true,
    "notificaciones_email": true,
    "notificaciones_push": false,
    "paciente": null,
    "odontologo": {
      "especialidad": "Ortodoncia",
      "experienciaprofesional": "10 años de experiencia en ortodoncia y rehabilitación oral",
      "nromatricula": "ODONT-2024-001"
    },
    "recepcionista": null
  }
}
```

---

### 3. Crear Recepcionista

**Request:**
```http
POST /api/crear-usuario/
Content-Type: application/json
Authorization: Token <tu_token_admin>
X-Tenant-Subdomain: smilestudio

{
  "tipo_usuario": 4,
  "datos": {
    "nombre": "Ana",
    "apellido": "Martínez",
    "correoelectronico": "ana.martinez@test.com",
    "sexo": "F",
    "telefono": "73456789",
    "habilidadessoftware": "Microsoft Office, Sistema de Gestión Dental, Agenda Digital"
  }
}
```

**Respuesta Esperada (201):**
```json
{
  "mensaje": "Usuario creado exitosamente como Recepcionista",
  "usuario": {
    "codigo": 29,
    "nombre": "Ana",
    "apellido": "Martínez",
    "correoelectronico": "ana.martinez@test.com",
    "sexo": "F",
    "telefono": "73456789",
    "idtipousuario": 4,
    "tipo_usuario_nombre": "Recepcionista",
    "recibir_notificaciones": true,
    "notificaciones_email": true,
    "notificaciones_push": false,
    "paciente": null,
    "odontologo": null,
    "recepcionista": {
      "habilidadessoftware": "Microsoft Office, Sistema de Gestión Dental, Agenda Digital"
    }
  }
}
```

---

### 4. Crear Administrador

**Request:**
```http
POST /api/crear-usuario/
Content-Type: application/json
Authorization: Token <tu_token_admin>
X-Tenant-Subdomain: smilestudio

{
  "tipo_usuario": 1,
  "datos": {
    "nombre": "Luis",
    "apellido": "Fernández",
    "correoelectronico": "luis.fernandez@test.com",
    "sexo": "M",
    "telefono": "74567890"
  }
}
```

**Respuesta Esperada (201):**
```json
{
  "mensaje": "Usuario creado exitosamente como Administrador",
  "usuario": {
    "codigo": 30,
    "nombre": "Luis",
    "apellido": "Fernández",
    "correoelectronico": "luis.fernandez@test.com",
    "sexo": "M",
    "telefono": "74567890",
    "idtipousuario": 1,
    "tipo_usuario_nombre": "Administrador",
    "recibir_notificaciones": true,
    "notificaciones_email": true,
    "notificaciones_push": false,
    "paciente": null,
    "odontologo": null,
    "recepcionista": null
  }
}
```

---

## 🧪 Testing con cURL

### Paciente
```bash
curl -X POST "http://smilestudio.localhost:8000/api/crear-usuario/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token TU_TOKEN_AQUI" \
  -d '{
    "tipo_usuario": 2,
    "datos": {
      "nombre": "María",
      "apellido": "González",
      "correoelectronico": "maria.gonzalez@test.com",
      "sexo": "F",
      "telefono": "71234567",
      "carnetidentidad": "9876543",
      "fechanacimiento": "1995-03-15",
      "direccion": "Av. Arce #2345, La Paz"
    }
  }'
```

### Odontólogo
```bash
curl -X POST "http://smilestudio.localhost:8000/api/crear-usuario/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token TU_TOKEN_AQUI" \
  -d '{
    "tipo_usuario": 3,
    "datos": {
      "nombre": "Dr. Carlos",
      "apellido": "Rodríguez",
      "correoelectronico": "carlos.rodriguez@test.com",
      "sexo": "M",
      "telefono": "72345678",
      "especialidad": "Ortodoncia",
      "experienciaprofesional": "10 años de experiencia",
      "nromatricula": "ODONT-2024-001"
    }
  }'
```

### Recepcionista
```bash
curl -X POST "http://smilestudio.localhost:8000/api/crear-usuario/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token TU_TOKEN_AQUI" \
  -d '{
    "tipo_usuario": 4,
    "datos": {
      "nombre": "Ana",
      "apellido": "Martínez",
      "correoelectronico": "ana.martinez@test.com",
      "sexo": "F",
      "telefono": "73456789",
      "habilidadessoftware": "Microsoft Office, Sistema de Gestión"
    }
  }'
```

### Administrador
```bash
curl -X POST "http://smilestudio.localhost:8000/api/crear-usuario/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token TU_TOKEN_AQUI" \
  -d '{
    "tipo_usuario": 1,
    "datos": {
      "nombre": "Luis",
      "apellido": "Fernández",
      "correoelectronico": "luis.fernandez@test.com",
      "sexo": "M",
      "telefono": "74567890"
    }
  }'
```

---

## 🧪 Testing con Postman

### Setup
1. **URL Base**: `http://smilestudio.localhost:8000/api/crear-usuario/`
2. **Method**: POST
3. **Headers**:
   ```
   Content-Type: application/json
   Authorization: Token <tu_token_admin>
   ```

### Body (JSON) - Ejemplo Odontólogo
```json
{
  "tipo_usuario": 3,
  "datos": {
    "nombre": "Dr. Carlos",
    "apellido": "Rodríguez",
    "correoelectronico": "carlos.rodriguez@test.com",
    "sexo": "M",
    "telefono": "72345678",
    "especialidad": "Ortodoncia",
    "experienciaprofesional": "10 años de experiencia en ortodoncia y rehabilitación oral",
    "nromatricula": "ODONT-2024-001"
  }
}
```

---

## 🐛 Testing con Python Requests

```python
import requests
import json

# Configuración
BASE_URL = "http://smilestudio.localhost:8000/api"
TOKEN = "tu_token_aqui"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Token {TOKEN}"
}

# Datos para crear odontólogo
data = {
    "tipo_usuario": 3,
    "datos": {
        "nombre": "Dr. Carlos",
        "apellido": "Rodríguez",
        "correoelectronico": "carlos.rodriguez@test.com",
        "sexo": "M",
        "telefono": "72345678",
        "especialidad": "Ortodoncia",
        "experienciaprofesional": "10 años de experiencia",
        "nromatricula": "ODONT-2024-001"
    }
}

# Hacer la petición
response = requests.post(
    f"{BASE_URL}/crear-usuario/",
    headers=headers,
    json=data
)

# Mostrar resultado
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
```

---

## ⚠️ Errores Comunes

### Error: Email duplicado
```json
{
  "error": "Datos inválidos",
  "detalles": {
    "datos": {
      "correoelectronico": ["Este correo electrónico ya está registrado."]
    }
  }
}
```

### Error: CI duplicado
```json
{
  "error": "Datos inválidos",
  "detalles": {
    "datos": {
      "carnetidentidad": ["Este carnet de identidad ya está registrado."]
    }
  }
}
```

### Error: Matrícula duplicada
```json
{
  "error": "Datos inválidos",
  "detalles": {
    "datos": {
      "nromatricula": ["Este número de matrícula ya está registrado."]
    }
  }
}
```

### Error: No es administrador
```json
{
  "error": "Solo los administradores pueden crear usuarios."
}
```

---

## ✅ Verificación Post-Creación

Después de crear un usuario, puedes verificarlo con:

```bash
# Listar todos los usuarios
curl "http://smilestudio.localhost:8000/api/usuarios/" \
  -H "Authorization: Token TU_TOKEN"

# Ver usuario específico
curl "http://smilestudio.localhost:8000/api/usuarios/27/" \
  -H "Authorization: Token TU_TOKEN"
```

---

## 🎯 Datos Mínimos por Tipo

### Paciente (tipo_usuario: 2)
```json
{
  "tipo_usuario": 2,
  "datos": {
    "nombre": "Test",
    "apellido": "Paciente",
    "correoelectronico": "test.paciente@example.com"
  }
}
```

### Odontólogo (tipo_usuario: 3)
```json
{
  "tipo_usuario": 3,
  "datos": {
    "nombre": "Test",
    "apellido": "Odontologo",
    "correoelectronico": "test.odontologo@example.com"
  }
}
```

### Recepcionista (tipo_usuario: 4)
```json
{
  "tipo_usuario": 4,
  "datos": {
    "nombre": "Test",
    "apellido": "Recepcionista",
    "correoelectronico": "test.recepcionista@example.com"
  }
}
```

### Administrador (tipo_usuario: 1)
```json
{
  "tipo_usuario": 1,
  "datos": {
    "nombre": "Test",
    "apellido": "Admin",
    "correoelectronico": "test.admin@example.com"
  }
}
```

---

**Nota**: Asegúrate de que tu servidor esté corriendo y que la base de datos esté activa antes de hacer las pruebas.
