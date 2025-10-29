# Chatbot Odontológico - Documentación Completa

## 📋 Descripción

Sistema de chatbot inteligente para clínicas dentales que utiliza **OpenAI GPT-4 Turbo** y la **Assistant API**. El chatbot puede:

- ✅ Conversar con pacientes sobre síntomas dentales
- ✅ Evaluar nivel de urgencia (alta, media, baja)
- ✅ Buscar disponibilidad de horarios
- ✅ Agendar citas (pre-consultas para aprobación de recepcionista)
- ✅ Crear pacientes automáticamente si son nuevos
- ✅ Funciona en modo anónimo (sin login requerido)

---

## 🚀 Configuración Inicial

### 1. Obtener API Key de OpenAI

Sigue las instrucciones en `SETUP_OPENAI.md` para:
1. Crear cuenta en OpenAI
2. Obtener tu API key
3. Configurar límites de gasto

### 2. Variables de Entorno

Agrega estas variables a tu archivo `.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXX
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_ASSISTANT_ID=  # Se llenará automáticamente en el primer uso
```

### 3. Instalar Dependencias

El paquete `openai==1.3.7` ya está instalado.

### 4. Crear Tablas en Base de Datos

Las migraciones ya están ejecutadas. Las tablas creadas son:
- `chatbot_conversacionchatbot` - Conversaciones
- `chatbot_mensajechatbot` - Mensajes individuales
- `chatbot_preconsulta` - Pre-consultas (datos recopilados)

---

## 📡 API Endpoints

### Base URL
```
https://{tenant}.notificct.dpdns.org/api/chatbot/
```

### 1. Iniciar Conversación

**POST** `/api/chatbot/chatbot/iniciar/`

```json
// Request (opcional: paciente_id si el usuario está logueado)
{
  "paciente_id": 123  // Opcional
}

// Response
{
  "conversacion_id": 456,
  "thread_id": "thread_abc123",
  "mensaje_bienvenida": "¡Hola! Soy el asistente virtual de Clínica Norte...",
  "estado": "activa"
}
```

**Headers necesarios:**
- `X-Tenant-Subdomain: norte` (para desarrollo local)
- O usar subdomain real: `https://norte.notificct.dpdns.org`

### 2. Enviar Mensaje

**POST** `/api/chatbot/chatbot/mensaje/`

```json
// Request
{
  "conversacion_id": 456,
  "mensaje": "Tengo un dolor de muelas muy fuerte"
}

// Response
{
  "respuesta": "Lamento que tengas dolor de muelas. Para poder ayudarte mejor, ¿podrías describirme más sobre el dolor?",
  "function_call": null,  // o datos de función llamada
  "estado_conversacion": "activa"
}
```

**Ejemplo de respuesta con function_call:**

```json
{
  "respuesta": "He encontrado varios horarios disponibles para el 15 de marzo...",
  "function_call": {
    "function": "buscar_disponibilidad",
    "arguments": {
      "fecha": "2024-03-15"
    }
  },
  "estado_conversacion": "activa"
}
```

### 3. Obtener Conversación

**GET** `/api/chatbot/chatbot/{id}/conversacion/`

```json
// Response
{
  "id": 456,
  "paciente": 123,
  "paciente_nombre": "Juan Pérez",
  "empresa": 1,
  "thread_id": "thread_abc123",
  "assistant_id": "asst_xyz789",
  "estado": "activa",
  "created_at": "2024-03-10T10:00:00Z",
  "updated_at": "2024-03-10T10:15:00Z",
  "closed_at": null,
  "mensajes": [
    {
      "id": 1,
      "role": "assistant",
      "contenido": "¡Hola! Soy el asistente...",
      "metadata": null,
      "created_at": "2024-03-10T10:00:00Z"
    },
    {
      "id": 2,
      "role": "user",
      "contenido": "Tengo dolor de muelas",
      "metadata": null,
      "created_at": "2024-03-10T10:05:00Z"
    }
  ]
}
```

### 4. Listar Conversaciones

**GET** `/api/chatbot/chatbot/historial/`

**Query params:**
- `paciente_id` - Filtrar por paciente
- `estado` - Filtrar por estado (activa, cerrada, cita_agendada, derivada_humano)

```json
// Response
[
  {
    "id": 456,
    "estado": "cita_agendada",
    "created_at": "2024-03-10T10:00:00Z",
    // ... más campos
  }
]
```

### 5. Cerrar Conversación

**POST** `/api/chatbot/chatbot/{id}/cerrar/`

```json
// Response
{
  "mensaje": "Conversación cerrada",
  "estado": "cerrada"
}
```

---

## 🏥 Gestión de Pre-Consultas (Recepcionista)

### 6. Listar Pre-Consultas

**GET** `/api/chatbot/pre-consultas/`

**Query params:**
- `procesada=false` - Solo pendientes
- `urgencia=alta` - Filtrar por urgencia

**Requiere:** Token de autenticación

```json
// Response
[
  {
    "id": 789,
    "conversacion_id": 456,
    "consulta_id": null,
    "paciente_nombre": null,  // Conversación anónima
    "empresa_nombre": "Clínica Norte",
    "nombre": "María García",
    "edad": 28,
    "telefono": "70123456",
    "email": "maria@example.com",
    "sintomas": "Dolor de muelas intenso en el lado derecho",
    "dolor_nivel": 8,
    "alergias": "Penicilina",
    "condiciones_medicas": "",
    "urgencia": "alta",
    "fecha_preferida": "2024-03-15",
    "horario_preferido": "10:30",
    "procesada": false,
    "notas_recepcion": "",
    "created_at": "2024-03-10T10:00:00Z",
    "dias_desde_solicitud": 0
  }
]
```

### 7. Procesar Pre-Consulta (Crear Cita Real)

**POST** `/api/chatbot/pre-consultas/procesar/`

**Requiere:** Token de autenticación

```json
// Request
{
  "pre_consulta_id": 789,
  "odontologo_id": 5,
  "fecha": "2024-03-15",
  "hora": "10:30",
  "notas": "Paciente con dolor agudo, prioridad alta"
}

// Response
{
  "mensaje": "Pre-consulta procesada exitosamente",
  "consulta_id": 1024,
  "paciente_id": 567  // ID del paciente creado o existente
}
```

**Proceso automático:**
1. Si la conversación no tiene paciente vinculado, se crea automáticamente
2. Se crea el `Usuario` con rol 'paciente'
3. Se crea el `Paciente` con los datos recopilados
4. Se crea la `Consulta` en estado "Agendada"
5. Se marca la pre-consulta como `procesada=True`

### 8. Estadísticas del Chatbot

**GET** `/api/chatbot/pre-consultas/estadisticas/`

**Requiere:** Token de autenticación

```json
// Response
{
  "total_conversaciones": 150,
  "conversaciones_activas": 12,
  "conversaciones_cerradas": 120,
  "citas_agendadas": 18,
  "pre_consultas_pendientes": 8,
  "pre_consultas_procesadas": 10,
  "urgencia_alta": 3,
  "urgencia_media": 10,
  "urgencia_baja": 5,
  "promedio_mensajes_por_conversacion": 6.5
}
```

---

## 🤖 Funciones del Asistente (Function Calling)

El asistente tiene dos funciones definidas:

### 1. buscar_disponibilidad

**Descripción:** Busca horarios disponibles para agendar citas

**Parámetros:**
- `fecha` (requerido): Fecha en formato YYYY-MM-DD
- `odontologo_id` (opcional): ID del odontólogo

**Ejemplo de respuesta:**
```json
{
  "fecha": "2024-03-15",
  "horarios_disponibles": [
    "08:00", "08:30", "09:00", "09:30", "10:00"
  ],
  "odontologos": [
    {"id": 5, "nombre": "Dr. Juan Pérez"},
    {"id": 7, "nombre": "Dra. Ana López"}
  ]
}
```

### 2. agendar_cita

**Descripción:** Crea una pre-consulta con los datos del paciente

**Parámetros:**
- `nombre` (requerido): Nombre completo
- `telefono` (requerido): Teléfono de contacto
- `email` (opcional): Email del paciente
- `fecha` (requerido): Fecha deseada YYYY-MM-DD
- `hora` (requerido): Hora deseada HH:MM
- `motivo` (requerido): Motivo de consulta
- `odontologo_id` (opcional): ID del odontólogo

**Ejemplo de respuesta:**
```json
{
  "success": true,
  "mensaje": "Hemos registrado tu solicitud de cita para el 2024-03-15 a las 10:30. Un miembro de nuestro equipo te contactará pronto al 70123456 para confirmar tu cita. ¡Gracias!"
}
```

---

## 💡 Flujo de Uso Completo

### Frontend (Paciente)

```javascript
// 1. Iniciar conversación
const response = await fetch('https://norte.notificct.dpdns.org/api/chatbot/chatbot/iniciar/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({})  // Anónimo
});

const { conversacion_id, mensaje_bienvenida } = await response.json();

// 2. Enviar mensajes
const chatResponse = await fetch('https://norte.notificct.dpdns.org/api/chatbot/chatbot/mensaje/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    conversacion_id: conversacion_id,
    mensaje: userInput
  })
});

const { respuesta } = await chatResponse.json();
// Mostrar respuesta en UI
```

### Frontend (Recepcionista)

```javascript
// 1. Obtener pre-consultas pendientes
const response = await fetch('https://norte.notificct.dpdns.org/api/chatbot/pre-consultas/?procesada=false', {
  headers: {
    'Authorization': `Token ${userToken}`
  }
});

const preConsultas = await response.json();

// 2. Procesar una pre-consulta
const procesarResponse = await fetch('https://norte.notificct.dpdns.org/api/chatbot/pre-consultas/procesar/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${userToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    pre_consulta_id: preConsulta.id,
    odontologo_id: selectedDoctor.id,
    fecha: selectedDate,
    hora: selectedTime,
    notas: "Paciente urgente"
  })
});
```

---

## 🔧 Configuración del Asistente

### Primera Ejecución

La primera vez que se use el chatbot, se creará automáticamente un asistente en OpenAI. El sistema mostrará:

```
✅ Asistente creado con ID: asst_abc123xyz
⚠️ IMPORTANTE: Agrega este ID a tu archivo .env:
OPENAI_ASSISTANT_ID=asst_abc123xyz
```

**Agrégalo al .env** para evitar crear asistentes duplicados.

### Personalizar el Asistente

En `settings.py` puedes modificar:

```python
OPENAI_ASSISTANT_NAME = "Asistente Dental"
OPENAI_ASSISTANT_INSTRUCTIONS = """
Eres un asistente virtual de una clínica dental...
[Personaliza las instrucciones aquí]
"""
```

---

## 📊 Modelos de Base de Datos

### ConversacionChatbot
- `id` - ID único
- `paciente` - FK a Paciente (nullable)
- `empresa` - FK a Empresa (tenant)
- `thread_id` - ID del thread en OpenAI
- `assistant_id` - ID del asistente
- `estado` - activa, cerrada, cita_agendada, derivada_humano
- `created_at`, `updated_at`, `closed_at`

### MensajeChatbot
- `id` - ID único
- `conversacion` - FK a ConversacionChatbot
- `role` - user, assistant, system
- `contenido` - Texto del mensaje
- `metadata` - JSON (para function calls)
- `created_at`

### PreConsulta
- `id` - ID único
- `conversacion` - OneToOne con ConversacionChatbot
- `consulta` - FK a Consulta (nullable, se llena al procesar)
- `nombre`, `edad`, `telefono`, `email` - Datos del paciente
- `sintomas`, `dolor_nivel`, `alergias`, `condiciones_medicas`
- `urgencia` - alta, media, baja
- `fecha_preferida`, `horario_preferido`
- `procesada` - Boolean
- `notas_recepcion` - Notas de la recepcionista
- `created_at`

---

## 🧪 Testing

### Test Manual con cURL

```bash
# 1. Iniciar conversación
curl -X POST https://norte.notificct.dpdns.org/api/chatbot/chatbot/iniciar/ \
  -H "Content-Type: application/json" \
  -d '{}'

# 2. Enviar mensaje
curl -X POST https://norte.notificct.dpdns.org/api/chatbot/chatbot/mensaje/ \
  -H "Content-Type: application/json" \
  -d '{
    "conversacion_id": 1,
    "mensaje": "Tengo dolor de muelas"
  }'
```

### Test con Python

```python
import requests

BASE_URL = "https://norte.notificct.dpdns.org/api/chatbot"

# Iniciar conversación
response = requests.post(f"{BASE_URL}/chatbot/iniciar/")
data = response.json()
conversacion_id = data['conversacion_id']

# Enviar mensaje
response = requests.post(
    f"{BASE_URL}/chatbot/mensaje/",
    json={
        "conversacion_id": conversacion_id,
        "mensaje": "Tengo dolor de muelas"
    }
)
print(response.json()['respuesta'])
```

---

## 💰 Costos Estimados

### OpenAI GPT-4 Turbo Pricing

- **Input**: ~$0.01 por 1,000 tokens
- **Output**: ~$0.03 por 1,000 tokens

### Estimación para 1,000 conversaciones/mes

- Promedio: 6-8 mensajes por conversación
- ~500 tokens por conversación
- **Costo mensual: $50-100 USD**

**Recomendación:** Configurar límite de $100/mes en OpenAI dashboard

---

## 🔒 Seguridad

### API Key
- ✅ Nunca expongas `OPENAI_API_KEY` en frontend
- ✅ Siempre usa variables de entorno
- ✅ Configura límites de gasto en OpenAI

### Multi-Tenancy
- ✅ Todas las consultas filtran por `empresa`
- ✅ TenantMiddleware resuelve empresa automáticamente
- ✅ Pre-consultas solo visibles para su empresa

### Acceso Anónimo
- ✅ Endpoint `iniciar/` y `mensaje/` son públicos
- ✅ No requieren autenticación (permiten conversaciones anónimas)
- ⚠️ Considera agregar rate limiting en producción

---

## 🐛 Troubleshooting

### Error: "OPENAI_API_KEY no está configurada"

**Solución:** Verifica que el .env tenga la variable y que esté cargada:

```python
from django.conf import settings
print(settings.OPENAI_API_KEY)  # Debe mostrar tu key
```

### Error: "Tiempo de espera agotado"

**Causa:** OpenAI tardó más de 30 segundos en responder

**Solución:** Aumenta el timeout en `services.py`:
```python
def _esperar_respuesta(self, thread_id, run_id, conversacion, timeout=60):
```

### Error: "Function call no implementada"

**Causa:** El asistente llamó a una función que no existe en el código

**Solución:** Verifica que las funciones en `services.py` coincidan con las definidas en `crear_o_obtener_asistente()`

### Conversaciones duplicadas

**Solución:** Siempre guarda el `conversacion_id` en el frontend para reutilizarlo

---

## 📈 Próximas Mejoras

- [ ] Rate limiting para conversaciones anónimas
- [ ] Integración con WhatsApp Business API
- [ ] Dashboard de análisis de conversaciones
- [ ] Training del asistente con datos reales de la clínica
- [ ] Soporte para imágenes (radiografías)
- [ ] Detección de urgencias médicas reales

---

## 📞 Soporte

Para más información, revisa:
- `SETUP_OPENAI.md` - Configuración de OpenAI
- `PLAN_CHATBOT_ODONTOLOGICO.md` - Plan de implementación completo
- OpenAI Docs: https://platform.openai.com/docs/assistants

---

**¡El chatbot está listo para usar! 🎉**

Recuerda:
1. Configurar OPENAI_API_KEY en .env
2. Agregar OPENAI_ASSISTANT_ID después del primer uso
3. Configurar límites de gasto en OpenAI
4. Implementar el frontend para las conversaciones
