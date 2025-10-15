# Script para configurar subdominios - EJECUTAR COMO ADMINISTRADOR
# Guardar como: configurar_hosts.ps1
# Ejecutar: PowerShell como Admin → .\configurar_hosts.ps1

# Verificar si se está ejecutando como administrador
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator"))
{
    Write-Host "ESTE SCRIPT DEBE EJECUTARSE COMO ADMINISTRADOR" -ForegroundColor Red
    Write-Host "1. Clic derecho en PowerShell → 'Ejecutar como administrador'" -ForegroundColor Yellow
    Write-Host "2. Navegar a esta carpeta: cd 'C:\Users\asus\Documents\Nueva carpeta (5)\sitwo-project-backend-master'" -ForegroundColor Yellow
    Write-Host "3. Ejecutar: .\configurar_hosts.ps1" -ForegroundColor Yellow
    pause
    exit 1
}

# Ruta del archivo hosts
$hostsPath = "C:\Windows\System32\drivers\etc\hosts"

# Backup del archivo hosts original
$backupPath = "$hostsPath.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item $hostsPath $backupPath
Write-Host "Backup creado: $backupPath" -ForegroundColor Green

# Verificar si ya existen las entradas
$existingContent = Get-Content $hostsPath
$hasNorte = $existingContent | Where-Object { $_ -match "norte\.localhost" }
$hasSur = $existingContent | Where-Object { $_ -match "sur\.localhost" }
$hasEste = $existingContent | Where-Object { $_ -match "este\.localhost" }

if ($hasNorte -or $hasSur -or $hasEste) {
    Write-Host "Algunos subdominios ya existen en el archivo hosts:" -ForegroundColor Yellow
    if ($hasNorte) { Write-Host "  - norte.localhost ya existe" }
    if ($hasSur) { Write-Host "  - sur.localhost ya existe" }
    if ($hasEste) { Write-Host "  - este.localhost ya existe" }
    
    $confirm = Read-Host "¿Deseas continuar de todos modos? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "Operación cancelada" -ForegroundColor Yellow
        exit 0
    }
}

# Agregar las nuevas entradas
$newEntries = @"

# Subdominios para Dental Clinic Multi-Tenant (Agregado $(Get-Date))
127.0.0.1    norte.localhost
127.0.0.1    sur.localhost
127.0.0.1    este.localhost
"@

Add-Content -Path $hostsPath -Value $newEntries

Write-Host "¡Subdominios configurados exitosamente!" -ForegroundColor Green
Write-Host ""
Write-Host "URLs disponibles:" -ForegroundColor Cyan
Write-Host "  - http://norte.localhost:8000/api/clinic/health/" -ForegroundColor White
Write-Host "  - http://sur.localhost:8000/api/users/health/" -ForegroundColor White  
Write-Host "  - http://este.localhost:8000/api/notifications/health/" -ForegroundColor White
Write-Host "  - http://localhost:8000/api/tenancy/health/ (público)" -ForegroundColor White
Write-Host ""
Write-Host "Para probar:" -ForegroundColor Yellow
Write-Host "1. Asegúrate de que Django esté corriendo: python manage.py runserver 8000"
Write-Host "2. Prueba las URLs en el navegador o con PowerShell"
Write-Host ""
Write-Host "Ejemplo de testing:"
Write-Host 'Invoke-WebRequest -Uri "http://norte.localhost:8000/api/tenancy/health/"' -ForegroundColor Gray

# Verificar la configuración
Write-Host ""
Write-Host "Verificando configuración..." -ForegroundColor Yellow
$content = Get-Content $hostsPath | Select-String "localhost"
$content | ForEach-Object { Write-Host "  $($_)" -ForegroundColor Gray }

Write-Host ""
Write-Host "¡Configuración completada!" -ForegroundColor Green
pause