#!/bin/bash
# JARVIS AI Assistant - Desktop Launcher Script

# Colors for notifications
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# JARVIS project directory
JARVIS_DIR="/home/neo/Documents/augment-projects/Sauron"
VENV_PATH="$JARVIS_DIR/nemo_env"

# Function to send desktop notification
send_notification() {
    local title="$1"
    local message="$2"
    local icon="$3"
    
    if command -v notify-send &> /dev/null; then
        notify-send -i "$icon" "$title" "$message"
    fi
}

# Function to check if JARVIS is already running
check_jarvis_running() {
    if pgrep -f "jarvis.*launcher" > /dev/null || pgrep -f "python.*jarvis" > /dev/null; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

# Function to open browser to JARVIS interface
open_jarvis_browser() {
    sleep 3  # Wait for server to start
    
    # Try different browsers
    for browser in firefox google-chrome chromium-browser chrome; do
        if command -v $browser &> /dev/null; then
            $browser "http://localhost:5000" &
            break
        fi
    done
    
    # Fallback to xdg-open
    if ! pgrep -f "http://localhost:5000" > /dev/null; then
        xdg-open "http://localhost:5000" 2>/dev/null &
    fi
}

# Function to launch JARVIS web interface
launch_web_interface() {
    echo -e "${BLUE}🚀 Launching JARVIS Web Interface...${NC}"
    
    # Check if already running
    if check_jarvis_running; then
        send_notification "JARVIS AI Assistant" "JARVIS is already running! Opening web interface..." "dialog-information"
        open_jarvis_browser
        return 0
    fi
    
    # Change to JARVIS directory
    cd "$JARVIS_DIR" || {
        send_notification "JARVIS Error" "Could not find JARVIS directory" "dialog-error"
        exit 1
    }
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_PATH" ]; then
        send_notification "JARVIS Error" "Virtual environment not found. Please run setup first." "dialog-error"
        exit 1
    fi
    
    # Send startup notification
    send_notification "JARVIS AI Assistant" "Starting JARVIS... Please wait..." "dialog-information"
    
    # Activate virtual environment and launch
    source "$VENV_PATH/bin/activate"
    
    # Try simple launcher first
    if [ -f "jarvis_simple_launcher.py" ]; then
        echo -e "${GREEN}🌐 Starting JARVIS Simple Launcher...${NC}"
        
        # Start JARVIS in background
        nohup python jarvis_simple_launcher.py > /tmp/jarvis.log 2>&1 &
        JARVIS_PID=$!
        
        # Wait a moment and check if it started successfully
        sleep 5
        
        if kill -0 $JARVIS_PID 2>/dev/null; then
            send_notification "JARVIS AI Assistant" "JARVIS is now running! Opening web interface..." "dialog-information"
            open_jarvis_browser
            
            # Show success message
            echo -e "${GREEN}✅ JARVIS started successfully!${NC}"
            echo -e "${BLUE}🌐 Web Interface: http://localhost:5000${NC}"
            echo -e "${YELLOW}💡 Say 'Hello JARVIS' to start voice interaction${NC}"
            
        else
            send_notification "JARVIS Error" "Failed to start JARVIS. Check logs for details." "dialog-error"
            echo -e "${RED}❌ Failed to start JARVIS${NC}"
            exit 1
        fi
        
    else
        send_notification "JARVIS Error" "JARVIS launcher not found" "dialog-error"
        exit 1
    fi
}

# Function to launch terminal mode
launch_terminal_mode() {
    echo -e "${BLUE}🖥️ Launching JARVIS Terminal Mode...${NC}"
    
    cd "$JARVIS_DIR" || exit 1
    
    if [ ! -d "$VENV_PATH" ]; then
        echo -e "${RED}❌ Virtual environment not found${NC}"
        exit 1
    fi
    
    # Launch in new terminal
    gnome-terminal --title="JARVIS AI Assistant" -- bash -c "
        cd '$JARVIS_DIR'
        source '$VENV_PATH/bin/activate'
        echo -e '${GREEN}🤖 JARVIS AI Assistant - Terminal Mode${NC}'
        echo -e '${BLUE}=================================${NC}'
        python jarvis_robust.py
        echo -e '${YELLOW}Press Enter to close...${NC}'
        read
    "
}

# Function to launch Docker deployment
launch_docker_deployment() {
    echo -e "${BLUE}🐳 Launching JARVIS Docker Deployment...${NC}"

    cd "$JARVIS_DIR" || exit 1

    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        send_notification "JARVIS Docker" "Docker is not installed. Would you like to install it?" "dialog-question"

        # Launch Docker installation in terminal
        gnome-terminal --title="JARVIS Docker Installation" -- bash -c "
            cd '$JARVIS_DIR'
            echo -e '${YELLOW}🐳 Docker is not installed${NC}'
            echo -e '${BLUE}=========================${NC}'
            echo 'Docker is required for containerized deployment.'
            echo 'JARVIS has created an automated Docker installation script.'
            echo ''
            echo 'Options:'
            echo '1. Install Docker automatically: ./install_docker.sh'
            echo '2. Install Docker manually: See DOCKER_SETUP_GUIDE.md'
            echo '3. Use JARVIS without Docker: ./launch_jarvis_desktop.sh --web'
            echo ''
            read -p 'Install Docker now? (y/N): ' -n 1 -r
            echo
            if [[ \$REPLY =~ ^[Yy]$ ]]; then
                echo 'Installing Docker...'
                ./install_docker.sh
            else
                echo 'Docker installation skipped.'
                echo 'You can install Docker later with: ./install_docker.sh'
                echo 'Or use JARVIS without Docker: ./launch_jarvis_desktop.sh --web'
            fi
            echo ''
            echo -e '${YELLOW}Press Enter to close...${NC}'
            read
        "
        return 1
    fi

    # Check if deploy script exists
    if [ ! -f "deploy.sh" ]; then
        send_notification "JARVIS Error" "Docker deployment script not found" "dialog-error"
        exit 1
    fi

    send_notification "JARVIS AI Assistant" "Starting Docker deployment... This may take a few minutes." "dialog-information"

    # Launch in new terminal
    gnome-terminal --title="JARVIS Docker Deployment" -- bash -c "
        cd '$JARVIS_DIR'
        echo -e '${GREEN}🐳 JARVIS Docker Deployment${NC}'
        echo -e '${BLUE}=========================${NC}'
        ./deploy.sh
        echo -e '${YELLOW}Press Enter to close...${NC}'
        read
    "
}

# Function to show JARVIS status
show_status() {
    echo -e "${BLUE}📊 JARVIS Status Check${NC}"
    echo -e "${BLUE}===================${NC}"
    
    if check_jarvis_running; then
        echo -e "${GREEN}✅ JARVIS is running${NC}"
        echo -e "${BLUE}🌐 Web Interface: http://localhost:5000${NC}"
        
        # Check if web interface is responding
        if curl -s http://localhost:5000/api/status > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Web interface is responding${NC}"
        else
            echo -e "${YELLOW}⚠️ Web interface may not be ready yet${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ JARVIS is not running${NC}"
    fi
    
    # Check system requirements
    echo -e "\n${BLUE}System Requirements:${NC}"
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        echo -e "${GREEN}✅ Python: $PYTHON_VERSION${NC}"
    else
        echo -e "${RED}❌ Python 3 not found${NC}"
    fi
    
    # Check virtual environment
    if [ -d "$VENV_PATH" ]; then
        echo -e "${GREEN}✅ Virtual environment: Found${NC}"
    else
        echo -e "${RED}❌ Virtual environment: Not found${NC}"
    fi
    
    # Check Docker
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}✅ Docker: Available${NC}"
    else
        echo -e "${YELLOW}⚠️ Docker: Not available${NC}"
    fi
}

# Function to stop JARVIS
stop_jarvis() {
    echo -e "${YELLOW}🛑 Stopping JARVIS...${NC}"
    
    # Kill JARVIS processes
    pkill -f "jarvis.*launcher" 2>/dev/null
    pkill -f "python.*jarvis" 2>/dev/null
    
    # Stop Docker containers if running
    if command -v docker-compose &> /dev/null; then
        cd "$JARVIS_DIR" 2>/dev/null && docker-compose down 2>/dev/null
    fi
    
    sleep 2
    
    if ! check_jarvis_running; then
        echo -e "${GREEN}✅ JARVIS stopped successfully${NC}"
        send_notification "JARVIS AI Assistant" "JARVIS has been stopped" "dialog-information"
    else
        echo -e "${RED}❌ Some JARVIS processes may still be running${NC}"
    fi
}

# Main function
main() {
    case "${1:-web}" in
        "--web"|"web"|"")
            launch_web_interface
            ;;
        "--terminal"|"terminal")
            launch_terminal_mode
            ;;
        "--docker"|"docker")
            launch_docker_deployment
            ;;
        "--status"|"status")
            show_status
            ;;
        "--stop"|"stop")
            stop_jarvis
            ;;
        "--help"|"help")
            echo "JARVIS AI Assistant Desktop Launcher"
            echo "Usage: $0 [option]"
            echo ""
            echo "Options:"
            echo "  --web       Launch web interface (default)"
            echo "  --terminal  Launch terminal mode"
            echo "  --docker    Launch Docker deployment"
            echo "  --status    Show JARVIS status"
            echo "  --stop      Stop JARVIS"
            echo "  --help      Show this help"
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
