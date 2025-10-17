# 🔐 ACCESO AL PANEL DE ADMINISTRACIÓN DJANGO

## 📍 URL DE ACCESO

```
http://localhost:8000/admin/
```

O con subdominio:
```
http://smilestudio.localhost:8000/admin/
```

---

## 👤 USUARIOS CON ACCESO

Según tu sistema, estos usuarios tienen acceso al admin (is_staff=True):

### 1. **admin**
- Email: `paulriff.prb@gmail.com`
- Contraseña: (la que configuraste al crear el superusuario)

### 2. **rimberty.ramos@gmail.com**
- Es staff (administrador)

### 3. **rimberty.ruben@gmail.com**
- Es staff (administrador)

### 4. **marcohernandez@gmail.com**
- Es staff (odontólogo)

---

## 🚀 SI NO TIENES LA CONTRASEÑA

### Opción 1: Cambiar contraseña desde Django shell

```bash
cd "C:\Disco D\SI 2\ProyectoSi2P\ClinicaDental-backend"
python manage.py shell
```

Dentro del shell:
```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Cambiar contraseña del usuario admin
user = User.objects.get(username='admin')
user.set_password('nueva_contraseña_123')
user.save()

print("✅ Contraseña cambiada para:", user.username)
exit()
```

### Opción 2: Usar script de cambio de contraseña

```bash
python manage.py changepassword admin
```

Te pedirá la nueva contraseña dos veces.

---

## 📊 QUÉ PUEDES HACER EN EL ADMIN

Una vez dentro del panel admin (`/admin/`), puedes:

### ✅ **Gestión de Usuarios**
- Ver/editar usuarios del sistema
- Cambiar roles (Administrador, Paciente, Odontólogo, Recepcionista)
- Activar/desactivar usuarios

### ✅ **Gestión de Empresas**
- Ver todas las empresas registradas
- Editar subdominios
- Activar/desactivar empresas
- Ver suscripciones de Stripe

### ✅ **Gestión de Citas**
- Ver todas las consultas agendadas
- Modificar estados de citas
- Ver historial completo

### ✅ **Gestión de Pacientes**
- Ver todos los pacientes
- Editar información médica
- Ver historial clínico

### ✅ **Gestión de Odontólogos**
- Ver todos los odontólogos
- Editar especialidades
- Gestionar horarios

### ✅ **Tipos de Consulta**
- Crear nuevos tipos
- Editar descripciones
- Establecer precios

### ✅ **Horarios**
- Ver horarios disponibles
- Crear nuevos bloques horarios

### ✅ **Consentimientos**
- Ver consentimientos firmados
- Verificar firmas digitales

### ✅ **Bitácora**
- Ver registro de acciones
- Auditoría del sistema

### ✅ **Reportes**
- Acceder a reportes del sistema

---

## 🔧 CREAR SUPERUSUARIO NUEVO

Si quieres crear un nuevo superusuario:

```bash
python manage.py createsuperuser
```

Te pedirá:
- Username (email)
- Email
- Password (2 veces)

---

## ⚠️ SOLUCIÓN DE PROBLEMAS

### Error: "No such table: django_session"

```bash
python manage.py migrate
```

### Error: "CSRF verification failed"

1. Limpia cookies del navegador
2. Prueba en ventana incógnito
3. Verifica que `CSRF_TRUSTED_ORIGINS` incluya tu URL

### No aparecen modelos en el admin

Verifica que los modelos estén registrados en `api/admin.py`

---

## 📝 EJEMPLO DE USO

1. **Accede al admin:**
   ```
   http://localhost:8000/admin/
   ```

2. **Ingresa credenciales:**
   - Usuario: `admin` (o tu email)
   - Contraseña: (la que configuraste)

3. **Explora las secciones:**
   - API → Usuarios, Pacientes, Odontólogos, Consultas
   - AUTH → Users (usuarios Django)
   - API_EMPRESA → Empresas

---

## 🎯 ACCESO DIRECTO A SECCIONES

Después de loguearte:

- **Usuarios:** `http://localhost:8000/admin/api/usuario/`
- **Pacientes:** `http://localhost:8000/admin/api/paciente/`
- **Odontólogos:** `http://localhost:8000/admin/api/odontologo/`
- **Consultas:** `http://localhost:8000/admin/api/consulta/`
- **Empresas:** `http://localhost:8000/admin/api_empresa/empresa/`
- **Consentimientos:** `http://localhost:8000/admin/api/consentimiento/`

---

## 🔒 SEGURIDAD

**En producción:**
- Cambia todas las contraseñas por defecto
- Usa contraseñas seguras (12+ caracteres)
- Habilita autenticación de dos factores
- Limita acceso por IP si es posible
- Desactiva DEBUG=False
- Configura ALLOWED_HOSTS correctamente

---

✅ **Panel admin listo para usar**
