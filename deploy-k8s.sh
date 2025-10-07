#!/bin/bash

# Jerry AI Assistant - Kubernetes Deployment & Testing Script
# This script handles testing, debugging, and production deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
NAMESPACE="jerry"
CONTEXT="${KUBE_CONTEXT:-$(kubectl config current-context)}"
GPU_TYPE="${GPU_TYPE:-cpu}"  # cpu, nvidia, intel
BUILD_CACHE="${BUILD_CACHE:-false}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${PURPLE}[DEBUG]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    local required_tools=("kubectl" "podman" "uv")
    local missing_tools=()
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install the missing tools before continuing."
        exit 1
    fi
    
    # Check Kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Dependencies check completed"
}

run_tests() {
    log_info "Running tests and code quality checks..."
    
    cd "$PROJECT_ROOT"
    
    # Sync dependencies without llama-cpp-python (host testing)
    log_info "Syncing dependencies for testing..."
    uv sync
    
    # Run linting with ruff
    log_info "Running code linting..."
    if uv run ruff check src/ tests/ --fix; then
        log_success "Code linting passed"
    else
        log_warning "Code linting found issues (fixed automatically)"
    fi
    
    # Run formatting check
    log_info "Checking code formatting..."
    if uv run ruff format src/ tests/ --check; then
        log_success "Code formatting is correct"
    else
        log_warning "Code formatting issues found. Run 'uv run ruff format src/ tests/' to fix."
    fi
    
    # Run type checking (if mypy is available)
    if uv run python -c "import mypy" &> /dev/null; then
        log_info "Running type checking..."
        if uv run mypy src/ --ignore-missing-imports; then
            log_success "Type checking passed"
        else
            log_warning "Type checking found issues"
        fi
    fi
    
    # Run unit tests
    log_info "Running unit tests..."
    if uv run pytest tests/unit/ -v --tb=short; then
        log_success "Unit tests passed"
    else
        log_error "Unit tests failed"
        return 1
    fi
    
    # Run contract tests (if services are available)
    log_info "Running contract tests..."
    if uv run pytest tests/contract/ -v --tb=short; then
        log_success "Contract tests passed"
    else
        log_warning "Contract tests failed (services may not be running)"
    fi
    
    log_success "Testing completed"
}

debug_services() {
    log_info "Debugging Jerry services..."
    
    # Check namespace
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE does not exist"
        return 1
    fi
    
    # Check all deployments
    log_info "Checking deployment status..."
    kubectl get deployments -n "$NAMESPACE"
    
    # Check pods
    log_info "Checking pod status..."
    kubectl get pods -n "$NAMESPACE" -o wide
    
    # Check services
    log_info "Checking service status..."
    kubectl get services -n "$NAMESPACE"
    
    # Check for unhealthy pods
    local unhealthy_pods
    unhealthy_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running -o name 2>/dev/null || true)
    
    if [[ -n "$unhealthy_pods" ]]; then
        log_warning "Found unhealthy pods:"
        echo "$unhealthy_pods"
        
        # Show logs for unhealthy pods
        for pod in $unhealthy_pods; do
            pod_name=$(echo "$pod" | cut -d'/' -f2)
            log_debug "Logs for $pod_name:"
            kubectl logs -n "$NAMESPACE" "$pod_name" --tail=20 || true
            echo "---"
        done
    fi
    
    # Check resource usage
    log_info "Checking resource usage..."
    kubectl top pods -n "$NAMESPACE" 2>/dev/null || log_warning "Metrics server not available"
    
    log_success "Debug information gathered"
}

build_images() {
    log_info "Building Podman images for Jerry services..."
    
    cd "$PROJECT_ROOT"
    
    local build_args=""
    if [[ "$GPU_TYPE" != "cpu" ]]; then
        build_args="--build-arg ACCELERATION=$GPU_TYPE"
    fi
    
    # Build base image for all services
    log_info "Building base service images..."
    
    # Model service (with GPU support)
    log_info "Building model service image..."
    podman build -f configs/Dockerfile.model.multi-gpu \
        $build_args \
        -t jerry/model-service:latest \
        -t jerry/model-service:$GPU_TYPE \
        .
    
    # RAG service
    log_info "Building RAG service image..."
    podman build -f configs/Dockerfile.rag \
        -t jerry/rag-service:latest \
        .
    
    # Agent service
    log_info "Building agent service image..."
    podman build -f configs/Dockerfile.agent \
        -t jerry/agent-service:latest \
        .
    
    # Web chat service
    log_info "Building web chat service image..."
    podman build -f configs/Dockerfile.webchat \
        -t jerry/web-chat:latest \
        .
    
    log_success "Podman images built successfully"
}

create_namespace() {
    log_info "Creating Kubernetes namespace and resources..."
    
    # Apply namespace and config
    kubectl apply -f k8s/00-namespace-config.yaml
    
    # Wait for namespace to be ready
    kubectl wait --for=condition=Active namespace/$NAMESPACE --timeout=30s
    
    log_success "Namespace created"
}

deploy_storage() {
    log_info "Deploying storage resources..."
    
    # Create data directories on nodes (if using local storage)
    local nodes
    nodes=$(kubectl get nodes -o jsonpath='{.items[*].metadata.name}')
    
    for node in $nodes; do
        log_info "Creating data directories on node: $node"
        # This assumes you have SSH access to nodes or can run privileged pods
        kubectl debug node/"$node" -it --image=busybox -- sh -c "
            mkdir -p /host/data/jerry/{vector_db,models,documents}
            chmod 755 /host/data/jerry
            chmod 755 /host/data/jerry/*
        " 2>/dev/null || log_warning "Could not create directories on $node"
    done
    
    # Apply storage resources
    kubectl apply -f k8s/01-storage.yaml
    
    log_success "Storage resources deployed"
}

deploy_services() {
    log_info "Deploying Jerry services..."
    
    # Deploy in order of dependencies
    local services=(
        "02-vector-db.yaml"
        "03-model-service.yaml"
        "04-rag-service.yaml"
        "05-agent-service.yaml"
        "06-web-chat.yaml"
    )
    
    for service_file in "${services[@]}"; do
        log_info "Deploying $service_file..."
        
        # Update GPU configuration in model service
        if [[ "$service_file" == "03-model-service.yaml" && "$GPU_TYPE" != "cpu" ]]; then
            # Create temporary file with GPU configuration
            local temp_file="/tmp/jerry-model-service.yaml"
            sed "s/jerry.ai\/gpu-type: cpu/jerry.ai\/gpu-type: $GPU_TYPE/g" "k8s/$service_file" > "$temp_file"
            
            if [[ "$GPU_TYPE" == "nvidia" ]]; then
                sed -i 's/# nvidia.com\/gpu: 1/nvidia.com\/gpu: 1/g' "$temp_file"
            elif [[ "$GPU_TYPE" == "intel" ]]; then
                sed -i 's/# intel.com\/gpu: 1/intel.com\/gpu: 1/g' "$temp_file"
            fi
            
            kubectl apply -f "$temp_file"
            rm -f "$temp_file"
        else
            kubectl apply -f "k8s/$service_file"
        fi
        
        # Wait for deployment to be ready
        if [[ "$service_file" != "06-web-chat.yaml" ]]; then  # Skip ingress
            local deployment_name
            deployment_name=$(basename "$service_file" .yaml | sed 's/^[0-9]*-//')
            log_info "Waiting for $deployment_name to be ready..."
            kubectl wait --for=condition=available deployment/"$deployment_name" -n "$NAMESPACE" --timeout=300s
        fi
    done
    
    log_success "All services deployed"
}

verify_deployment() {
    log_info "Verifying deployment health..."
    
    local services=("vector-db:8000" "model-service:8001" "rag-service:8002" "agent-service:8003" "web-chat:8004")
    local failed_services=()
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r service_name port <<< "$service_info"
        
        log_info "Checking $service_name health..."
        
        # Port forward and test
        local pf_pid
        kubectl port-forward -n "$NAMESPACE" "service/$service_name" "$port:$port" &
        pf_pid=$!
        
        sleep 5  # Give port-forward time to establish
        
        local health_endpoint="/health"
        if [[ "$service_name" == "vector-db" ]]; then
            health_endpoint="/api/v1/heartbeat"
        fi
        
        if curl -sf "http://localhost:$port$health_endpoint" > /dev/null; then
            log_success "$service_name is healthy"
        else
            log_error "$service_name health check failed"
            failed_services+=("$service_name")
        fi
        
        # Clean up port forward
        kill $pf_pid 2>/dev/null || true
        sleep 2
    done
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        log_error "Health checks failed for: ${failed_services[*]}"
        return 1
    fi
    
    log_success "All services are healthy"
}

run_integration_tests() {
    log_info "Running integration tests..."
    
    # Port forward to web chat service for testing
    kubectl port-forward -n "$NAMESPACE" service/web-chat 8004:8004 &
    local pf_pid=$!
    
    sleep 5
    
    # Run integration tests
    cd "$PROJECT_ROOT"
    if uv run pytest tests/integration/ -v --tb=short; then
        log_success "Integration tests passed"
    else
        log_error "Integration tests failed"
        kill $pf_pid 2>/dev/null || true
        return 1
    fi
    
    # Clean up port forward
    kill $pf_pid 2>/dev/null || true
    
    log_success "Integration testing completed"
}

prepare_production() {
    log_info "Preparing for production deployment..."
    
    # Security checks
    log_info "Running security checks..."
    
    # Check for default secrets
    local default_secrets
    default_secrets=$(kubectl get secret jerry-secrets -n "$NAMESPACE" -o yaml | grep -E "(staging-secret|change-me)" || true)
    
    if [[ -n "$default_secrets" ]]; then
        log_error "Default/staging secrets found! Please update secrets for production."
        log_info "Update the following secrets in k8s/00-namespace-config.yaml:"
        log_info "  - AUTH_SECRET_KEY"
        log_info "  - JWT_SECRET"
        log_info "  - ENCRYPTION_KEY"
        log_info "  - Cloudflare tunnel credentials (if using)"
        return 1
    fi
    
    # Check resource limits
    log_info "Checking resource limits..."
    local pods_without_limits
    pods_without_limits=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].resources.limits}{"\n"}{end}' | grep -v "map\[" || true)
    
    if [[ -n "$pods_without_limits" ]]; then
        log_warning "Some pods don't have resource limits set"
    fi
    
    # Generate production configuration
    log_info "Generating production configuration..."
    
    cat > k8s/production-config.yaml << EOF
# Production Configuration for Jerry AI Assistant
# Apply this configuration for production deployment

apiVersion: v1
kind: ConfigMap
metadata:
  name: jerry-production-config
  namespace: jerry
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  LOG_LEVEL: "WARNING"
  
  # Security Settings
  SECURE_COOKIES: "true"
  REQUIRE_HTTPS: "true"
  SESSION_TIMEOUT_MINUTES: "15"
  MAX_LOGIN_ATTEMPTS: "3"
  LOCKOUT_DURATION_MINUTES: "30"
  
  # Performance Settings
  MODEL_CONTEXT_LENGTH: "8192"
  RAG_MAX_RESULTS: "10"
  RATE_LIMIT_PER_MINUTE: "30"

---
# Production Ingress with TLS
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: jerry-production-ingress
  namespace: jerry
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/rate-limit: "30"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - jerry.yourdomain.com
    secretName: jerry-production-tls
  rules:
  - host: jerry.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-chat
            port:
              number: 8004
EOF
    
    log_info "Production configuration generated at k8s/production-config.yaml"
    
    # Create backup of current deployment
    log_info "Creating deployment backup..."
    local backup_dir="backups/$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    
    kubectl get all -n "$NAMESPACE" -o yaml > "$backup_dir/jerry-deployment.yaml"
    kubectl get secrets -n "$NAMESPACE" -o yaml > "$backup_dir/jerry-secrets.yaml"
    kubectl get configmaps -n "$NAMESPACE" -o yaml > "$backup_dir/jerry-configmaps.yaml"
    
    log_success "Backup created at $backup_dir"
    
    # Production checklist
    cat << EOF

${GREEN}Production Deployment Checklist:${NC}
================================

${YELLOW}Before deploying to production:${NC}

1. 🔐 Update all secrets in k8s/00-namespace-config.yaml
   - AUTH_SECRET_KEY (generate new 64-char random string)
   - JWT_SECRET (generate new 64-char random string)
   - ENCRYPTION_KEY (generate new 32-char random string)
   - Cloudflare tunnel credentials

2. 🌐 Configure your domain and DNS
   - Update hostname in k8s/production-config.yaml
   - Set up SSL certificates

3. 📊 Set up monitoring and logging
   - Deploy Prometheus/Grafana for metrics
   - Configure log aggregation (ELK/Loki)
   - Set up alerting

4. 🔄 Configure backups
   - Database backups
   - Model file backups
   - Configuration backups

5. 🛡️  Security hardening
   - Network policies
   - Pod security policies
   - RBAC configuration

6. 🧪 Load testing
   - Test with expected user load
   - Verify auto-scaling works

${GREEN}Commands to deploy to production:${NC}
kubectl apply -f k8s/production-config.yaml
kubectl patch deployment web-chat -n jerry -p '{"spec":{"template":{"spec":{"containers":[{"name":"web-chat","envFrom":[{"configMapRef":{"name":"jerry-production-config"}}]}]}}}}'

EOF
    
    log_success "Production preparation completed"
}

show_status() {
    log_info "Jerry AI Assistant - Deployment Status"
    echo "========================================"
    
    echo
    log_info "Namespace: $NAMESPACE"
    log_info "Context: $CONTEXT"
    log_info "GPU Type: $GPU_TYPE"
    
    echo
    log_info "Deployments:"
    kubectl get deployments -n "$NAMESPACE" -o wide 2>/dev/null || log_warning "No deployments found"
    
    echo
    log_info "Services:"
    kubectl get services -n "$NAMESPACE" -o wide 2>/dev/null || log_warning "No services found"
    
    echo
    log_info "Pods:"
    kubectl get pods -n "$NAMESPACE" -o wide 2>/dev/null || log_warning "No pods found"
    
    echo
    log_info "Ingress:"
    kubectl get ingress -n "$NAMESPACE" 2>/dev/null || log_warning "No ingress found"
    
    echo
    log_info "Useful Commands:"
    echo "  View logs:        kubectl logs -f deployment/[service] -n $NAMESPACE"
    echo "  Port forward:     kubectl port-forward service/web-chat 8004:8004 -n $NAMESPACE"
    echo "  Scale service:    kubectl scale deployment [service] --replicas=N -n $NAMESPACE"
    echo "  Debug pod:        kubectl exec -it deployment/[service] -n $NAMESPACE -- /bin/bash"
    echo "  Delete all:       kubectl delete namespace $NAMESPACE"
}

cleanup() {
    log_info "Cleaning up Jerry deployment..."
    kubectl delete namespace "$NAMESPACE" --wait=true
    log_success "Cleanup completed"
}

main() {
    case "${1:-deploy}" in
        "test")
            check_dependencies
            run_tests
            ;;
        "debug")
            check_dependencies
            debug_services
            ;;
        "build")
            check_dependencies
            build_images
            ;;
        "deploy")
            check_dependencies
            run_tests
            build_images
            create_namespace
            deploy_storage
            deploy_services
            verify_deployment
            run_integration_tests
            log_success "🎉 Jerry AI Assistant deployed successfully!"
            show_status
            ;;
        "prod"|"production")
            check_dependencies
            debug_services
            prepare_production
            ;;
        "status")
            show_status
            ;;
        "cleanup"|"delete")
            cleanup
            ;;
        "help"|"--help"|"-h")
            cat << EOF
Usage: $0 [command]

Commands:
  test        - Run tests and code quality checks
  debug       - Debug current deployment
  build       - Build Docker images
  deploy      - Full deployment (test, build, deploy, verify)
  prod        - Prepare for production deployment
  status      - Show deployment status
  cleanup     - Delete all Jerry resources
  help        - Show this help

Environment Variables:
  GPU_TYPE    - GPU acceleration type (cpu, nvidia, intel) [default: cpu]
  KUBE_CONTEXT - Kubernetes context to use [default: current]

Examples:
  $0 deploy                    # Deploy with CPU-only
  GPU_TYPE=nvidia $0 deploy    # Deploy with NVIDIA GPU support
  $0 test                      # Run tests only
  $0 prod                      # Prepare for production
EOF
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Use '$0 help' for available commands"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
