#!/bin/bash
# JARVIS AI Assistant - Deployment Script

set -e

echo "🚀 JARVIS AI Assistant - Docker Deployment Script"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if Docker is installed
check_docker() {
    print_status "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Check for NVIDIA Docker support
check_nvidia_docker() {
    print_status "Checking NVIDIA Docker support..."
    if command -v nvidia-docker &> /dev/null || docker info | grep -q nvidia; then
        print_success "NVIDIA Docker support detected"
        export NVIDIA_DOCKER_AVAILABLE=true
    else
        print_warning "NVIDIA Docker support not detected. GPU acceleration will not be available."
        export NVIDIA_DOCKER_AVAILABLE=false
    fi
}

# Create environment file if it doesn't exist
create_env_file() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        print_status "Creating .env file..."
        cat > .env << EOF
# JARVIS Environment Configuration
OPENAI_API_KEY=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
OPENWEATHER_API_KEY=your_weather_api_key_here
NEWS_API_KEY=your_news_api_key_here

# JARVIS Configuration
JARVIS_NAME=JARVIS
JARVIS_VOICE_ENABLED=true
JARVIS_CAMERA_ENABLED=true
JARVIS_WEB_ENABLED=true

# Web Interface Configuration
WEB_HOST=0.0.0.0
WEB_PORT=5000
WEB_DEBUG=false

# Logging Configuration
LOG_LEVEL=INFO
EOF
        print_success ".env file created with OpenRouter API key"
    else
        print_success ".env file already exists"
    fi
}

# Build Docker image
build_image() {
    print_status "Building JARVIS Docker image..."
    
    if [ "$NVIDIA_DOCKER_AVAILABLE" = true ]; then
        docker build -t jarvis-ai:latest .
    else
        # Build without NVIDIA base image for systems without GPU
        docker build -t jarvis-ai:latest -f Dockerfile.cpu .
    fi
    
    print_success "Docker image built successfully"
}

# Create CPU-only Dockerfile if needed
create_cpu_dockerfile() {
    if [ "$NVIDIA_DOCKER_AVAILABLE" = false ]; then
        print_status "Creating CPU-only Dockerfile..."
        cat > Dockerfile.cpu << 'EOF'
# JARVIS AI Assistant - CPU-only Docker Image
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    git \
    wget \
    curl \
    ffmpeg \
    portaudio19-dev \
    libasound2-dev \
    libsndfile1-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 jarvis && chown -R jarvis:jarvis /app
USER jarvis

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (CPU versions)
RUN python3 -m pip install --user --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN python3 -m pip install --user --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=jarvis:jarvis . .

# Create necessary directories
RUN mkdir -p jarvis/logs jarvis/photos jarvis/temp jarvis/models

# Set Python path
ENV PYTHONPATH=/app
ENV PATH=/home/jarvis/.local/bin:$PATH

# Expose ports
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1

# Default command
CMD ["python3", "jarvis_simple_launcher.py"]
EOF
        print_success "CPU-only Dockerfile created"
    fi
}

# Start services
start_services() {
    print_status "Starting JARVIS services..."
    
    # Create necessary directories
    mkdir -p jarvis/logs jarvis/photos jarvis/temp
    
    # Start with docker-compose
    docker-compose up -d
    
    print_success "JARVIS services started"
    print_status "Web interface will be available at: http://localhost:5000"
    print_status "Logs can be viewed with: docker-compose logs -f jarvis"
}

# Show status
show_status() {
    print_status "Checking service status..."
    docker-compose ps
    
    echo ""
    print_status "JARVIS is now running!"
    print_status "🌐 Web Interface: http://localhost:5000"
    print_status "📊 Health Check: http://localhost:5000/api/status"
    print_status "📝 View Logs: docker-compose logs -f jarvis"
    print_status "🛑 Stop Services: docker-compose down"
}

# Main deployment process
main() {
    echo ""
    print_status "Starting JARVIS deployment process..."
    
    check_docker
    check_nvidia_docker
    create_env_file
    create_cpu_dockerfile
    build_image
    start_services
    
    echo ""
    print_success "🎉 JARVIS deployment completed successfully!"
    echo ""
    show_status
    
    echo ""
    print_status "Next steps:"
    echo "1. Open http://localhost:5000 in your browser"
    echo "2. Test voice commands or text chat"
    echo "3. Check logs with: docker-compose logs -f jarvis"
    echo "4. Edit .env file to add more API keys if needed"
    echo ""
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "build")
        check_docker
        check_nvidia_docker
        create_cpu_dockerfile
        build_image
        ;;
    "start")
        start_services
        ;;
    "stop")
        print_status "Stopping JARVIS services..."
        docker-compose down
        print_success "Services stopped"
        ;;
    "status")
        show_status
        ;;
    "logs")
        docker-compose logs -f jarvis
        ;;
    "clean")
        print_status "Cleaning up Docker resources..."
        docker-compose down -v
        docker rmi jarvis-ai:latest 2>/dev/null || true
        print_success "Cleanup completed"
        ;;
    *)
        echo "Usage: $0 {deploy|build|start|stop|status|logs|clean}"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full deployment (default)"
        echo "  build   - Build Docker image only"
        echo "  start   - Start services"
        echo "  stop    - Stop services"
        echo "  status  - Show service status"
        echo "  logs    - Show service logs"
        echo "  clean   - Clean up all resources"
        exit 1
        ;;
esac
