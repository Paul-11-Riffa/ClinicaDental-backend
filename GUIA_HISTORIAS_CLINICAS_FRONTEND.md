# 📋 Guía: Implementar Historia Clínica en Frontend

## ❌ Problema Actual

URLs dan error 404:
```
http://norte.localhost:5174/registrar-historia-clinica
http://norte.localhost:5174/consultar-historia-clinica
```

**Causa:** Las rutas NO están configuradas en React Router del frontend.

---

## ✅ Backend - Endpoints Disponibles

El backend YA tiene los endpoints funcionando:

### 1. Crear Historia Clínica
```http
POST /api/historias-clinicas/
Content-Type: application/json
Authorization: Token <tu-token>

{
  "pacientecodigo": 1,
  "motivoconsulta": "Dolor de muela",
  "antecedentesfamiliares": "Madre con diabetes",
  "antecedentespersonales": "Ninguno relevante",
  "examengeneral": "Paciente en buen estado general",
  "examenregional": "Edema en encía superior derecha",
  "examenbucal": "Caries en molar superior derecho",
  "diagnostico": "Caries dental profunda",
  "tratamiento": "Endodoncia + Corona",
  "receta": "Ibuprofeno 400mg cada 8h por 3 días"
}
```

### 2. Listar Historias Clínicas
```http
GET /api/historias-clinicas/
GET /api/historias-clinicas/?paciente=1
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "pacientecodigo": {
      "codigo": 1,
      "codusuario": {
        "nombre": "Juan",
        "apellido": "Pérez",
        "rut": "12345678-9"
      }
    },
    "episodio": 1,
    "fecha": "2025-10-15",
    "motivoconsulta": "Dolor de muela",
    "diagnostico": "Caries dental profunda",
    "tratamiento": "Endodoncia + Corona"
  }
]
```

---

## 🔧 Frontend - Configuración de Rutas

### 1. Agregar Rutas en React Router

**Archivo:** `src/routes/AppRoutes.tsx` (o donde tengas tus rutas)

```tsx
import { Routes, Route } from 'react-router-dom';
import RegistrarHistoriaClinica from '../pages/HistoriaClinica/RegistrarHistoriaClinica';
import ConsultarHistoriaClinica from '../pages/HistoriaClinica/ConsultarHistoriaClinica';

function AppRoutes() {
  return (
    <Routes>
      {/* ... tus rutas existentes ... */}
      
      {/* Rutas de Historia Clínica */}
      <Route 
        path="/registrar-historia-clinica" 
        element={<RegistrarHistoriaClinica />} 
      />
      <Route 
        path="/consultar-historia-clinica" 
        element={<ConsultarHistoriaClinica />} 
      />
    </Routes>
  );
}

export default AppRoutes;
```

---

## 📄 Frontend - Componentes a Crear

### 1. Interfaz TypeScript

**Archivo:** `src/interfaces/HistoriaClinica.ts`

```typescript
export interface HistoriaClinica {
  id: number;
  pacientecodigo: {
    codigo: number;
    codusuario: {
      nombre: string;
      apellido: string;
      rut: string;
    };
  };
  episodio: number;
  fecha: string;
  motivoconsulta: string;
  antecedentesfamiliares?: string;
  antecedentespersonales?: string;
  examengeneral?: string;
  examenregional?: string;
  examenbucal?: string;
  diagnostico: string;
  tratamiento: string;
  receta?: string;
}

export interface HistoriaClinicaCreate {
  pacientecodigo: number;
  motivoconsulta: string;
  antecedentesfamiliares?: string;
  antecedentespersonales?: string;
  examengeneral?: string;
  examenregional?: string;
  examenbucal?: string;
  diagnostico: string;
  tratamiento: string;
  receta?: string;
}
```

---

### 2. Servicio API

**Archivo:** `src/services/historiaClinicaService.ts`

```typescript
import api from './axiosConfig';
import { HistoriaClinica, HistoriaClinicaCreate } from '../interfaces/HistoriaClinica';

/**
 * Crea una nueva historia clínica
 */
export const crearHistoriaClinica = async (
  data: HistoriaClinicaCreate
): Promise<HistoriaClinica> => {
  const response = await api.post<HistoriaClinica>('/historias-clinicas/', data);
  return response.data;
};

/**
 * Obtiene todas las historias clínicas
 * @param pacienteId - Opcional: filtrar por paciente
 */
export const obtenerHistoriasClinicas = async (
  pacienteId?: number
): Promise<HistoriaClinica[]> => {
  const url = pacienteId 
    ? `/historias-clinicas/?paciente=${pacienteId}`
    : '/historias-clinicas/';
  
  const response = await api.get<HistoriaClinica[]>(url);
  return response.data;
};

/**
 * Obtiene una historia clínica específica
 */
export const obtenerHistoriaClinica = async (
  id: number
): Promise<HistoriaClinica> => {
  const response = await api.get<HistoriaClinica>(`/historias-clinicas/${id}/`);
  return response.data;
};
```

---

### 3. Página: Registrar Historia Clínica

**Archivo:** `src/pages/HistoriaClinica/RegistrarHistoriaClinica.tsx`

```tsx
import React, { useState, useEffect } from 'react';
import { crearHistoriaClinica } from '../../services/historiaClinicaService';
import { obtenerPacientes } from '../../services/pacienteService';
import { HistoriaClinicaCreate } from '../../interfaces/HistoriaClinica';
import './HistoriaClinica.css';

interface Paciente {
  codigo: number;
  codusuario: {
    nombre: string;
    apellido: string;
    rut: string;
  };
}

const RegistrarHistoriaClinica: React.FC = () => {
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<HistoriaClinicaCreate>({
    pacientecodigo: 0,
    motivoconsulta: '',
    antecedentesfamiliares: '',
    antecedentespersonales: '',
    examengeneral: '',
    examenregional: '',
    examenbucal: '',
    diagnostico: '',
    tratamiento: '',
    receta: ''
  });

  // Cargar pacientes al montar el componente
  useEffect(() => {
    cargarPacientes();
  }, []);

  const cargarPacientes = async () => {
    try {
      const data = await obtenerPacientes();
      setPacientes(data);
    } catch (err) {
      console.error('Error al cargar pacientes:', err);
      setError('Error al cargar la lista de pacientes');
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'pacientecodigo' ? parseInt(value) : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    // Validaciones
    if (!formData.pacientecodigo || formData.pacientecodigo === 0) {
      setError('Debe seleccionar un paciente');
      setLoading(false);
      return;
    }

    if (!formData.motivoconsulta.trim()) {
      setError('El motivo de consulta es obligatorio');
      setLoading(false);
      return;
    }

    if (!formData.diagnostico.trim()) {
      setError('El diagnóstico es obligatorio');
      setLoading(false);
      return;
    }

    if (!formData.tratamiento.trim()) {
      setError('El tratamiento es obligatorio');
      setLoading(false);
      return;
    }

    try {
      await crearHistoriaClinica(formData);
      setSuccess(true);
      
      // Limpiar formulario
      setFormData({
        pacientecodigo: 0,
        motivoconsulta: '',
        antecedentesfamiliares: '',
        antecedentespersonales: '',
        examengeneral: '',
        examenregional: '',
        examenbucal: '',
        diagnostico: '',
        tratamiento: '',
        receta: ''
      });

      // Ocultar mensaje de éxito después de 3 segundos
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      console.error('Error al crear historia clínica:', err);
      setError(err.response?.data?.detail || 'Error al crear la historia clínica');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="historia-clinica-page">
      <h1>Registrar Historia Clínica</h1>

      {success && (
        <div className="alert alert-success">
          ✅ Historia clínica registrada exitosamente
        </div>
      )}

      {error && (
        <div className="alert alert-error">
          ❌ {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="historia-form">
        {/* Selección de Paciente */}
        <div className="form-group">
          <label htmlFor="pacientecodigo">Paciente *</label>
          <select
            id="pacientecodigo"
            name="pacientecodigo"
            value={formData.pacientecodigo}
            onChange={handleChange}
            required
          >
            <option value={0}>Seleccione un paciente</option>
            {pacientes.map(p => (
              <option key={p.codigo} value={p.codigo}>
                {p.codusuario.nombre} {p.codusuario.apellido} - {p.codusuario.rut}
              </option>
            ))}
          </select>
        </div>

        {/* Motivo de Consulta */}
        <div className="form-group">
          <label htmlFor="motivoconsulta">Motivo de Consulta *</label>
          <textarea
            id="motivoconsulta"
            name="motivoconsulta"
            value={formData.motivoconsulta}
            onChange={handleChange}
            rows={3}
            required
            placeholder="Describa el motivo de la consulta..."
          />
        </div>

        {/* Antecedentes Familiares */}
        <div className="form-group">
          <label htmlFor="antecedentesfamiliares">Antecedentes Familiares</label>
          <textarea
            id="antecedentesfamiliares"
            name="antecedentesfamiliares"
            value={formData.antecedentesfamiliares}
            onChange={handleChange}
            rows={2}
            placeholder="Antecedentes familiares relevantes..."
          />
        </div>

        {/* Antecedentes Personales */}
        <div className="form-group">
          <label htmlFor="antecedentespersonales">Antecedentes Personales</label>
          <textarea
            id="antecedentespersonales"
            name="antecedentespersonales"
            value={formData.antecedentespersonales}
            onChange={handleChange}
            rows={2}
            placeholder="Antecedentes personales relevantes..."
          />
        </div>

        {/* Examen General */}
        <div className="form-group">
          <label htmlFor="examengeneral">Examen General</label>
          <textarea
            id="examengeneral"
            name="examengeneral"
            value={formData.examengeneral}
            onChange={handleChange}
            rows={2}
            placeholder="Observaciones del examen general..."
          />
        </div>

        {/* Examen Regional */}
        <div className="form-group">
          <label htmlFor="examenregional">Examen Regional</label>
          <textarea
            id="examenregional"
            name="examenregional"
            value={formData.examenregional}
            onChange={handleChange}
            rows={2}
            placeholder="Observaciones del examen regional..."
          />
        </div>

        {/* Examen Bucal */}
        <div className="form-group">
          <label htmlFor="examenbucal">Examen Bucal</label>
          <textarea
            id="examenbucal"
            name="examenbucal"
            value={formData.examenbucal}
            onChange={handleChange}
            rows={2}
            placeholder="Observaciones del examen bucal..."
          />
        </div>

        {/* Diagnóstico */}
        <div className="form-group">
          <label htmlFor="diagnostico">Diagnóstico *</label>
          <textarea
            id="diagnostico"
            name="diagnostico"
            value={formData.diagnostico}
            onChange={handleChange}
            rows={3}
            required
            placeholder="Diagnóstico del paciente..."
          />
        </div>

        {/* Tratamiento */}
        <div className="form-group">
          <label htmlFor="tratamiento">Tratamiento *</label>
          <textarea
            id="tratamiento"
            name="tratamiento"
            value={formData.tratamiento}
            onChange={handleChange}
            rows={3}
            required
            placeholder="Tratamiento prescrito..."
          />
        </div>

        {/* Receta */}
        <div className="form-group">
          <label htmlFor="receta">Receta</label>
          <textarea
            id="receta"
            name="receta"
            value={formData.receta}
            onChange={handleChange}
            rows={3}
            placeholder="Medicamentos recetados..."
          />
        </div>

        {/* Botones */}
        <div className="form-actions">
          <button 
            type="submit" 
            className="btn-primary"
            disabled={loading}
          >
            {loading ? 'Guardando...' : 'Guardar Historia Clínica'}
          </button>
          
          <button 
            type="button" 
            className="btn-secondary"
            onClick={() => window.history.back()}
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
};

export default RegistrarHistoriaClinica;
```

---

### 4. Página: Consultar Historia Clínica

**Archivo:** `src/pages/HistoriaClinica/ConsultarHistoriaClinica.tsx`

```tsx
import React, { useState, useEffect } from 'react';
import { obtenerHistoriasClinicas } from '../../services/historiaClinicaService';
import { obtenerPacientes } from '../../services/pacienteService';
import { HistoriaClinica } from '../../interfaces/HistoriaClinica';
import './HistoriaClinica.css';

interface Paciente {
  codigo: number;
  codusuario: {
    nombre: string;
    apellido: string;
    rut: string;
  };
}

const ConsultarHistoriaClinica: React.FC = () => {
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [historias, setHistorias] = useState<HistoriaClinica[]>([]);
  const [pacienteSeleccionado, setPacienteSeleccionado] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [historiaExpandida, setHistoriaExpandida] = useState<number | null>(null);

  useEffect(() => {
    cargarPacientes();
  }, []);

  const cargarPacientes = async () => {
    try {
      const data = await obtenerPacientes();
      setPacientes(data);
    } catch (err) {
      console.error('Error al cargar pacientes:', err);
      setError('Error al cargar la lista de pacientes');
    }
  };

  const buscarHistorias = async () => {
    if (pacienteSeleccionado === 0) {
      setError('Debe seleccionar un paciente');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await obtenerHistoriasClinicas(pacienteSeleccionado);
      setHistorias(data);
      
      if (data.length === 0) {
        setError('No se encontraron historias clínicas para este paciente');
      }
    } catch (err) {
      console.error('Error al buscar historias:', err);
      setError('Error al cargar las historias clínicas');
    } finally {
      setLoading(false);
    }
  };

  const toggleHistoria = (id: number) => {
    setHistoriaExpandida(historiaExpandida === id ? null : id);
  };

  return (
    <div className="historia-clinica-page">
      <h1>Consultar Historia Clínica</h1>

      {/* Filtro por Paciente */}
      <div className="filtro-paciente">
        <label htmlFor="paciente">Seleccione Paciente:</label>
        <select
          id="paciente"
          value={pacienteSeleccionado}
          onChange={(e) => setPacienteSeleccionado(parseInt(e.target.value))}
        >
          <option value={0}>Seleccione un paciente</option>
          {pacientes.map(p => (
            <option key={p.codigo} value={p.codigo}>
              {p.codusuario.nombre} {p.codusuario.apellido} - {p.codusuario.rut}
            </option>
          ))}
        </select>
        
        <button onClick={buscarHistorias} className="btn-primary">
          Buscar Historias
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {loading && (
        <div className="loading">
          <p>Cargando historias clínicas...</p>
        </div>
      )}

      {/* Lista de Historias */}
      {!loading && historias.length > 0 && (
        <div className="historias-lista">
          <h2>Historias Clínicas ({historias.length})</h2>
          
          {historias.map(historia => (
            <div key={historia.id} className="historia-card">
              <div 
                className="historia-header"
                onClick={() => toggleHistoria(historia.id)}
              >
                <div className="historia-info">
                  <h3>Episodio #{historia.episodio} - {historia.fecha}</h3>
                  <p className="diagnostico-preview">{historia.diagnostico}</p>
                </div>
                <button className="btn-expand">
                  {historiaExpandida === historia.id ? '▼' : '▶'}
                </button>
              </div>

              {historiaExpandida === historia.id && (
                <div className="historia-detalle">
                  <div className="campo">
                    <strong>Motivo de Consulta:</strong>
                    <p>{historia.motivoconsulta}</p>
                  </div>

                  {historia.antecedentesfamiliares && (
                    <div className="campo">
                      <strong>Antecedentes Familiares:</strong>
                      <p>{historia.antecedentesfamiliares}</p>
                    </div>
                  )}

                  {historia.antecedentespersonales && (
                    <div className="campo">
                      <strong>Antecedentes Personales:</strong>
                      <p>{historia.antecedentespersonales}</p>
                    </div>
                  )}

                  {historia.examengeneral && (
                    <div className="campo">
                      <strong>Examen General:</strong>
                      <p>{historia.examengeneral}</p>
                    </div>
                  )}

                  {historia.examenregional && (
                    <div className="campo">
                      <strong>Examen Regional:</strong>
                      <p>{historia.examenregional}</p>
                    </div>
                  )}

                  {historia.examenbucal && (
                    <div className="campo">
                      <strong>Examen Bucal:</strong>
                      <p>{historia.examenbucal}</p>
                    </div>
                  )}

                  <div className="campo">
                    <strong>Diagnóstico:</strong>
                    <p>{historia.diagnostico}</p>
                  </div>

                  <div className="campo">
                    <strong>Tratamiento:</strong>
                    <p>{historia.tratamiento}</p>
                  </div>

                  {historia.receta && (
                    <div className="campo">
                      <strong>Receta:</strong>
                      <p>{historia.receta}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ConsultarHistoriaClinica;
```

---

### 5. Estilos CSS

**Archivo:** `src/pages/HistoriaClinica/HistoriaClinica.css`

```css
.historia-clinica-page {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.historia-clinica-page h1 {
  color: #333;
  margin-bottom: 30px;
}

/* Formulario */
.historia-form {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #555;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  font-family: inherit;
}

.form-group textarea {
  resize: vertical;
  min-height: 60px;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.1);
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 30px;
}

/* Botones */
.btn-primary {
  background: #4CAF50;
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.3s;
}

.btn-primary:hover:not(:disabled) {
  background: #45a049;
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f44336;
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.3s;
}

.btn-secondary:hover {
  background: #da190b;
}

/* Alertas */
.alert {
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.alert-success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.alert-error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

/* Consultar Historias */
.filtro-paciente {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
  display: flex;
  gap: 15px;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.filtro-paciente label {
  font-weight: 600;
  color: #555;
}

.filtro-paciente select {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.historias-lista h2 {
  color: #333;
  margin-bottom: 20px;
}

.historia-card {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 15px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.historia-header {
  padding: 15px 20px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background 0.2s;
}

.historia-header:hover {
  background: #f5f5f5;
}

.historia-info h3 {
  margin: 0 0 5px 0;
  color: #333;
  font-size: 1.1rem;
}

.diagnostico-preview {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.btn-expand {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #666;
  padding: 5px 10px;
}

.historia-detalle {
  padding: 20px;
  border-top: 1px solid #eee;
  background: #fafafa;
}

.historia-detalle .campo {
  margin-bottom: 15px;
}

.historia-detalle .campo:last-child {
  margin-bottom: 0;
}

.historia-detalle strong {
  display: block;
  color: #333;
  margin-bottom: 5px;
  font-size: 0.9rem;
}

.historia-detalle p {
  margin: 0;
  padding: 10px;
  background: white;
  border-radius: 4px;
  border: 1px solid #ddd;
  white-space: pre-wrap;
}
```

---

## 📝 Resumen de Pasos

1. **✅ Backend:** Ya funcionando (`/api/historias-clinicas/`)

2. **Frontend:**
   - [ ] Agregar rutas en React Router
   - [ ] Crear interfaz TypeScript
   - [ ] Crear servicio API
   - [ ] Crear página "Registrar Historia Clínica"
   - [ ] Crear página "Consultar Historia Clínica"
   - [ ] Agregar estilos CSS
   - [ ] Probar funcionalidad

---

## 🧪 Testing

### 1. Probar Backend Directamente

```bash
# Crear historia clínica
curl -X POST http://localhost:8000/api/historias-clinicas/ \
  -H "Authorization: Token <tu-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "pacientecodigo": 1,
    "motivoconsulta": "Prueba",
    "diagnostico": "Diagnóstico de prueba",
    "tratamiento": "Tratamiento de prueba"
  }'

# Listar historias
curl -X GET http://localhost:8000/api/historias-clinicas/ \
  -H "Authorization: Token <tu-token>"
```

### 2. Probar Frontend

1. Navegar a `http://norte.localhost:5174/registrar-historia-clinica`
2. Llenar el formulario
3. Verificar que se crea correctamente
4. Navegar a `http://norte.localhost:5174/consultar-historia-clinica`
5. Seleccionar paciente y buscar
6. Verificar que muestra las historias

---

## 📞 Soporte

Si tienes problemas:
1. Verifica que las rutas estén agregadas en React Router
2. Revisa la consola del navegador para errores
3. Verifica que el token de autenticación esté presente
4. Confirma que el backend esté corriendo

**Backend:** ✅ Funcionando en `http://0.0.0.0:8000`
