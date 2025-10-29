# 🔑 SETUP DE OPENAI - PASO A PASO

## 1️⃣ Crear Cuenta en OpenAI

1. Ve a: **https://platform.openai.com/signup**
2. Regístrate con tu email
3. Verifica tu email
4. Completa información de perfil

## 2️⃣ Obtener API Key

1. Inicia sesión en: **https://platform.openai.com/**
2. Click en tu perfil (esquina superior derecha)
3. Click en **"API keys"** o ve a: https://platform.openai.com/api-keys
4. Click en **"Create new secret key"**
5. Dale un nombre: `dental-chatbot-key`
6. **¡IMPORTANTE!** Copia la key inmediatamente (solo se muestra una vez)
7. Guárdala en un lugar seguro

**Ejemplo de API Key:**
```
sk-proj-abc123def456...xyz789
```

## 3️⃣ Agregar Créditos

OpenAI te da **$5 USD gratis** al crear cuenta nueva, pero necesitas agregar método de pago:

1. Ve a: **https://platform.openai.com/account/billing/overview**
2. Click en **"Add payment method"**
3. Agrega tarjeta de crédito
4. **Opcional:** Agrega $10-20 USD iniciales para pruebas

### Configurar Límites de Gasto

**¡MUY IMPORTANTE!** Para evitar gastos inesperados:

1. Ve a: **https://platform.openai.com/account/billing/limits**
2. Configura **Hard limit**: $100 USD/mes (o menos)
3. Configura **Soft limit**: $50 USD/mes
4. Activa **Email notifications** cuando llegues al 75%

## 4️⃣ Agregar API Key al Proyecto

### Editar archivo `.env`

Abre tu archivo `.env` en el proyecto y agrega:

```bash
# OpenAI Chatbot Configuration
OPENAI_API_KEY=sk-proj-TU_KEY_AQUI
OPENAI_ASSISTANT_ID=  # Dejar vacío por ahora, se llenará después
OPENAI_MODEL=gpt-4-turbo-preview
```

### Si no tienes archivo `.env`

Crea uno nuevo en la raíz del proyecto:

```bash
# .env
OPENAI_API_KEY=sk-proj-TU_KEY_AQUI
OPENAI_ASSISTANT_ID=
OPENAI_MODEL=gpt-4-turbo-preview
```

### Agregar al `.gitignore`

**¡CRÍTICO!** Asegúrate que `.env` esté en `.gitignore`:

```bash
# .gitignore
.env
*.env
```

## 5️⃣ Verificar Instalación

Ejecuta este comando en tu terminal de Django:

```bash
pip install openai==1.3.7
```

Luego prueba la conexión:

```python
# test_openai.py
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Prueba simple
response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[
        {"role": "user", "content": "Hola, ¿funcionas?"}
    ]
)

print(response.choices[0].message.content)
```

Ejecuta:
```bash
python test_openai.py
```

Si ves una respuesta del bot, ¡está funcionando! ✅

## 6️⃣ Monitorear Uso

Ve a: **https://platform.openai.com/usage**

Aquí puedes ver:
- Requests realizados
- Tokens consumidos
- Costo acumulado
- Gráficos de uso

## ⚠️ SEGURIDAD

### ❌ NUNCA hagas esto:
- Subir API key a GitHub
- Compartir la key públicamente
- Hardcodear la key en el código

### ✅ SIEMPRE:
- Usar variables de entorno
- Agregar `.env` al `.gitignore`
- Rotar keys cada 3-6 meses
- Configurar límites de gasto

## 📊 Costos Esperados

Para 1000 conversaciones/mes:

| Item | Cantidad | Costo |
|------|----------|-------|
| Input tokens | ~2M | $20 |
| Output tokens | ~1M | $30 |
| **TOTAL** | | **~$50/mes** |

## ✅ Checklist

- [ ] Cuenta OpenAI creada
- [ ] Email verificado
- [ ] API Key obtenida
- [ ] API Key guardada en `.env`
- [ ] Método de pago agregado
- [ ] Límites de gasto configurados ($100 hard limit)
- [ ] Package `openai` instalado
- [ ] Conexión probada con script de prueba
- [ ] `.env` agregado a `.gitignore`

## 🆘 Problemas Comunes

### "Invalid API Key"
- Verifica que copiaste la key completa
- Verifica que empiece con `sk-`
- Regenera la key en la plataforma

### "Insufficient quota"
- Agrega método de pago
- Verifica que tengas créditos disponibles

### "Rate limit exceeded"
- Espera 1 minuto
- Estás enviando muchos requests muy rápido

---

**Siguiente paso:** Una vez completado este setup, continuamos con la creación de la app Django del chatbot.
