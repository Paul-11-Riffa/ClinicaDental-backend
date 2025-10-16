# 📋 Project Summary - Multi-Tenant Dental Clinic SaaS

## 📖 Overview

Sistema SaaS multi-tenant para gestión de clínicas dentales con aislamiento completo de datos por subdominio.

---

## 🏗️ Architecture

### Multi-Tenancy Strategy: **Subdomain-Based**

```
┌─────────────────────────────────────────────┐
│         Client Request with Subdomain       │
│   norte.notificct.dpdns.org/api/patients/   │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│         TenantMiddleware                    │
│  • Extracts "norte" from subdomain          │
│  • Queries Empresa.objects.get(subdomain)   │
│  • Attaches to request.tenant               │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│      TenantRoutingMiddleware                │
│  • Checks if request.tenant exists          │
│  • Sets URLconf to tenant or public         │
│  • Routes to appropriate admin panel        │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│         ViewSets / Views                    │
│  • queryset.filter(empresa=request.tenant)  │
│  • All queries automatically filtered       │
│  • Data isolation guaranteed                │
└─────────────────────────────────────────────┘
```

---

## 🗂️ Database Schema (Simplified)

```sql
-- Master table (shared across all tenants)
Empresa (codempresa, nombre, subdomain, activo, ...)

-- Tenant-scoped tables (all have empresa FK)
Usuario (codusuario, nombre, apellido, empresa_id, ...)
Paciente (codpaciente, codusuario, carnetidentidad, ...)
Odontologo (cododontologo, codusuario, especialidad, ...)
Consulta (codconsulta, paciente_id, odontologo_id, empresa_id, ...)
Multa (codmulta, paciente_id, empresa_id, ...)
BloqueoUsuario (codbloqueousuario, usuario_id, empresa_id, ...)

-- Catalog tables (scoped to empresa)
TipoTratamiento (codtipodetratamiento, nombre, empresa_id, ...)
CanalNotificacion (codcanalnotificacion, nombre, empresa_id, ...)
```

### Key Relationships
- All business models → FK to `Empresa`
- `Paciente` → OneToOne to `Usuario`
- `Odontologo` → OneToOne to `Usuario`
- `Consulta` → FK to `Paciente`, `Odontologo`, `Empresa`

---

## 🔑 Core Components

### 1. Middleware Stack

**TenantMiddleware** (`api/middleware_tenant.py`)
- Resolves tenant from subdomain or `X-Tenant-Subdomain` header
- Priority: Header → Subdomain → None (public access)
- Attaches `Empresa` instance to `request.tenant`

**TenantRoutingMiddleware** (`dental_clinic_backend/middleware_routing.py`)
- Switches URLconf based on tenant presence
- `urlconf_tenant.py` → Tenant-specific URLs (admin + clinic APIs)
- `urlconf_public.py` → Public URLs (tenancy APIs + super admin)

### 2. Admin Sites

**PublicAdminSite** (`dental_clinic_backend/admin_sites.py`)
- Accessed via `localhost:8000/admin/`
- Manages: Empresa, global users, system config
- Super-admin only

**TenantAdminSite** (`dental_clinic_backend/admin_sites.py`)
- Accessed via `norte.localhost:8000/admin/`
- Manages: Patients, appointments, clinic users
- Automatically filters by `request.tenant`
- Clinic admin level

### 3. Authentication Flow

```
Frontend → Supabase Auth → Django API
         (email/password)   (token validation)

1. POST /api/auth/register/
   → Creates Supabase user
   → Creates Django Usuario
   → Returns JWT access_token

2. POST /api/auth/login/
   → Validates with Supabase
   → Returns session + user data

3. Subsequent requests:
   Authorization: Bearer {access_token}
```

### 4. Notification System

**FCM Integration** (`api/notifications_mobile/`)

```python
# Signal-based triggers
@receiver(post_save, sender=Consulta)
def send_appointment_notification(sender, instance, created, **kwargs):
    if created:
        queue_notification(
            user=instance.paciente.codusuario,
            template="appointment_created",
            data={...}
        )
```

**Queue Processing**:
- Async notification processing
- Device token management
- User preferences respected
- Retry logic for failed sends

### 5. No-Show Policy Engine

**Automated Workflow** (`no_show_policies/`)

```python
# 1. Appointment marked as "No-Show"
consulta.estadoconsulta = EstadoConsulta.objects.get(nombre="No-Show")
consulta.save()

# 2. Signal triggers policy evaluation
→ PoliticaNoShow.objects.filter(
    empresa=consulta.empresa,
    estado_consulta="No-Show",
    activo=True
)

# 3. Actions executed
→ Create Multa (penalty)
→ Check if should block user
→ Send notification
→ Log to Bitacora
```

---

## 🔐 Security & Isolation

### Tenant Isolation Guarantees

1. **Database Level**: All queries filtered by `empresa` FK
2. **Middleware Level**: Request context includes tenant only
3. **Admin Level**: Different admin sites, different permissions
4. **API Level**: ViewSets automatically filter querysets

### Query Pattern (Enforced)

```python
# ✅ CORRECT - Always filtered by tenant
def get_queryset(self):
    return Paciente.objects.filter(empresa=self.request.tenant)

# ❌ WRONG - Cross-tenant data leak
def get_queryset(self):
    return Paciente.objects.all()  # NEVER do this!
```

---

## 📡 API Endpoints Structure

### Public Endpoints (No Tenant Required)
```
GET  /api/tenancy/empresas/           # List all tenants
GET  /api/tenancy/empresas/{subdomain}/  # Tenant details
POST /api/auth/register/              # User registration
POST /api/auth/login/                 # User login
```

### Tenant-Scoped Endpoints (Requires Subdomain)
```
GET    /api/clinic/pacientes/         # List patients (filtered by tenant)
POST   /api/clinic/pacientes/         # Create patient
GET    /api/clinic/consultas/         # List appointments
POST   /api/clinic/consultas/         # Create appointment
GET    /api/clinic/odontologos/       # List dentists
POST   /api/notifications/devices/    # Register FCM token
GET    /api/no-show/multas/           # Get penalties
```

---

## 🚀 Deployment Architecture

### AWS Production Stack

```
┌──────────────────────────────────────────────┐
│         Route 53 (DNS)                       │
│  *.notificct.dpdns.org → EC2 IP              │
└────────────────┬─────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────┐
│         Nginx (Reverse Proxy)                │
│  • SSL termination                           │
│  • Static files serving                      │
│  • Proxy to Gunicorn                         │
└────────────────┬─────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────┐
│         Gunicorn (WSGI Server)               │
│  • Django application                        │
│  • 4 worker processes                        │
└────────────────┬─────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────┐
│      PostgreSQL (Supabase)                   │
│  • Managed database                          │
│  • Automatic backups                         │
└──────────────────────────────────────────────┘
```

---

## 📊 Key Models & Fields

### Empresa (Tenant)
```python
codempresa: AutoField (PK)
nombre: CharField
subdomain: CharField (unique, slug)
activo: BooleanField
direccion: TextField
telefono: CharField
stripe_customer_id: CharField (nullable)
```

### Usuario (Base User)
```python
codusuario: AutoField (PK)
nombre: CharField
apellido: CharField
correoelectronico: EmailField (unique)
telefono: CharField
empresa: ForeignKey(Empresa)
tipodeusuario: ForeignKey(Tipodeusuario)
activo: BooleanField
```

### Paciente (Patient)
```python
codpaciente: AutoField (PK)
codusuario: OneToOneField(Usuario)
carnetidentidad: CharField
fechanacimiento: DateField
direccion: TextField
```

### Consulta (Appointment)
```python
codconsulta: AutoField (PK)
paciente: ForeignKey(Paciente)
odontologo: ForeignKey(Odontologo)
empresa: ForeignKey(Empresa)
fechahora: DateTimeField
motivoconsulta: TextField
estadoconsulta: ForeignKey(EstadoConsulta)
observaciones: TextField
```

---

## 🔔 Notification Templates

**Defined in**: `api/notifications_mobile/taxonomy.py`

```python
NOTIFICATION_TEMPLATES = {
    "appointment_reminder": {
        "title": "Recordatorio de Cita",
        "body": "Tienes una cita en {hours} horas",
        "data": {"type": "reminder", "consulta_id": "..."}
    },
    "appointment_confirmed": {...},
    "appointment_cancelled": {...},
    "no_show_penalty": {...}
}
```

---

## 📝 Audit Trail (Bitácora)

All significant actions are logged:

```python
Bitacora.objects.create(
    empresa=request.tenant,
    usuario=request.user.usuario,
    accion="CREAR_CONSULTA",
    tabla_afectada="consulta",
    detalles=json.dumps({
        "paciente": paciente.nombre,
        "fecha": consulta.fechahora
    })
)
```

**Tracked actions**:
- CRUD on Patients, Appointments, Users
- No-show policy triggers
- Penalty applications
- User blocks/unblocks

---

## 🛠️ Development Tools

### Create Sample Tenant
```python
from api.models import Empresa

Empresa.objects.create(
    nombre="Clínica Prueba",
    subdomain="prueba",
    activo=True
)
```

### Test Tenant Isolation
```bash
# As Norte tenant
curl -H "X-Tenant-Subdomain: norte" \
     http://localhost:8000/api/clinic/pacientes/

# As Sur tenant
curl -H "X-Tenant-Subdomain: sur" \
     http://localhost:8000/api/clinic/pacientes/
     
# Results should be different!
```

---

## 📈 Scalability Considerations

### Current Implementation
- Single PostgreSQL database (Supabase managed)
- Row-level tenant filtering via `empresa` FK
- Shared schema approach

### Future Enhancements
- Database connection pooling (pgBouncer)
- Read replicas for heavy queries
- Caching layer (Redis) for catalog data
- Celery for async tasks (notifications, reports)

---

## 🔗 External Integrations

1. **Supabase**
   - Authentication (email/password)
   - PostgreSQL database hosting
   - Future: Storage for documents

2. **Firebase Cloud Messaging**
   - Push notifications to mobile apps
   - Topic-based messaging per tenant

3. **Stripe** (Prepared, not implemented)
   - Subscription billing per tenant
   - Payment processing

---

## 📚 Documentation Files

- **README.md** - Project overview & quick start
- **API_DOCUMENTATION.md** - Complete API reference for frontend
- **SETUP_DEVELOPMENT.md** - Development environment setup
- **GUIA_DESPLIEGUE_AWS.md** - AWS deployment guide
- **.github/copilot-instructions.md** - AI coding guidelines

---

## ✅ Quality Checklist

Before deployment:
- [ ] All models have `empresa` FK (except Empresa itself)
- [ ] All ViewSets filter by `request.tenant`
- [ ] Bitacora entries created for significant actions
- [ ] FCM notifications respect user preferences
- [ ] No-show policies configured per tenant
- [ ] Environment variables properly set
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] SSL certificates configured (production)

---

**Last Updated**: October 15, 2025  
**Version**: 1.0  
**Django**: 5.2.6 | **Python**: 3.10+
