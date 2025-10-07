#!/bin/bash#!/bin/bash



# Jerry AI Production Deployment Manager# Jerry AI Production Deployment Manager

# Organizational script - manages containerized services using Podman

# Main services run in containers, only organizational functions on host# Organizational script that manages containerized services using Podman Kubernetes# Organizational script that manages containerized services using Podman Kubernetes



set -e# All main services run in containers, only organizational functions on host# All main services run in containers, only organizational functions on host



# Colors

RED='\033[0;31m'

GREEN='\033[0;32m'set -euo pipefailset -euo pipefail

YELLOW='\033[1;33m'

BLUE='\033[0;34m'

NC='\033[0m'

# Colors for output# Colors for output

log_info() {

    echo -e "${BLUE}[INFO]${NC} $1"RED='\033[0;31m'RED='\033[0;31m'

}

GREEN='\033[0;32m'GREEN='\033[0;32m'

log_success() {

    echo -e "${GREEN}[SUCCESS]${NC} $1"YELLOW='\033[1;33m'YELLOW='\033[1;33m'

}

BLUE='\033[0;34m'BLUE='\033[0;34m'

log_warning() {

    echo -e "${YELLOW}[WARNING]${NC} $1"PURPLE='\033[0;35m'PURPLE='\033[0;35m'

}

NC='\033[0m' # No ColorNC='\033[0m' # No Color

log_error() {

    echo -e "${RED}[ERROR]${NC} $1"

}

# Configuration# Configuration

check_prerequisites() {

    log_info "Checking prerequisites..."SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    

    if ! command -v podman &> /dev/null; thenPROJECT_ROOT="$SCRIPT_DIR"PROJECT_ROOT="$SCRIPT_DIR"

        log_error "Podman is not installed"

        exit 1NAMESPACE="jerry"NAMESPACE="jerry"

    fi

    POD_NAME="jerry-stack"POD_NAME="jerry-stack"

    if ! podman info &> /dev/null; then

        log_error "Podman service is not running"

        exit 1

    fi# Functions# Functions

    

    log_success "Prerequisites OK"log_info() {log_info() {

}

    echo -e "${BLUE}[INFO]${NC} $1"    echo -e "${BLUE}[INFO]${NC} $1"

create_minimal_pod() {

    log_info "Creating minimal Jerry pod manifest..."}}

    

    cat > jerry-minimal.yaml << 'EOF'

apiVersion: v1

kind: Podlog_success() {log_success() {

metadata:

  name: jerry-minimal    echo -e "${GREEN}[SUCCESS]${NC} $1"    echo -e "${GREEN}[SUCCESS]${NC} $1"

  labels:

    app: jerry-ai}}

    environment: production

spec:

  containers:

  - name: vector-dblog_warning() {log_warning() {

    image: docker.io/chromadb/chroma:latest

    ports:    echo -e "${YELLOW}[WARNING]${NC} $1"    echo -e "${YELLOW}[WARNING]${NC} $1"

    - containerPort: 8000

      hostPort: 8000}}

    env:

    - name: ALLOW_RESET

      value: "true"

    - name: ANONYMIZED_TELEMETRYlog_error() {log_error() {

      value: "false"

    volumeMounts:    echo -e "${RED}[ERROR]${NC} $1"    echo -e "${RED}[ERROR]${NC} $1"

    - name: chroma-data

      mountPath: /chroma/chroma}}

      

  volumes:

  - name: chroma-data

    hostPath:check_prerequisites() {check_prerequisites() {

      path: ./data/chroma

      type: DirectoryOrCreate    log_info "Checking prerequisites..."    log_info "Checking prerequisites..."

EOF

        

    log_success "Created jerry-minimal.yaml"

}    # Check Podman    # Check Podman



deploy_pod() {    if ! command -v podman &> /dev/null; then    if ! command -v podman &> /dev/null; then

    log_info "Deploying Jerry minimal infrastructure..."

            log_error "Podman is not installed"        log_error "Podman is not installed"

    # Ensure directories exist

    mkdir -p data/chroma logs        exit 1        exit 1

    

    # Stop existing pod if running    fi    fi

    podman kube down jerry-minimal.yaml 2>/dev/null || true

            

    # Deploy

    if podman kube play jerry-minimal.yaml; then    # Check if Podman service is running    # Check if Podman service is running

        log_success "Jerry infrastructure deployed"

        return 0    if ! podman info &> /dev/null; then    if ! podman info &> /dev/null; then

    else

        log_error "Deployment failed"        log_error "Podman service is not running"        log_error "Podman service is not running"

        return 1

    fi        log_info "Start with: sudo systemctl start podman"        log_info "Start with: sudo systemctl start podman"

}

        exit 1        exit 1

start_dashboard() {

    log_info "Starting organizational dashboard..."    fi    fi

    

    # Stop existing dashboard        

    pkill -f simple_dashboard.py 2>/dev/null || true

    sleep 1    # Check uv    # Check uv

    

    # Start new dashboard    if ! command -v uv &> /dev/null; then    if ! command -v uv &> /dev/null; then

    python3 simple_dashboard.py &

    local pid=$!        log_error "uv is not installed"        log_error "uv is not installed"

    

    log_success "Dashboard started (PID: $pid)"        exit 1        exit 1

    log_info "Access at: http://localhost:8080"

}    fi    fi



show_status() {        

    log_info "Jerry AI Status:"

    echo    log_success "Prerequisites check passed"    log_success "Prerequisites check passed"

    

    echo "Pods:"}}

    podman pod ls | grep jerry || echo "No Jerry pods"

    echo

    

    echo "Containers:"create_minimal_pod() {build_images() {

    podman ps | grep jerry || echo "No Jerry containers"

    echo    log_info "Creating minimal Jerry pod (ChromaDB only)..."    log_info "Building Jerry service images..."

    

    echo "Health Checks:"        

    if curl -s --connect-timeout 2 http://localhost:8000/api/v1/heartbeat >/dev/null 2>&1; then

        echo "  ✅ ChromaDB: http://localhost:8000"    cat > jerry-minimal.yaml << 'EOF'    cd "$PROJECT_ROOT"

    else

        echo "  ❌ ChromaDB: http://localhost:8000"apiVersion: v1    

    fi

    kind: Pod    # Build images using existing Dockerfiles

    if curl -s --connect-timeout 2 http://localhost:8080 >/dev/null 2>&1; then

        echo "  ✅ Dashboard: http://localhost:8080"metadata:    local images=(

    else

        echo "  ❌ Dashboard: http://localhost:8080"  name: jerry-minimal        "configs/Dockerfile.model:jerry-model:latest"

    fi

}  labels:        "configs/Dockerfile.rag:jerry-rag:latest" 



cleanup() {    app: jerry-ai        "configs/Dockerfile.agent:jerry-agent:latest"

    log_info "Cleaning up..."

        environment: production        "configs/Dockerfile.webchat:jerry-webchat:latest"

    podman kube down jerry-minimal.yaml 2>/dev/null || true

    pkill -f simple_dashboard.py 2>/dev/null || true    tier: infrastructure    )

    rm -f jerry-minimal.yaml

    spec:    

    log_success "Cleanup completed"

}  containers:    for image_spec in "${images[@]}"; do



main() {  # ChromaDB Vector Database        IFS=':' read -r dockerfile image_name tag <<< "$image_spec"

    case "${1:-help}" in

        "deploy")  - name: vector-db        

            check_prerequisites

            create_minimal_pod    image: docker.io/chromadb/chroma:latest        if [[ -f "$dockerfile" ]]; then

            deploy_pod

            start_dashboard    ports:            log_info "Building $image_name:$tag from $dockerfile"

            show_status

            ;;    - containerPort: 8000            podman build -f "$dockerfile" -t "$image_name:$tag" . || {

        "status")

            show_status      hostPort: 8000                log_warning "Failed to build $image_name:$tag - skipping"

            ;;

        "stop")    env:                continue

            cleanup

            ;;    - name: ALLOW_RESET            }

        "dashboard")

            start_dashboard      value: "true"            log_success "Built $image_name:$tag"

            ;;

        "help"|*)    - name: ANONYMIZED_TELEMETRY        else

            echo "Jerry AI Production Deployment Manager"

            echo      value: "false"            log_warning "Dockerfile not found: $dockerfile - skipping"

            echo "Commands:"

            echo "  deploy    - Deploy infrastructure (ChromaDB + Dashboard)"    volumeMounts:        fi

            echo "  status    - Show service status"

            echo "  stop      - Stop all services"    - name: chroma-data    done

            echo "  dashboard - Start dashboard only"

            echo "  help      - Show this help"      mountPath: /chroma/chroma}

            echo

            echo "Architecture: Containerized services with host-based organization"      

            ;;

    esac  volumes:create_pod_manifest() {

}

  - name: chroma-data    log_info "Creating Jerry pod manifest..."

main "$@"
    hostPath:    

      path: ./data/chroma    cat > jerry-pod.yaml << 'EOF'

      type: DirectoryOrCreateapiVersion: v1

EOFkind: Pod

metadata:

    log_success "Created jerry-minimal.yaml"  name: jerry-stack

}  labels:

    app: jerry-ai

deploy_pod() {    environment: production

    local manifest_file="$1"spec:

    local pod_name="$2"  containers:

      # ChromaDB Vector Database

    log_info "Deploying $pod_name using $manifest_file..."  - name: vector-db

        image: docker.io/chromadb/chroma:latest

    # Ensure data directories exist    ports:

    mkdir -p data/chroma data/models logs    - containerPort: 8000

          hostPort: 8000

    # Stop existing pod if running    env:

    podman kube down "$manifest_file" 2>/dev/null || true    - name: ALLOW_RESET

          value: "true"

    # Deploy the pod    - name: ANONYMIZED_TELEMETRY

    if podman kube play "$manifest_file"; then      value: "false"

        log_success "$pod_name deployed successfully"    volumeMounts:

        return 0    - name: chroma-data

    else      mountPath: /chroma/chroma

        log_error "Failed to deploy $pod_name"    

        return 1  # Model Service (if image built successfully)

    fi  - name: model-service

}    image: localhost/jerry-model:latest

    ports:

show_status() {    - containerPort: 8001

    log_info "Jerry AI Service Status:"      hostPort: 8001

    echo ""    env:

        - name: MODEL_PATH

    # Show pods      value: "/app/models"

    echo "Podman Pods:"    - name: MODEL_CONTEXT_LENGTH

    podman pod ls | grep -E "(POD ID|jerry)" || echo "No Jerry pods found"      value: "4096"

    echo ""    - name: LOG_LEVEL

          value: "INFO"

    # Show containers    volumeMounts:

    echo "Running Containers:"    - name: models-data

    podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -1      mountPath: /app/models

    podman ps | grep jerry || echo "No Jerry containers running"    - name: logs-data

    echo ""      mountPath: /app/logs

          

    # Test service endpoints  # RAG Service (if image built successfully)  

    echo "Service Health Checks:"  - name: rag-service

    test_endpoint "ChromaDB" "http://localhost:8000/api/v1/heartbeat"    image: localhost/jerry-rag:latest

    test_endpoint "Model Service" "http://localhost:8001/health"    ports:

    test_endpoint "RAG Service" "http://localhost:8002/health"      - containerPort: 8002

    test_endpoint "Agent Service" "http://localhost:8003/health"      hostPort: 8002

    test_endpoint "Web Chat" "http://localhost:8004/health"    env:

        - name: CHROMA_HOST

    echo ""      value: "localhost"

    log_info "Dashboard available at: http://localhost:8080"    - name: CHROMA_PORT

}      value: "8000"

    - name: LOG_LEVEL

test_endpoint() {      value: "INFO"

    local service_name="$1"    dependsOn:

    local endpoint="$2"    - vector-db

        

    if curl -s --connect-timeout 2 "$endpoint" >/dev/null 2>&1; then  # Agent Service (if image built successfully)

        echo "  ✅ $service_name: $endpoint"  - name: agent-service

    else    image: localhost/jerry-agent:latest

        echo "  ❌ $service_name: $endpoint"    ports:

    fi    - containerPort: 8003

}      hostPort: 8003

    env:

cleanup() {    - name: MODEL_SERVICE_URL

    log_info "Cleaning up Jerry deployment..."      value: "http://localhost:8001"

        - name: RAG_SERVICE_URL

    # Stop pods      value: "http://localhost:8002"

    podman kube down jerry-minimal.yaml 2>/dev/null || true    - name: LOG_LEVEL

          value: "INFO"

    # Remove any standalone containers    dependsOn:

    podman rm -f $(podman ps -a --filter label=app=jerry-ai -q) 2>/dev/null || true    - model-service

        - rag-service

    # Clean up pod manifests    

    rm -f jerry-minimal.yaml  # Web Chat Interface (if image built successfully)

      - name: web-chat

    log_success "Cleanup completed"    image: localhost/jerry-webchat:latest

}    ports:

    - containerPort: 8004

start_dashboard() {      hostPort: 8004

    log_info "Starting organizational dashboard..."    env:

        - name: AGENT_SERVICE_URL

    # Kill any existing dashboard      value: "http://localhost:8003"

    pkill -f simple_dashboard || true    - name: LOG_LEVEL

          value: "INFO"

    # Start dashboard in background    dependsOn:

    python3 simple_dashboard.py &    - agent-service

    local dashboard_pid=$!    

      volumes:

    log_success "Dashboard started (PID: $dashboard_pid)"  - name: chroma-data

    log_info "Access at: http://localhost:8080"    hostPath:

}      path: ./data/chroma

      type: DirectoryOrCreate

# Main deployment logic  - name: models-data

main() {    hostPath:

    case "${1:-help}" in      path: ./data/models

        "deploy")      type: DirectoryOrCreate

            check_prerequisites  - name: logs-data

            create_minimal_pod    hostPath:

            deploy_pod "jerry-minimal.yaml" "jerry-minimal"      path: ./logs

            start_dashboard      type: DirectoryOrCreate

            show_statusEOF

            ;;

        "status")    log_success "Created jerry-pod.yaml"

            show_status}

            ;;

        "stop")create_minimal_pod() {

            cleanup    log_info "Creating minimal Jerry pod (ChromaDB only)..."

            pkill -f simple_dashboard || true    

            ;;    cat > jerry-minimal.yaml << 'EOF'

        "restart")apiVersion: v1

            cleanupkind: Pod

            sleep 2metadata:

            main deploy  name: jerry-minimal

            ;;  labels:

        "dashboard")    app: jerry-ai

            start_dashboard    environment: production

            ;;    tier: infrastructure

        "help"|"--help"|"-h")spec:

            echo "Jerry AI Production Deployment Manager"  containers:

            echo ""  # ChromaDB Vector Database

            echo "Usage: $0 <command>"  - name: vector-db

            echo ""    image: docker.io/chromadb/chroma:latest

            echo "Commands:"    ports:

            echo "  deploy     - Deploy Jerry infrastructure (ChromaDB + Dashboard)"    - containerPort: 8000

            echo "  status     - Show current deployment status"      hostPort: 8000

            echo "  stop       - Stop and clean up deployment"    env:

            echo "  restart    - Restart deployment"    - name: ALLOW_RESET

            echo "  dashboard  - Start organizational dashboard only"      value: "true"

            echo "  help       - Show this help message"    - name: ANONYMIZED_TELEMETRY

            echo ""      value: "false"

            echo "Examples:"    volumeMounts:

            echo "  $0 deploy     # Deploy infrastructure"    - name: chroma-data

            echo "  $0 status     # Check status"      mountPath: /chroma/chroma

            echo "  $0 dashboard  # Start dashboard only"      

            echo ""  volumes:

            echo "Architecture:"  - name: chroma-data

            echo "  - All main services run in Podman containers"    hostPath:

            echo "  - Only organizational functions run on host"      path: ./data/chroma

            echo "  - ChromaDB provides vector storage foundation"      type: DirectoryOrCreate

            echo "  - Dashboard provides monitoring and status"EOF

            ;;

        *)    log_success "Created jerry-minimal.yaml"

            log_error "Unknown command: $1"}

            main help

            exit 1deploy_pod() {

            ;;    local manifest_file="$1"

    esac    local pod_name="$2"

}    

    log_info "Deploying $pod_name using $manifest_file..."

# Run main function with all arguments    

main "$@"    # Ensure data directories exist
    mkdir -p data/chroma data/models logs
    
    # Stop existing pod if running
    podman kube down "$manifest_file" 2>/dev/null || true
    
    # Deploy the pod
    if podman kube play "$manifest_file"; then
        log_success "$pod_name deployed successfully"
        return 0
    else
        log_error "Failed to deploy $pod_name"
        return 1
    fi
}

show_status() {
    log_info "Jerry AI Service Status:"
    echo ""
    
    # Show pods
    echo "Podman Pods:"
    podman pod ls | grep -E "(POD ID|jerry)" || echo "No Jerry pods found"
    echo ""
    
    # Show containers
    echo "Running Containers:"
    podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -1
    podman ps | grep jerry || echo "No Jerry containers running"
    echo ""
    
    # Test service endpoints
    echo "Service Health Checks:"
    test_endpoint "ChromaDB" "http://localhost:8000/api/v1/heartbeat"
    test_endpoint "Model Service" "http://localhost:8001/health"
    test_endpoint "RAG Service" "http://localhost:8002/health"  
    test_endpoint "Agent Service" "http://localhost:8003/health"
    test_endpoint "Web Chat" "http://localhost:8004/health"
    
    echo ""
    log_info "Dashboard available at: http://localhost:8080"
}

test_endpoint() {
    local service_name="$1"
    local endpoint="$2"
    
    if curl -s --connect-timeout 2 "$endpoint" >/dev/null 2>&1; then
        echo "  ✅ $service_name: $endpoint"
    else
        echo "  ❌ $service_name: $endpoint"
    fi
}

cleanup() {
    log_info "Cleaning up Jerry deployment..."
    
    # Stop pods
    podman kube down jerry-pod.yaml 2>/dev/null || true
    podman kube down jerry-minimal.yaml 2>/dev/null || true
    
    # Remove any standalone containers
    podman rm -f $(podman ps -a --filter label=app=jerry-ai -q) 2>/dev/null || true
    
    # Clean up pod manifests
    rm -f jerry-pod.yaml jerry-minimal.yaml
    
    log_success "Cleanup completed"
}

# Main deployment logic
main() {
    case "${1:-help}" in
        "build")
            check_prerequisites
            build_images
            ;;
        "deploy")
            check_prerequisites
            create_pod_manifest
            if deploy_pod "jerry-pod.yaml" "jerry-stack"; then
                show_status
            else
                log_warning "Full deployment failed, trying minimal deployment..."
                create_minimal_pod
                deploy_pod "jerry-minimal.yaml" "jerry-minimal"
                show_status
            fi
            ;;
        "minimal")
            check_prerequisites
            create_minimal_pod
            deploy_pod "jerry-minimal.yaml" "jerry-minimal"
            show_status
            ;;
        "status")
            show_status
            ;;
        "stop")
            cleanup
            ;;
        "restart")
            cleanup
            sleep 2
            main deploy
            ;;
        "help"|"--help"|"-h")
            echo "Jerry AI Production Deployment Manager"
            echo ""
            echo "Usage: $0 <command>"
            echo ""
            echo "Commands:"
            echo "  build    - Build all Jerry service images"
            echo "  deploy   - Deploy full Jerry stack (with fallback to minimal)"
            echo "  minimal  - Deploy minimal stack (ChromaDB only)"
            echo "  status   - Show current deployment status"
            echo "  stop     - Stop and clean up deployment"
            echo "  restart  - Restart deployment"
            echo "  help     - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 minimal    # Start with ChromaDB only"
            echo "  $0 build      # Build service images"  
            echo "  $0 deploy     # Full deployment"
            echo "  $0 status     # Check status"
            ;;
        *)
            log_error "Unknown command: $1"
            main help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
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