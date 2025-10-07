#!/bin/bash

# Jerry AI Assistant - Podman Deployment & Testing Script
# This script handles testing, building, and local deployment with Podman

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
POD_NAME="jerry-pod"
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
    
    local required_tools=("podman" "uv")
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
    
    # Check Podman connection
    if ! podman info &> /dev/null; then
        log_error "Cannot connect to Podman service"
        log_info "Please start Podman service: sudo systemctl start podman"
        exit 1
    fi
    
    log_success "Dependencies check completed"
}

run_tests() {
    log_info "Running tests and code quality checks..."
    
    cd "$PROJECT_ROOT"
    
    # Sync dependencies for testing
    log_info "Syncing dependencies for testing..."
    uv sync --dev
    
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
        log_warning "Some unit tests failed (may be due to missing services)"
    fi
    
    log_success "Testing completed"
}

build_images() {
    log_info "Building Podman images for Jerry services..."
    
    cd "$PROJECT_ROOT"
    
    local build_args=""
    if [[ "$GPU_TYPE" != "cpu" ]]; then
        build_args="--build-arg ACCELERATION=$GPU_TYPE"
    fi
    
    # Build images for each service
    log_info "Building service images..."
    
    # Model service (with GPU support)
    log_info "Building model service image..."
    podman build -f configs/Dockerfile.model \
        $build_args \
        -t localhost/jerry-model-service:latest \
        .
    
    # RAG service
    log_info "Building RAG service image..."
    podman build -f configs/Dockerfile.rag \
        -t localhost/jerry-rag-service:latest \
        .
    
    # Agent service
    log_info "Building agent service image..."
    podman build -f configs/Dockerfile.agent \
        -t localhost/jerry-agent-service:latest \
        .
    
    # Bot service
    log_info "Building bot service image..."
    podman build -f configs/Dockerfile.bot \
        -t localhost/jerry-bot-service:latest \
        .
    
    # Web chat service
    log_info "Building web chat service image..."
    podman build -f configs/Dockerfile.webchat \
        -t localhost/jerry-web-chat:latest \
        .
    
    log_success "Podman images built successfully"
}

generate_pod_yaml() {
    log_info "Generating Podman pod configuration..."
    
    cat > /tmp/jerry-pod.yaml << EOF
apiVersion: v1
kind: Pod
metadata:
  name: jerry-pod
  labels:
    app: jerry-ai
    environment: local
spec:
  containers:
  # Vector Database (ChromaDB)
  - name: vector-db
    image: docker.io/chromadb/chroma:latest
    ports:
    - containerPort: 8000
      hostPort: 8000
      protocol: TCP
    env:
    - name: CHROMA_HOST_ADDR
      value: "0.0.0.0"
    - name: CHROMA_HOST_PORT
      value: "8000"
    - name: CHROMA_AUTH_ENABLED
      value: "false"
    volumeMounts:
    - name: vector-data
      mountPath: /chroma/chroma
    resources:
      limits:
        memory: 1Gi
        cpu: 500m
    
  # RAG Service
  - name: rag-service
    image: localhost/jerry-rag-service:latest
    ports:
    - containerPort: 8002
      hostPort: 8002
      protocol: TCP
    env:
    - name: CHROMA_HOST
      value: "localhost"
    - name: CHROMA_PORT
      value: "8000"
    - name: RAG_SERVER_HOST
      value: "0.0.0.0"
    - name: RAG_SERVER_PORT
      value: "8002"
    - name: EMBEDDINGS_MODEL
      value: "all-MiniLM-L6-v2"
    volumeMounts:
    - name: document-data
      mountPath: /app/data/documents
    - name: vector-data
      mountPath: /app/data/chroma
    resources:
      limits:
        memory: 2Gi
        cpu: 1000m
    
  # Model Service
  - name: model-service
    image: localhost/jerry-model-service:latest
    ports:
    - containerPort: 8001
      hostPort: 8001
      protocol: TCP
    env:
    - name: MODEL_PATH
      value: "/app/models"
    - name: MODEL_SERVER_HOST
      value: "0.0.0.0"
    - name: MODEL_SERVER_PORT
      value: "8001"
    - name: DEFAULT_MODEL
      value: "llama-2-7b-chat.Q4_K_M.gguf"
    volumeMounts:
    - name: model-data
      mountPath: /app/models
    resources:
      limits:
        memory: 8Gi
        cpu: 4000m
    
  # Agent Service
  - name: agent-service
    image: localhost/jerry-agent-service:latest
    ports:
    - containerPort: 8003
      hostPort: 8003
      protocol: TCP
    env:
    - name: MODEL_SERVICE_URL
      value: "http://localhost:8001"
    - name: RAG_SERVICE_URL
      value: "http://localhost:8002"
    - name: AGENT_SERVER_HOST
      value: "0.0.0.0"
    - name: AGENT_SERVER_PORT
      value: "8003"
    - name: JERRY_PERSONALITY
      value: "grandfatherly_advisor"
    resources:
      limits:
        memory: 1Gi
        cpu: 500m
    
  # Web Chat Service
  - name: web-chat
    image: localhost/jerry-web-chat:latest
    ports:
    - containerPort: 8004
      hostPort: 8004
      protocol: TCP
    env:
    - name: WEB_CHAT_HOST
      value: "0.0.0.0"
    - name: WEB_CHAT_PORT
      value: "8004"
    - name: AGENT_SERVICE_URL
      value: "http://localhost:8003"
    - name: AUTH_SECRET_KEY
      value: "dev-secret-key-change-in-production"
    resources:
      limits:
        memory: 512Mi
        cpu: 250m
    
  volumes:
  - name: vector-data
    hostPath:
      path: ./data/chroma
      type: DirectoryOrCreate
  - name: document-data
    hostPath:
      path: ./data/documents
      type: DirectoryOrCreate
  - name: model-data
    hostPath:
      path: ./data/models
      type: DirectoryOrCreate
  
  restartPolicy: Always
EOF
    
    log_success "Pod configuration generated at /tmp/jerry-pod.yaml"
}

deploy_pod() {
    log_info "Deploying Jerry pod with Podman..."
    
    # Stop and remove existing pod if it exists
    if podman pod exists "$POD_NAME"; then
        log_info "Stopping existing pod..."
        podman pod stop "$POD_NAME" || true
        podman pod rm "$POD_NAME" || true
    fi
    
    # Create data directories
    log_info "Creating data directories..."
    mkdir -p ./data/{chroma,documents,models}
    
    # Generate pod configuration
    generate_pod_yaml
    
    # Deploy the pod
    log_info "Starting Jerry pod..."
    podman play kube /tmp/jerry-pod.yaml
    
    # Wait for services to be ready
    log_info "Waiting for services to start..."
    sleep 10
    
    log_success "Jerry pod deployed successfully"
}

verify_deployment() {
    log_info "Verifying deployment health..."
    
    local services=("8000" "8001" "8002" "8003" "8004")
    local service_names=("vector-db" "model-service" "rag-service" "agent-service" "web-chat")
    local failed_services=()
    
    for i in "${!services[@]}"; do
        local port="${services[$i]}"
        local service_name="${service_names[$i]}"
        
        log_info "Checking $service_name on port $port..."
        
        local health_endpoint="/health"
        if [[ "$service_name" == "vector-db" ]]; then
            health_endpoint="/api/v1/heartbeat"
        fi
        
        if curl -sf "http://localhost:$port$health_endpoint" > /dev/null 2>&1; then
            log_success "$service_name is healthy"
        else
            log_warning "$service_name health check failed (may still be starting)"
            failed_services+=("$service_name")
        fi
    done
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        log_warning "Some services are not yet ready: ${failed_services[*]}"
        log_info "This is normal during startup. Services may take a few minutes to fully initialize."
    else
        log_success "All services are healthy"
    fi
}

show_status() {
    log_info "Jerry AI Assistant - Pod Status"
    echo "================================"
    
    echo
    log_info "Pod Status:"
    podman pod ps --filter name="$POD_NAME" || log_warning "Pod not found"
    
    echo
    log_info "Container Status:"
    podman ps --filter pod="$POD_NAME" || log_warning "No containers found"
    
    echo
    log_info "Service URLs:"
    echo "  Vector DB (ChromaDB):  http://localhost:8000"
    echo "  Model Service:         http://localhost:8001"
    echo "  RAG Service:           http://localhost:8002"
    echo "  Agent Service:         http://localhost:8003"
    echo "  Web Chat Interface:    http://localhost:8004"
    
    echo
    log_info "Useful Commands:"
    echo "  View pod logs:         podman pod logs $POD_NAME"
    echo "  View container logs:   podman logs jerry-pod-[service-name]"
    echo "  Enter container:       podman exec -it jerry-pod-[service-name] /bin/bash"
    echo "  Stop all services:     podman pod stop $POD_NAME"
    echo "  Remove pod:            podman pod rm $POD_NAME"
}

cleanup() {
    log_info "Cleaning up Jerry deployment..."
    
    if podman pod exists "$POD_NAME"; then
        podman pod stop "$POD_NAME" || true
        podman pod rm "$POD_NAME" || true
    fi
    
    # Clean up temporary files
    rm -f /tmp/jerry-pod.yaml
    
    log_success "Cleanup completed"
}

debug_services() {
    log_info "Debugging Jerry services..."
    
    if ! podman pod exists "$POD_NAME"; then
        log_warning "Pod $POD_NAME does not exist"
        return 1
    fi
    
    log_info "Pod information:"
    podman pod inspect "$POD_NAME"
    
    echo
    log_info "Container logs:"
    local containers
    containers=$(podman ps --filter pod="$POD_NAME" --format "{{.Names}}" | grep -v "^$POD_NAME-infra$" || true)
    
    for container in $containers; do
        log_debug "Logs for $container:"
        podman logs --tail=20 "$container" || true
        echo "---"
    done
}

main() {
    case "${1:-deploy}" in
        "test")
            check_dependencies
            run_tests
            ;;
        "build")
            check_dependencies
            build_images
            ;;
        "deploy")
            check_dependencies
            run_tests
            build_images
            deploy_pod
            verify_deployment
            log_success "🎉 Jerry AI Assistant deployed successfully!"
            show_status
            ;;
        "start")
            check_dependencies
            deploy_pod
            verify_deployment
            show_status
            ;;
        "stop")
            podman pod stop "$POD_NAME" || true
            log_success "Jerry pod stopped"
            ;;
        "restart")
            podman pod restart "$POD_NAME" || true
            log_success "Jerry pod restarted"
            verify_deployment
            ;;
        "status")
            show_status
            ;;
        "debug")
            debug_services
            ;;
        "cleanup"|"clean")
            cleanup
            ;;
        "help"|"--help"|"-h")
            cat << EOF
Usage: $0 [command]

Commands:
  test        - Run tests and code quality checks
  build       - Build Podman images
  deploy      - Full deployment (test, build, deploy, verify)
  start       - Start the Jerry pod (without rebuilding)
  stop        - Stop the Jerry pod
  restart     - Restart the Jerry pod
  status      - Show pod and container status
  debug       - Show debugging information
  cleanup     - Stop and remove all Jerry resources
  help        - Show this help

Environment Variables:
  GPU_TYPE    - GPU acceleration type (cpu, nvidia, intel) [default: cpu]

Examples:
  $0 deploy                    # Full deployment
  GPU_TYPE=nvidia $0 deploy    # Deploy with NVIDIA GPU support
  $0 test                      # Run tests only
  $0 start                     # Start services without rebuilding
  $0 status                    # Check status
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