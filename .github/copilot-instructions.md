# Dental Clinic SaaS Backend - AI Coding Instructions

## Architecture Overview

This is a **multi-tenant Django REST API** for dental clinic management deployed on AWS EC2. The core tenant isolation is handled through subdomain-based routing with PostgreSQL database filtering.

### Key Components
- **Main App**: `api/` - Core business logic (patients, appointments, odontologists)
- **Multi-tenancy**: `api/middleware_tenant.py` - Resolves `Empresa` (tenant) from subdomain
- **Notifications**: `api/notifications_mobile/` - FCM push notifications with queue system
- **No-Show Policies**: `no_show_policies/` - Automated penalty and blocking system
- **Authentication**: Supabase Auth integration + Django Token auth

## Multi-Tenancy Pattern

**Critical**: All queries must be filtered by `empresa` (tenant). The system uses:

```python
# TenantMiddleware resolves tenant from subdomain
# Example: norte.notificct.dpdns.org → Empresa(subdomain="norte")
request.tenant  # Available in all views after middleware

# Query pattern for tenant isolation
queryset = Model.objects.filter(empresa=request.tenant)
```

### Tenant Resolution Order (TenantMiddleware)
1. `X-Tenant-Subdomain` header (development)
2. Subdomain extraction from domain
3. Fallback: Allow public API access without tenant

## Database Patterns

### Core Models Structure
- `Empresa` - Tenant/client (dental clinic)
- `Usuario` - Base user model (linked to empresa)
- `Paciente`, `Odontologo`, `Recepcionista` - Role-specific models
- `Consulta` - Appointments (core business entity)
- All business models have `empresa` FK for tenant isolation

### Audit Trail Pattern
```python
# Every significant action creates Bitacora entry
from .models import Bitacora
Bitacora.objects.create(
    empresa=request.tenant,
    usuario=request.user.usuario if hasattr(request.user, 'usuario') else None,
    accion="DESCRIPCION_ACCION",
    tabla_afectada="modelo_name",
    detalles="JSON or text details"
)
```

## ViewSet Patterns

### Standard Multi-Tenant ViewSet
```python
class MyViewSet(ModelViewSet):
    def get_queryset(self):
        return MyModel.objects.filter(empresa=self.request.tenant)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.tenant)
```

### EmpresaFromRequestMixin Pattern
Used in `no_show_policies/views.py` - Resolves tenant from multiple sources (headers, params, user).

## Authentication Integration

### Dual Auth System
1. **Supabase Auth** (`api/supabase_client.py`) - User registration/login
2. **Django Token Auth** - API access after Supabase verification

### User Resolution Pattern
```python
# Standard pattern in authenticated views
usuario = getattr(request.user, 'usuario', None)
if not usuario:
    return Response({"error": "Usuario not found"}, status=400)
```

## Notification System

### FCM Integration (`api/notifications_mobile/`)
- Service account based authentication (FCM_SA_JSON_B64)
- Queue-based notification processing
- Template system for notification content
- Device registration and preference management

### Key Files
- `config.py` - Environment configuration with validation
- `queue.py` - Async notification processing
- `signals_consulta.py` - Auto-trigger notifications on appointment changes

## No-Show Policy Engine

### Automated Workflow (`no_show_policies/`)
1. Appointment state change triggers signal
2. `PoliticaNoShow` rules evaluated
3. Actions executed: penalties, blocks, notifications
4. `Multa` (fine) records created automatically

### Key Pattern
```python
# Policies are empresa-specific and estado_consulta-triggered
politicas = PoliticaNoShow.objects.filter(
    empresa=empresa,
    estado_consulta=nuevo_estado,
    activo=True
)
```

## Deployment & Environment

### Key Environment Variables
```bash
# Database (Supabase PostgreSQL)
DB_HOST=your-project.supabase.co
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password

# Supabase Auth
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# FCM Notifications
FCM_PROJECT_ID=your-project-id
FCM_SA_JSON_B64=base64-encoded-service-account-json
```

### AWS Deployment
- EC2 Ubuntu with Nginx + Gunicorn
- Route 53 for wildcard subdomain routing
- S3 for static files
- Scripts in `deploy/` for automated deployment

## Development Commands

```bash
# Local development with tenant simulation
curl -H "X-Tenant-Subdomain: norte" http://localhost:8000/api/consultas/

# Database migrations (important for multi-tenant schema)
python manage.py migrate

# Create test tenant data
python create_sample_data.py

# Run with specific subdomain testing
python manage.py runserver 0.0.0.0:8000
```

## Critical Debugging Points

1. **Tenant Not Resolved**: Check subdomain format and `TenantMiddleware` logs
2. **CORS Issues**: Verify subdomain in `CORS_ALLOWED_ORIGIN_REGEXES`
3. **FCM Failures**: Validate service account JSON and project ID
4. **No-Show Policies Not Triggering**: Check `signals_consulta.py` connections

## Code Review Checklist

- [ ] All queries filtered by `empresa=request.tenant`
- [ ] Audit trail (`Bitacora`) created for significant actions
- [ ] Proper error handling for tenant resolution
- [ ] FCM notification preferences respected
- [ ] No-show policy rules properly configured