# UATP Capsule Engine - Production Deployment Guide

This guide provides step-by-step instructions for deploying the UATP Capsule Engine to a production environment.

##  Quick Start

For a quick production deployment:

```bash
# 1. Clone and configure
git clone <repository>
cd uatp-capsule-engine

# 2. Copy production environment
cp .env.production.example .env.production

# 3. Edit production settings (IMPORTANT!)
nano .env.production

# 4. Run deployment script
./scripts/deploy_production.sh
```

##  Prerequisites

### System Requirements

- **OS**: Ubuntu 20.04+ or RHEL 8+ (recommended)
- **RAM**: Minimum 4GB, recommended 8GB+
- **CPU**: Minimum 2 cores, recommended 4+ cores
- **Storage**: Minimum 50GB, recommended 100GB+ SSD
- **Network**: Static IP address and domain name

### Required Software

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker & Docker Compose (optional)
- Nginx
- SSL certificates (Let's Encrypt recommended)

##  Manual Deployment Steps

### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.11 python3.11-venv python3-pip \
  postgresql postgresql-contrib nginx certbot python3-certbot-nginx \
  redis-server supervisor ufw fail2ban

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE uatp_production;
CREATE USER uatp_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE uatp_production TO uatp_user;
\q

# Or use the automated script
python3 scripts/setup_production_db.py
```

### 3. Application Deployment

```bash
# Create application directory
sudo mkdir -p /opt/uatp-capsule-engine
sudo chown $USER:$USER /opt/uatp-capsule-engine

# Copy application files
cp -r . /opt/uatp-capsule-engine/

# Create virtual environment
cd /opt/uatp-capsule-engine
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Frontend Build

```bash
cd frontend
npm ci --production
npm run build
```

### 5. Configuration

```bash
# Copy and edit production configuration
cp .env.production.example .env.production
nano .env.production
```

**Critical settings to update:**

```bash
# Security Keys (GENERATE SECURE VALUES!)
UATP_SIGNING_KEY=your_64_character_hex_key
JWT_SECRET_KEY=your_256_bit_secret_key
ENCRYPTION_KEY=your_fernet_key

# Database
DATABASE_URL=postgresql+asyncpg://uatp_user:password@localhost:5432/uatp_production

# AI API Keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Domain and CORS
CORS_ORIGINS=https://your-domain.com

# API Keys for production
API_KEYS_CONFIG='{"prod-key":{"permissions":["read","write"],"agent_id":"production","description":"Production API key"}}'
```

### 6. SSL Certificate Setup

```bash
# Install Let's Encrypt certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### 7. Service Configuration

Create systemd service file:

```bash
sudo nano /etc/systemd/system/uatp.service
```

```ini
[Unit]
Description=UATP Capsule Engine
After=network.target postgresql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/uatp-capsule-engine
Environment=PATH=/opt/uatp-capsule-engine/venv/bin
EnvironmentFile=/opt/uatp-capsule-engine/.env.production
ExecStart=/opt/uatp-capsule-engine/venv/bin/python -m quart --app src.api.server:app run --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable uatp
sudo systemctl start uatp
```

### 8. Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/uatp
```

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_private_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/uatp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

##  Docker Deployment

For containerized deployment:

```bash
# Copy production environment
cp .env.production.example .env.production

# Edit configuration
nano .env.production

# Deploy with Docker Compose
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps
```

##  Security Hardening

### Firewall Configuration

```bash
# Enable UFW
sudo ufw enable

# Allow necessary ports
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Deny all other inbound
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

### Fail2ban Configuration

```bash
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
```

### SSL Security

Test SSL configuration:
```bash
curl -I https://your-domain.com
# Should return security headers

# Test SSL rating
curl -s "https://api.ssllabs.com/api/v3/analyze?host=your-domain.com" | jq
```

##  Monitoring Setup

### Health Checks

```bash
# API health
curl https://your-domain.com/api/health

# Database connection
curl https://your-domain.com/api/health/detailed
```

### Log Monitoring

```bash
# Application logs
tail -f /opt/uatp-capsule-engine/logs/uatp.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# System logs
journalctl -u uatp -f
```

### Performance Monitoring

Set up Prometheus and Grafana:

```bash
# Metrics endpoint
curl https://your-domain.com/metrics

# Grafana dashboard
# Access at https://your-domain.com:3000
```

##  Backup Strategy

### Automated Database Backups

```bash
# Create backup script
sudo nano /opt/uatp-capsule-engine/scripts/backup_db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/uatp-capsule-engine/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U uatp_user -d uatp_production > $BACKUP_DIR/uatp_backup_$DATE.sql
gzip $BACKUP_DIR/uatp_backup_$DATE.sql

# Keep only last 30 days
find $BACKUP_DIR -name "uatp_backup_*.sql.gz" -mtime +30 -delete
```

Add to crontab:
```bash
sudo crontab -e
# Add: 0 2 * * * /opt/uatp-capsule-engine/scripts/backup_db.sh
```

##  Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   sudo systemctl status uatp
   sudo journalctl -u uatp -n 50
   ```

2. **Database connection errors**
   ```bash
   sudo -u postgres psql -c "SELECT version();"
   netstat -tlnp | grep 5432
   ```

3. **Frontend build fails**
   ```bash
   cd frontend
   rm -rf .next node_modules
   npm ci
   npm run build
   ```

4. **SSL certificate issues**
   ```bash
   sudo certbot certificates
   sudo certbot renew --force-renewal
   ```

### Performance Tuning

1. **Database optimization**
   ```sql
   -- Add indexes for frequent queries
   CREATE INDEX IF NOT EXISTS idx_capsule_timestamp ON capsules(timestamp);
   CREATE INDEX IF NOT EXISTS idx_capsule_agent_id ON capsules(agent_id);
   ```

2. **Application tuning**
   ```bash
   # Adjust worker count in .env.production
   WORKER_COUNT=8
   MAX_REQUESTS_PER_WORKER=5000
   ```

##  Updates and Maintenance

### Application Updates

```bash
# Backup current version
cp -r /opt/uatp-capsule-engine /opt/uatp-capsule-engine.backup

# Pull updates
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Rebuild frontend
cd frontend && npm ci && npm run build

# Restart services
sudo systemctl restart uatp
sudo systemctl restart nginx
```

### Database Migrations

```bash
# Run migrations
python3 scripts/migrate_database.py

# Verify
python3 -c "from src.core.database import db; print('Database OK')"
```

##  Support

For production support:

- Check logs first: `/opt/uatp-capsule-engine/logs/`
- Monitor system resources: `htop`, `df -h`, `free -h`
- Database status: `sudo systemctl status postgresql`
- API health: `curl https://your-domain.com/health`

##  Production Checklist

- [ ] Secure passwords and API keys configured
- [ ] SSL certificates installed and auto-renewal working
- [ ] Database backups automated
- [ ] Firewall rules configured
- [ ] Monitoring and alerting setup
- [ ] Log rotation configured
- [ ] Performance tuning applied
- [ ] Health checks passing
- [ ] Documentation updated
- [ ] Team access configured

---

**[WARN] Security Notice**: Always review and customize security settings for your specific environment. Never use default passwords or keys in production.
