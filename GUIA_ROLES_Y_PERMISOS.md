# 📋 Guía Completa de Roles y Permisos - Sistema de Clínica Dental

## 🎯 **Resumen de Roles**

El sistema tiene **4 roles principales** por clínica:

| Rol | ID | Descripción | Usuarios Típicos |
|-----|-----|-------------|------------------|
| **Administrador** | 1 | Gestión completa de la clínica | Dueño, Gerente |
| **Paciente** | 2 | Usuario final que recibe atención | Clientes de la clínica |
| **Odontólogo** | 3 | Profesional que atiende pacientes | Doctores, Dentistas |
| **Recepcionista** | 4 | Personal administrativo | Recepción, Asistente |

---

## 👤 **ROL 1: ADMINISTRADOR**

### ✅ **Permisos Completos**

El Administrador tiene **acceso total** a todas las funcionalidades del sistema:

#### **1. Gestión de Usuarios**
- ✅ Crear nuevos usuarios (pacientes, odontólogos, recepcionistas)
- ✅ Editar información de cualquier usuario
- ✅ Desactivar/activar usuarios
- ✅ Ver lista completa de usuarios
- ✅ Asignar roles y permisos
- ✅ Resetear contraseñas

#### **2. Gestión de Pacientes**
- ✅ Registrar nuevos pacientes
- ✅ Editar datos personales de pacientes
- ✅ Ver lista completa de pacientes
- ✅ Ver historial médico de cualquier paciente
- ✅ Eliminar pacientes (con precaución)

#### **3. Gestión de Citas/Consultas**
- ✅ Agendar citas para cualquier paciente
- ✅ Modificar citas existentes
- ✅ Cancelar citas
- ✅ Ver todas las citas de la clínica
- ✅ Cambiar estados de citas (Pendiente, Confirmada, Completada, Cancelada)
- ✅ Asignar/reasignar odontólogos a citas
- ✅ Ver agenda completa

#### **4. Gestión de Odontólogos**
- ✅ Registrar nuevos odontólogos
- ✅ Editar información profesional
- ✅ Ver horarios y disponibilidad
- ✅ Asignar especialidades

#### **5. Gestión de Tratamientos**
- ✅ Crear planes de tratamiento
- ✅ Modificar precios de servicios
- ✅ Ver todos los tratamientos
- ✅ Gestionar catálogo de servicios

#### **6. Gestión Financiera**
- ✅ Ver facturas y pagos
- ✅ Generar reportes financieros
- ✅ Gestionar descuentos
- ✅ Ver estadísticas de ingresos

#### **7. Reportes y Estadísticas**
- ✅ Ver dashboard con métricas de la clínica
- ✅ Reportes de citas por período
- ✅ Estadísticas de pacientes atendidos
- ✅ Reportes de ingresos
- ✅ Análisis de ocupación de agenda

#### **8. Configuración del Sistema**
- ✅ Configurar horarios de atención
- ✅ Gestionar tipos de consulta
- ✅ Configurar notificaciones
- ✅ Personalizar catálogos (medicamentos, insumos)

### 🔧 **Endpoints Principales**
```
GET/POST/PUT/DELETE /api/clinic/usuarios/
GET/POST/PUT/DELETE /api/clinic/pacientes/
GET/POST/PUT/DELETE /api/clinic/consultas/
GET/POST/PUT/DELETE /api/clinic/odontologos/
GET/POST/PUT/DELETE /api/clinic/recepcionistas/
GET/POST/PUT/DELETE /api/clinic/tratamientos/
GET/POST/PUT/DELETE /api/clinic/facturas/
GET /api/clinic/reportes/*
```

---

## 🦷 **ROL 2: PACIENTE**

### ✅ **Permisos Habilitados**

El Paciente puede **gestionar sus propias citas** y ver su información médica:

#### **1. Gestión de Citas (IMPORTANTE: ✅ PUEDE AGENDAR)**
- ✅ **AGENDAR nuevas citas** (seleccionar odontólogo, fecha, hora, tipo de consulta)
- ✅ Ver sus propias citas (pasadas y futuras)
- ✅ Cancelar sus citas (con anticipación mínima)
- ✅ Ver estados de sus citas
- ✅ Recibir notificaciones de confirmación/recordatorio

#### **2. Visualización de Información Personal**
- ✅ Ver su perfil personal
- ✅ Ver su historial clínico (solo propio)
- ✅ Ver tratamientos recibidos
- ✅ Ver planes de tratamiento activos
- ✅ Ver recetas médicas (solo propias)

#### **3. Gestión de Perfil**
- ✅ Editar datos personales (teléfono, dirección)
- ✅ Cambiar contraseña
- ✅ Configurar preferencias de notificaciones

#### **4. Información de Facturas**
- ✅ Ver sus propias facturas
- ✅ Ver estado de pagos
- ✅ Consultar deuda pendiente

### ❌ **Restricciones**

- ❌ NO puede ver información de otros pacientes
- ❌ NO puede editar su historial clínico (solo lectura)
- ❌ NO puede crear/modificar tratamientos
- ❌ NO puede ver agenda completa de la clínica
- ❌ NO puede gestionar otros usuarios

### 🔧 **Endpoints Principales**
```
POST /api/clinic/consultas/                    # ✅ AGENDAR CITA
GET  /api/clinic/consultas/?codpaciente={id}   # Ver sus citas
DELETE /api/clinic/consultas/{id}/             # Cancelar su cita
GET  /api/clinic/odontologos/                  # Ver lista de odontólogos
GET  /api/clinic/horarios/                     # Ver horarios disponibles
GET  /api/clinic/tipos-consulta/               # Ver tipos de consulta
GET  /api/clinic/historias-clinicas/?pacientecodigo={id}  # Su historial
GET  /api/clinic/pacientes/{id}/               # Su perfil
PUT  /api/clinic/pacientes/{id}/               # Editar su perfil
```

### 📱 **Flujo de Agendamiento para Paciente**

```javascript
// 1. Paciente hace login
POST /api/auth/login/
{ email: "juan.perez@norte.com", password: "norte123" }

// 2. Ver odontólogos disponibles
GET /api/clinic/odontologos/

// 3. Ver horarios disponibles
GET /api/clinic/horarios/

// 4. Ver tipos de consulta
GET /api/clinic/tipos-consulta/

// 5. AGENDAR CITA ✅
POST /api/clinic/consultas/
{
  "fecha": "2025-10-20",
  "codpaciente": 1,              // Su propio ID (auto-asignado)
  "cododontologo": 3,            // Odontólogo seleccionado
  "idhorario": 2,                // 09:00 AM
  "idtipoconsulta": 1,           // Consulta General
  "idestadoconsulta": 1          // Pendiente (confirmación)
}
```

---

## 🩺 **ROL 3: ODONTÓLOGO**

### ✅ **Permisos Habilitados**

El Odontólogo puede **gestionar consultas y registros médicos**:

#### **1. Gestión de Consultas**
- ✅ Ver sus propias citas asignadas
- ✅ Ver detalles de sus consultas
- ✅ Cambiar estado de consulta (En Atención, Completada)
- ✅ Ver agenda personal

#### **2. Gestión Clínica**
- ✅ Ver lista de pacientes de la clínica
- ✅ Ver historial clínico de pacientes
- ✅ **Crear/editar historiales clínicos**
- ✅ Registrar diagnósticos
- ✅ Documentar tratamientos realizados

#### **3. Tratamientos**
- ✅ Crear planes de tratamiento para pacientes
- ✅ Registrar servicios realizados
- ✅ Actualizar odontograma

#### **4. Prescripciones**
- ✅ Crear recetas médicas
- ✅ Prescribir medicamentos
- ✅ Generar indicaciones médicas

### ❌ **Restricciones**

- ❌ NO puede agendar citas (solo recepcionista/admin)
- ❌ NO puede modificar datos personales de pacientes
- ❌ NO puede gestionar usuarios
- ❌ NO puede ver/editar información financiera
- ❌ NO puede eliminar registros

### 🔧 **Endpoints Principales**
```
GET  /api/clinic/consultas/?cododontologo={id}  # Sus consultas
PUT  /api/clinic/consultas/{id}/                # Actualizar estado
GET  /api/clinic/pacientes/                     # Ver pacientes
GET/POST /api/clinic/historias-clinicas/        # Gestionar historiales
POST /api/clinic/plandetratamiento/             # Crear plan tratamiento
POST /api/clinic/recetamedica/                  # Crear receta
```

---

## 📋 **ROL 4: RECEPCIONISTA**

### ✅ **Permisos Habilitados**

La Recepcionista gestiona **agenda y pacientes**:

#### **1. Gestión de Citas (Principal)**
- ✅ **Agendar citas para pacientes**
- ✅ Modificar citas existentes
- ✅ Cancelar citas
- ✅ Confirmar citas
- ✅ Ver agenda completa de la clínica
- ✅ Ver disponibilidad de odontólogos
- ✅ Gestionar lista de espera

#### **2. Gestión de Pacientes**
- ✅ Registrar nuevos pacientes
- ✅ Editar información personal de pacientes
- ✅ Ver lista completa de pacientes
- ✅ Buscar pacientes

#### **3. Información General**
- ✅ Ver horarios de atención
- ✅ Ver odontólogos disponibles
- ✅ Ver tipos de consulta

### ❌ **Restricciones**

- ❌ NO puede ver/editar historiales clínicos
- ❌ NO puede crear planes de tratamiento
- ❌ NO puede gestionar odontólogos
- ❌ NO puede gestionar usuarios del sistema
- ❌ NO puede acceder a reportes financieros

### 🔧 **Endpoints Principales**
```
POST /api/clinic/pacientes/                     # Registrar paciente
GET/PUT /api/clinic/pacientes/                  # Gestionar pacientes
POST /api/clinic/consultas/                     # Agendar cita
GET/PUT/DELETE /api/clinic/consultas/           # Gestionar citas
GET /api/clinic/odontologos/                    # Ver odontólogos
GET /api/clinic/horarios/                       # Ver horarios
```

---

## 🔄 **Matriz de Permisos Detallada**

| Funcionalidad | Admin | Paciente | Odontólogo | Recepcionista |
|--------------|-------|----------|------------|---------------|
| **CITAS** |
| Ver todas las citas | ✅ | ❌ (solo propias) | ❌ (solo asignadas) | ✅ |
| Agendar citas | ✅ | ✅ **SÍ** | ❌ | ✅ |
| Modificar citas | ✅ | ❌ | ❌ | ✅ |
| Cancelar citas | ✅ | ✅ (propias) | ❌ | ✅ |
| Cambiar estado citas | ✅ | ❌ | ✅ (sus citas) | ✅ |
| **PACIENTES** |
| Ver lista pacientes | ✅ | ❌ | ✅ | ✅ |
| Registrar pacientes | ✅ | ❌ | ❌ | ✅ |
| Editar datos pacientes | ✅ | ✅ (solo propio) | ❌ | ✅ |
| Ver historial clínico | ✅ | ✅ (solo propio) | ✅ | ❌ |
| Editar historial clínico | ✅ | ❌ | ✅ | ❌ |
| **TRATAMIENTOS** |
| Crear planes tratamiento | ✅ | ❌ | ✅ | ❌ |
| Ver tratamientos | ✅ | ✅ (solo propios) | ✅ | ❌ |
| **USUARIOS** |
| Gestionar usuarios | ✅ | ❌ | ❌ | ❌ |
| Ver odontólogos | ✅ | ✅ | ✅ | ✅ |
| **FINANZAS** |
| Ver facturas | ✅ | ✅ (solo propias) | ❌ | ❌ |
| Gestionar pagos | ✅ | ❌ | ❌ | ❌ |
| Reportes financieros | ✅ | ❌ | ❌ | ❌ |

---

## 📱 **Flujos de Trabajo por Rol**

### **FLUJO 1: Paciente Agenda una Cita**

```
1. Paciente hace login → Recibe token
2. Ve lista de odontólogos disponibles
3. Selecciona fecha deseada
4. Ve horarios disponibles para esa fecha
5. Selecciona tipo de consulta (General, Limpieza, etc.)
6. Confirma el agendamiento
7. Sistema crea cita con estado "Pendiente"
8. Paciente recibe notificación de confirmación
9. Recepcionista puede confirmar/modificar la cita
```

### **FLUJO 2: Recepcionista Agenda Cita para Paciente**

```
1. Recepcionista hace login
2. Busca/selecciona paciente existente (o registra nuevo)
3. Selecciona odontólogo
4. Elige fecha y horario disponible
5. Selecciona tipo de consulta
6. Crea la cita con estado "Confirmada"
7. Sistema envía notificación al paciente
```

### **FLUJO 3: Odontólogo Atiende Consulta**

```
1. Odontólogo hace login
2. Ve su agenda del día
3. Selecciona consulta en estado "Confirmada"
4. Cambia estado a "En Atención"
5. Ve historial clínico del paciente
6. Registra diagnóstico y tratamiento
7. Actualiza historial clínico
8. Crea plan de tratamiento (si aplica)
9. Genera receta médica (si aplica)
10. Cambia estado a "Completada"
```

### **FLUJO 4: Administrador Gestiona la Clínica**

```
1. Admin hace login
2. Ve dashboard con métricas
3. Gestiona usuarios (crear odontólogo nuevo)
4. Configura horarios de atención
5. Ve reportes de citas del mes
6. Gestiona catálogo de servicios y precios
7. Revisa facturas pendientes
```

---

## 🚀 **Implementación en Frontend**

### **Hook de Permisos (React)**

```typescript
// hooks/usePermissions.ts
export const usePermissions = () => {
  const { userData } = useAuth();
  const rol = userData?.subtipo;
  
  return {
    // Roles
    isAdmin: rol === "administrador",
    isPaciente: rol === "paciente",
    isOdontologo: rol === "odontologo",
    isRecepcionista: rol === "recepcionista",
    
    // Permisos específicos de CITAS
    canAgendarCita: ["administrador", "paciente", "recepcionista"].includes(rol),
    canVerTodasLasCitas: ["administrador", "recepcionista"].includes(rol),
    canModificarCitas: ["administrador", "recepcionista"].includes(rol),
    canCancelarCitaPropia: rol === "paciente",
    
    // Permisos de PACIENTES
    canRegistrarPacientes: ["administrador", "recepcionista"].includes(rol),
    canVerTodosPacientes: ["administrador", "odontologo", "recepcionista"].includes(rol),
    
    // Permisos CLÍNICOS
    canVerHistorialClinico: ["administrador", "odontologo"].includes(rol),
    canEditarHistorialClinico: ["administrador", "odontologo"].includes(rol),
    
    // Permisos ADMINISTRATIVOS
    canGestionarUsuarios: rol === "administrador",
    canVerReportes: rol === "administrador",
    canGestionarFinanzas: rol === "administrador",
  };
};
```

### **Ejemplo de Uso en Componentes**

```typescript
// components/AgendarCita.tsx
const AgendarCita = () => {
  const { canAgendarCita, isPaciente } = usePermissions();
  const { userData } = useAuth();
  
  if (!canAgendarCita) {
    return <div>No tienes permiso para agendar citas</div>;
  }
  
  const handleSubmit = async (formData) => {
    const citaData = {
      fecha: formData.fecha,
      codpaciente: isPaciente ? userData.codigo : formData.pacienteId,
      cododontologo: formData.odontologoId,
      idhorario: formData.horarioId,
      idtipoconsulta: formData.tipoConsultaId,
      idestadoconsulta: 1 // Pendiente
    };
    
    await api.post('/api/clinic/consultas/', citaData);
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Formulario de agendamiento */}
    </form>
  );
};
```

---

## 📝 **Resumen de Correcciones**

### ✅ **LO MÁS IMPORTANTE**

**El PACIENTE SÍ PUEDE AGENDAR CITAS**

Anteriormente puede haber habido confusión, pero el comportamiento correcto es:

- ✅ **Paciente**: Puede agendar SUS PROPIAS citas
- ✅ **Recepcionista**: Puede agendar citas para CUALQUIER paciente
- ✅ **Administrador**: Puede agendar citas para CUALQUIER paciente
- ❌ **Odontólogo**: NO puede agendar citas (solo atenderlas)

### 🔧 **En el Backend**

El endpoint `POST /api/clinic/consultas/` debe permitir:

1. Si es **Paciente**: Auto-asignar `codpaciente` del usuario logueado
2. Si es **Recepcionista/Admin**: Permitir especificar cualquier `codpaciente`

---

## 📧 **Contacto y Soporte**

Para dudas sobre permisos o funcionalidades:

- Revisar esta guía completa
- Verificar el rol del usuario en el login (`subtipo`)
- Consultar `FRONTEND_ROLES_GUIDE.md` para implementación
- Ver `CREDENCIALES_USUARIOS.md` para usuarios de prueba

---

**Última actualización:** Octubre 15, 2025  
**Versión:** 2.0 - Sistema Multi-Tenant con 4 Roles
