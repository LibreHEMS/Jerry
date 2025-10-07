#!/bin/bash
# Production Readiness Validation Script for Jerry AI Assistant
# This script validates that all production requirements are met

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
WARNINGS=0

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
}

check_project_structure() {
    log_info "Validating project structure..."
    
    # Required directories
    local required_dirs=(
        "src/services"
        "src/utils"
        "src/data"
        "src/rag"
        "src/prompts"
        "tests/unit"
        "tests/integration"
        "tests/contract"
        "Resources"
        "docs"
        "configs"
        "specs/001-jerry-self-hosted"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            log_success "Directory exists: $dir"
        else
            log_error "Missing required directory: $dir"
        fi
    done
    
    # Required files
    local required_files=(
        "pyproject.toml"
        "README.md"
        "LICENSE"
        ".env.example"
        "deploy-podman.sh"
        "deploy-production.sh"
        "ruff.toml"
    )
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "File exists: $file"
        else
            log_error "Missing required file: $file"
        fi
    done
}

check_python_environment() {
    log_info "Validating Python environment..."
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        local python_version
        python_version=$(python3 --version | cut -d' ' -f2)
        if [[ "$python_version" =~ ^3\.(9|10|11|12) ]]; then
            if [[ "$python_version" =~ ^3\.(11|12) ]]; then
                log_success "Python version: $python_version (recommended)"
            else
                log_warning "Python version: $python_version (3.11+ recommended)"
            fi
        else
            log_error "Python 3.9+ required (found: $python_version)"
        fi
    else
        log_error "Python 3 not found"
    fi
    
    # Check uv
    if command -v uv &> /dev/null; then
        log_success "uv package manager available"
    else
        log_error "uv package manager not found"
    fi
    
    # Check dependencies
    if [[ -f "pyproject.toml" ]]; then
        log_success "pyproject.toml configuration found"
    else
        log_error "pyproject.toml not found"
    fi
}

check_containerization() {
    log_info "Validating containerization setup..."
    
    # Check Podman
    if command -v podman &> /dev/null; then
        log_success "Podman available"
    else
        log_warning "Podman not found (Docker may be used instead)"
    fi
    
    # Check Dockerfiles
    local dockerfiles=(
        "configs/Dockerfile.agent"
        "configs/Dockerfile.model"
        "configs/Dockerfile.rag"
        "configs/Dockerfile.webchat"
    )
    
    for dockerfile in "${dockerfiles[@]}"; do
        if [[ -f "$dockerfile" ]]; then
            log_success "Dockerfile exists: $dockerfile"
        else
            log_error "Missing Dockerfile: $dockerfile"
        fi
    done
    
    # Check deployment scripts
    local deploy_scripts=(
        "deploy-podman.sh"
        "deploy-production.sh"
    )
    
    for script in "${deploy_scripts[@]}"; do
        if [[ -f "$script" && -x "$script" ]]; then
            log_success "Deployment script: $script"
        else
            log_error "Missing or non-executable deployment script: $script"
        fi
    done
}

check_services() {
    log_info "Validating service implementations..."
    
    # Core services
    local services=(
        "src/services/agent_service.py"
        "src/services/model_service.py"
        "src/services/local_model_service.py"
        "src/services/rag_server.py"
        "src/services/web_chat_server.py"
    )
    
    for service in "${services[@]}"; do
        if [[ -f "$service" ]]; then
            log_success "Service implemented: $(basename "$service")"
        else
            log_error "Missing service: $service"
        fi
    done
    
    # Utils and data models
    local core_modules=(
        "src/utils/config.py"
        "src/utils/auth.py"
        "src/utils/health.py"
        "src/utils/metrics.py"
        "src/utils/cache.py"
        "src/data/models.py"
        "src/rag/vector_store.py"
        "src/rag/retriever.py"
    )
    
    for module in "${core_modules[@]}"; do
        if [[ -f "$module" ]]; then
            log_success "Module implemented: $(basename "$module")"
        else
            log_error "Missing module: $module"
        fi
    done
}

check_documentation() {
    log_info "Validating documentation..."
    
    # Core documentation
    local core_docs=(
        "README.md"
        "docs/api.md"
        "docs/deployment.md"
        "specs/001-jerry-self-hosted/plan.md"
        "specs/001-jerry-self-hosted/spec.md"
        "specs/001-jerry-self-hosted/tasks.md"
    )
    
    for doc in "${core_docs[@]}"; do
        if [[ -f "$doc" ]]; then
            log_success "Documentation: $(basename "$doc")"
        else
            log_error "Missing documentation: $doc"
        fi
    done
    
    # Energy-specific documentation
    local energy_docs=(
        "Resources/emhass_integration.md"
        "Resources/home_assistant_integration.md"
        "Resources/jinja2_templates.md"
        "Resources/amber_electric_integration.md"
        "Resources/vehicle_to_grid_v2g.md"
        "Resources/feed_in_tariffs.md"
        "Resources/guide_to_household_solar.md"
        "Resources/open_source_ems.md"
    )
    
    for doc in "${energy_docs[@]}"; do
        if [[ -f "$doc" ]]; then
            log_success "Energy documentation: $(basename "$doc")"
        else
            log_error "Missing energy documentation: $doc"
        fi
    done
}

check_testing() {
    log_info "Validating testing infrastructure..."
    
    # Test files
    local test_files=(
        "tests/unit/test_auth.py"
        "tests/unit/test_config.py"
        "tests/unit/test_health.py"
        "tests/contract/test_agent_service.py"
        "tests/contract/test_model_service.py"
        "tests/contract/test_rag_service.py"
        "tests/integration/test_agent_rag.py"
    )
    
    for test_file in "${test_files[@]}"; do
        if [[ -f "$test_file" ]]; then
            log_success "Test file: $(basename "$test_file")"
        else
            log_error "Missing test file: $test_file"
        fi
    done
    
    # Run tests if possible
    if command -v uv &> /dev/null && [[ -f "pyproject.toml" ]]; then
        log_info "Running test suite..."
        if uv run pytest tests/unit/ -q --tb=no; then
            log_success "Unit tests pass"
        else
            log_error "Unit tests failed"
        fi
    else
        log_warning "Cannot run tests - uv or pyproject.toml missing"
    fi
}

check_security() {
    log_info "Validating security implementation..."
    
    # Security modules
    if [[ -f "src/utils/auth.py" ]]; then
        if grep -q "JWT" "src/utils/auth.py"; then
            log_success "JWT authentication implemented"
        else
            log_warning "JWT authentication not found in auth.py"
        fi
        
        if grep -q "encrypt" "src/utils/auth.py" || grep -q "encrypt" "src/utils/config.py"; then
            log_success "Encryption capabilities implemented"
        else
            log_warning "Encryption not found"
        fi
    else
        log_error "Authentication module missing"
    fi
    
    # Check for sensitive file handling
    if [[ -f ".env.example" ]]; then
        log_success "Environment template provided"
    else
        log_error ".env.example template missing"
    fi
    
    # Check .gitignore
    if [[ -f ".gitignore" ]]; then
        if grep -q ".env" ".gitignore"; then
            log_success ".env files properly ignored"
        else
            log_warning ".env files not in .gitignore"
        fi
    else
        log_warning ".gitignore file missing"
    fi
}

check_monitoring() {
    log_info "Validating monitoring and observability..."
    
    # Health checks
    if [[ -f "src/utils/health.py" ]]; then
        log_success "Health check system implemented"
    else
        log_error "Health check system missing"
    fi
    
    # Metrics
    if [[ -f "src/utils/metrics.py" ]]; then
        if grep -q "prometheus" "src/utils/metrics.py"; then
            log_success "Prometheus metrics implemented"
        else
            log_warning "Prometheus metrics not found"
        fi
    else
        log_error "Metrics system missing"
    fi
    
    # Logging
    if [[ -f "src/utils/logging.py" ]]; then
        log_success "Logging system implemented"
    else
        log_error "Logging system missing"
    fi
}

check_configuration() {
    log_info "Validating configuration management..."
    
    if [[ -f "src/utils/config.py" ]]; then
        if grep -q "dataclass" "src/utils/config.py"; then
            log_success "Structured configuration with dataclasses"
        else
            log_warning "Configuration structure unclear"
        fi
        
        if grep -q "validate" "src/utils/config.py"; then
            log_success "Configuration validation implemented"
        else
            log_warning "Configuration validation not found"
        fi
    else
        log_error "Configuration module missing"
    fi
    
    # Environment configuration
    if [[ -f ".env.example" ]]; then
        local required_vars=(
            "ENVIRONMENT"
            "AUTH_SECRET_KEY"
            "JWT_SECRET"
            "ENCRYPTION_KEY"
        )
        
        for var in "${required_vars[@]}"; do
            if grep -q "^${var}=" ".env.example"; then
                log_success "Environment variable documented: $var"
            else
                log_error "Missing environment variable in template: $var"
            fi
        done
    fi
}

check_performance() {
    log_info "Validating performance optimizations..."
    
    # Caching
    if [[ -f "src/utils/cache.py" ]]; then
        log_success "Caching system implemented"
    else
        log_error "Caching system missing"
    fi
    
    # Database optimization
    if grep -q "connection.*pool" src/services/*.py src/utils/*.py; then
        log_success "Database connection pooling found"
    else
        log_warning "Database connection pooling not clearly implemented"
    fi
    
    # Resource limits in containers
    if grep -q "resources:" configs/*.yml deploy-*.sh 2>/dev/null; then
        log_success "Container resource limits configured"
    else
        log_warning "Container resource limits not found"
    fi
}

show_summary() {
    echo
    echo "========================================"
    echo "  Production Readiness Validation Summary"
    echo "========================================"
    echo
    echo -e "${GREEN}✓ Checks Passed:${NC} $CHECKS_PASSED"
    echo -e "${RED}✗ Checks Failed:${NC} $CHECKS_FAILED"
    echo -e "${YELLOW}⚠ Warnings:${NC} $WARNINGS"
    echo
    
    local total_checks=$((CHECKS_PASSED + CHECKS_FAILED))
    local pass_rate=0
    if [[ $total_checks -gt 0 ]]; then
        pass_rate=$((CHECKS_PASSED * 100 / total_checks))
    fi
    
    echo "Pass Rate: ${pass_rate}%"
    echo
    
    if [[ $CHECKS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}🎉 Jerry is production ready!${NC}"
        echo
        echo "Next steps:"
        echo "1. Configure production environment variables"
        echo "2. Run './deploy-production.sh deploy'"
        echo "3. Review PRODUCTION_CHECKLIST.md"
        echo "4. Set up monitoring and alerting"
        exit 0
    else
        echo -e "${RED}❌ Production readiness issues found${NC}"
        echo
        echo "Please address the failed checks before production deployment."
        exit 1
    fi
}

main() {
    echo "🔍 Jerry AI Assistant - Production Readiness Validation"
    echo "========================================================"
    echo
    
    check_project_structure
    check_python_environment
    check_containerization
    check_services
    check_documentation
    check_testing
    check_security
    check_monitoring
    check_configuration
    check_performance
    
    show_summary
}

# Run validation
main "$@"