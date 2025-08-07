#!/bin/bash
# JARVIS Docker Installation Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect Linux distribution
detect_distro() {
    if [ -f /etc/arch-release ]; then
        echo "arch"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    elif [ -f /etc/redhat-release ]; then
        echo "redhat"
    else
        echo "unknown"
    fi
}

# Check if Docker is already installed
check_docker_installed() {
    if command -v docker &> /dev/null; then
        print_success "Docker is already installed: $(docker --version)"
        
        if command -v docker-compose &> /dev/null; then
            print_success "Docker Compose is already installed: $(docker-compose --version)"
        else
            print_warning "Docker Compose not found, will install it"
            return 1
        fi
        
        # Check if Docker daemon is running
        if docker info &> /dev/null 2>&1; then
            print_success "Docker daemon is running"
            return 0
        else
            print_warning "Docker daemon is not running, will start it"
            return 1
        fi
    else
        print_status "Docker not found, will install it"
        return 1
    fi
}

# Install Docker on Arch Linux
install_docker_arch() {
    print_status "Installing Docker on Arch Linux..."
    
    # Update package database
    sudo pacman -Sy
    
    # Install Docker and Docker Compose
    sudo pacman -S --noconfirm docker docker-compose
    
    print_success "Docker packages installed"
}

# Install Docker on Debian/Ubuntu
install_docker_debian() {
    print_status "Installing Docker on Debian/Ubuntu..."
    
    # Update package index
    sudo apt update
    
    # Install prerequisites
    sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    
    # Add Docker repository
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    
    # Update package index again
    sudo apt update
    
    # Install Docker
    sudo apt install -y docker-ce docker-compose
    
    print_success "Docker packages installed"
}

# Install Docker on Red Hat/CentOS/Fedora
install_docker_redhat() {
    print_status "Installing Docker on Red Hat/CentOS/Fedora..."
    
    # Install Docker
    sudo dnf install -y docker docker-compose
    
    print_success "Docker packages installed"
}

# Configure Docker
configure_docker() {
    print_status "Configuring Docker..."
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    print_success "Added $USER to docker group"
    
    # Start and enable Docker service
    sudo systemctl start docker
    sudo systemctl enable docker
    print_success "Docker service started and enabled"
    
    # Check if Docker daemon is running
    if sudo docker info &> /dev/null; then
        print_success "Docker daemon is running"
    else
        print_error "Docker daemon failed to start"
        return 1
    fi
}

# Test Docker installation
test_docker() {
    print_status "Testing Docker installation..."
    
    # Test Docker
    if sudo docker run --rm hello-world &> /dev/null; then
        print_success "Docker test passed"
    else
        print_error "Docker test failed"
        return 1
    fi
    
    # Test Docker Compose
    if docker-compose --version &> /dev/null; then
        print_success "Docker Compose test passed"
    else
        print_error "Docker Compose test failed"
        return 1
    fi
}

# Install NVIDIA Docker support (if NVIDIA GPU detected)
install_nvidia_docker() {
    if command -v nvidia-smi &> /dev/null; then
        print_status "NVIDIA GPU detected, installing NVIDIA Docker support..."
        
        DISTRO=$(detect_distro)
        
        case $DISTRO in
            "arch")
                # Install nvidia-container-toolkit from AUR
                if command -v yay &> /dev/null; then
                    yay -S --noconfirm nvidia-container-toolkit
                elif command -v paru &> /dev/null; then
                    paru -S --noconfirm nvidia-container-toolkit
                else
                    print_warning "AUR helper not found, skipping NVIDIA Docker support"
                    return 0
                fi
                ;;
            "debian")
                # Add NVIDIA Docker repository
                distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
                curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
                curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
                
                sudo apt update
                sudo apt install -y nvidia-container-toolkit
                ;;
            *)
                print_warning "NVIDIA Docker support not available for this distribution"
                return 0
                ;;
        esac
        
        # Restart Docker
        sudo systemctl restart docker
        print_success "NVIDIA Docker support installed"
    else
        print_status "No NVIDIA GPU detected, skipping NVIDIA Docker support"
    fi
}

# Main installation function
main() {
    echo "🐳 JARVIS Docker Installation Script"
    echo "===================================="
    
    # Detect distribution
    DISTRO=$(detect_distro)
    print_status "Detected distribution: $DISTRO"
    
    # Check if already installed
    if check_docker_installed; then
        print_success "Docker is already properly installed and running!"
        
        # Test JARVIS Docker deployment
        print_status "Testing JARVIS Docker deployment..."
        cd /home/neo/Documents/augment-projects/Sauron
        
        if [ -f "deploy.sh" ]; then
            print_success "JARVIS Docker deployment is ready!"
            echo ""
            echo "🚀 To deploy JARVIS with Docker:"
            echo "   ./deploy.sh"
            echo ""
            echo "🐳 Docker commands:"
            echo "   docker-compose up -d    # Start JARVIS"
            echo "   docker-compose down     # Stop JARVIS"
            echo "   docker-compose logs -f  # View logs"
        else
            print_error "JARVIS Docker files not found"
        fi
        
        return 0
    fi
    
    # Install Docker based on distribution
    case $DISTRO in
        "arch")
            install_docker_arch
            ;;
        "debian")
            install_docker_debian
            ;;
        "redhat")
            install_docker_redhat
            ;;
        *)
            print_error "Unsupported distribution: $DISTRO"
            print_status "Please install Docker manually for your distribution"
            exit 1
            ;;
    esac
    
    # Configure Docker
    configure_docker
    
    # Install NVIDIA Docker support if available
    install_nvidia_docker
    
    # Test installation
    test_docker
    
    print_success "🎉 Docker installation completed successfully!"
    
    echo ""
    echo "📋 Next Steps:"
    echo "1. Log out and log back in (or run: newgrp docker)"
    echo "2. Test Docker: docker run hello-world"
    echo "3. Deploy JARVIS: ./deploy.sh"
    echo ""
    echo "🐳 Docker Commands:"
    echo "   docker --version           # Check Docker version"
    echo "   docker-compose --version   # Check Compose version"
    echo "   docker ps                  # List running containers"
    echo "   docker images              # List images"
    echo ""
    echo "🚀 JARVIS Docker Deployment:"
    echo "   cd /home/neo/Documents/augment-projects/Sauron"
    echo "   ./deploy.sh                # Deploy JARVIS"
    echo ""
    
    print_warning "Please log out and log back in to use Docker without sudo"
}

# Handle command line arguments
case "${1:-install}" in
    "install")
        main
        ;;
    "check")
        check_docker_installed
        ;;
    "test")
        test_docker
        ;;
    *)
        echo "Usage: $0 {install|check|test}"
        echo ""
        echo "Commands:"
        echo "  install  - Install Docker and Docker Compose"
        echo "  check    - Check if Docker is installed"
        echo "  test     - Test Docker installation"
        exit 1
        ;;
esac
