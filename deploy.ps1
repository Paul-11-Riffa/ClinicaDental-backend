# Script de despliegue a AWS EC2
# Configuracion actualizada automaticamente

Write-Host "Iniciando despliegue en AWS EC2..." -ForegroundColor Cyan

$EC2_IP = "18.222.133.184"
$EC2_USER = "ubuntu"
$KEY_FILE = "C:\Users\paulr\.ssh\dental-clinic-2025.pem"
$REPO_URL = "https://github.com/Paul-11-Riffa/ClinicaDental-backend.git"
$PROJECT_DIR = "/home/ubuntu/ClinicaDental-backend"
$DOMAIN = "notificct.dpdns.org"

Write-Host "`n[1/7] Verificando archivo .pem..." -ForegroundColor Yellow

if (-not (Test-Path $KEY_FILE)) {
    Write-Host "ERROR: No se encontro $KEY_FILE" -ForegroundColor Red
    exit 1
}

Write-Host "Archivo .pem encontrado" -ForegroundColor Green

Write-Host "`n[2/7] Creando archivo .env de produccion..." -ForegroundColor Yellow

$envContent = @"
# Este archivo .env debe ser configurado en el servidor
# NO incluir credenciales reales en el repositorio
DEBUG=False
DJANGO_SECRET_KEY=CAMBIAR_EN_PRODUCCION

FRONTEND_URL=https://buy-dental-smile.vercel.app

# Database
DB_NAME=CAMBIAR
DB_USER=CAMBIAR
DB_PASSWORD=CAMBIAR
DB_HOST=CAMBIAR
DB_PORT=5432

# AWS S3
AWS_ACCESS_KEY_ID=CAMBIAR
AWS_SECRET_ACCESS_KEY=CAMBIAR
AWS_STORAGE_BUCKET_NAME=CAMBIAR

# Stripe
STRIPE_SECRET_KEY=CAMBIAR
STRIPE_PUBLIC_KEY=CAMBIAR
STRIPE_PRICE_ID=CAMBIAR
STRIPE_WEBHOOK_SECRET=CAMBIAR

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# FCM
FCM_PROJECT_ID=CAMBIAR
FCM_SA_JSON_B64=CAMBIAR

# Clinic Info
CLINIC_NAME=Clínica Dental
CLINIC_ADDRESS=Ciudad, País
CLINIC_PHONE=+000 00000000
CLINIC_EMAIL=info@clinica.com
"@

$tempEnvFile = Join-Path $PSScriptRoot ".env.production"
$envContent | Out-File -FilePath $tempEnvFile -Encoding UTF8 -NoNewline
Write-Host "Archivo .env creado" -ForegroundColor Green

function Invoke-SSHCommand {
    param([string]$Command)
    & ssh -i $KEY_FILE -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" $Command
}

function Copy-ToEC2 {
    param([string]$LocalPath, [string]$RemotePath)
    & scp -i $KEY_FILE -o StrictHostKeyChecking=no $LocalPath "${EC2_USER}@${EC2_IP}:$RemotePath"
}

Write-Host "`n[3/7] Subiendo archivo .env al servidor..." -ForegroundColor Yellow
Copy-ToEC2 -LocalPath $tempEnvFile -RemotePath "/tmp/.env.production"
Write-Host "Archivo subido" -ForegroundColor Green

Write-Host "`n[4/7] Preparando servidor..." -ForegroundColor Yellow

$setupCommands = @'
sudo apt-get update -y
OLD_PROJECTS=("/home/ubuntu/sitwo-project-backend" "/home/ubuntu/sitwo-project-backend-master")
for old_dir in "${OLD_PROJECTS[@]}"; do
    if [ -d "$old_dir" ]; then
        echo "Limpiando proyecto antiguo: $old_dir"
        sudo rm -rf "$old_dir"
    fi
done
if [ ! -d "/home/ubuntu/ClinicaDental-backend" ]; then
    echo "Clonando repositorio nuevo..."
    cd /home/ubuntu
    git clone https://github.com/Paul-11-Riffa/ClinicaDental-backend.git
else
    echo "Actualizando repositorio..."
    cd /home/ubuntu/ClinicaDental-backend
    git fetch --all
    git reset --hard origin/main 2>/dev/null || git reset --hard origin/master
    git pull origin main 2>/dev/null || git pull origin master
fi
cp /tmp/.env.production /home/ubuntu/ClinicaDental-backend/.env
sudo chown -R ubuntu:ubuntu /home/ubuntu/ClinicaDental-backend
chmod 600 /home/ubuntu/ClinicaDental-backend/.env
echo "Servidor preparado"
'@

Invoke-SSHCommand -Command $setupCommands
Write-Host "Servidor preparado" -ForegroundColor Green

Write-Host "`n[5/7] Ejecutando script de despliegue (esto toma 5-10 min)..." -ForegroundColor Yellow

$deployCommand = @'
cd /home/ubuntu/ClinicaDental-backend
chmod +x deploy_to_aws.sh
sudo ./deploy_to_aws.sh
'@

Invoke-SSHCommand -Command $deployCommand

Write-Host "`n[6/7] Verificando servicios..." -ForegroundColor Yellow

$checkCommand = @'
echo "=== Estado de Gunicorn ==="
sudo supervisorctl status gunicorn
echo ""
echo "=== Estado de Nginx ==="
sudo systemctl status nginx --no-pager | head -5
echo ""
echo "=== Test de salud ==="
curl -s http://localhost:8000/api/health/ || echo "Endpoint no disponible"
'@

Invoke-SSHCommand -Command $checkCommand

Write-Host "`n[7/7] Probando conectividad..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://$EC2_IP/api/health/" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "Backend esta respondiendo correctamente" -ForegroundColor Green
        Write-Host "Respuesta: $($response.Content)" -ForegroundColor Gray
    }
} catch {
    Write-Host "Backend aun no esta respondiendo (es normal)" -ForegroundColor Yellow
}

Write-Host "`n======================================" -ForegroundColor Green
Write-Host "DESPLIEGUE COMPLETADO" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

Write-Host "`nURLs de acceso:" -ForegroundColor Cyan
Write-Host "  Backend HTTP:  http://$EC2_IP/api/" -ForegroundColor White
Write-Host "  Backend HTTPS: https://$DOMAIN/api/ (configurar SSL)" -ForegroundColor White
Write-Host "  Admin Django:  https://$DOMAIN/admin/" -ForegroundColor White

Write-Host "`nComandos utiles:" -ForegroundColor Cyan
Write-Host "  Conectar:  ssh -i `"$KEY_FILE`" $EC2_USER@$EC2_IP" -ForegroundColor White
Write-Host "  Ver logs:  sudo tail -f /var/log/gunicorn/gunicorn.err.log" -ForegroundColor White
Write-Host "  Reiniciar: sudo supervisorctl restart gunicorn" -ForegroundColor White

Write-Host "`nProximos pasos:" -ForegroundColor Cyan
Write-Host "1. Configurar SSL: sudo certbot --nginx -d $DOMAIN -d *.$DOMAIN" -ForegroundColor Yellow
Write-Host "2. Actualizar variables en Vercel con la nueva URL" -ForegroundColor Yellow
Write-Host "3. Limpiar instancias antiguas (ver instrucciones)" -ForegroundColor Yellow

Write-Host "`nScript finalizado exitosamente" -ForegroundColor Green