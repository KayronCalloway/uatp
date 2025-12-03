#!/bin/bash

# UATP Production Testing Suite
# Comprehensive testing for production deployment validation

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Default configuration
BASE_URL="${BASE_URL:-https://api.uatp.com}"
ENVIRONMENT="${ENVIRONMENT:-production}"
TIMEOUT="${TIMEOUT:-30}"
QUICK_MODE="${QUICK_MODE:-false}"
VERBOSE="${VERBOSE:-false}"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local color=""
    
    case "$level" in
        "PASS")  color="$GREEN" ;;
        "FAIL")  color="$RED" ;;
        "WARN")  color="$YELLOW" ;;
        "INFO")  color="$BLUE" ;;
        "TEST")  color="$BOLD" ;;
    esac
    
    echo -e "${color}[$timestamp] [$level] $*${NC}"
}

# Usage information
usage() {
    cat << EOF
UATP Production Testing Suite

Usage: $0 [OPTIONS]

Options:
    -u, --url URL            Base URL for testing (default: https://api.uatp.com)
    -e, --environment ENV    Environment to test (default: production)
    -t, --timeout SECONDS    Request timeout (default: 30)
    -q, --quick              Run quick tests only
    -v, --verbose            Verbose output
    -h, --help               Show this help message

Examples:
    $0                                    # Test production with defaults
    $0 -u https://staging.uatp.com       # Test staging environment
    $0 --quick                           # Run quick health checks only
    $0 --verbose                         # Detailed test output

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -u|--url)
                BASE_URL="$2"
                shift 2
                ;;
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -t|--timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            -q|--quick)
                QUICK_MODE="true"
                shift
                ;;
            -v|--verbose)
                VERBOSE="true"
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log WARN "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# HTTP request helper
http_request() {
    local method="$1"
    local url="$2"
    local expected_status="${3:-200}"
    local data="${4:-}"
    local headers="${5:-}"
    
    local curl_opts=(-s -w "HTTPSTATUS:%{http_code}\nTIME:%{time_total}\nSIZE:%{size_download}")
    curl_opts+=(--max-time "$TIMEOUT")
    curl_opts+=(--connect-timeout 10)
    curl_opts+=(-X "$method")
    
    if [ -n "$headers" ]; then
        while IFS= read -r header; do
            curl_opts+=(-H "$header")
        done <<< "$headers"
    fi
    
    if [ -n "$data" ]; then
        curl_opts+=(-d "$data")
    fi
    
    local response
    response=$(curl "${curl_opts[@]}" "$url" 2>/dev/null) || {
        log FAIL "HTTP request failed: $method $url"
        return 1
    }
    
    local body=$(echo "$response" | sed -E '$d;$d;$d')
    local status=$(echo "$response" | grep "HTTPSTATUS:" | cut -d: -f2)
    local time=$(echo "$response" | grep "TIME:" | cut -d: -f2)
    local size=$(echo "$response" | grep "SIZE:" | cut -d: -f2)
    
    if [ "$VERBOSE" = "true" ]; then
        log INFO "Request: $method $url"
        log INFO "Status: $status, Time: ${time}s, Size: ${size} bytes"
    fi
    
    if [ "$status" != "$expected_status" ]; then
        log FAIL "Expected status $expected_status, got $status"
        if [ "$VERBOSE" = "true" ]; then
            log INFO "Response body: $body"
        fi
        return 1
    fi
    
    echo "$body"
    return 0
}

# Test function wrapper
run_test() {
    local test_name="$1"
    local test_function="$2"
    
    log TEST "Running test: $test_name"
    
    if "$test_function"; then
        log PASS "$test_name"
        ((TESTS_PASSED++))
    else
        log FAIL "$test_name"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("$test_name")
    fi
}

# Basic connectivity tests
test_basic_connectivity() {
    http_request GET "$BASE_URL/health" 200 > /dev/null
}

test_https_redirect() {
    local http_url=$(echo "$BASE_URL" | sed 's/https:/http:/')
    local status=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$http_url" 2>/dev/null || echo "000")
    
    if [ "$status" = "301" ] || [ "$status" = "302" ]; then
        return 0
    else
        log FAIL "HTTP to HTTPS redirect failed (status: $status)"
        return 1
    fi
}

test_ssl_certificate() {
    local domain=$(echo "$BASE_URL" | sed 's|https://||' | sed 's|/.*||')
    
    # Check certificate validity
    local cert_info
    cert_info=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null) || {
        log FAIL "Failed to retrieve SSL certificate"
        return 1
    }
    
    # Check if certificate is not expired
    local not_after
    not_after=$(echo "$cert_info" | grep "notAfter" | cut -d= -f2)
    local expiry_timestamp
    expiry_timestamp=$(date -d "$not_after" +%s 2>/dev/null) || {
        log FAIL "Failed to parse certificate expiry date"
        return 1
    }
    
    local current_timestamp
    current_timestamp=$(date +%s)
    
    if [ "$expiry_timestamp" -gt "$current_timestamp" ]; then
        local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        if [ "$VERBOSE" = "true" ]; then
            log INFO "SSL certificate valid for $days_until_expiry more days"
        fi
        return 0
    else
        log FAIL "SSL certificate is expired"
        return 1
    fi
}

# Health check tests
test_health_endpoint() {
    local response
    response=$(http_request GET "$BASE_URL/health" 200) || return 1
    
    # Verify response contains expected fields
    if echo "$response" | grep -q "status.*healthy"; then
        return 0
    else
        log FAIL "Health endpoint response invalid: $response"
        return 1
    fi
}

test_readiness_endpoint() {
    local response
    response=$(http_request GET "$BASE_URL/health/ready" 200) || return 1
    
    # Check if service reports as ready
    if echo "$response" | grep -q "ready.*true"; then
        return 0
    else
        log FAIL "Readiness endpoint indicates service not ready: $response"
        return 1
    fi
}

test_liveness_endpoint() {
    http_request GET "$BASE_URL/health/live" 200 > /dev/null
}

# Security tests
test_security_headers() {
    local response_headers
    response_headers=$(curl -s -I "$BASE_URL/health" --max-time "$TIMEOUT" 2>/dev/null) || return 1
    
    local required_headers=(
        "X-Frame-Options"
        "X-Content-Type-Options"
        "X-XSS-Protection"
        "Strict-Transport-Security"
    )
    
    for header in "${required_headers[@]}"; do
        if ! echo "$response_headers" | grep -qi "$header"; then
            log FAIL "Missing security header: $header"
            return 1
        fi
    done
    
    return 0
}

# Performance tests
test_response_time() {
    local endpoint="$BASE_URL/health"
    local max_response_time=2.0
    
    local response_time
    response_time=$(curl -s -w "%{time_total}" -o /dev/null --max-time "$TIMEOUT" "$endpoint" 2>/dev/null) || return 1
    
    # Compare response time (using awk for floating point comparison)
    if awk "BEGIN {exit !($response_time < $max_response_time)}"; then
        if [ "$VERBOSE" = "true" ]; then
            log INFO "Response time: ${response_time}s"
        fi
        return 0
    else
        log FAIL "Response time too slow: ${response_time}s (max: ${max_response_time}s)"
        return 1
    fi
}

# Main test runner
main() {
    log INFO "Starting UATP production tests..."
    log INFO "Base URL: $BASE_URL"
    log INFO "Environment: $ENVIRONMENT"
    log INFO "Quick Mode: $QUICK_MODE"
    
    local start_time=$(date +%s)
    
    # Basic connectivity tests
    run_test "Basic Connectivity" test_basic_connectivity
    run_test "HTTPS Redirect" test_https_redirect
    run_test "SSL Certificate" test_ssl_certificate
    
    # Health check tests
    run_test "Health Endpoint" test_health_endpoint
    run_test "Readiness Endpoint" test_readiness_endpoint
    run_test "Liveness Endpoint" test_liveness_endpoint
    
    if [ "$QUICK_MODE" = "false" ]; then
        # Security tests
        run_test "Security Headers" test_security_headers
        
        # Performance tests
        run_test "Response Time" test_response_time
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Summary
    local total_tests=$((TESTS_PASSED + TESTS_FAILED))
    log INFO "Test Summary:"
    log INFO "Total Tests: $total_tests"
    log PASS "Passed: $TESTS_PASSED"
    
    if [ "$TESTS_FAILED" -gt 0 ]; then
        log FAIL "Failed: $TESTS_FAILED"
        log FAIL "Failed Tests: ${FAILED_TESTS[*]}"
        log FAIL "Some tests failed! Please investigate."
        exit 1
    else
        log PASS "All tests passed!"
    fi
    
    log INFO "Test execution completed in ${duration}s"
    log INFO "Production deployment is healthy and functioning correctly."
}

# Check prerequisites
check_prerequisites() {
    local missing_tools=()
    local required_tools=("curl" "openssl" "awk")
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        log FAIL "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi
}

# Parse arguments and run
parse_args "$@"
check_prerequisites
main