Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "🧪 PROBANDO LOGIN DE USUARIOS - CLÍNICA NORTE" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Juan Pérez (Paciente)
Write-Host "📝 Probando: Juan Pérez (Paciente - Norte)" -ForegroundColor Yellow
Write-Host "   Email: juan.perez@norte.com"
Write-Host "   URL: http://127.0.0.1:8000/api/auth/login/"
Write-Host "   Header: X-Tenant-Subdomain: norte"
Write-Host ""

$body = @{
    email = "juan.perez@norte.com"
    password = "norte123"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/auth/login/' `
        -Method POST `
        -Body $body `
        -ContentType 'application/json' `
        -Headers @{"X-Tenant-Subdomain"="norte"} `
        -ErrorAction Stop
    
    Write-Host "   ✅ LOGIN EXITOSO!" -ForegroundColor Green
    Write-Host "   Token: $($response.token.Substring(0, [Math]::Min(50, $response.token.Length)))..."
    Write-Host "   Usuario: $($response.usuario.nombre) $($response.usuario.apellido)"
    Write-Host "   Subtipo: $($response.usuario.subtipo)"
    Write-Host "   Recibir notificaciones: $($response.usuario.recibir_notificaciones)"
} catch {
    Write-Host "   ❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        $errorBody = $reader.ReadToEnd()
        Write-Host "   Respuesta: $($errorBody.Substring(0, [Math]::Min(200, $errorBody.Length)))" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "✅ PRUEBA COMPLETADA" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
