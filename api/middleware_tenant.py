from django.http import HttpResponseForbidden
from api.models import Empresa, Usuario
import logging

logger = logging.getLogger(__name__)


class TenantMiddleware:
    """
    Middleware para Multi-Tenancy basado en subdominios.

    Identifica la empresa (tenant) según el subdominio de la petición y:
    1. Resuelve el objeto Empresa desde la BD
    2. Lo almacena en request.tenant
    3. Valida que usuarios autenticados pertenezcan a su empresa
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ==========================================
        # PASO 1: EXCLUIR RUTAS PÚBLICAS PRIMERO
        # ==========================================
        # Estas rutas NO requieren tenant y deben pasar sin validación
        excluded_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/auth/csrf/',
            '/api/health/',
            '/api/db/',
            '/api/auth/logout/',
            '/api/auth/me/',
            '/api/ping/',
            '/api/public/',  # ⭐ CRÍTICO: Rutas públicas de SaaS (registro, Stripe)
        ]
        
        # Si la ruta es pública, saltar toda la lógica de tenant
        if any(request.path.startswith(path) for path in excluded_paths):
            logger.debug(f"[TenantMiddleware] Ruta pública detectada: {request.path} - Saltando validación de tenant")
            request.tenant = None  # Explícitamente sin tenant
            response = self.get_response(request)
            return response

        # ==========================================
        # PASO 2: DETECTAR TENANT POR SUBDOMAIN
        # ==========================================
        domain = request.get_host().split(':')[0].lower()

        # PRIORIDAD 1: Leer header del frontend (desarrollo local)
        subdomain_from_header = request.headers.get('X-Tenant-Subdomain')

        # PRIORIDAD 2: Extraer subdominio del dominio
        parts = domain.split('.')
        
        # Detectar subdominios en diferentes escenarios
        if len(parts) >= 2:
            last_part = parts[-1]
            if last_part in ['localhost', 'test'] and len(parts) == 2:
                subdomain_from_domain = parts[0] if parts[0] not in ['localhost', 'test'] else None
            elif len(parts) > 2:
                subdomain_from_domain = parts[0]
            else:
                subdomain_from_domain = None
        else:
            subdomain_from_domain = None

        # Usar header si está disponible, sino usar domain
        subdomain = subdomain_from_header or subdomain_from_domain

        # Resolver el objeto Empresa desde el subdominio
        tenant_empresa = None
        if subdomain and subdomain not in ['www', 'api']:
            try:
                tenant_empresa = Empresa.objects.get(
                    subdomain__iexact=subdomain,
                    activo=True
                )
                logger.debug(f"[TenantMiddleware] Tenant resuelto: {tenant_empresa.nombre} (subdomain: {subdomain})")
            except Empresa.DoesNotExist:
                logger.warning(f"[TenantMiddleware] Subdominio '{subdomain}' no encontrado o inactivo")
            except Empresa.MultipleObjectsReturned:
                logger.error(f"[TenantMiddleware] Múltiples empresas con subdomain '{subdomain}'")
                tenant_empresa = Empresa.objects.filter(
                    subdomain__iexact=subdomain,
                    activo=True
                ).first()

        # Guardar el tenant en el request
        request.tenant = tenant_empresa

        # ==========================================
        # PASO 3: VALIDAR PERTENENCIA DE USUARIO
        # ==========================================
        if request.user.is_authenticated and tenant_empresa:
            # Superusuarios tienen acceso a todo
            if request.user.is_superuser or request.user.is_staff:
                logger.debug(f"[TenantMiddleware] Superusuario '{request.user.email}' accede sin restricción")
                response = self.get_response(request)
                return response

            # Verificar que el usuario pertenece a esta empresa
            try:
                usuario = Usuario.objects.filter(
                    correoelectronico__iexact=request.user.email,
                    empresa=tenant_empresa
                ).first()

                if not usuario:
                    logger.warning(
                        f"[TenantMiddleware] Acceso denegado: '{request.user.email}' "
                        f"no pertenece a '{tenant_empresa.nombre}'. Path: {request.path}"
                    )

                    usuario_otra_empresa = Usuario.objects.filter(
                        correoelectronico__iexact=request.user.email
                    ).select_related('empresa').first()

                    if usuario_otra_empresa:
                        logger.warning(
                            f"[TenantMiddleware] Usuario pertenece a '{usuario_otra_empresa.empresa.nombre}' "
                            f"(subdomain: {usuario_otra_empresa.empresa.subdomain})"
                        )

                    return HttpResponseForbidden(
                        "Acceso denegado: No tienes permisos para esta empresa. "
                        "Accede a través del subdominio correcto."
                    )
            except Exception as e:
                logger.error(f"[TenantMiddleware] Error verificando pertenencia: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return HttpResponseForbidden("Error de validación de acceso")

        response = self.get_response(request)
        return response
