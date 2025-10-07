#!/bin/bash

# Jerry AI Production Infrastructure Manager
# Organizational script for managing fully containerized Jerry AI infrastructure
# ALL services run in containers - this script only provides organizational functions

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_status() {
    log_info "Jerry AI Infrastructure Status"
    echo "================================================"
    
    echo
    echo "Pods:"
    podman pod ls | head -1
    podman pod ls | grep jerry || echo "No Jerry pods running"
    
    echo
    echo "Containers:"
    podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -1
    podman ps | grep jerry || echo "No Jerry containers running"
    
    echo
    echo "Service Health:"
    if curl -s --connect-timeout 3 http://localhost:8000/api/v1/version >/dev/null 2>&1; then
        echo "  ✅ ChromaDB Vector Database: http://localhost:8000"
    else
        echo "  ❌ ChromaDB Vector Database: http://localhost:8000"
    fi
    
    if curl -s --connect-timeout 3 http://localhost:8080 >/dev/null 2>&1; then
        echo "  ✅ Organizational Dashboard: http://localhost:8080"
    else
        echo "  ❌ Organizational Dashboard: http://localhost:8080"
    fi
    
    echo
    echo "Architecture:"
    echo "  📦 All services containerized with Podman"
    echo "  🏗️  Infrastructure-as-Code with Kubernetes manifests"
    echo "  🔧 Host provides organizational functions only"
}

deploy() {
    log_info "Deploying Jerry AI Infrastructure..."
    
    # Ensure directories exist
    mkdir -p data/chroma logs
    
    # Deploy infrastructure pod
    if podman kube play jerry-minimal.yaml; then
        log_success "Jerry infrastructure deployed successfully"
        echo
        log_info "Services starting up..."
        sleep 5
        show_status
    else
        log_error "Infrastructure deployment failed"
        return 1
    fi
}

stop() {
    log_info "Stopping Jerry AI Infrastructure..."
    
    podman kube down jerry-minimal.yaml 2>/dev/null || true
    
    log_success "Infrastructure stopped"
}

restart() {
    stop
    sleep 2
    deploy
}

logs() {
    local container_name=${1:-jerry-infrastructure-dashboard}
    log_info "Showing logs for: $container_name"
    podman logs -f "$container_name"
}

main() {
    case "${1:-help}" in
        "deploy"|"start")
            deploy
            ;;
        "status")
            show_status
            ;;
        "stop")
            stop
            ;;
        "restart")
            restart
            ;;
        "logs")
            logs "$2"
            ;;
        "help"|*)
            echo "Jerry AI Production Infrastructure Manager"
            echo
            echo "Commands:"
            echo "  deploy/start  - Deploy infrastructure (ChromaDB + Dashboard)"
            echo "  status        - Show infrastructure status" 
            echo "  stop          - Stop all infrastructure"
            echo "  restart       - Restart infrastructure"
            echo "  logs [name]   - Show container logs"
            echo "  help          - Show this help"
            echo
            echo "Examples:"
            echo "  $0 deploy                           # Deploy infrastructure"
            echo "  $0 status                           # Check status"
            echo "  $0 logs jerry-infrastructure-dashboard  # View dashboard logs"
            echo
            echo "Best Practices Implementation:"
            echo "  ✅ All main services containerized"
            echo "  ✅ Host runs organizational functions only"
            echo "  ✅ Infrastructure-as-Code with Kubernetes manifests"
            echo "  ✅ Proper container orchestration with Podman"
            echo
            echo "Access Points:"
            echo "  📊 ChromaDB: http://localhost:8000"
            echo "  📈 Dashboard: http://localhost:8080"
            ;;
    esac
}

main "$@"