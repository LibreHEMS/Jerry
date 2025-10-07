#!/bin/bash
# Production Deployment Script for Jerry AI Assistant
# This script ensures all production-grade features are properly configured

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/backups/$(date +%Y%m%d-%H%M%S)"
ENV_FILE="${PROJECT_ROOT}/.env"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites for production deployment..."
    
    # Check if running as root (not recommended for production)
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root is not recommended for production"
    fi
    
    # Check required tools
    local required_tools=("uv" "podman" "python3")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is required but not installed"
            return 1
        fi
    done
    
    # Check Python version (use uv python if available)
    local python_version
    if command -v uv &> /dev/null && uv python list | grep -q "cpython-3.11"; then
        python_version="3.11.13 (via uv)"
        log_info "Using uv-managed Python 3.11.13"
    else
        python_version=$(python3 --version | cut -d' ' -f2)
        if [[ ! "$python_version" =~ ^3\.(11|12|13|14) ]]; then
                log_error "Python 3.11+ is required (found: $python_version)"
            return 1
        fi
    fi
    
    log_success "Prerequisites check passed"
}

validate_production_config() {
    log_info "Validating production configuration..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error ".env file not found. Please copy from .env.example and configure"
        return 1
    fi
    
    # Check for default/staging secrets
    local default_secrets=(
        "staging-secret-key"
        "staging-jwt-secret"
        "change-me"
        "dev-secret"
        "test-secret"
    )
    
    for secret in "${default_secrets[@]}"; do
        if grep -q "$secret" "$ENV_FILE"; then
            log_error "Default secret '$secret' found in .env - please update for production"
            return 1
        fi
    done
    
    # Check required environment variables
    local required_vars=(
        "AUTH_SECRET_KEY"
        "JWT_SECRET"
        "ENCRYPTION_KEY"
        "ENVIRONMENT"
    )
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE"; then
            log_error "Required environment variable $var not found in .env"
            return 1
        fi
    done
    
    # Check if environment is set to production
    if ! grep -q "^ENVIRONMENT=production" "$ENV_FILE"; then
        log_warning "ENVIRONMENT is not set to 'production' in .env"
    fi
    
    log_success "Production configuration validation passed"
}

create_backup() {
    log_info "Creating backup of current deployment..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup configuration files
    cp "$ENV_FILE" "$BACKUP_DIR/"
    cp -r configs/ "$BACKUP_DIR/" 2>/dev/null || true
    cp -r k8s/ "$BACKUP_DIR/" 2>/dev/null || true
    
    # Backup data if it exists
    if [[ -d "data" ]]; then
        log_info "Backing up data directory (this may take a while)..."
        cp -r data/ "$BACKUP_DIR/"
    fi
    
    log_success "Backup created at $BACKUP_DIR"
}

run_security_checks() {
    log_info "Running security checks..."
    
    # Check file permissions
    local sensitive_files=("$ENV_FILE" "configs/")
    for file in "${sensitive_files[@]}"; do
        if [[ -e "$file" ]]; then
            local perms
            perms=$(stat -c %a "$file")
            if [[ "$perms" =~ [2-7][2-7][2-7] ]]; then
                log_warning "File $file has world-writable permissions ($perms)"
            fi
        fi
    done
    
    # Check for exposed secrets in logs
    if [[ -d "logs" ]]; then
        local secret_patterns=("password" "secret" "key" "token")
        for pattern in "${secret_patterns[@]}"; do
            if grep -ri "$pattern" logs/ 2>/dev/null | grep -v "DEBUG" | head -5; then
                log_warning "Potential secrets found in logs - review log files"
                break
            fi
        done
    fi
    
    log_success "Security checks completed"
}

run_comprehensive_tests() {
    log_info "Running comprehensive test suite..."
    
    # Install dependencies
    log_info "Installing dependencies..."
    uv sync --dev
    
    # Run unit tests
    log_info "Running unit tests..."
    if ! uv run pytest tests/unit/ -v --tb=short; then
        log_error "Unit tests failed"
        return 1
    fi
    
    # Run linting
    log_info "Running code quality checks..."
    if ! uv run ruff check src/ tests/; then
        log_warning "Code quality issues found - consider fixing"
    fi
    
    # Run type checking (if mypy is available)
    if command -v mypy &> /dev/null; then
        log_info "Running type checking..."
        uv run mypy src/ --ignore-missing-imports || log_warning "Type checking issues found"
    fi
    
    log_success "Test suite completed"
}

setup_production_directories() {
    log_info "Setting up production directories..."
    
    # Create required directories with proper permissions
    local directories=(
        "data/chroma"
        "data/documents" 
        "data/models"
        "data/cache"
        "logs"
        "backups"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        chmod 755 "$dir"
    done
    
    # Create log files with proper permissions
    touch logs/jerry.log
    chmod 644 logs/jerry.log
    
    log_success "Production directories created"
}

generate_production_secrets() {
    log_info "Generating secure production secrets..."
    
    # Generate secrets using Python
    cat > /tmp/generate_secrets.py << 'EOF'
import secrets
import base64

# Generate secure secrets
auth_secret = secrets.token_urlsafe(64)
jwt_secret = secrets.token_urlsafe(64)
encryption_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
api_key = secrets.token_urlsafe(32)

print(f"AUTH_SECRET_KEY={auth_secret}")
print(f"JWT_SECRET={jwt_secret}")
print(f"ENCRYPTION_KEY={encryption_key}")
print(f"API_KEY={api_key}")
EOF
    
    python3 /tmp/generate_secrets.py > /tmp/production_secrets.env
    rm /tmp/generate_secrets.py
    
    log_success "Production secrets generated at /tmp/production_secrets.env"
    log_warning "Please update your .env file with these secrets and delete the temporary file"
}

optimize_for_production() {
    log_info "Applying production optimizations..."
    
    # Create production-optimized configuration
    cat > configs/production.env << EOF
# Production optimizations
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# Performance settings
MODEL_CONTEXT_LENGTH=8192
RAG_MAX_RESULTS=10
CONVERSATION_MEMORY_SIZE=50

# Security settings
SECURE_COOKIES=true
REQUIRE_HTTPS=true
SESSION_TIMEOUT_MINUTES=15
MAX_LOGIN_ATTEMPTS=3
LOCKOUT_DURATION_MINUTES=30

# Rate limiting
RATE_LIMIT_PER_MINUTE=30

# Cache settings
CACHE_TTL_SECONDS=3600
CACHE_MAX_ENTRIES=10000

# Health check settings
HEALTH_CHECK_TIMEOUT=30
HEALTH_CHECK_RETRIES=3
EOF
    
    log_success "Production optimizations applied"
}

deploy_with_monitoring() {
    log_info "Deploying with monitoring enabled..."
    
    # Deploy using the appropriate script
    if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then
        log_info "Kubernetes cluster detected - using K8s deployment"
        ./deploy-k8s.sh deploy
    else
        log_info "Using Podman deployment"
        ./deploy-podman.sh deploy
    fi
    
    # Wait for services to be ready
    log_info "Waiting for services to become ready..."
    sleep 30
    
    # Verify deployment
    local services=("8000" "8001" "8002" "8003" "8004")
    local failed_services=()
    
    for port in "${services[@]}"; do
        if ! curl -sf "http://localhost:$port/health" > /dev/null 2>&1; then
            failed_services+=("$port")
        fi
    done
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        log_error "Health checks failed for services on ports: ${failed_services[*]}"
        return 1
    fi
    
    log_success "All services are healthy"
}

setup_monitoring_alerts() {
    log_info "Setting up monitoring and alerts..."
    
    # Create monitoring configuration
    cat > configs/monitoring.yml << EOF
# Basic monitoring configuration
monitoring:
  enabled: true
  metrics_port: 9090
  health_check_interval: 30
  
alerts:
  email: admin@your-domain.com
  slack_webhook: ""  # Configure if using Slack
  
thresholds:
  cpu_usage: 80
  memory_usage: 85
  disk_usage: 90
  response_time_ms: 2000
  error_rate_percent: 5
EOF
    
    log_success "Monitoring configuration created"
}

generate_production_checklist() {
    log_info "Generating production deployment checklist..."
    
    cat > PRODUCTION_CHECKLIST.md << EOF
# Jerry AI Assistant - Production Deployment Checklist

## Pre-Deployment
- [ ] Updated all secrets from defaults
- [ ] Set ENVIRONMENT=production in .env
- [ ] Configured HTTPS/TLS certificates
- [ ] Set up domain name and DNS
- [ ] Configured firewall rules
- [ ] Set up backup strategy

## Security
- [ ] Generated strong, unique secrets
- [ ] Enabled secure cookies (SECURE_COOKIES=true)
- [ ] Configured HTTPS requirement (REQUIRE_HTTPS=true)
- [ ] Set appropriate session timeouts
- [ ] Configured rate limiting
- [ ] Reviewed file permissions

## Performance
- [ ] Allocated sufficient resources (CPU/RAM)
- [ ] Configured model caching
- [ ] Set up monitoring and alerts
- [ ] Optimized database settings
- [ ] Configured log rotation

## Monitoring
- [ ] Health check endpoints working
- [ ] Metrics collection enabled
- [ ] Log aggregation configured
- [ ] Alerting rules set up
- [ ] Backup monitoring enabled

## Documentation
- [ ] Updated API documentation
- [ ] Created operational runbooks
- [ ] Documented recovery procedures
- [ ] Updated user guides

## Testing
- [ ] Load testing completed
- [ ] Security testing done
- [ ] Backup/restore tested
- [ ] Disaster recovery tested

## Post-Deployment
- [ ] Monitor initial performance
- [ ] Verify all features working
- [ ] Test alert mechanisms
- [ ] Review logs for errors
- [ ] Schedule regular maintenance

## Maintenance
- [ ] Set up automatic updates
- [ ] Schedule regular backups
- [ ] Plan capacity monitoring
- [ ] Document escalation procedures
EOF
    
    log_success "Production checklist created: PRODUCTION_CHECKLIST.md"
}

show_production_summary() {
    log_info "Production Deployment Summary"
    echo "================================="
    echo
    echo "✅ Prerequisites verified"
    echo "✅ Configuration validated"
    echo "✅ Security checks completed"
    echo "✅ Tests passed"
    echo "✅ Services deployed"
    echo "✅ Monitoring configured"
    echo
    echo "🔗 Service URLs:"
    echo "  Web Chat:          http://localhost:8004"
    echo "  Agent Service:     http://localhost:8003"
    echo "  RAG Service:       http://localhost:8002"
    echo "  Model Service:     http://localhost:8001"
    echo "  Vector Database:   http://localhost:8000"
    echo
    echo "📊 Monitoring:"
    echo "  Health checks:     /health endpoint on each service"
    echo "  Metrics:           /metrics endpoint on each service"
    echo "  Logs:              ./logs/jerry.log"
    echo
    echo "🔒 Security:"
    echo "  Environment:       production"
    echo "  HTTPS:             $(grep -q "REQUIRE_HTTPS=true" "$ENV_FILE" && echo "enabled" || echo "disabled")"
    echo "  Rate limiting:     enabled"
    echo "  Session timeout:   $(grep "SESSION_TIMEOUT" "$ENV_FILE" | cut -d'=' -f2) minutes"
    echo
    echo "⚠️  Important Next Steps:"
    echo "1. Review PRODUCTION_CHECKLIST.md"
    echo "2. Configure domain and HTTPS certificates"
    echo "3. Set up external monitoring and alerting"
    echo "4. Schedule regular backups"
    echo "5. Test disaster recovery procedures"
    echo
}

main() {
    local command="${1:-help}"
    
    case "$command" in
        "deploy")
            check_prerequisites
            validate_production_config
            create_backup
            run_security_checks
            run_comprehensive_tests
            setup_production_directories
            optimize_for_production
            deploy_with_monitoring
            setup_monitoring_alerts
            generate_production_checklist
            show_production_summary
            ;;
        "secrets")
            generate_production_secrets
            ;;
        "test")
            run_comprehensive_tests
            ;;
        "validate")
            check_prerequisites
            validate_production_config
            run_security_checks
            ;;
        "backup")
            create_backup
            ;;
        "help"|*)
            cat << EOF
Jerry AI Assistant - Production Deployment Script

Usage: $0 [command]

Commands:
  deploy      Full production deployment with all checks
  secrets     Generate secure production secrets
  test        Run comprehensive test suite
  validate    Validate configuration and security
  backup      Create backup of current deployment
  help        Show this help message

Production Features:
  ✅ Security hardening with secure secrets
  ✅ Comprehensive health checks and monitoring
  ✅ Performance optimization
  ✅ Automated testing and validation
  ✅ Backup and recovery procedures
  ✅ Production configuration management
  ✅ Monitoring and alerting setup
  ✅ Documentation generation

For more information, see docs/deployment.md
EOF
            ;;
    esac
}

# Run main function with all arguments
main "$@"