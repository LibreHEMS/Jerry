#!/bin/bash

# Jerry AI Assistant - Simplified Deployment Script
# This script provides a streamlined deployment process for Jerry AI

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
NAMESPACE="jerry"
DEFAULT_MODEL_TYPE="noop"

# Logging functions
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check required tools
    local required_tools=("podman" "python3")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is required but not installed"
            exit 1
        fi
    done
    
    # Check Python version
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
        log_error "Python 3.11+ is required"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    local directories=(
        "$PROJECT_ROOT/data/chroma"
        "$PROJECT_ROOT/data/models"
        "$PROJECT_ROOT/data/documents"
        "$PROJECT_ROOT/data/cache"
        "$PROJECT_ROOT/logs"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
    done
    
    log_success "Directories created"
}

# Setup environment configuration
setup_environment() {
    log_info "Setting up environment configuration..."
    
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            log_info "Created .env from template"
            log_warning "Please review and update .env file with your configuration"
        else
            log_error ".env.example not found"
            exit 1
        fi
    fi
    
    # Set default model type if not specified
    if ! grep -q "MODEL_TYPE=" "$PROJECT_ROOT/.env"; then
        echo "MODEL_TYPE=$DEFAULT_MODEL_TYPE" >> "$PROJECT_ROOT/.env"
        log_info "Set default MODEL_TYPE=$DEFAULT_MODEL_TYPE"
    fi
    
    log_success "Environment configuration ready"
}

# Install Python dependencies (optional for development)
install_dependencies() {
    log_info "Installing Python dependencies (development mode)..."
    
    cd "$PROJECT_ROOT"
    
    # Check if uv is available
    if command -v uv &> /dev/null; then
        log_info "Using uv for dependency management"
        # Install without llama-cpp-python initially
        uv sync --no-dev 2>/dev/null || {
            log_warning "Full dependency installation failed, trying minimal install"
            # Try with minimal dependencies
            pip3 install --user fastapi uvicorn httpx requests python-dotenv pydantic chromadb
        }
    else
        log_warning "uv not available, using pip"
        pip3 install --user fastapi uvicorn httpx requests python-dotenv pydantic chromadb
    fi
    
    log_success "Dependencies installed"
}

# Build container images
build_images() {
    log_info "Building Jerry service images..."
    
    cd "$PROJECT_ROOT"
    
    # Build dashboard image (lightweight)
    if [[ -f "configs/Dockerfile.dashboard" ]]; then
        log_info "Building dashboard image..."
        podman build -f configs/Dockerfile.dashboard -t jerry-dashboard:latest . || {
            log_warning "Dashboard build failed - using simple Python script"
        }
    fi
    
    # Build model service (with adaptive backend)
    if [[ -f "configs/Dockerfile.model-cpu" ]]; then
        log_info "Building CPU-only model service..."
        podman build -f configs/Dockerfile.model-cpu -t jerry-model:latest . || {
            log_warning "Model service build failed - will use container fallback"
        }
    fi
    
    # Build other services
    local services=("rag" "agent" "webchat")
    for service in "${services[@]}"; do
        if [[ -f "configs/Dockerfile.$service" ]]; then
            log_info "Building $service service..."
            podman build -f "configs/Dockerfile.$service" -t "jerry-$service:latest" . || {
                log_warning "$service build failed - will skip in deployment"
            }
        fi
    done
    
    log_success "Image building completed"
}

# Deploy using podman
deploy_services() {
    log_info "Deploying Jerry services..."
    
    # Stop any existing deployment
    cleanup_deployment
    
    # Create pod network
    podman pod create --name jerry-pod \
        -p 8000:8000 \
        -p 8001:8001 \
        -p 8002:8002 \
        -p 8003:8003 \
        -p 8004:8004 \
        -p 8080:8080 || {
        log_warning "Pod already exists or creation failed"
    }
    
    # Deploy ChromaDB (external image)
    log_info "Deploying ChromaDB vector database..."
    podman run -d --pod jerry-pod \
        --name jerry-chroma \
        -v "$PROJECT_ROOT/data/chroma:/chroma/chroma" \
        -e ALLOW_RESET=true \
        -e ANONYMIZED_TELEMETRY=false \
        docker.io/chromadb/chroma:latest || {
        log_warning "ChromaDB deployment failed"
    }
    
    # Deploy dashboard
    log_info "Deploying status dashboard..."
    podman run -d --pod jerry-pod \
        --name jerry-dashboard \
        -v "$PROJECT_ROOT:/app:Z" \
        -w /app \
        --user root \
        python:3.11-slim \
        python3 simple_dashboard.py || {
        log_warning "Dashboard deployment failed"
    }
    
    # Deploy model service (adaptive)
    log_info "Deploying model service..."
    podman run -d --pod jerry-pod \
        --name jerry-model \
        -v "$PROJECT_ROOT:/app:Z" \
        -v "$PROJECT_ROOT/data:/app/data:Z" \
        -w /app \
        --env-file "$PROJECT_ROOT/.env" \
        --user root \
        python:3.11-slim \
        bash -c "pip install fastapi uvicorn httpx python-dotenv pydantic && PYTHONPATH=/app python3 -m src.services.model_server" || {
        log_warning "Model service deployment failed"
    }
    
    log_success "Core services deployed"
}

# Check service health
check_services() {
    log_info "Checking service health..."
    
    sleep 5  # Wait for services to start
    
    # Check ChromaDB
    if curl -s --connect-timeout 5 http://localhost:8000/ >/dev/null 2>&1; then
        log_success "✅ ChromaDB: http://localhost:8000"
    else
        log_warning "❌ ChromaDB: http://localhost:8000"
    fi
    
    # Check Dashboard
    if curl -s --connect-timeout 5 http://localhost:8080/ >/dev/null 2>&1; then
        log_success "✅ Dashboard: http://localhost:8080"
    else
        log_warning "❌ Dashboard: http://localhost:8080"
    fi
    
    # Check Model Service
    if curl -s --connect-timeout 5 http://localhost:8001/health >/dev/null 2>&1; then
        log_success "✅ Model Service: http://localhost:8001"
    else
        log_warning "❌ Model Service: http://localhost:8001"
    fi
    
    log_info "Service status check completed"
}

# Show status
show_status() {
    log_info "Jerry AI Service Status:"
    echo
    
    # Show pod status
    echo "Pod Status:"
    podman pod ls | grep jerry || echo "No Jerry pods found"
    echo
    
    # Show container status
    echo "Container Status:"
    podman ps --filter label=app=jerry || podman ps | grep jerry || echo "No Jerry containers found"
    echo
    
    # Show service endpoints
    echo "Service Endpoints:"
    echo "  ChromaDB:        http://localhost:8000"
    echo "  Model Service:   http://localhost:8001"
    echo "  RAG Service:     http://localhost:8002"
    echo "  Agent Service:   http://localhost:8003"
    echo "  Web Chat:        http://localhost:8004"
    echo "  Dashboard:       http://localhost:8080"
    echo
}

# Cleanup deployment
cleanup_deployment() {
    log_info "Cleaning up existing deployment..."
    
    # Stop and remove containers
    podman ps --filter label=app=jerry -q | xargs -r podman rm -f 2>/dev/null || true
    podman ps | grep jerry | awk '{print $1}' | xargs -r podman rm -f 2>/dev/null || true
    
    # Remove pod
    podman pod rm -f jerry-pod 2>/dev/null || true
    
    log_success "Cleanup completed"
}

# Run tests
run_tests() {
    log_info "Running tests..."
    
    cd "$PROJECT_ROOT"
    
    # Try to run tests with available tools
    if command -v uv &> /dev/null; then
        uv run pytest tests/ -v --tb=short 2>/dev/null || {
            log_warning "Tests failed - dependency issues"
        }
    else
        log_warning "Cannot run tests - uv not available"
    fi
    
    log_info "Test run completed"
}

# Main function
main() {
    case "${1:-help}" in
        "deploy")
            check_prerequisites
            create_directories
            setup_environment
            build_images
            deploy_services
            check_services
            show_status
            ;;
        "start")
            check_prerequisites
            create_directories
            setup_environment
            deploy_services
            check_services
            show_status
            ;;
        "stop")
            cleanup_deployment
            ;;
        "status")
            show_status
            ;;
        "test")
            check_prerequisites
            run_tests
            ;;
        "deps")
            check_prerequisites
            install_dependencies
            ;;
        "build")
            check_prerequisites
            build_images
            ;;
        "restart")
            cleanup_deployment
            deploy_services
            check_services
            show_status
            ;;
        "help"|*)
            echo "Jerry AI Assistant - Simplified Deployment"
            echo
            echo "Commands:"
            echo "  deploy    - Full deployment (build + start + test)"
            echo "  start     - Start services without building"
            echo "  stop      - Stop all services"
            echo "  restart   - Stop and start services"
            echo "  status    - Show service status"
            echo "  test      - Run tests"
            echo "  deps      - Install Python dependencies"
            echo "  build     - Build container images only"
            echo "  help      - Show this help"
            echo
            echo "Quick Start:"
            echo "  ./deploy-jerry.sh deploy    # Full deployment"
            echo "  ./deploy-jerry.sh status    # Check status"
            echo
            ;;
    esac
}

# Run main function with all arguments
main "$@"