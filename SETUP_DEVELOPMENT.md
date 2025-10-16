# 🚀 Quick Setup Guide - Development

## For Windows Developers (Recommended: Acrylic DNS Proxy)

### Step 1: Install Acrylic DNS Proxy
Download from: https://mayakron.altervista.org/support/acrylic/Home.htm

### Step 2: Run Setup Script (as Administrator)
```powershell
# Open PowerShell as Administrator
cd path\to\project
.\setup_acrylic.ps1
```

This script will:
- ✅ Configure Acrylic hosts file
- ✅ Restart Acrylic service
- ✅ Set Windows DNS to 127.0.0.1
- ✅ Flush DNS cache

### Step 3: Verify Configuration
```powershell
ping norte.localhost
# Should reply from 127.0.0.1
```

### Step 4: Start Django Server
```powershell
python manage.py runserver 0.0.0.0:8000
```

### Step 5: Access Subdomains
- http://norte.localhost:8000/admin/
- http://sur.localhost:8000/admin/
- http://este.localhost:8000/admin/

---

## For Mac/Linux Developers

### Step 1: Edit Hosts File
```bash
sudo nano /etc/hosts
```

Add these lines:
```
127.0.0.1 localhost
127.0.0.1 norte.localhost
127.0.0.1 sur.localhost
127.0.0.1 este.localhost
127.0.0.1 norte.test
127.0.0.1 sur.test
127.0.0.1 este.test
```

### Step 2: Flush DNS Cache

**Mac:**
```bash
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

**Linux:**
```bash
sudo systemctl restart systemd-resolved
```

### Step 3: Start Server
```bash
python manage.py runserver 0.0.0.0:8000
```

---

## Alternative: Using Headers (Without Subdomain Setup)

If you can't configure subdomains, use HTTP headers:

```bash
curl -H "X-Tenant-Subdomain: norte" http://localhost:8000/api/clinic/pacientes/
```

**In your frontend axios/fetch:**
```javascript
axios.get('/api/clinic/pacientes/', {
  headers: {
    'X-Tenant-Subdomain': 'norte'
  }
});
```

---

## Quick Test

```bash
# Test DNS resolution
ping norte.localhost

# Test API endpoint
curl http://norte.localhost:8000/api/tenancy/empresas/

# Test with authentication
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://norte.localhost:8000/api/clinic/pacientes/
```

---

## Troubleshooting

### Subdomain not resolving
1. Check Acrylic service is running (Windows)
2. Verify hosts file entries
3. Flush DNS cache
4. Restart browser

### 404 on subdomain
1. Check Django server is running on `0.0.0.0:8000`
2. Verify `ALLOWED_HOSTS` in settings includes `.localhost`
3. Check middleware configuration

### Can't login to admin
```bash
# Create superuser
python manage.py createsuperuser
```

---

**Need help?** See full documentation in `API_DOCUMENTATION.md`
