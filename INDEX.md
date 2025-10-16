# 📚 Documentación del Proyecto - Dental Clinic SaaS

> Sistema SaaS multi-tenant para gestión de clínicas dentales con Django REST Framework

---

## 🚀 Inicio Rápido

Para comenzar rápidamente con el proyecto:

1. **[INICIO_RAPIDO.md](INICIO_RAPIDO.md)** - Guía de configuración inicial y primeros pasos
2. **[SETUP_DEVELOPMENT.md](SETUP_DEVELOPMENT.md)** - Configuración completa del entorno de desarrollo

---

## 📖 Documentación Principal

### Arquitectura y Diseño

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Arquitectura del sistema, patrones multi-tenant, estructura de base de datos
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Documentación completa de endpoints REST API

### Integración Frontend

- **[FRONTEND_API_GUIDE.md](FRONTEND_API_GUIDE.md)** - Guía de integración para desarrolladores frontend
- **[GUIA_ROLES_Y_PERMISOS.md](GUIA_ROLES_Y_PERMISOS.md)** - Sistema de roles y permisos (Admin, Odontólogo, Recepcionista, Paciente)

---

## 🎯 Guías por Funcionalidad

### Reportes y Filtros

- **[GUIA_FILTROS_REPORTES_FRONTEND.md](GUIA_FILTROS_REPORTES_FRONTEND.md)**  
  Implementación de filtros en reportes (fechas, odontólogo)
  - Endpoints: `GET /api/reportes/`
  - Parámetros: `fecha_inicio`, `fecha_fin`, `odontologo`

- **[SOLUCION_EXCEL_OBJECT_OBJECT.md](SOLUCION_EXCEL_OBJECT_OBJECT.md)**  
  Solución para exportación a Excel (valores planos vs objetos anidados)
  - Serializer: `ConsultaReporteSerializer`
  - Fix: Campos planos para compatibilidad con Excel

### Historia Clínica

- **[GUIA_HISTORIAS_CLINICAS_FRONTEND.md](GUIA_HISTORIAS_CLINICAS_FRONTEND.md)**  
  Implementación completa de historias clínicas
  - Endpoints: `POST /api/historias-clinicas/`, `GET /api/historias-clinicas/`
  - Componentes: Registro y consulta de historias
  - Código completo TypeScript/React

---

## ☁️ Despliegue

### AWS Deployment

- **[GUIA_DESPLIEGUE_AWS.md](GUIA_DESPLIEGUE_AWS.md)** - Guía completa de despliegue en AWS EC2
- **[DESPLIEGUE_RAPIDO.md](DESPLIEGUE_RAPIDO.md)** - Comandos rápidos para despliegue
- **[INFORME_AWS_ACTUAL.md](INFORME_AWS_ACTUAL.md)** - Estado actual de la infraestructura AWS

### Infraestructura

- **EC2**: Ubuntu con Nginx + Gunicorn
- **Route 53**: Wildcard DNS para multi-tenant (`*.notificct.dpdns.org`)
- **RDS**: PostgreSQL (Supabase)
- **S3**: Archivos estáticos

---

## 🔑 Características Principales

### Multi-Tenancy

- **Isolación por subdominio**: `norte.notificct.dpdns.org`, `sur.notificct.dpdns.org`
- **Middleware**: `TenantMiddleware` resuelve empresa desde subdomain
- **Patrón**: Todas las consultas filtradas por `empresa`

### Autenticación

- **Supabase Auth**: Registro y login de usuarios
- **Django Token Auth**: Acceso a API
- **Dual System**: Integración Supabase + Django

### Roles y Permisos

| Rol | Permisos |
|-----|----------|
| **Admin** | Acceso completo al tenant |
| **Odontólogo** | Gestión de consultas propias |
| **Recepcionista** | Agendar y gestionar citas |
| **Paciente** | Ver sus citas e historias |

### Notificaciones

- **FCM Push**: Notificaciones móviles
- **Queue System**: Procesamiento asíncrono
- **Templates**: Configurables por tipo de evento

---

## 📊 Endpoints Principales

### Consultas

```http
GET    /api/consultas/              # Listar consultas
POST   /api/consultas/              # Crear consulta
PATCH  /api/consultas/{id}/         # Actualizar consulta
GET    /api/consultas/?fecha=hoy    # Filtrar por fecha
```

### Reportes

```http
GET /api/reportes/                                         # Todas las consultas
GET /api/reportes/?fecha_inicio=DD/MM/YYYY&fecha_fin=...  # Con filtros
GET /api/reportes/pacientes/                               # Reporte de pacientes
GET /api/reportes/estadisticas/                            # Estadísticas
```

### Historias Clínicas

```http
POST  /api/historias-clinicas/            # Crear historia
GET   /api/historias-clinicas/            # Listar todas
GET   /api/historias-clinicas/?paciente=1 # Filtrar por paciente
```

### Usuarios y Roles

```http
GET   /api/usuarios/                 # Listar usuarios del tenant
PATCH /api/usuarios/{codigo}/        # Cambiar rol (solo admin)
GET   /api/usuarios/por-roles/?ids=1,3  # Filtrar por tipo de usuario
```

---

## 🛠️ Stack Tecnológico

### Backend

- **Django 5.2.6**: Framework principal
- **Django REST Framework**: API REST
- **PostgreSQL**: Base de datos (Supabase)
- **Gunicorn**: WSGI server
- **Nginx**: Reverse proxy

### Frontend (Recomendado)

- **React + TypeScript**: UI framework
- **Axios**: Cliente HTTP
- **React Router**: Navegación
- **XLSX**: Exportación Excel

### Infraestructura

- **AWS EC2**: Servidor de aplicación
- **AWS Route 53**: DNS management
- **Supabase**: PostgreSQL + Auth
- **Git**: Control de versiones

---

## 🔧 Configuración Rápida

### Variables de Entorno

```bash
# Base de datos (Supabase)
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

### Comandos Esenciales

```bash
# Desarrollo local
python manage.py runserver 0.0.0.0:8000

# Migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Colectar estáticos
python manage.py collectstatic --noinput
```

---

## 📁 Estructura del Proyecto

```
sitwo-project-backend/
├── api/                          # App principal
│   ├── models.py                 # Modelos de datos
│   ├── views.py                  # ViewSets
│   ├── serializers.py            # Serializers
│   ├── middleware_tenant.py      # Multi-tenancy
│   └── notifications_mobile/     # Sistema de notificaciones
├── no_show_policies/             # Políticas de no-show
├── dental_clinic_backend/        # Configuración Django
│   ├── settings.py
│   └── urls.py
├── deploy/                       # Scripts de despliegue
└── docs/                         # Documentación (este directorio)
```

---

## 🐛 Debugging

### Problemas Comunes

1. **Tenant No Resuelto**
   - Verificar subdomain en request
   - Revisar `TenantMiddleware` logs

2. **CORS Errors**
   - Validar subdomain en `CORS_ALLOWED_ORIGIN_REGEXES`

3. **Autenticación Fallida**
   - Verificar token en headers: `Authorization: Token <token>`

4. **Errores de Permisos**
   - Verificar rol del usuario (`idtipousuario`)
   - Revisar función `_es_admin_por_tabla()`

---

## 📞 Soporte y Contacto

- **Repositorio**: [GitHub](https://github.com/herlandt/sitwo-project-backend-master)
- **Servidor Demo**: `https://norte.notificct.dpdns.org`
- **Admin Django**: `/admin/`
- **Tenant Admin**: `/tenant-admin/`

---

## 📝 Notas de Versión

### Última Actualización: Octubre 2025

**Nuevas Funcionalidades:**
- ✅ Sistema de reportes con filtros
- ✅ Exportación a Excel (valores planos)
- ✅ Historias clínicas completas
- ✅ Sistema de roles y permisos mejorado
- ✅ Notificaciones FCM

**Correcciones:**
- ✅ Fix objetos anidados en Excel
- ✅ Filtros de reportes funcionando
- ✅ Permisos multi-tenant
- ✅ CORS configurado correctamente

---

## 📚 Recursos Adicionales

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Supabase Docs](https://supabase.com/docs)
- [AWS EC2 Guide](https://docs.aws.amazon.com/ec2/)

---

**Última actualización:** Octubre 15, 2025  
**Versión del proyecto:** 1.0.0  
**Django:** 5.2.6 | **DRF:** 3.14.0 | **Python:** 3.11+
