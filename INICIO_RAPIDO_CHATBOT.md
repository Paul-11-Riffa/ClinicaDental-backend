# 🚀 Guía Rápida - Chatbot Odontológico

## ⚡ Inicio Rápido en 5 Pasos

### 1️⃣ Obtener API Key de OpenAI (5 minutos)

1. Ve a https://platform.openai.com/signup
2. Crea una cuenta (o inicia sesión)
3. Ve a **API Keys** → **Create new secret key**
4. Copia la key (comienza con `sk-proj-...`)
5. ⚠️ **GUÁRDALA** - solo se muestra una vez

### 2️⃣ Configurar Variables de Entorno (1 minuto)

Agrega estas líneas a tu archivo `.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_ASSISTANT_ID=
```

### 3️⃣ Configurar Límite de Gasto (2 minutos)

1. Ve a https://platform.openai.com/account/billing/limits
2. Configura **Monthly budget**: $100
3. Agrega un método de pago
4. Activa alertas de email al 75% y 90%

### 4️⃣ Verificar Instalación (1 minuto)

Ejecuta:

```bash
python test_openai_config.py
```

**Resultado esperado:**
```
✅ API Key encontrada
✅ Modelo configurado: gpt-4-turbo-preview
✅ Cliente OpenAI inicializado correctamente
✅ Asistente creado: asst_XXXXXXXXXX
```

**⚠️ IMPORTANTE:** Si el script te muestra un `OPENAI_ASSISTANT_ID`, cópialo y pégalo en el `.env`

### 5️⃣ Probar el Chatbot (2 minutos)

**Opción A: Con cURL**

```bash
# 1. Iniciar conversación
curl -X POST http://localhost:8000/api/chatbot/chatbot/iniciar/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Subdomain: norte" \
  -d '{}'

# Respuesta:
# {
#   "conversacion_id": 1,
#   "mensaje_bienvenida": "¡Hola! Soy el asistente..."
# }

# 2. Enviar mensaje
curl -X POST http://localhost:8000/api/chatbot/chatbot/mensaje/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Subdomain: norte" \
  -d '{
    "conversacion_id": 1,
    "mensaje": "Hola, tengo dolor de muelas"
  }'
```

**Opción B: Con Postman**

1. Importa esta colección:

```json
{
  "info": {
    "name": "Chatbot Dental",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Iniciar Conversación",
      "request": {
        "method": "POST",
        "header": [
          {"key": "Content-Type", "value": "application/json"},
          {"key": "X-Tenant-Subdomain", "value": "norte"}
        ],
        "url": "http://localhost:8000/api/chatbot/chatbot/iniciar/",
        "body": {
          "mode": "raw",
          "raw": "{}"
        }
      }
    },
    {
      "name": "Enviar Mensaje",
      "request": {
        "method": "POST",
        "header": [
          {"key": "Content-Type", "value": "application/json"},
          {"key": "X-Tenant-Subdomain", "value": "norte"}
        ],
        "url": "http://localhost:8000/api/chatbot/chatbot/mensaje/",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"conversacion_id\": 1,\n  \"mensaje\": \"Tengo dolor de muelas\"\n}"
        }
      }
    }
  ]
}
```

---

## 🎨 Implementación del Frontend

### Widget de Chat Básico (React)

```jsx
import React, { useState, useEffect } from 'react';

function ChatbotWidget() {
  const [conversacionId, setConversacionId] = useState(null);
  const [mensajes, setMensajes] = useState([]);
  const [inputMensaje, setInputMensaje] = useState('');
  const [cargando, setCargando] = useState(false);

  const BASE_URL = 'https://norte.notificct.dpdns.org/api/chatbot';

  // Iniciar conversación al montar el componente
  useEffect(() => {
    iniciarConversacion();
  }, []);

  const iniciarConversacion = async () => {
    const response = await fetch(`${BASE_URL}/chatbot/iniciar/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    
    const data = await response.json();
    setConversacionId(data.conversacion_id);
    
    setMensajes([{
      role: 'assistant',
      contenido: data.mensaje_bienvenida
    }]);
  };

  const enviarMensaje = async () => {
    if (!inputMensaje.trim()) return;

    // Agregar mensaje del usuario a la UI
    const nuevoMensajeUsuario = {
      role: 'user',
      contenido: inputMensaje
    };
    setMensajes([...mensajes, nuevoMensajeUsuario]);
    setInputMensaje('');
    setCargando(true);

    // Enviar a la API
    const response = await fetch(`${BASE_URL}/chatbot/mensaje/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversacion_id: conversacionId,
        mensaje: inputMensaje
      })
    });

    const data = await response.json();
    
    // Agregar respuesta del asistente
    setMensajes(prev => [...prev, {
      role: 'assistant',
      contenido: data.respuesta
    }]);
    
    setCargando(false);
  };

  return (
    <div className="chatbot-widget">
      <div className="mensajes-container">
        {mensajes.map((msg, idx) => (
          <div key={idx} className={`mensaje ${msg.role}`}>
            <p>{msg.contenido}</p>
          </div>
        ))}
        {cargando && <div className="cargando">Escribiendo...</div>}
      </div>
      
      <div className="input-container">
        <input
          type="text"
          value={inputMensaje}
          onChange={(e) => setInputMensaje(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && enviarMensaje()}
          placeholder="Escribe tu mensaje..."
        />
        <button onClick={enviarMensaje}>Enviar</button>
      </div>
    </div>
  );
}

export default ChatbotWidget;
```

### CSS Básico

```css
.chatbot-widget {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 350px;
  height: 500px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
}

.mensajes-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.mensaje {
  margin-bottom: 15px;
  padding: 10px 15px;
  border-radius: 8px;
  max-width: 80%;
}

.mensaje.user {
  background: #007bff;
  color: white;
  margin-left: auto;
}

.mensaje.assistant {
  background: #f1f3f5;
  color: #333;
}

.input-container {
  display: flex;
  padding: 15px;
  border-top: 1px solid #e9ecef;
}

.input-container input {
  flex: 1;
  padding: 10px;
  border: 1px solid #dee2e6;
  border-radius: 5px;
  margin-right: 10px;
}

.input-container button {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.cargando {
  color: #6c757d;
  font-style: italic;
  padding: 10px;
}
```

---

## 📊 Panel de Pre-Consultas (Para Recepcionista)

```jsx
import React, { useState, useEffect } from 'react';

function PanelPreConsultas({ token }) {
  const [preConsultas, setPreConsultas] = useState([]);
  const [odontologos, setOdontologos] = useState([]);
  
  const BASE_URL = 'https://norte.notificct.dpdns.org/api';

  useEffect(() => {
    cargarPreConsultas();
    cargarOdontologos();
  }, []);

  const cargarPreConsultas = async () => {
    const response = await fetch(`${BASE_URL}/chatbot/pre-consultas/?procesada=false`, {
      headers: { 'Authorization': `Token ${token}` }
    });
    const data = await response.json();
    setPreConsultas(data);
  };

  const cargarOdontologos = async () => {
    const response = await fetch(`${BASE_URL}/odontologos/`, {
      headers: { 'Authorization': `Token ${token}` }
    });
    const data = await response.json();
    setOdontologos(data);
  };

  const procesarPreConsulta = async (preConsultaId, fecha, hora, odontologoId) => {
    const response = await fetch(`${BASE_URL}/chatbot/pre-consultas/procesar/`, {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        pre_consulta_id: preConsultaId,
        odontologo_id: odontologoId,
        fecha: fecha,
        hora: hora,
        notas: ''
      })
    });

    if (response.ok) {
      alert('Pre-consulta procesada exitosamente');
      cargarPreConsultas();
    }
  };

  return (
    <div className="panel-preconsultas">
      <h2>Pre-Consultas Pendientes</h2>
      
      {preConsultas.map(pc => (
        <div key={pc.id} className={`preconsulta urgencia-${pc.urgencia}`}>
          <div className="header">
            <h3>{pc.nombre}</h3>
            <span className={`badge urgencia-${pc.urgencia}`}>
              {pc.urgencia.toUpperCase()}
            </span>
          </div>
          
          <div className="datos">
            <p><strong>Teléfono:</strong> {pc.telefono}</p>
            <p><strong>Email:</strong> {pc.email}</p>
            <p><strong>Edad:</strong> {pc.edad}</p>
            <p><strong>Síntomas:</strong> {pc.sintomas}</p>
            {pc.dolor_nivel && <p><strong>Nivel de dolor:</strong> {pc.dolor_nivel}/10</p>}
            <p><strong>Fecha preferida:</strong> {pc.fecha_preferida} {pc.horario_preferido}</p>
          </div>
          
          <button 
            onClick={() => {
              // Aquí abrir modal para seleccionar doctor, fecha, hora
              const odontologo = prompt('ID de odontólogo:');
              const fecha = prompt('Fecha (YYYY-MM-DD):', pc.fecha_preferida);
              const hora = prompt('Hora (HH:MM):', pc.horario_preferido);
              
              if (odontologo && fecha && hora) {
                procesarPreConsulta(pc.id, fecha, hora, parseInt(odontologo));
              }
            }}
            className="btn-procesar"
          >
            Agendar Cita
          </button>
        </div>
      ))}
    </div>
  );
}

export default PanelPreConsultas;
```

---

## 🔍 Troubleshooting Rápido

### ❌ Error: "OPENAI_API_KEY no está configurada"
**Solución:** Verifica que el `.env` tenga la variable y reinicia el servidor Django

### ❌ Error: "No se pudo determinar la empresa/clínica"
**Solución:** Agrega el header `X-Tenant-Subdomain: norte` en tus requests

### ❌ Error: "Tiempo de espera agotado"
**Solución:** OpenAI está tardando mucho. Verifica tu conexión a internet.

### ❌ Chatbot responde en inglés
**Solución:** Modifica las instrucciones en `settings.py` agregando "Siempre responde en español"

---

## 📞 Siguientes Pasos

1. ✅ **Ahora:** Probar el chatbot con Postman o cURL
2. ✅ **Hoy:** Implementar widget básico en frontend
3. ✅ **Esta semana:** Panel de pre-consultas para recepcionistas
4. ✅ **Mes 1:** Training con datos reales de tu clínica

---

## 📚 Documentación Completa

- **Documentación técnica:** `chatbot/README.md`
- **Configuración OpenAI:** `SETUP_OPENAI.md`
- **Resumen completo:** `CHATBOT_IMPLEMENTACION_COMPLETA.md`

---

## 💡 Tips Pro

1. **Guarda el conversacion_id** en localStorage para mantener la conversación
2. **Usa WebSockets** para respuestas en tiempo real (futuro)
3. **Agrega rate limiting** para evitar abuse
4. **Monitorea costos** en el dashboard de OpenAI semanalmente
5. **Personaliza las instrucciones** del asistente según tu clínica

---

🎉 **¡Listo! En menos de 15 minutos deberías tener el chatbot funcionando.**

¿Problemas? Revisa `chatbot/README.md` sección "Troubleshooting"
