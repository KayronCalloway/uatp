#!/bin/bash

# UATP Capsule Engine Health Check Script
# Comprehensive health monitoring for all system components

set -euo pipefail

# Configuration
HEALTH_CHECK_URL="${HEALTH_CHECK_URL:-http://localhost:8080/health}"
METRICS_URL="${METRICS_URL:-http://localhost:9090/metrics}"
DATABASE_HOST="${DB_HOST:-localhost}"
DATABASE_PORT="${DB_PORT:-5432}"
DATABASE_NAME="${DB_NAME:-uatp_capsule_engine}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Health check results
OVERALL_HEALTH="healthy"
HEALTH_REPORT=""

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    HEALTH_REPORT+="\nWARNING: $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    OVERALL_HEALTH="unhealthy"
    HEALTH_REPORT+="\nERROR: $1"
}

# Function to check HTTP endpoint
check_http_endpoint() {
    local url="$1"
    local name="$2"
    local timeout="${3:-10}"

    if curl -s -f -m "$timeout" "$url" > /dev/null 2>&1; then
        log_info "$name is responding"
        return 0
    else
        log_error "$name is not responding at $url"
        return 1
    fi
}

# Function to check database connectivity
check_database() {
    log_info "Checking database connectivity..."

    if command -v pg_isready > /dev/null 2>&1; then
        if pg_isready -h "$DATABASE_HOST" -p "$DATABASE_PORT" -d "$DATABASE_NAME" -t 10; then
            log_info "Database is accessible"

            # Check database load if psql is available
            if command -v psql > /dev/null 2>&1; then
                local connections=$(psql -h "$DATABASE_HOST" -p "$DATABASE_PORT" -d "$DATABASE_NAME" -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | tr -d ' \n' || echo "unknown")
                log_info "Database connections: $connections"

                if [[ "$connections" =~ ^[0-9]+$ ]] && [ "$connections" -gt 50 ]; then
                    log_warn "High number of database connections: $connections"
                fi
            fi
        else
            log_error "Database is not accessible"
        fi
    else
        log_warn "pg_isready not available, skipping database check"
    fi
}

# Function to check Redis connectivity
check_redis() {
    log_info "Checking Redis connectivity..."

    if command -v redis-cli > /dev/null 2>&1; then
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping > /dev/null 2>&1; then
            log_info "Redis is accessible"

            # Check Redis memory usage
            local memory_used=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" info memory | grep "used_memory:" | cut -d: -f2 | tr -d '\r' || echo "unknown")
            local memory_max=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" config get maxmemory | tail -1 || echo "unknown")

            if [[ "$memory_used" != "unknown" && "$memory_max" != "unknown" && "$memory_max" != "0" ]]; then
                local memory_percent=$((memory_used * 100 / memory_max))
                log_info "Redis memory usage: ${memory_percent}%"

                if [ "$memory_percent" -gt 80 ]; then
                    log_warn "High Redis memory usage: ${memory_percent}%"
                fi
            fi
        else
            log_error "Redis is not accessible"
        fi
    else
        log_warn "redis-cli not available, skipping Redis check"
    fi
}

# Function to check system resources
check_system_resources() {
    log_info "Checking system resources..."

    # Check disk space
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    log_info "Disk usage: ${disk_usage}%"

    if [ "$disk_usage" -gt 85 ]; then
        log_error "Critical disk usage: ${disk_usage}%"
    elif [ "$disk_usage" -gt 75 ]; then
        log_warn "High disk usage: ${disk_usage}%"
    fi

    # Check memory usage
    if command -v free > /dev/null 2>&1; then
        local memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
        log_info "Memory usage: ${memory_usage}%"

        if [ "$memory_usage" -gt 90 ]; then
            log_error "Critical memory usage: ${memory_usage}%"
        elif [ "$memory_usage" -gt 80 ]; then
            log_warn "High memory usage: ${memory_usage}%"
        fi
    fi

    # Check CPU load
    if [ -f /proc/loadavg ]; then
        local load_avg=$(cat /proc/loadavg | awk '{print $1}')
        local cpu_cores=$(nproc)
        local load_percent=$(echo "$load_avg * 100 / $cpu_cores" | bc -l 2>/dev/null | cut -d. -f1 || echo "unknown")

        if [[ "$load_percent" != "unknown" ]]; then
            log_info "CPU load: ${load_percent}% (${load_avg} on ${cpu_cores} cores)"

            if [ "$load_percent" -gt 90 ]; then
                log_error "Critical CPU load: ${load_percent}%"
            elif [ "$load_percent" -gt 80 ]; then
                log_warn "High CPU load: ${load_percent}%"
            fi
        fi
    fi
}

# Function to check application health
check_application_health() {
    log_info "Checking application health endpoint..."

    if check_http_endpoint "$HEALTH_CHECK_URL" "Application health endpoint"; then
        # Parse health response if possible
        local health_response=$(curl -s -f -m 10 "$HEALTH_CHECK_URL" 2>/dev/null || echo "{}")

        if command -v jq > /dev/null 2>&1; then
            local app_status=$(echo "$health_response" | jq -r '.status // "unknown"')
            log_info "Application status: $app_status"

            if [ "$app_status" != "healthy" ] && [ "$app_status" != "unknown" ]; then
                log_warn "Application reports unhealthy status: $app_status"
            fi
        fi
    fi
}

# Function to check metrics endpoint
check_metrics() {
    log_info "Checking metrics endpoint..."

    if check_http_endpoint "$METRICS_URL" "Metrics endpoint"; then
        # Check for basic metrics
        local metrics_response=$(curl -s -f -m 10 "$METRICS_URL" 2>/dev/null || echo "")

        if echo "$metrics_response" | grep -q "http_requests_total"; then
            log_info "HTTP request metrics are available"
        else
            log_warn "HTTP request metrics not found"
        fi

        if echo "$metrics_response" | grep -q "system_cpu_usage_percent"; then
            log_info "System metrics are available"
        else
            log_warn "System metrics not found"
        fi
    fi
}

# Function to check Docker containers (if running in Docker)
check_docker_containers() {
    if command -v docker > /dev/null 2>&1 && docker info > /dev/null 2>&1; then
        log_info "Checking Docker containers..."

        local containers=$(docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "")

        if [ -n "$containers" ]; then
            echo "$containers" | while IFS=$'\t' read -r name status; do
                if [[ "$name" == "NAMES" ]]; then
                    continue
                fi

                if echo "$status" | grep -q "Up"; then
                    log_info "Container $name is running"
                else
                    log_error "Container $name is not running: $status"
                fi
            done
        fi
    fi
}

# Function to check log files
check_log_files() {
    log_info "Checking log files..."

    local log_dir="/app/logs"
    if [ -d "$log_dir" ]; then
        # Check if logs are being written
        local recent_logs=$(find "$log_dir" -name "*.log" -newermt "5 minutes ago" 2>/dev/null | wc -l)

        if [ "$recent_logs" -gt 0 ]; then
            log_info "Log files are being updated"
        else
            log_warn "No recent log file updates in $log_dir"
        fi

        # Check log file sizes
        find "$log_dir" -name "*.log" -size +100M 2>/dev/null | while read -r large_log; do
            log_warn "Large log file detected: $large_log"
        done
    else
        log_warn "Log directory $log_dir not found"
    fi
}

# Function to send health report
send_health_report() {
    local timestamp=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
    local hostname=$(hostname)

    echo "=================================="
    echo "UATP Health Check Report"
    echo "=================================="
    echo "Timestamp: $timestamp"
    echo "Hostname: $hostname"
    echo "Overall Health: $OVERALL_HEALTH"

    if [ -n "$HEALTH_REPORT" ]; then
        echo -e "\nIssues Found:$HEALTH_REPORT"
    else
        echo -e "\nNo issues found."
    fi

    echo "=================================="

    # Send to monitoring system if configured
    if [ -n "${WEBHOOK_URL:-}" ]; then
        local payload=$(cat <<EOF
{
    "timestamp": "$timestamp",
    "hostname": "$hostname",
    "overall_health": "$OVERALL_HEALTH",
    "report": "$HEALTH_REPORT"
}
EOF
)

        if curl -s -X POST -H "Content-Type: application/json" -d "$payload" "$WEBHOOK_URL" > /dev/null 2>&1; then
            log_info "Health report sent to monitoring system"
        else
            log_warn "Failed to send health report to monitoring system"
        fi
    fi
}

# Main execution
main() {
    echo "Starting UATP Capsule Engine health check..."

    check_application_health
    check_database
    check_redis
    check_system_resources
    check_metrics
    check_docker_containers
    check_log_files

    send_health_report

    # Exit with appropriate code
    if [ "$OVERALL_HEALTH" = "healthy" ]; then
        echo "Health check completed successfully"
        exit 0
    else
        echo "Health check completed with issues"
        exit 1
    fi
}

# Run main function
main "$@"
