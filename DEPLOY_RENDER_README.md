# 🚀 Guía Rápida de Despliegue en Render

## Dominio: clinicadentalservices.shop

---

## ✅ PASO 1: Crear Web Service en Render

1. Ve a https://render.com
2. Conecta con GitHub → Autoriza repositorio
3. New+ → Web Service
4. Selecciona: **Paul-11-Riffa/ClinicaDental-backend**

### Configuración Inicial:
```
Name: dental-clinic-backend
Region: Oregon (US West)
Branch: Realizar-pagos
Runtime: Python 3
Build Command: ./build.sh
Start Command: gunicorn dental_clinic_backend.wsgi:application
Instance Type: FREE  ⬅️ Comenzar gratis
```

5. Click "Create Web Service" → Esperar 5-10 min

---

## ✅ PASO 2: Configurar Variables de Entorno

En Render Dashboard → Environment → Add Environment Variable

⚠️ **IMPORTANTE**: Copia tus valores reales del archivo `DEPLOY_RENDER_GUIDE.txt` (local)

### Variables Esenciales:
```bash
DJANGO_SECRET_KEY=<generar-nuevo-en-render>  # Click "Generate"
DEBUG=False
PYTHON_VERSION=3.11.0
```

### Base de Datos (Neon - ya tienes):
```bash
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=<tu_password>
DB_HOST=<tu_host>.aws.neon.tech
DB_PORT=5432
```

### AWS, Stripe, FCM, OpenAI:
Ver archivo `DEPLOY_RENDER_GUIDE.txt` local para valores completos

---

## ✅ PASO 3: Upgrade a Standard ($7/mes)

En Render:
1. Settings → Instance Type
2. Change → **Standard** ($7/mes)
3. Save

**Beneficios**:
- Sin sleep después de inactividad
- 512 MB RAM
- Deploy más rápido

---

## ✅ PASO 4: Configurar Custom Domain

En Render → Settings → Custom Domains:

### Agregar dominios:
```
1. api.clinicadentalservices.shop
2. clinicadentalservices.shop
3. www.clinicadentalservices.shop
```

Render te dará valor CNAME: `dental-clinic-backend.onrender.com`

---

## ✅ PASO 5: Configurar DNS en Namecheap

Ve a Namecheap → Domain List → clinicadentalservices.shop → Advanced DNS

### Agregar estos registros:

**Record 1 - API Subdomain:**
```
Type: CNAME
Host: api
Value: dental-clinic-backend.onrender.com
TTL: Automatic
```

**Record 2 - Root Domain:**
```
Type: CNAME (flattening) o URL Redirect
Host: @
Value: dental-clinic-backend.onrender.com
TTL: Automatic
```

**Record 3 - WWW:**
```
Type: CNAME
Host: www
Value: dental-clinic-backend.onrender.com
TTL: Automatic
```

Save All Changes

---

## ✅ PASO 6: Verificar Propagación DNS

- **Tiempo**: 5 minutos a 48 horas
- **Verificar en**: https://dnschecker.org
- **Buscar**: api.clinicadentalservices.shop
- **Debe mostrar**: dental-clinic-backend.onrender.com

---

## ✅ PASO 7: SSL Automático

Render auto-provisiona SSL Let's Encrypt cuando DNS propaga.

**URLs finales**:
```
https://api.clinicadentalservices.shop/api/
https://api.clinicadentalservices.shop/admin/
```

---

## 🧪 Probar la API

```bash
# Health check
curl https://api.clinicadentalservices.shop/api/

# Admin
https://api.clinicadentalservices.shop/admin/
```

---

## 💰 Costos Mensuales

| Servicio | Costo |
|----------|-------|
| Render Standard | $7/mes |
| Neon PostgreSQL | $0/mes (free tier) |
| Dominio Namecheap | ~$10/año |
| **TOTAL** | **$7/mes** |

---

## 📝 Comandos Útiles Post-Deploy

### Ver Logs:
Render Dashboard → Logs tab

### Ejecutar Migraciones:
Render Dashboard → Shell tab:
```bash
python manage.py migrate
```

### Crear Superusuario:
```bash
python manage.py createsuperuser
```

---

## ⚠️ Troubleshooting

### Error 502:
- Revisar logs en Render
- Verificar que build.sh terminó exitoso

### CSS no aparece en /admin:
```bash
python manage.py collectstatic --no-input
```

### CORS errors:
- Verificar CORS_ALLOWED_ORIGINS en settings.py incluye tu dominio

### Domain not working:
- Esperar propagación DNS (hasta 48h)
- Verificar CNAME en dnschecker.org

---

## 📚 Documentación Completa

Ver archivo local: `DEPLOY_RENDER_GUIDE.txt` (contiene credenciales - NO subir a GitHub)

---

## ✅ ¡Listo!

Tu API estará disponible en:
**https://api.clinicadentalservices.shop**

🎉 ¡Deployment completado!
