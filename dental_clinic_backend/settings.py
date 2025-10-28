"""
Django settings for dental_clinic_backend project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

# ... resto de la configuración
# ------------------------------------
# Seguridad / Debug
# ------------------------------------
# IMPORTANTE: Usa variables de entorno en producción
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise Exception("DJANGO_SECRET_KEY no está configurada en .env")

DEBUG = os.environ.get('DEBUG', 'False') == 'True'  # Por defecto False en producción
# ------------------------------------
# Seguridad - Allowed Hosts / CORS / CSRF
# ------------------------------------
ALLOWED_HOSTS = [
    "localhost",
    ".dpdns.org",
    "127.0.0.1",
    "3.137.195.59",
    "18.220.214.178",
    "18.224.189.52",
    ".amazonaws.com",
    "ec2-18-220-214-178.us-east-2.compute.amazonaws.com",
    "notificct.dpdns.org",
    "balancearin-1841542738.us-east-2.elb.amazonaws.com",
    ".localhost",
    ".test",  # Para desarrollo local con subdominios
    ".notificct.dpdns.org",
    # Vercel deployment
    "buy-dental-smile.vercel.app",
    # Desarrollo móvil
    "10.0.2.2",  # Emulador Android
    "10.0.3.2",  # Emulador Android (alternativo)
]

# En desarrollo, permitir también IPs de red local (192.168.*.*)
if DEBUG:
    import socket
    # Obtener IP local automáticamente
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        if local_ip not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(local_ip)
    except:
        pass
    # Permitir rango común de red local
    ALLOWED_HOSTS.extend([
        "192.168.1.1", "192.168.1.2", "192.168.1.3", "192.168.1.4", "192.168.1.5",
        "192.168.0.1", "192.168.0.2", "192.168.0.3", "192.168.0.4", "192.168.0.5",
    ])

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://\w+\.dpdns\.org$",  # Permite https://cualquier-subdominio.dpdns.org
    r"^https://[\w-]+\.notificct\.dpdns\.org$",  # Subdominios de tenants
    r"^https://[\w-]+\.vercel\.app$",  # Vercel deployments
    r"^http://localhost:\d+$",  # Desarrollo local en cualquier puerto
]

# En desarrollo, permitir todos los orígenes (incluyendo subdominios)
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    # En producción, lista específica de orígenes permitidos
    CORS_ALLOWED_ORIGINS = [
        "https://notificct.dpdns.org",  # Dominio público (landing page)
        # Los subdominios de tenants se manejan por el regex de arriba
        "https://norte.notificct.dpdns.org",
        "https://sur.notificct.dpdns.org",
        "https://este.notificct.dpdns.org",
        # Vercel frontend
        "https://buy-dental-smile.vercel.app",
        "https://norte.localhost:5173",
        "http://localhost:5173",
    ]

CORS_ALLOW_CREDENTIALS = True

# Permitir headers personalizados (especialmente x-tenant-subdomain)
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-tenant-subdomain',  # Header personalizado para multi-tenancy
]

CSRF_TRUSTED_ORIGINS = [
    "http://18.220.214.178",
    "https://18.220.214.178",
    "https://ec2-18-220-214-178.us-east-2.compute.amazonaws.com",
    # Multi-tenancy: Permitir subdominios en desarrollo
    "http://localhost:5173",
    "http://*.localhost:5173",
    "http://norte.localhost:5173",
    "http://sur.localhost:5173",
    "http://este.localhost:5173",
    # Multi-tenancy: Permitir subdominios en Django development server
    "http://localhost:8000",
    "http://*.localhost:8000",
    "http://norte.localhost:8000",
    "http://sur.localhost:8000",
    "http://este.localhost:8000",
    # Multi-tenancy: Permitir subdominios en producción
    "https://notificct.dpdns.org",
    "https://*.notificct.dpdns.org",
    "https://*.dpdns.org",
    # Vercel frontend
    "https://buy-dental-smile.vercel.app",
    "https://*.vercel.app",
]

# ------------------------------------
# Apps
# ------------------------------------
INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    'django_filters',
    "rest_framework.authtoken",
    # App principal - contiene todos los modelos
    "api",            # App principal (Empresa, Usuario, Paciente, Consulta, etc)
    "no_show_policies", # Políticas de no-show
    "whitenoise.runserver_nostatic",
    # Apps modularizadas - COMENTADAS TEMPORALMENTE (duplican tablas)
    # "tenancy",          # Gestión de empresas y multi-tenancy
    # "users",            # Usuarios y autenticación
    # "clinic",           # Lógica de clínica dental
    # "notifications",    # Sistema de notificaciones
]

# ------------------------------------
# Middleware
# ------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Health check middleware (debe ir antes de TenantMiddleware)
    "api.middleware_health.HealthCheckMiddleware",
    # Multi-tenancy: Identificar empresa (tenant)
    "api.middleware_tenant.TenantMiddleware",
    # DIAGNÓSTICO TEMPORAL: Verificar tenant en admin
    "api.middleware_admin_diagnostic.AdminTenantDiagnosticMiddleware",
    # Multi-tenancy: Enrutamiento dinámico (después de TenantMiddleware)
    "dental_clinic_backend.middleware_routing.TenantRoutingMiddleware",
    # Auditoría (después de todo)
    # "users.middleware.AuditMiddleware",  # Migrar después
]

ROOT_URLCONF = "dental_clinic_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "dental_clinic_backend.wsgi.application"

# ------------------------------------
# Base de datos (Configuración simplificada para Render + Supabase)
# ------------------------------------

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_SIGNATURE_NAME = 's3v4',
AWS_S3_REGION_NAME = 'us-east-2'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_VERITY = True
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get('DB_NAME'),
        "USER": os.environ.get('DB_USER'),
        "PASSWORD": os.environ.get('DB_PASSWORD'),
        "HOST": os.environ.get('DB_HOST'),
        "PORT": os.environ.get('DB_PORT', '5432'),
        "OPTIONS": {
            "sslmode": "disable" if os.environ.get('DB_HOST') == 'localhost' else "require",
        },
    }
}

# ------------------------------------
# Password validators
# ------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------
# Localización
# ------------------------------------
LANGUAGE_CODE = "es"
TIME_ZONE = "America/La_Paz"
USE_I18N = True
USE_TZ = True

# ------------------------------------
# Archivos estáticos (WhiteNoise)
# ------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = "/media/"  # Corregido: era MEDIA_URLS
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ------------------------------------
# Configuración de Upload de Archivos
# ------------------------------------
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Tipos de archivo permitidos para evidencias
ALLOWED_UPLOAD_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf']
ALLOWED_UPLOAD_MIMETYPES = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'application/pdf'
]

# ------------------------------------
# DRF - CORREGIDO
# ------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    'DEFAULT_THROTTLE_RATES': {
        'notifications': '100/hour',
        'device_registration': '10/day',
        'preference_updates': '50/hour',
        # SP3-T003: Throttling para presupuestos digitales
        'aceptacion_presupuesto': '10/hour',  # Limitar aceptaciones
        'presupuesto_list': '100/hour',  # Limitar consultas de lista
        'presupuesto_anon': '20/day',  # Usuarios anónimos más restrictivo
    }
}

# ------------------------------------
# Otros
# ------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------
# Frontend y Email (para recuperar contraseña)
# ------------------------------------
FRONTEND_URL = "https://buy-dental-smile.vercel.app"
DEFAULT_FROM_EMAIL = "no-reply@clinica.local"

# ------------------------------------
# SaaS Multi-Tenant Configuration
# ------------------------------------
# Dominio base para tenants (sin https://)
SAAS_BASE_DOMAIN = "notificct.dpdns.org"

# URL del sitio público (landing page de ventas)
# Este es el dominio SIN subdominio donde los clientes se registran
SAAS_PUBLIC_URL = f"https://{SAAS_BASE_DOMAIN}"

# Ejemplo de URLs resultantes:
# - Sitio público: https://notificct.dpdns.org
# - Tenant "norte": https://norte.notificct.dpdns.org
# - Tenant "sur": https://sur.notificct.dpdns.org

# ------------------------------------
# Configuración de Email (SMTP)
# ------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.resend.com"  # Cambia esto por tu proveedor de email
EMAIL_PORT = 587
EMAIL_HOST_USER = "apikey"  # Usuario de tu servicio de email
EMAIL_HOST_PASSWORD = ""  # IMPORTANTE: Agrega aquí tu API key de email
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

# ------------------------------------
# CONFIGURACIÓN DE NOTIFICACIONES
# ------------------------------------

# Push Notifications (OneSignal - Opcional)
ONESIGNAL_APP_ID = ""  # Agrega tu OneSignal App ID aquí
ONESIGNAL_REST_API_KEY = ""  # Agrega tu OneSignal REST API Key aquí

# ------------------------------------
# Stripe (Pagos SaaS - Opcional)
# ------------------------------------
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PRICE_ID = os.environ.get('STRIPE_PRICE_ID')

STRIPE_PRICE_AMOUNT = 99  # Precio en USD del plan mensual (solo para mostrar al usuario)
STRIPE_CURRENCY = "usd"  # Moneda
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')  # Agrega tu webhook secret de Stripe
if not all([STRIPE_PUBLIC_KEY, STRIPE_SECRET_KEY, STRIPE_PRICE_ID]):
    raise Exception("Configuración de Stripe incompleta en .env")

# Configuración de notificaciones por email
DEFAULT_REMINDER_HOURS = 24
MAX_NOTIFICATION_RETRIES = 3
NOTIFICATION_RETRY_DELAY = 30

# Información de la clínica para emails
CLINIC_INFO = {
    'name': "Clínica Dental",
    'address': "Santa Cruz, Bolivia",
    'phone': "+591 XXXXXXXX",
    'email': "info@clinica.com",
    'website': FRONTEND_URL,
}

# Configuración de logging para notificaciones
import os

logs_dir = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Throttling para APIs de notificaciones
REST_FRAMEWORK.update({
    'DEFAULT_THROTTLE_RATES': {
        'notifications': '100/hour',
        'device_registration': '10/day',
        'preference_updates': '50/hour',
    }
})
# Al final de settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',  # Cambiado de WARNING a INFO para ver más logs
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',  # Cambiado de WARNING a INFO
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',  # Agregado para ver peticiones HTTP
            'propagate': False,
        },
        'api': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Logs de tu app
            'propagate': False,
        },
    },
}

# ------------------------------------
# Configuraciones de Seguridad para Producción
# ------------------------------------
if not DEBUG:
    # HTTPS/SSL Settings
    # IMPORTANTE: SECURE_SSL_REDIRECT deshabilitado para permitir health checks HTTP desde ALB
    # El Load Balancer maneja HTTPS, pero hace health checks por HTTP
    SECURE_SSL_REDIRECT = False  # Cambio: Deshabilitado para health checks
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Security Headers
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
