# 🦷 Dental Clinic SaaS - Backend API

Sistema de gestión para clínicas dentales con arquitectura multi-tenant basada en subdominios.

> **📚 [Ver Documentación Completa](INDEX.md)**

## 🚀 **Características Principales**

- ✅ **Multi-Tenant**: Aislamiento completo de datos por clínica (subdominio)
- ✅ **Autenticación**: Integración Supabase + Django Token Auth
- ✅ **Notificaciones Push**: Sistema FCM para notificaciones móviles
- ✅ **API RESTful**: Endpoints completos para gestión dental
- ✅ **Admin Panels**: Interfaces separadas (super-admin y tenant-admin)
- ✅ **No-Show Policies**: Sistema automatizado de penalizaciones
- ✅ **Audit Trail**: Registro completo de acciones (Bitácora)

---

## 📖 **Guías Rápidas**

- **[Inicio Rápido](INICIO_RAPIDO.md)** - Configuración inicial
- **[Arquitectura](ARCHITECTURE.md)** - Diseño del sistema
- **[API Documentation](API_DOCUMENTATION.md)** - Endpoints REST
- **[Frontend Guide](FRONTEND_API_GUIDE.md)** - Integración con frontend
- **[Roles y Permisos](GUIA_ROLES_Y_PERMISOS.md)** - Sistema de permisos
- **[Historias Clínicas](GUIA_HISTORIAS_CLINICAS_FRONTEND.md)** - Historia clínica
- **[Filtros de Reportes](GUIA_FILTROS_REPORTES_FRONTEND.md)** - Reportes con filtros

---

## 📋 **Requisitos**

- Python 3.13+
- PostgreSQL 12+ (Supabase)
- Virtual Environment

---

## ⚡ **Inicio Rápido**

### **1. Clonar el Repositorio**
```bash
git clone <repo-url>
cd sitwo-project-backend-master
```

### **2. Crear Entorno Virtual**
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
source .venv/bin/activate      # Linux/Mac
```

### **3. Instalar Dependencias**
```bash
pip install -r requirements.txt
```

### **4. Configurar Variables de Entorno**

Crea un archivo `.env` en la raíz del proyecto:

```env
# Database (Supabase PostgreSQL)
DB_HOST=your-project.supabase.co
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password
DB_PORT=5432

# Supabase Auth
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Django
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,.localhost,.test

# FCM (Opcional - para notificaciones push)
FCM_PROJECT_ID=your-firebase-project-id
FCM_SA_JSON_B64=base64-encoded-service-account-json

# AWS S3 (Opcional - para archivos estáticos)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-bucket-name
```

### **5. Aplicar Migraciones**
```bash
python manage.py migrate
```

### **6. Crear Super Usuario** (Opcional)
```bash
python manage.py createsuperuser
```

### **7. Iniciar Servidor**
```bash
python manage.py runserver 0.0.0.0:8000
```

El servidor estará disponible en:
- **Localhost**: `http://localhost:8000`
- **Subdominio Norte**: `http://norte.localhost:8000`
- **Subdominio Sur**: `http://sur.localhost:8000`

---

## 🏗️ **Arquitectura**

```
sitwo-project-backend-master/
├── api/                          # App principal
│   ├── models.py                 # Modelos de datos
│   ├── serializers.py            # Serializadores DRF
│   ├── views.py                  # ViewSets y endpoints
│   ├── urls.py                   # Rutas de la API
│   ├── middleware_tenant.py      # Multi-tenant middleware
│   └── notifications_mobile/     # Sistema de notificaciones FCM
├── dental_clinic_backend/        # Configuración Django
│   ├── settings.py               # Configuración principal
│   ├── urls.py                   # URLs principales
│   ├── urlconf_public.py         # URLs super-admin
│   ├── urlconf_tenant.py         # URLs tenant
│   ├── admin_sites.py            # Admin sites personalizados
│   └── middleware_routing.py     # Routing middleware
├── no_show_policies/             # Políticas de no-show
└── tenancy/                      # Utils multi-tenant
```

---

## 🌐 **Subdominios y Multi-Tenancy**

### **¿Cómo funciona?**

1. Cada clínica tiene un **subdominio único** (ej: `norte`, `sur`, `este`)
2. El middleware `TenantMiddleware` detecta el subdominio de la URL
3. Todos los queries se filtran automáticamente por empresa (tenant)
4. Datos completamente aislados entre clínicas

### **URLs Disponibles**

| Tipo | URL | Descripción |
|------|-----|-------------|
| Super-Admin | `http://localhost:8000/admin/` | Panel global de administración |
| Tenant Admin | `http://norte.localhost:8000/admin/` | Panel de Clínica Norte |
| API Tenant | `http://norte.localhost:8000/api/clinic/` | API de Clínica Norte |
| API Pública | `http://localhost:8000/api/tenancy/` | API de gestión de empresas |

---

## 📚 **Documentación para Frontend**

👉 **[FRONTEND_API_GUIDE.md](./FRONTEND_API_GUIDE.md)** - Guía completa de integración con ejemplos de código, endpoints, autenticación y ejemplos en React.

### **Endpoints Principales**

```
GET  /api/clinic/pacientes/           # Listar pacientes
POST /api/clinic/pacientes/           # Crear paciente
GET  /api/clinic/odontologos/         # Listar odontólogos
GET  /api/clinic/consultas/           # Listar consultas
POST /api/clinic/consultas/           # Crear consulta
GET  /api/clinic/horarios/            # Horarios disponibles
GET  /api/clinic/tipos-consulta/      # Tipos de consulta
GET  /api/clinic/historias-clinicas/  # Historial clínico
POST /api/users/register/             # Registro de usuario
POST /api/users/login/                # Login
POST /api/users/logout/               # Logout
```

---

## 🧪 **Datos de Prueba**

### **Empresas Creadas**
- **Norte**: Clínica Dental Norte (`norte`)
- **Sur**: Clínica Dental Sur (`sur`)
- **Este**: Clínica Dental Este (`este`)

### **Usuarios de Ejemplo**

**Clínica Norte:**
- Paciente: Juan Pérez (juan.perez@norte.com)
- Odontólogo: Dr. Pedro Martínez (pedro.martinez@norte.com)
- Recepcionista: Laura Fernández (laura.fernandez@norte.com)

**Clínica Sur:**
- Paciente: Roberto Sánchez (roberto.sanchez@sur.com)
- Odontólogo: Dr. Miguel Vargas (miguel.vargas@sur.com)

**Clínica Este:**
- Paciente: Luis Ramírez (luis.ramirez@este.com)
- Odontólogo: Dra. Isabel Castro (isabel.castro@este.com)

---

## 🔐 **Autenticación**

El sistema usa **autenticación dual**:

1. **Supabase Auth** - Para registro/login inicial
2. **Django Token Auth** - Para acceso a la API

### **Flujo de Autenticación**

```javascript
// 1. Login
POST /api/users/login/
{
  "email": "usuario@example.com",
  "password": "contraseña123"
}

// Respuesta
{
  "token": "django-token-aqui",
  "user": { ... }
}

// 2. Usar token en requests
GET /api/clinic/pacientes/
Authorization: Token django-token-aqui
```

---

## 🛠️ **Desarrollo Local con Subdominios**

### **Opción 1: Acrylic DNS Proxy** (Recomendado para Windows)

1. Instalar [Acrylic DNS Proxy](http://mayakron.altervista.org/support/acrylic/Home.htm)
2. Ejecutar: `.\setup_acrylic.ps1` (como Administrador)
3. Acceder directamente: `http://norte.localhost:8000`

📖 Ver guía completa: [CONFIGURACION_ACRYLIC_DNS.md](./CONFIGURACION_ACRYLIC_DNS.md)

### **Opción 2: Headers HTTP** (Sin configuración DNS)

```javascript
fetch('http://localhost:8000/api/clinic/pacientes/', {
  headers: {
    'X-Tenant-Subdomain': 'norte'  // Simular subdominio
  }
})
```

---

## 📦 **Despliegue en Producción**

### **AWS EC2 + Nginx + Gunicorn**

Ver guías de despliegue:
- [GUIA_DESPLIEGUE_AWS.md](./GUIA_DESPLIEGUE_AWS.md) - Configuración completa de AWS
- [DESPLIEGUE_RAPIDO.md](./DESPLIEGUE_RAPIDO.md) - Pasos rápidos de despliegue

### **Scripts de Despliegue**

```bash
# Deploy completo
./deploy_to_ec2.sh

# Actualizar aplicación
./update_app.sh

# Configurar Route 53 (DNS)
./setup_route53.sh
```

---

## 📊 **Base de Datos**

### **Modelos Principales**

| Modelo | Descripción |
|--------|-------------|
| `Empresa` | Tenant/clínica (multi-tenant) |
| `Usuario` | Usuario base del sistema |
| `Paciente` | Pacientes de la clínica |
| `Odontologo` | Profesionales dentales |
| `Recepcionista` | Personal administrativo |
| `Consulta` | Citas/consultas médicas |
| `Historialclinico` | Historiales médicos |
| `Tratamiento` | Catálogo de tratamientos |
| `Factura` | Facturas y pagos |

### **Migraciones**

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Ver estado
python manage.py showmigrations
```

---

## 🔔 **Notificaciones Push (FCM)**

Sistema de notificaciones automáticas para:
- Recordatorios de citas
- Cambios de estado de consultas
- Políticas de no-show

### **Configuración**

1. Obtener credenciales de Firebase
2. Codificar service account en Base64:
   ```bash
   cat service-account.json | base64 > fcm_credentials.txt
   ```
3. Agregar a `.env`:
   ```env
   FCM_SA_JSON_B64=contenido-del-archivo-base64
   ```

Ver más: `api/notifications_mobile/README.md`

---

## 🧹 **Mantenimiento**

### **Comandos Útiles**

```bash
# Ver logs de bitácora
python manage.py shell -c "from api.models import Bitacora; [print(b) for b in Bitacora.objects.all()[:10]]"

# Limpiar sesiones expiradas
python manage.py clearsessions

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Ver rutas disponibles
python manage.py show_urls
```

---

## 📝 **Estructura de Archivos Importante**

```
.
├── FRONTEND_API_GUIDE.md          # 📘 Guía para frontend (LEER PRIMERO)
├── CONFIGURACION_ACRYLIC_DNS.md   # Configuración DNS local
├── GUIA_DESPLIEGUE_AWS.md         # Despliegue en AWS
├── manage.py                       # Comando Django
├── requirements.txt                # Dependencias Python
├── .env.example                    # Ejemplo de variables de entorno
└── setup_acrylic.ps1               # Script de configuración DNS
```

---

## 🤝 **Contribuir**

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/NuevaCaracteristica`)
3. Commit cambios (`git commit -m 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Abrir Pull Request

---

## 📄 **Licencia**

Este proyecto es privado y propietario.

---

## 📞 **Soporte**

Para problemas técnicos o consultas:
- Revisar la documentación en `FRONTEND_API_GUIDE.md`
- Consultar logs del servidor: `python manage.py runserver`
- Revisar modelos en `api/models.py`

---

**Última Actualización**: Octubre 15, 2025
