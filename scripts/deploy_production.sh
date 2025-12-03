#!/bin/bash

# UATP Production Deployment Script
# This script deploys the UATP Capsule Engine to a production environment

set -e  # Exit on any error

# Configuration
APP_NAME="uatp-capsule-engine"
APP_DIR="/opt/${APP_NAME}"
SERVICE_USER="uatp"
PYTHON_VERSION="3.11"
NODE_VERSION="18"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
        error "Please run as a regular user with sudo privileges"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check OS
    if [[ ! -f /etc/os-release ]]; then
        error "Cannot determine OS version"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed"
        exit 1
    fi
    
    # Check PostgreSQL client
    if ! command -v psql &> /dev/null; then
        warn "PostgreSQL client not found. Database setup may not work."
    fi
    
    log "System requirements check passed"
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    # Update package list
    sudo apt-get update -y
    
    # Install required packages
    sudo apt-get install -y \
        nginx \
        postgresql-client \
        redis-tools \
        supervisor \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        libpq-dev \
        libssl-dev \
        libffi-dev \
        curl \
        git \
        htop \
        fail2ban \
        ufw \
        certbot \
        python3-certbot-nginx
    
    log "System dependencies installed"
}

# Create service user
create_service_user() {
    log "Creating service user..."
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        sudo useradd --system --shell /bin/bash --home-dir "$APP_DIR" --create-home "$SERVICE_USER"
        log "Service user '$SERVICE_USER' created"
    else
        info "Service user '$SERVICE_USER' already exists"
    fi
}

# Setup application directory
setup_app_directory() {
    log "Setting up application directory..."
    
    # Create directories
    sudo mkdir -p "$APP_DIR"
    sudo mkdir -p "$APP_DIR/logs"
    sudo mkdir -p "$APP_DIR/backups"
    sudo mkdir -p "$APP_DIR/ssl"
    
    # Set ownership
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"
    
    log "Application directory setup complete"
}

# Deploy application code
deploy_application() {
    log "Deploying application code..."
    
    # Copy application files
    sudo cp -r . "$APP_DIR/app"
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR/app"
    
    # Create Python virtual environment
    sudo -u "$SERVICE_USER" python3 -m venv "$APP_DIR/venv"
    
    # Install Python dependencies
    sudo -u "$SERVICE_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip
    sudo -u "$SERVICE_USER" "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/app/requirements.txt"
    
    log "Application deployment complete"
}

# Deploy frontend
deploy_frontend() {
    log "Deploying frontend..."
    
    cd "$APP_DIR/app/frontend"
    
    # Install Node.js dependencies
    sudo -u "$SERVICE_USER" npm ci --production
    
    # Build frontend
    sudo -u "$SERVICE_USER" npm run build
    
    log "Frontend deployment complete"
}

# Setup environment configuration
setup_environment() {
    log "Setting up environment configuration..."
    
    # Copy production environment template
    if [[ ! -f "$APP_DIR/.env.production" ]]; then
        sudo cp "$APP_DIR/app/.env.production.example" "$APP_DIR/.env.production"
        sudo chown "$SERVICE_USER:$SERVICE_USER" "$APP_DIR/.env.production"
        sudo chmod 600 "$APP_DIR/.env.production"
        
        warn "Please edit $APP_DIR/.env.production with your production settings"
        warn "This includes database credentials, API keys, and security settings"
    else
        info "Production environment file already exists"
    fi
    
    log "Environment configuration setup complete"
}

# Setup systemd services
setup_systemd_services() {
    log "Setting up systemd services..."
    
    # UATP Backend Service
    sudo tee /etc/systemd/system/uatp-backend.service > /dev/null <<EOF
[Unit]
Description=UATP Capsule Engine Backend
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR/app
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env.production
ExecStart=$APP_DIR/venv/bin/python -m quart --app src.api.server:app run --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$APP_DIR
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectControlGroups=yes
RestrictRealtime=yes

[Install]
WantedBy=multi-user.target
EOF

    # Enable and start services
    sudo systemctl daemon-reload
    sudo systemctl enable uatp-backend.service
    
    log "Systemd services setup complete"
}

# Setup Nginx
setup_nginx() {
    log "Setting up Nginx..."
    
    # Create Nginx configuration
    sudo tee /etc/nginx/sites-available/uatp > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL Configuration (placeholder - update with real certificates)
    ssl_certificate /etc/ssl/certs/uatp.crt;
    ssl_private_key /etc/ssl/private/uatp.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";
    
    # Frontend (Next.js)
    location / {
        root $APP_DIR/app/frontend/.next/static;
        try_files \$uri @frontend;
    }
    
    location @frontend {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # API Rate limiting
        limit_req zone=api burst=10 nodelay;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
    
    # Static files
    location /static {
        alias $APP_DIR/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Logs
    access_log $APP_DIR/logs/nginx_access.log;
    error_log $APP_DIR/logs/nginx_error.log;
}

# Rate limiting
http {
    limit_req_zone \$binary_remote_addr zone=api:10m rate=60r/m;
}
EOF
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/uatp /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test configuration
    sudo nginx -t
    
    log "Nginx setup complete"
}

# Setup firewall
setup_firewall() {
    log "Setting up firewall..."
    
    # Reset UFW
    sudo ufw --force reset
    
    # Default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH
    sudo ufw allow ssh
    
    # Allow HTTP and HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Allow database (if on same server)
    sudo ufw allow from 127.0.0.1 to any port 5432
    
    # Enable firewall
    sudo ufw --force enable
    
    log "Firewall setup complete"
}

# Setup monitoring and logs
setup_monitoring() {
    log "Setting up monitoring and logs..."
    
    # Setup log rotation
    sudo tee /etc/logrotate.d/uatp > /dev/null <<EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload uatp-backend || true
        systemctl reload nginx || true
    endscript
}
EOF
    
    log "Monitoring and logs setup complete"
}

# Start services
start_services() {
    log "Starting services..."
    
    # Start database (if local)
    if systemctl is-enabled postgresql &>/dev/null; then
        sudo systemctl start postgresql
    fi
    
    # Start Redis (if available)
    if systemctl list-unit-files | grep -q redis; then
        sudo systemctl start redis
    fi
    
    # Start UATP backend
    sudo systemctl start uatp-backend
    
    # Start Nginx
    sudo systemctl start nginx
    
    log "Services started successfully"
}

# Main deployment function
main() {
    log "Starting UATP Production Deployment"
    log "===================================="
    
    check_root
    check_requirements
    install_dependencies
    create_service_user
    setup_app_directory
    deploy_application
    deploy_frontend
    setup_environment
    setup_systemd_services
    setup_nginx
    setup_firewall
    setup_monitoring
    start_services
    
    log "===================================="
    log "🎉 UATP Production Deployment Complete!"
    log "===================================="
    
    info "Next Steps:"
    info "1. Edit $APP_DIR/.env.production with your production settings"
    info "2. Setup database with: python3 $APP_DIR/app/scripts/setup_production_db.py"
    info "3. Configure SSL certificates with Let's Encrypt: sudo certbot --nginx"
    info "4. Update Nginx configuration with your domain name"
    info "5. Test the deployment: curl https://your-domain.com/health"
    
    warn "IMPORTANT SECURITY REMINDERS:"
    warn "- Change all default passwords and API keys"
    warn "- Configure SSL certificates"
    warn "- Review firewall rules"
    warn "- Setup automated backups"
    warn "- Configure monitoring and alerting"
}

# Run main function
main "$@"