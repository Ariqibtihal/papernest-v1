# 🚀 DEPLOYMENT GUIDE - PaperLens
## Production Deployment Checklist & Instructions

**Last Updated:** 8 Mei 2026  
**Version:** 1.0

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### Security Requirements
- [ ] JWT_SECRET_KEY generated and set (min 32 characters)
- [ ] PostgreSQL database configured
- [ ] CORS origins configured for production domain
- [ ] All API keys secured in environment variables
- [ ] SSL/TLS certificate configured
- [ ] Firewall rules configured
- [ ] Database backups configured

### Testing Requirements
- [ ] All unit tests passing
- [ ] Security tests passing
- [ ] Integration tests passing
- [ ] Load testing completed
- [ ] Penetration testing completed (optional but recommended)

### Infrastructure Requirements
- [ ] Server/VM provisioned (min 2GB RAM, 2 CPU cores)
- [ ] PostgreSQL 14+ installed and configured
- [ ] Python 3.11+ installed
- [ ] Reverse proxy (Nginx/Caddy) configured
- [ ] Process manager (systemd/supervisor) configured
- [ ] Monitoring tools configured (optional)

---

## 🔧 STEP-BY-STEP DEPLOYMENT

### Step 1: Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install Nginx (reverse proxy)
sudo apt install nginx -y

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 2: Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE paperlens;
CREATE USER paperlens_user WITH ENCRYPTED PASSWORD 'YourSecurePassword123!';
GRANT ALL PRIVILEGES ON DATABASE paperlens TO paperlens_user;
\q

# Test connection
psql -h localhost -U paperlens_user -d paperlens
```

### Step 3: Application Setup

```bash
# Create application directory
sudo mkdir -p /opt/paperlens
sudo chown $USER:$USER /opt/paperlens
cd /opt/paperlens

# Clone repository (or upload files)
git clone https://github.com/yourusername/paperlens.git .

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
uv sync --extra dev
```

### Step 4: Environment Configuration

```bash
# Create .env file
cp .env.example .env
nano .env
```

**Production .env Configuration:**
```env
# Application
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://paperlens_user:YourSecurePassword123!@localhost:5432/paperlens

# Contact
CONTACT_EMAIL=admin@yourdomain.com
USER_AGENT=PaperLens/1.0 (mailto:admin@yourdomain.com)

# JWT Authentication (CRITICAL - Generate with: openssl rand -hex 32)
JWT_SECRET_KEY=<your-generated-64-character-hex-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Configuration
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=Content-Type,Authorization,Accept

# API Keys (optional but recommended)
SEMANTIC_SCHOLAR_API_KEY=your_key_here
CORE_API_KEY=your_key_here
NCBI_API_KEY=your_key_here

# Cache
CACHE_TTL_SECONDS=86400
```

**Generate JWT Secret:**
```bash
# Method 1: OpenSSL
openssl rand -hex 32

# Method 2: Python
python3 -c "import secrets; print(secrets.token_hex(32))"

# Copy output and paste into .env as JWT_SECRET_KEY
```

### Step 5: Database Migration

```bash
# Run migrations
source .venv/bin/activate
uv run alembic upgrade head

# Verify tables created
psql -h localhost -U paperlens_user -d paperlens -c "\dt"
```

### Step 6: Build Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Verify dist folder created
ls -la dist/

# Return to root
cd ..
```

### Step 7: Test Application

```bash
# Test configuration
uv run python -c "from app.config import get_settings; s = get_settings(); print('✅ Config OK')"

# Run security tests
uv run pytest tests/test_security.py -v

# Start application (test mode)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# In another terminal, test endpoints
curl http://localhost:8000/healthz
curl http://localhost:8000/api/v1/sources/status
```

### Step 8: Configure Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/paperlens.service
```

**Service Configuration:**
```ini
[Unit]
Description=PaperLens API Service
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/paperlens
Environment="PATH=/opt/paperlens/.venv/bin"
ExecStart=/opt/paperlens/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/paperlens

[Install]
WantedBy=multi-user.target
```

```bash
# Set permissions
sudo chown -R www-data:www-data /opt/paperlens

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable paperlens
sudo systemctl start paperlens

# Check status
sudo systemctl status paperlens

# View logs
sudo journalctl -u paperlens -f
```

### Step 9: Configure Nginx Reverse Proxy

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/paperlens
```

**Nginx Configuration:**
```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=10r/m;

# Upstream
upstream paperlens_backend {
    server 127.0.0.1:8000;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers (additional to app headers)
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Logging
    access_log /var/log/nginx/paperlens_access.log;
    error_log /var/log/nginx/paperlens_error.log;
    
    # API endpoints
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://paperlens_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Auth endpoints (stricter rate limit)
    location /api/v1/auth/ {
        limit_req zone=auth_limit burst=5 nodelay;
        
        proxy_pass http://paperlens_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check (no rate limit)
    location /healthz {
        proxy_pass http://paperlens_backend;
        access_log off;
    }
    
    # Static files (frontend)
    location / {
        root /opt/paperlens/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/paperlens /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Step 10: SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run

# Certificate will auto-renew via cron
```

### Step 11: Configure Firewall

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Step 12: Setup Monitoring (Optional)

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs -y

# Setup log rotation
sudo nano /etc/logrotate.d/paperlens
```

**Log Rotation Configuration:**
```
/var/log/nginx/paperlens_*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

---

## 🧪 POST-DEPLOYMENT TESTING

### 1. Health Check
```bash
curl https://yourdomain.com/healthz
# Expected: {"status":"ok"}
```

### 2. API Endpoints
```bash
# Sources status
curl https://yourdomain.com/api/v1/sources/status

# Search (should require rate limiting after 30 requests)
curl -X POST https://yourdomain.com/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query":"machine learning","filters":{},"limit":10}'
```

### 3. Security Headers
```bash
curl -I https://yourdomain.com/
# Check for: X-Content-Type-Options, X-Frame-Options, CSP, etc.
```

### 4. Rate Limiting
```bash
# Test rate limit (should get 429 after 30 requests)
for i in {1..35}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST https://yourdomain.com/api/v1/search \
    -H "Content-Type: application/json" \
    -d '{"query":"test","filters":{},"limit":10}'
done
```

### 5. SSL/TLS
```bash
# Test SSL configuration
curl -I https://yourdomain.com/
# Should return 200 with HTTPS

# Test SSL grade (external tool)
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com
```

---

## 📊 MONITORING & MAINTENANCE

### Daily Checks
```bash
# Check service status
sudo systemctl status paperlens

# Check logs for errors
sudo journalctl -u paperlens --since "1 hour ago" | grep ERROR

# Check disk space
df -h

# Check memory usage
free -h
```

### Weekly Checks
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Check database size
psql -h localhost -U paperlens_user -d paperlens -c "SELECT pg_size_pretty(pg_database_size('paperlens'));"

# Backup database
pg_dump -h localhost -U paperlens_user paperlens > backup_$(date +%Y%m%d).sql
```

### Monthly Checks
```bash
# Review access logs
sudo tail -n 1000 /var/log/nginx/paperlens_access.log

# Review error logs
sudo tail -n 1000 /var/log/nginx/paperlens_error.log

# Check for security updates
sudo apt list --upgradable
```

---

## 🔄 UPDATES & ROLLBACK

### Update Application
```bash
# Pull latest code
cd /opt/paperlens
git pull origin main

# Install new dependencies
source .venv/bin/activate
uv sync

# Run migrations
uv run alembic upgrade head

# Rebuild frontend
cd frontend
npm install
npm run build
cd ..

# Restart service
sudo systemctl restart paperlens

# Check status
sudo systemctl status paperlens
```

### Rollback
```bash
# Revert to previous commit
git revert HEAD

# Or checkout specific version
git checkout <commit-hash>

# Downgrade database (if needed)
uv run alembic downgrade -1

# Restart service
sudo systemctl restart paperlens
```

---

## 🐛 TROUBLESHOOTING

### Service Won't Start
```bash
# Check logs
sudo journalctl -u paperlens -n 50

# Check configuration
uv run python -c "from app.config import get_settings; get_settings()"

# Check database connection
psql -h localhost -U paperlens_user -d paperlens
```

### High Memory Usage
```bash
# Check process memory
ps aux | grep uvicorn

# Reduce workers in systemd service
# Edit: ExecStart=... --workers 2 (instead of 4)
sudo systemctl daemon-reload
sudo systemctl restart paperlens
```

### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connections
psql -h localhost -U paperlens_user -d paperlens -c "SELECT count(*) FROM pg_stat_activity;"

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Rate Limiting Too Strict
```bash
# Adjust in app/core/rate_limit.py
# Or adjust Nginx rate limits in /etc/nginx/sites-available/paperlens
sudo nano /etc/nginx/sites-available/paperlens
sudo nginx -t
sudo systemctl reload nginx
```

---

## 📞 SUPPORT & RESOURCES

- **Documentation:** `/docs` endpoint (FastAPI auto-docs)
- **Health Check:** `/healthz`
- **Source Status:** `/api/v1/sources/status`
- **Logs:** `sudo journalctl -u paperlens -f`

---

## ✅ DEPLOYMENT COMPLETE

Your PaperLens instance should now be:
- ✅ Running on HTTPS with valid SSL certificate
- ✅ Protected by rate limiting
- ✅ Secured with proper authentication
- ✅ Monitored and logged
- ✅ Backed up regularly

**Next Steps:**
1. Setup automated backups
2. Configure monitoring alerts
3. Setup CI/CD pipeline
4. Perform load testing
5. Security audit

---

**Deployed by:** [Your Name]  
**Date:** [Deployment Date]  
**Version:** 1.0
