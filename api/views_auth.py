from typing import Optional
import logging
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.conf import settings
from django.db import transaction, IntegrityError, DatabaseError, connection
from django.utils import timezone
from django.db.models import Q

from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView

from .models import (
    Usuario,
    Paciente,
    Odontologo,
    Recepcionista,
    Bitacora,
    BloqueoUsuario,  # Import del modelo de bloqueo
)
from .serializers import (
    UserNotificationSettingsSerializer,
    UsuarioMeSerializer,
    NotificationPreferencesSerializer,
)
from .serializers_auth import RegisterSerializer

User = get_user_model()

logger = logging.getLogger(__name__)
# ============================
# Utils
# ============================
def _client_ip(request):
    """
    Obtiene la IP del cliente de forma segura detrás de proxies.
    Siempre devuelve un valor (fallback "0.0.0.0") para no romper la bitácora.
    """
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or "0.0.0.0"


def close_db_connection():
    """Cerrar conexión de DB de forma segura"""
    try:
        connection.close()
    except Exception:
        pass


def _resolve_tipodeusuario(idtipousuario: Optional[int]) -> int:
    """Compatibilidad legacy si llegara vacío (default paciente=2)."""
    return idtipousuario if idtipousuario else 2


def _esta_bloqueado_usuario_por_email(email: str, tenant=None) -> tuple[bool, Optional[str]]:
    """
    Retorna (True, mensaje) si el usuario (api.Usuario) tiene un bloqueo vigente en BloqueoUsuario:
      - activo=True
      - fecha_fin nula (bloqueo indefinido) o mayor a ahora.
    Si 'tenant' viene, valida contra ese tenant.
    """
    if not email:
        return False, None

    q = Usuario.objects.filter(correoelectronico__iexact=email)
    if tenant is not None:
        q = q.filter(empresa=tenant)
    usuario = q.first()
    if not usuario:
        return False, None

    ahora = timezone.now()
    bloqueo = (
        BloqueoUsuario.objects.filter(usuario=usuario, activo=True)
        .filter(Q(fecha_fin__isnull=True) | Q(fecha_fin__gt=ahora))
        .order_by("-fecha_inicio")
        .first()
    )
    if bloqueo:
        msg = bloqueo.motivo or (f"Usuario bloqueado hasta {bloqueo.fecha_fin}." if bloqueo.fecha_fin else "Usuario bloqueado.")
        return True, msg
    return False, None


# ============================
# CSRF
# ============================
@api_view(["GET"])
@permission_classes([AllowAny])  # público
@authentication_classes([])  # no exigir sesión
@ensure_csrf_cookie
def csrf_token(request):
    """Siembra cookie CSRF (csrftoken). Útil si luego usas endpoints con sesión/CSRF."""
    return Response({"detail": "CSRF cookie set"}, status=status.HTTP_200_OK)


# ============================
# Registro
# ============================
@api_view(["POST"])
@authentication_classes([])  # público
@permission_classes([AllowAny])  # público
def auth_register(request):
    """
    Registro (NO inicia sesión):
      1) Crea Django User (username=email).
      2) Crea/actualiza fila en 'usuario' (idtipousuario según rol).
      3) Crea subtipo 1-1 según 'rol' (default: paciente).
    """
    try:
        # Pasar el request como contexto al serializer para multi-tenancy
        ser = RegisterSerializer(data=request.data, context={'request': request})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        email = data["email"].lower().strip()
        password = data["password"]
        nombre = (data.get("nombre") or "").strip()
        apellido = (data.get("apellido") or "").strip()
        telefono = (data.get("telefono") or "").strip() or None
        sexo = (data.get("sexo") or "").strip() or None

        rol_subtipo = (data.get("rol") or "paciente").strip().lower()
        idtu = data.get("idtipousuario") or _resolve_tipodeusuario(None)

        carnetidentidad = (data.get("carnetidentidad") or "").strip().upper()
        fechanacimiento = data.get("fechanacimiento")
        direccion = (data.get("direccion") or "").strip()

        with transaction.atomic():
            # 1) auth_user: email único
            try:
                _ = User.objects.get(username=email)
                return Response(
                    {"detail": "Ya existe un usuario con este email"},
                    status=status.HTTP_409_CONFLICT
                )
            except User.DoesNotExist:
                pass  # Correcto, el usuario no existe

            # Crear usuario Django
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=nombre,
                last_name=apellido,
            )

            # Obtener empresa del tenant (multi-tenancy)
            empresa = getattr(request, 'tenant', None)

            # 2) Fila en 'usuario'
            try:
                usuario = Usuario.objects.get(correoelectronico=email)
                # Actualizar datos
                usuario.nombre = nombre
                usuario.apellido = apellido
                usuario.telefono = telefono
                usuario.sexo = sexo
                usuario.idtipousuario_id = idtu
                if empresa:
                    usuario.empresa = empresa
                usuario.save()
            except Usuario.DoesNotExist:
                # Crear nuevo
                usuario = Usuario.objects.create(
                    nombre=nombre,
                    apellido=apellido,
                    correoelectronico=email,
                    telefono=telefono,
                    sexo=sexo,
                    idtipousuario_id=idtu,
                    empresa=empresa,  # Asignar empresa del tenant
                )

            # 3) Crear subtipo
            if rol_subtipo == "paciente":
                try:
                    paciente = Paciente.objects.get(codusuario=usuario)
                    # Actualizar
                    paciente.carnetidentidad = carnetidentidad
                    paciente.fechanacimiento = fechanacimiento
                    paciente.direccion = direccion
                    if empresa:
                        paciente.empresa = empresa
                    paciente.save()
                except Paciente.DoesNotExist:
                    # Crear
                    Paciente.objects.create(
                        codusuario=usuario,
                        carnetidentidad=carnetidentidad,
                        fechanacimiento=fechanacimiento,
                        direccion=direccion,
                        empresa=empresa,  # Asignar empresa del tenant
                    )

        return Response(
            {"detail": "Usuario registrado correctamente"},
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        return Response(
            {"detail": f"Error al registrar usuario: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        close_db_connection()


# ============================
# Login / Logout / User info
# ============================
@csrf_exempt
@api_view(["POST"])
@authentication_classes([])  # público
@permission_classes([AllowAny])  # público
def auth_login(request):
    """
    Login de usuario con manejo robusto de problemas de conexión PostgreSQL
    Devuelve información del usuario y token de autenticación

    Nota: Si existe un BloqueoUsuario ACTIVO y vigente (del tenant actual, si aplica),
    se responde 403 y no se emite token.
    """
    # Log al recibir petición de login
    logger.info(f"🔐 Petición de login recibida - IP: {_client_ip(request)}")
    
    try:
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password")
        
        logger.info(f"📧 Intento de login para: {email}")
        
        if not email or not password:
            logger.warning(f"❌ Login fallido: email o password vacío")
            return Response({"detail": "Email y contraseña son requeridos"}, status=status.HTTP_400_BAD_REQUEST)

        # Cerrar cualquier conexión previa
        close_db_connection()

        # Autenticación básica contra auth_user
        user = authenticate(username=email, password=password)

        if not user:
            logger.warning(f"❌ Credenciales inválidas para: {email}")
            return Response({"detail": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            logger.warning(f"❌ Cuenta desactivada para: {email}")
            return Response({"detail": "Cuenta desactivada"}, status=status.HTTP_401_UNAUTHORIZED)

        logger.info(f"✅ Usuario Django autenticado: {email}")

        # Tenant detectado (si tu middleware lo aporta)
        tenant = getattr(request, 'tenant', None)
        logger.info(f"🏢 Tenant detectado: {tenant.nombre if tenant else 'None'}")

        # Resolver el perfil de dominio y validar pertenencia al tenant ANTES de emitir token
        usuario_query = Usuario.objects.filter(correoelectronico=email)
        if tenant:
            usuario_query = usuario_query.filter(empresa=tenant)
        usuario = usuario_query.first()

        if not usuario:
            logger.warning(f"❌ Usuario no encontrado en BD o no pertenece al tenant: {email}")
            return Response(
                {"detail": "Credenciales inválidas o usuario no pertenece a esta empresa"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        logger.info(f"✅ Usuario encontrado en BD: {usuario.nombre} {usuario.apellido} (código: {usuario.codigo})")

        # BLOQUEO: verifica si existe un BloqueoUsuario vigente (activo y sin fecha_fin o con fecha_fin futura)
        bloqueado, mensaje = _esta_bloqueado_usuario_por_email(email=email, tenant=tenant)
        if bloqueado:
            logger.warning(f"🚫 Usuario bloqueado: {email} - {mensaje}")
            return Response({"detail": mensaje or "Tu cuenta está bloqueada."}, status=status.HTTP_403_FORBIDDEN)

        # Obtener o crear token (recién aquí, tras pasar validaciones)
        token, _ = Token.objects.get_or_create(user=user)
        
        logger.info(f"🎫 Token generado para: {email}")

        # Log de login (tolerante a fallos: jamás rompe el login)
        try:
            Bitacora.objects.create(
                accion='login',
                tabla_afectada='auth_user',
                usuario=usuario,
                empresa=tenant,
                ip_address=_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                valores_nuevos={'email': email, 'metodo': 'manual_login_view', 'nombre': usuario.nombre, 'apellido': usuario.apellido}
            )
        except Exception as log_error:
            # Importante: NO lanzar excepción aquí
            print(f"[Bitacora] No se pudo guardar el log de login: {log_error}")

        # Determinar subtipo
        subtipo = "usuario"
        try:
            if hasattr(usuario, "paciente"):
                subtipo = "paciente"
            elif hasattr(usuario, "odontologo"):
                subtipo = "odontologo"
            elif hasattr(usuario, "recepcionista"):
                subtipo = "recepcionista"
            elif usuario.idtipousuario_id == 1:
                subtipo = "administrador"
        except Exception:
            pass  # Mantener subtipo por defecto

        logger.info(f"✅ Login exitoso para: {email} - Subtipo: {subtipo}")

        return Response({
            "ok": True,
            "message": "Login exitoso",
            "token": token.key,
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
            },
            "usuario": {
                "codigo": usuario.codigo,
                "nombre": usuario.nombre,
                "apellido": usuario.apellido,
                "telefono": usuario.telefono,
                "sexo": usuario.sexo,
                "subtipo": subtipo,
                "idtipousuario": usuario.idtipousuario_id,
                "recibir_notificaciones": usuario.recibir_notificaciones,
            }
        })

    except Exception as e:
        logger.error(f"❌ Error crítico en login: {str(e)}", exc_info=True)
        return Response(
            {"detail": "Error del servidor. Intenta nuevamente."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    finally:
        close_db_connection()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def auth_logout(request):
    """Cerrar sesión - elimina el token del usuario"""
    try:
        if hasattr(request.user, "auth_token"):
            request.user.auth_token.delete()
        return Response({"detail": "Sesión cerrada correctamente"}, status=status.HTTP_200_OK)
    except Exception:
        return Response({"detail": "Error al cerrar sesión"}, status=status.HTTP_400_BAD_REQUEST)
    finally:
        close_db_connection()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def auth_user_info(request):
    """Información del usuario autenticado"""
    try:
        user = request.user

        # Filtrar por tenant si está disponible (multi-tenancy)
        usuario_query = Usuario.objects.filter(correoelectronico=user.email)
        tenant = getattr(request, 'tenant', None)
        if tenant:
            usuario_query = usuario_query.filter(empresa=tenant)

        usuario = usuario_query.first()

        if not usuario:
            return Response(
                {"detail": "Usuario no encontrado o no pertenece a esta empresa"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Determinar subtipo
        subtipo = "usuario"
        try:
            if hasattr(usuario, "paciente"):
                subtipo = "paciente"
            elif hasattr(usuario, "odontologo"):
                subtipo = "odontologo"
            elif hasattr(usuario, "recepcionista"):
                subtipo = "recepcionista"
            elif usuario.idtipousuario_id == 1:
                subtipo = "administrador"
        except Exception:
            pass

        return Response({
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
            },
            "usuario": {
                "codigo": usuario.codigo,
                "nombre": usuario.nombre,
                "apellido": usuario.apellido,
                "telefono": usuario.telefono,
                "sexo": usuario.sexo,
                "subtipo": subtipo,
                "idtipousuario": usuario.idtipousuario_id,
                "recibir_notificaciones": usuario.recibir_notificaciones,
            }
        })
    except Usuario.DoesNotExist:
        return Response({"detail": "Usuario no encontrado en el sistema"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"detail": f"Error obteniendo información del usuario: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        close_db_connection()


# ============================
# Usuario Me (legacy)
# ============================
class UsuarioMeView(APIView):
    """Vista para obtener/actualizar datos del usuario actual"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/usuario/me - Obtener datos del usuario"""

        try:
            user = request.user

            # Filtrar por tenant si está disponible (multi-tenancy)
            usuario_query = Usuario.objects.filter(correoelectronico=user.email)
            tenant = getattr(request, 'tenant', None)
            if tenant:
                usuario_query = usuario_query.filter(empresa=tenant)

            usuario = usuario_query.first()

            if not usuario:
                return Response(
                    {"detail": "Usuario no encontrado o no pertenece a esta empresa"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Serializar
            serializer = UsuarioMeSerializer(usuario)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Usuario.DoesNotExist:
            return Response(
                {"detail": "Usuario no encontrado en sistema local"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": f"Error obteniendo usuario: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            close_db_connection()

    def patch(self, request):
        """PATCH /api/usuario/me - Actualizar datos parciales"""
        try:
            user = request.user

            # Filtrar por tenant si está disponible (multi-tenancy)
            usuario_query = Usuario.objects.filter(correoelectronico=user.email)
            tenant = getattr(request, 'tenant', None)
            if tenant:
                usuario_query = usuario_query.filter(empresa=tenant)

            usuario = usuario_query.first()

            if not usuario:
                return Response(
                    {"detail": "Usuario no encontrado o no pertenece a esta empresa"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Serializar y validar
            serializer = UsuarioMeSerializer(usuario, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Usuario.DoesNotExist:
            return Response(
                {"detail": "Usuario no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": f"Error actualizando usuario: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            close_db_connection()


# ============================
# Reset de contraseña
# ============================
@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_request(request):
    """Solicitar reset de contraseña por email"""
    try:
        email = request.data.get("email", "").strip().lower()
        if not email:
            return Response({"detail": "Email es requerido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            # Generar token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # URL del frontend
            frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
            reset_url = f"{frontend_url}/reset-password/{uid}/{token}/"

            # Enviar email
            subject = "Restablecer contraseña - Clínica Dental"
            html_content = f"""
            <h2>Restablecer contraseña</h2>
            <p>Has solicitado restablecer tu contraseña.</p>
            <p>Haz clic en el siguiente enlace para continuar:</p>
            <a href="{reset_url}">Restablecer contraseña</a>
            <p>Si no solicitaste este cambio, puedes ignorar este email.</p>
            """

            try:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body="Restablecer contraseña",
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@clinica.local"),
                    to=[email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            except Exception as e:
                print(f"Error enviando email: {e}")
                # No fallar si el email no se puede enviar

            return Response({"detail": "Si el email existe, recibirás instrucciones para restablecer tu contraseña"})

        except User.DoesNotExist:
            # No revelar si el email existe o no
            return Response({"detail": "Si el email existe, recibirás instrucciones para restablecer tu contraseña"})

    except Exception as e:
        return Response({"detail": f"Error procesando solicitud: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        close_db_connection()


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """Confirmar reset de contraseña"""
    try:
        uid = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not all([uid, token, new_password]):
            return Response({"detail": "Todos los campos son requeridos"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Decodificar UID
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)

            # Verificar token
            if not default_token_generator.check_token(user, token):
                return Response({"detail": "Token inválido o expirado"}, status=status.HTTP_400_BAD_REQUEST)

            # Cambiar contraseña
            user.set_password(new_password)
            user.save()

            return Response({"detail": "Contraseña restablecida correctamente"})

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"detail": "Token inválido"}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"detail": f"Error restableciendo contraseña: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        close_db_connection()


# ============================
# Configuraciones de usuario
# ============================
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def auth_user_settings_update(request):
    """Obtener/actualizar configuraciones del usuario"""
    try:
        user = request.user

        # Filtrar por tenant si está disponible (multi-tenancy)
        usuario_query = Usuario.objects.filter(correoelectronico=user.email)
        tenant = getattr(request, 'tenant', None)
        if tenant:
            usuario_query = usuario_query.filter(empresa=tenant)

        usuario = usuario_query.first()

        if not usuario:
            return Response(
                {"detail": "Usuario no encontrado o no pertenece a esta empresa"},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method == "GET":
            serializer = UserNotificationSettingsSerializer(usuario)
            return Response(serializer.data)

        elif request.method == "PATCH":
            serializer = UserNotificationSettingsSerializer(usuario, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Usuario.DoesNotExist:
        return Response({"detail": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"detail": f"Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        close_db_connection()


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def notification_preferences(request):
    """Gestionar preferencias de notificaciones"""
    try:
        user = request.user

        # Filtrar por tenant si está disponible (multi-tenancy)
        usuario_query = Usuario.objects.filter(correoelectronico=user.email)
        tenant = getattr(request, 'tenant', None)
        if tenant:
            usuario_query = usuario_query.filter(empresa=tenant)

        usuario = usuario_query.first()

        if not usuario:
            return Response(
                {"detail": "Usuario no encontrado o no pertenece a esta empresa"},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method == "GET":
            serializer = NotificationPreferencesSerializer(usuario)
            return Response(serializer.data)

        elif request.method == "POST":
            serializer = NotificationPreferencesSerializer(usuario, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"detail": "Preferencias actualizadas correctamente"})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Usuario.DoesNotExist:
        return Response({"detail": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"detail": f"Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        close_db_connection()