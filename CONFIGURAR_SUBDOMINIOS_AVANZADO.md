# Configuración de Subdominios para Desarrollo Local

## Instrucciones para Windows

Para configurar subdominios locales en Windows, necesitas editar el archivo hosts como **Administrador**.

### Pasos:

1. **Abrir PowerShell como Administrador**
   - Clic derecho en PowerShell → "Ejecutar como administrador"

2. **Ejecutar el siguiente comando para configurar hosts:**

```powershell
# Comando para agregar subdominios al archivo hosts
Add-Content -Path "C:\Windows\System32\drivers\etc\hosts" -Value @"

# Subdominios para Dental Clinic Multi-Tenant (Agregado automáticamente)
127.0.0.1    norte.localhost
127.0.0.1    sur.localhost  
127.0.0.1    este.localhost
127.0.0.1    localhost
"@
```

3. **Verificar que se agregaron correctamente:**

```powershell
Get-Content "C:\Windows\System32\drivers\etc\hosts" | Select-String "localhost"
```

### URLs de Testing una vez configurado:

- **Tenant Norte**: http://norte.localhost:8000/api/clinic/health/
- **Tenant Sur**: http://sur.localhost:8000/api/users/health/  
- **Tenant Este**: http://este.localhost:8000/api/notifications/health/
- **Admin/Público**: http://localhost:8000/api/tenancy/health/

### Comando de testing directo:

```powershell
# Testing con subdominios reales
Invoke-WebRequest -Uri "http://norte.localhost:8000/api/clinic/health/"
Invoke-WebRequest -Uri "http://sur.localhost:8000/api/users/health/"
Invoke-WebRequest -Uri "http://este.localhost:8000/api/notifications/health/"
```

### Para deshacer la configuración (opcional):

```powershell
# Editar manualmente el archivo hosts para eliminar las líneas agregadas
notepad "C:\Windows\System32\drivers\etc\hosts"
```

## Alternativa con Headers (Recomendado para desarrollo)

Si no quieres modificar el archivo hosts, puedes seguir usando headers:

```powershell
# Con headers (no requiere permisos de administrador)
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/clinic/health/" -Headers @{"X-Tenant-Subdomain"="norte"}
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/users/health/" -Headers @{"X-Tenant-Subdomain"="sur"}
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/notifications/health/" -Headers @{"X-Tenant-Subdomain"="este"}
```

## Nota Importante

Las APIs `clinic`, `users` y `notifications` ahora **requieren autenticación**. Para probarlas completamente, necesitarás:

1. Crear un superusuario: `python manage.py createsuperuser`
2. Obtener un token de autenticación
3. Incluir el token en las peticiones

Ejemplo con autenticación:
```powershell
$headers = @{
    "X-Tenant-Subdomain" = "norte"
    "Authorization" = "Token tu_token_aqui"
}
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/clinic/pacientes/" -Headers $headers
```