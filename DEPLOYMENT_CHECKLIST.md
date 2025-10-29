# 🎯 CHECKLIST DESPLIEGUE RENDER - clinicadentalservices.shop

## ✅ PRE-REQUISITOS (YA TIENES)
- [x] Código en GitHub: Paul-11-Riffa/ClinicaDental-backend
- [x] Dominio: clinicadentalservices.shop (Namecheap)
- [x] Base de datos: Neon PostgreSQL configurada

---

## 📋 PASO A PASO

### 1️⃣ CREAR SERVICIO EN RENDER (10 min)

**Ir a**: https://render.com

✅ **Acción**:
1. Sign Up/Login con GitHub
2. Click "New +" → "Web Service"
3. Conectar repo: `Paul-11-Riffa/ClinicaDental-backend`

**Configurar**:
```
Name: dental-clinic-backend
Region: Oregon
Branch: Realizar-pagos
Runtime: Python 3
Build Command: ./build.sh
Start Command: gunicorn dental_clinic_backend.wsgi:application
Plan: FREE ⬅️ (upgrade después)
```

4. Click "Create Web Service"
5. **ESPERAR** 5-10 min (ver logs build)

---

### 2️⃣ CONFIGURAR VARIABLES DE ENTORNO (15 min)

**Ir a**: Settings → Environment

✅ **Acción**: Click "Add Environment Variable" para CADA una:

**IMPORTANTE**: Abrir archivo local `DEPLOY_RENDER_GUIDE.txt` y copiar valores reales

```bash
# Click "Generate" para esta:
DJANGO_SECRET_KEY=<auto-generar>

# Copiar del archivo DEPLOY_RENDER_GUIDE.txt:
DEBUG=False
PYTHON_VERSION=3.11.0
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=...
DB_PORT=5432
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=...
STRIPE_SECRET_KEY=...
STRIPE_PUBLIC_KEY=...
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
OPENAI_ASSISTANT_ID=...
FCM_PROJECT_ID=...
FCM_SA_JSON_B64=...
FRONTEND_URL=https://clinicadentalservices.shop
CLINIC_NAME=Clinica Dental
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

**Total**: ~20 variables

---

### 3️⃣ UPGRADE A STANDARD $7/MES (2 min)

**Ir a**: Settings → Instance Type

✅ **Acción**:
1. Click "Change"
2. Seleccionar **Standard** ($7/month)
3. Click "Save"

**Redeploy automático** → Esperar 3-5 min

---

### 4️⃣ AGREGAR CUSTOM DOMAINS (5 min)

**Ir a**: Settings → Custom Domains

✅ **Acción**: Click "Add Custom Domain" para CADA uno:

**Dominio 1**:
```
Domain: api.clinicadentalservices.shop
```
→ Render muestra: CNAME = `dental-clinic-backend.onrender.com`

**Dominio 2**:
```
Domain: clinicadentalservices.shop
```
→ Render muestra: CNAME = `dental-clinic-backend.onrender.com`

**Dominio 3**:
```
Domain: www.clinicadentalservices.shop
```
→ Render muestra: CNAME = `dental-clinic-backend.onrender.com`

---

### 5️⃣ CONFIGURAR DNS EN NAMECHEAP (10 min)

**Ir a**: https://namecheap.com → Domain List → clinicadentalservices.shop

✅ **Acción**: Advanced DNS → Agregar estos registros:

**Eliminar primero** cualquier registro @ o www existente

**Record 1**:
```
Type: CNAME Record
Host: api
Value: dental-clinic-backend.onrender.com
TTL: Automatic
```

**Record 2**:
```
Type: CNAME Record (o URL Redirect si CNAME no disponible para @)
Host: @
Value: dental-clinic-backend.onrender.com
TTL: Automatic
```

**Record 3**:
```
Type: CNAME Record
Host: www
Value: dental-clinic-backend.onrender.com
TTL: Automatic
```

✅ Click "Save All Changes"

---

### 6️⃣ ESPERAR PROPAGACIÓN DNS (5 min - 48 hrs)

**Verificar en**: https://dnschecker.org

✅ **Buscar**: `api.clinicadentalservices.shop`
✅ **Type**: CNAME
✅ **Debe mostrar**: `dental-clinic-backend.onrender.com`

**Tip**: Usualmente toma 5-30 minutos (no 48 hrs)

---

### 7️⃣ VERIFICAR SSL AUTOMÁTICO (Automático)

Cuando DNS propague, Render auto-provisiona SSL (Let's Encrypt)

✅ **Verificar** en navegador:
```
https://api.clinicadentalservices.shop/api/
```

Debe mostrar 🔒 (candado verde)

---

### 8️⃣ PROBAR LA API (5 min)

✅ **Test 1**: Health check
```bash
curl https://api.clinicadentalservices.shop/api/
```

✅ **Test 2**: Admin
```
https://api.clinicadentalservices.shop/admin/
```

✅ **Test 3**: Crear superuser (Render Shell)
```bash
python manage.py createsuperuser
```

---

## 🎉 ¡COMPLETADO!

### URLs Finales:
```
API: https://api.clinicadentalservices.shop/api/
Admin: https://api.clinicadentalservices.shop/admin/
```

### Costos:
- Render Standard: **$7/mes**
- Neon DB: **$0/mes**
- Total: **$7/mes**

---

## 📞 SIGUIENTE PASO

Conectar frontend a: `https://api.clinicadentalservices.shop`

**Actualizar en frontend**:
```javascript
const API_BASE_URL = 'https://api.clinicadentalservices.shop/api';
```

---

## ⚠️ IMPORTANTE

- ✅ Archivo `DEPLOY_RENDER_GUIDE.txt` tiene credenciales completas (NO subir a GitHub)
- ✅ Este checklist es la guía rápida
- ✅ Si hay errores, ver sección Troubleshooting en `DEPLOY_RENDER_README.md`

---

**Tiempo Total Estimado**: 45-60 minutos + espera DNS

🚀 ¡Buena suerte con el deployment!
