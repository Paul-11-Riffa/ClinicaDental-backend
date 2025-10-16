# 🚀 INICIO RÁPIDO - Guía de Pruebas

## ✅ CREDENCIALES LISTAS PARA USAR

### **Clínica Norte** (http://norte.localhost:8000)

**Paciente:**
```
Email: juan.perez@norte.com
Password: norte123
```

**Odontólogo:**
```
Email: pedro.martinez@norte.com
Password: norte123
```

**Recepcionista:**
```
Email: laura.fernandez@norte.com
Password: norte123
```

---

### **Clínica Sur** (http://sur.localhost:8000)

**Paciente:**
```
Email: roberto.sanchez@sur.com
Password: sur123
```

**Odontólogo:**
```
Email: miguel.vargas@sur.com
Password: sur123
```

---

### **Clínica Este** (http://este.localhost:8000)

**Paciente:**
```
Email: luis.ramirez@este.com
Password: este123
```

**Odontóloga:**
```
Email: isabel.castro@este.com
Password: este123
```

---

## 🧪 PRUEBA RÁPIDA

### **1. Iniciar Servidor**
```bash
python manage.py runserver 0.0.0.0:8000
```

### **2. Login (cURL)**
```bash
curl -X POST http://norte.localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"juan.perez@norte.com\",\"password\":\"norte123\"}"
```

### **3. Login (Postman/Thunder Client)**
```
POST http://norte.localhost:8000/api/users/login/

Body (JSON):
{
  "email": "juan.perez@norte.com",
  "password": "norte123"
}
```

### **4. Guardar el Token de la Respuesta**
```json
{
  "token": "abc123...",  ← COPIAR ESTE TOKEN
  "user": {...}
}
```

### **5. Listar Pacientes (usa el token)**
```bash
curl http://norte.localhost:8000/api/clinic/pacientes/ \
  -H "Authorization: Token {TU-TOKEN-AQUI}"
```

---

## 📱 PRUEBA EN NAVEGADOR

1. Abre: http://norte.localhost:8000/admin/
2. Login con: `juan.perez@norte.com` / `norte123`
3. Explora el panel de administración

---

## 📖 DOCUMENTACIÓN COMPLETA

- **FRONTEND_API_GUIDE.md** ← Todos los endpoints y ejemplos
- **CREDENCIALES_PRUEBA.md** ← Lista completa de usuarios
- **README.md** ← Documentación del proyecto

---

## ✅ TODO LISTO

```
✅ 10 usuarios creados con contraseñas
✅ 3 clínicas (Norte, Sur, Este)
✅ Datos de prueba en la base de datos
✅ API funcionando correctamente
✅ Documentación completa
```

**¡Empieza a probar el API ahora mismo!** 🎉
